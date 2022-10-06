import shutil
from pathlib import Path

from App.cli import arg_parser
from VTR import parser
from VTR.types import ParsedConfigType


def generate_client_subs(config: ParsedConfigType):
    subs = {}
    for proto, inb_all in config.items():
        for inb in inb_all:
            for cl_id, cl_verb, cl_ in inb.iter_clients():
                if cl_id not in subs.keys():
                    subs[cl_id] = {"verb": set(), "enc": []}
                subs[cl_id]["verb"].add(cl_verb)
                subs[cl_id]["enc"].append(inb.encode(cl_))
    return subs


def save(save_dir: Path, client_id, enc_data):
    dir_ = save_dir / client_id
    dir_.mkdir(parents=True, exist_ok=True)
    with (dir_ / "subscribe").open("w") as f_:
        for enc in enc_data:
            f_.write(enc)
            f_.write("\n")


def save_meta(save_dir: Path, subs_data):
    with (save_dir / "meta").open("w") as f_:
        for k_, v_ in subs_data.items():
            f_.write(f"{k_}:{v_['verb']}")
            f_.write("\n")


def clean(dir_path: Path):
    if dir_path.is_dir():
        shutil.rmtree(dir_path)


def run():
    args = arg_parser.parse_args()
    inbound_data = parser.parse_config(args.config_file, args.domain_map_file)
    subs = generate_client_subs(inbound_data)
    clean(args.save_dir)
    for k_, v_ in subs.items():
        save(args.save_dir, k_, v_["enc"])
    save_meta(args.save_dir, subs)


if __name__ == "__main__":
    run()
