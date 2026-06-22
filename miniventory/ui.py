from __future__ import annotations

import sys
from typing import Callable, TypeVar

T = TypeVar("T")


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def pause(message: str = "Press Enter to continue...") -> None:
    try:
        input(message)
    except (EOFError, KeyboardInterrupt):
        print()
        raise


def prompt_text(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            value = input(f"{label}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise
        if value:
            return value
        if default:
            return default
        print("  Value is required.")


def prompt_optional_text(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{label}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise
    return value or default


def prompt_tags(label: str = "Tags", current: list[str] | None = None) -> list[str]:
    current = current or []
    current_display = ", ".join(current) if current else "(none)"
    print(f"{label} (comma-separated, current: {current_display})")
    try:
        raw = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise
    if not raw:
        return list(current)
    return [part.strip() for part in raw.split(",") if part.strip()]


def prompt_choice(label: str, choices: list[str], default: str | None = None) -> str:
    choice_map = {str(index + 1): value for index, value in enumerate(choices)}
    options = ", ".join(f"{index + 1}. {value}" for index, value in enumerate(choices))
    default_index = None
    if default in choices:
        default_index = str(choices.index(default) + 1)

    while True:
        suffix = f" [{default_index}]" if default_index else ""
        try:
            selection = input(f"{label} ({options}){suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise
        if not selection and default_index:
            return choice_map[default_index]
        if selection in choice_map:
            return choice_map[selection]
        print("  Invalid choice. Enter a listed number.")


def prompt_yes_no(label: str, default: bool = False) -> bool:
    default_hint = "Y/n" if default else "y/N"
    while True:
        try:
            value = input(f"{label} ({default_hint}): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raise
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("  Please answer yes or no.")


def select_from_list(
    title: str,
    items: list[T],
    label_fn: Callable[[T], str],
    *,
    allow_cancel: bool = True,
) -> T | None:
    if not items:
        print(f"No {title.lower()} found.")
        return None

    print(f"\n{title}")
    print("-" * len(title))
    for index, item in enumerate(items, start=1):
        print(f"  {index}. {label_fn(item)}")
    if allow_cancel:
        print("  0. Cancel")

    while True:
        try:
            selection = input("Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise
        if allow_cancel and selection == "0":
            return None
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(items):
                return items[index]
        print("  Invalid selection.")


def run_menu(title: str, options: dict[str, Callable[[], None]]) -> None:
    while True:
        clear_screen()
        print(title)
        print("=" * len(title))
        keys = list(options.keys())
        for index, key in enumerate(keys, start=1):
            print(f"  {index}. {key}")
        print("  0. Back")

        try:
            selection = input("\nChoice: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            sys.exit(0)

        if selection == "0":
            return
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(keys):
                options[keys[index]]()
                continue
        print("Invalid choice.")
        pause()