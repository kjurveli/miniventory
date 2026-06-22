from __future__ import annotations

import argparse
from pathlib import Path

from miniventory.menus import MenuContext, main_menu
from miniventory.store import CollectionStore


def default_data_path() -> Path:
    return Path.home() / ".miniventory" / "collection.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track your Warhammer miniatures from the terminal."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=default_data_path(),
        help="Path to the JSON collection file (default: ~/.miniventory/collection.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = CollectionStore(args.data)
    store.load()
    ctx = MenuContext(store)
    main_menu(ctx)


if __name__ == "__main__":
    main()