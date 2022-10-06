import json
from pathlib import Path

from yarl import URL

from VTR.types import (
    TrojanInboundObj,
    VmessInboundObj,
    ParsedConfigType,
    DomainMapType,
    IPv4Address,
    DomainDataType,
)


def load_domain_map(domain_map_path: Path) -> DomainMapType:
    with domain_map_path.open() as f_:
        data: DomainMapType = json.load(f_)
    for k_, v_ in data.items():
        for c__, v__ in enumerate(v_):
            # ...... target typing
            _target: str = v__["target"]
            if _target.startswith("http"):
                v__["target"] = URL(_target)
            else:
                v__["target"] = IPv4Address(_target)
            # ...... sni typing
            _sni = v__.get("sni", None)
            v__["sni"] = _sni
            # ...... tag typing
            _tag = v__.get("tag", None)
            postfix = ""
            if c__ > 0 and _tag is None:
                postfix = f"__{c__}"
            v__["tag"] = (_tag or k_) + postfix
    return data


def parse_config(conf_path: Path, domain_map_path: Path) -> ParsedConfigType:
    with conf_path.open() as f_:
        conf = json.load(f_)
    inbounds_vmess = []
    inbounds_trojan = []

    outbounds_all = conf["inbounds"]
    domain_map = load_domain_map(domain_map_path)
    for i_ in outbounds_all:
        tag = i_["tag"]
        if tag not in domain_map.keys():
            continue
        proto = i_["protocol"]
        if proto == "trojan":
            inbound_cls = TrojanInboundObj
            inbound_list = inbounds_trojan
        elif proto == "vmess":
            inbound_cls = VmessInboundObj
            inbound_list = inbounds_vmess
        else:
            continue
        for dm__ in domain_map[tag]:
            dm__: DomainDataType
            inbound_list.append(
                inbound_cls(
                    config=i_,
                    target=dm__["target"],
                    tag=dm__["tag"],
                    sni=dm__["sni"],
                )
            )
    return {"vmess": inbounds_vmess, "trojan": inbounds_trojan}
