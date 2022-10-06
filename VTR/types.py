import base64
import json
from abc import abstractmethod
from typing import TypedDict, List, TypeVar, Dict, Optional, Union

from yarl import URL

# ===========================================================================================
# auxiliary
# ===========================================================================================
from utils.helpers import get_nested, drop_null_keys, GenericDictNamingMixin


class IPv4Address:
    DEFAULT_PORT = 80

    def __init__(self, ip_address: str):
        self.scheme = "http://"
        ip_address = ip_address.split(":")
        self.host = ip_address[0]
        self.port = (
            ip_address[1] if len(ip_address) == 2 else self.DEFAULT_PORT
        )


IPOrDomainType = Union[URL, IPv4Address]


class DomainDataType(TypedDict):
    target: IPOrDomainType
    sni: Optional[str]
    tag: Optional[str]


DomainMapType = TypeVar("DomainMapType", bound=Dict[str, List[DomainDataType]])


# ===========================================================================================
# transport
# ===========================================================================================
class BaseTransportObj(GenericDictNamingMixin):
    key: str
    generic_name_map = {"net": "type"}

    def __init__(self, transport_data: dict):
        self.transport_data = transport_data
        self.transport_specific_data = self.transport_data.get(
            f"{self.key}Settings", {}
        )
        self.host = None
        self.path = None

    def as_dict(self, generic_naming=True):
        d_ = dict(host=self.host, path=self.path, net=self.key)
        if not generic_naming:
            d_ = self.to_non_generic(d_)
        return drop_null_keys(d_)


class WSTransportObj(BaseTransportObj):
    key = "ws"

    def __init__(self, transport_data: dict):
        super().__init__(transport_data)
        trans = self.transport_specific_data
        self.path = trans.get("path", None)
        self.host = trans.get("headers", {}).get("Host", None)


class GRPCTransportObj(BaseTransportObj):
    key = "grpc"
    generic_name_map = {
        **BaseTransportObj.generic_name_map,
        "path": "serviceName",
    }

    def __init__(self, transport_data: dict):
        super().__init__(transport_data)
        trans = self.transport_specific_data
        self.path = trans.get("serviceName", None)


class TLSObj(GenericDictNamingMixin):
    generic_name_map = {"tls": "security"}

    def __init__(self, sni: str = None):
        self.sni = sni
        self.tls = "tls" if sni else None

    def as_dict(self, generic_naming=True):
        d_ = dict(sni=self.sni, tls=self.tls)
        if not generic_naming:
            d_ = self.to_non_generic(d_)
        return drop_null_keys(d_)


def get_transport_obj(transport_data: dict) -> BaseTransportObj:
    key = transport_data["network"]
    return {"ws": WSTransportObj, "grpc": GRPCTransportObj}[key](
        transport_data
    )


# ===========================================================================================
# Inbounds
# ===========================================================================================
class HostObj:
    def __init__(self, target: IPOrDomainType):
        self.host = target.host
        self.port = target.port


class BaseInboundObj:
    client_list_loc: str
    client_list_loc__uid: str
    client_list_loc__verb: str
    scheme: str

    def __init__(
        self,
        config: dict,
        target: IPOrDomainType,
        tag: str = None,
        sni: str = None,
    ):
        self.config = config
        self.tag = tag
        self.target = HostObj(target)
        self.transport_obj = get_transport_obj(config["streamSettings"])
        sni = sni or (
            target.host
            if (isinstance(target, URL) and target.scheme == "https")
            else None
        )
        self.tls_obj = TLSObj(sni)

    def iter_clients(self):
        clients = get_nested(self.config, self.client_list_loc)
        for cl_ in clients:
            yield get_nested(cl_, self.client_list_loc__uid), get_nested(
                cl_, self.client_list_loc__verb
            ), cl_

    @abstractmethod
    def proto_as_dict(self, user_data: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def encode(self, user_data: dict):
        raise NotImplementedError


class TrojanInboundObj(BaseInboundObj):
    client_list_loc = "settings.clients"
    client_list_loc__uid = "password"
    client_list_loc__verb = "email"
    scheme = "trojan"

    def proto_as_dict(self, user_data: dict):
        return dict(password=user_data["password"])

    def encode(self, user_data: dict):
        d_ = self.proto_as_dict(user_data)
        enc = URL.build(
            scheme=self.scheme,
            user=d_["password"],
            host=self.target.host,
            port=self.target.port,
        )
        q_ = {
            **self.transport_obj.as_dict(generic_naming=False),
            **self.tls_obj.as_dict(generic_naming=False),
        }
        enc = enc % q_
        enc = f"{enc}#{self.tag}"
        return enc


class VmessInboundObj(BaseInboundObj):
    client_list_loc = "settings.clients"
    client_list_loc__uid = "id"
    client_list_loc__verb = "email"
    scheme = "vmess"

    def proto_as_dict(self, user_data: dict):
        return dict(id=user_data["id"])

    def encode(self, user_data: dict):
        d_ = self.proto_as_dict(user_data)
        enc = dict(
            add=self.target.host,
            port=self.target.port,
            id=d_["id"],
            ps=self.tag,
            v="2",
            **self.transport_obj.as_dict(),
            **self.tls_obj.as_dict(),
        )
        enc = json.dumps(enc).encode()
        return f"{self.scheme}://{base64.b64encode(enc).decode()}"


class ParsedConfigType(TypedDict):
    vmess: List[VmessInboundObj]
    trojan: List[TrojanInboundObj]
