from functools import reduce
from pathlib import Path


class GenericDictNamingMixin:
    generic_name_map: dict = {}

    def to_non_generic(self, data: dict):
        data = data.copy()
        for g_, ng_ in self.generic_name_map.items():
            data[ng_] = data.pop(g_)
        return data


def drop_null_keys(data: dict):
    d_ = {}
    for k_, v_ in ((k__, v__) for k__, v__ in data.items() if v__ is not None):
        d_[k_] = v_
    return d_


def get_nested(data, loc):
    v_ = reduce(lambda d, key: d.get(key), loc.split("."), data)
    return v_


BASE_DIR = Path(__file__).parent.parent
