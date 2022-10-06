import argparse
from pathlib import Path

from utils.helpers import BASE_DIR

arg_parser = argparse.ArgumentParser(
    description="generate client subscription file"
)
arg_parser.add_argument(
    "--config_file",
    type=Path,
    default=BASE_DIR / "data/config.json",
    help="path to v2ray config.json file",
)
arg_parser.add_argument(
    "--domain_map_file",
    type=Path,
    default=BASE_DIR / "data/domain-map.json",
    help="path to domain-map.json file",
)
arg_parser.add_argument(
    "--save_dir",
    type=Path,
    help="dir to save subscription",
    default=BASE_DIR / "data/subs",
)
