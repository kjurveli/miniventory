from __future__ import annotations

import sys
from typing import Callable, TypeVar

from rich.console import Console
from rich.panel import Panel

T = TypeVar("T")

console = Console()


def clear_screen() -> None:
    console.clear()


def print_panel(title: str, subtitle: str = "") -> None:
    content = f"[bold]{title}[/]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/]"
    console.print(Panel(content, expand=False))


def print_filter_banner(active_tags: list[str]) -> None:
    if not active_tags:
        return
    tag_text = ", ".join(f"[cyan]{tag}[/]" for tag in active_tags)
    console.print(
        Panel(
            f"[bold yellow]Filter:[/] {tag_text}",
            expand=False,
            border_style="yellow",
        )
    )
    console.print()


def print_tags(tags: list[str]) -> str:
    if not tags:
        return "[dim](none)[/]"
    return ", ".join(f"[cyan]{tag}[/]" for tag in tags)


def print_success(message: str) -> None:
    console.print(f"\n[bold green]✓[/] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold red]✗[/] {message}")


def print_info(message: str) -> None:
    console.print(f"[dim]{message}[/]")


def print_numbered_list(
    items: list[str],
    *,
    back_label: str = "0. Back",
    show_back: bool = True,
) -> None:
    for index, item in enumerate(items, start=1):
        console.print(f"  [bold]{index}.[/] {item}")
    if show_back:
        console.print(f"  [dim]{back_label}[/]")


def pause(message: str = "Press Enter to continue...") -> None:
    try:
        console.input(f"\n[dim]{message}[/]")
    except (EOFError, KeyboardInterrupt):
        console.print()
        raise


def prompt_text(label: str, default: str = "") -> str:
    suffix = f" [dim][{default}][/]" if default else ""
    while True:
        try:
            value = console.input(f"{label}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            raise
        if value:
            return value
        if default:
            return default
        print_warning("Value is required.")


def prompt_optional_text(label: str, default: str = "") -> str:
    suffix = f" [dim][{default}][/]" if default else ""
    try:
        value = console.input(f"{label}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        console.print()
        raise
    return value or default


def prompt_tags(label: str = "Tags", current: list[str] | None = None) -> list[str]:
    current = current or []
    current_display = print_tags(current)
    console.print(f"{label} (comma-separated, current: {current_display})")
    try:
        raw = console.input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        console.print()
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
        suffix = f" [dim][{default_index}][/]" if default_index else ""
        try:
            selection = console.input(f"{label} ({options}){suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            raise
        if not selection and default_index:
            return choice_map[default_index]
        if selection in choice_map:
            return choice_map[selection]
        print_warning("Invalid choice. Enter a listed number.")


def prompt_yes_no(label: str, default: bool = False) -> bool:
    default_hint = "Y/n" if default else "y/N"
    while True:
        try:
            value = console.input(f"{label} [dim]({default_hint})[/]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            console.print()
            raise
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print_warning("Please answer yes or no.")


def select_from_list(
    title: str,
    items: list[T],
    label_fn: Callable[[T], str],
    *,
    allow_cancel: bool = True,
) -> T | None:
    if not items:
        print_warning(f"No {title.lower()} found.")
        return None

    console.print()
    print_panel(title)
    print_numbered_list(
        [label_fn(item) for item in items],
        show_back=allow_cancel,
        back_label="0. Cancel",
    )

    while True:
        try:
            selection = console.input("\nSelect: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            raise
        if allow_cancel and selection == "0":
            return None
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(items):
                return items[index]
        print_warning("Invalid selection.")


def run_menu(title: str, options: dict[str, Callable[[], None]]) -> None:
    while True:
        clear_screen()
        print_panel(title)
        keys = list(options.keys())
        print_numbered_list(keys)
        console.print()

        try:
            selection = console.input("Choice: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye!")
            sys.exit(0)

        if selection == "0":
            return
        if selection.isdigit():
            index = int(selection) - 1
            if 0 <= index < len(keys):
                options[keys[index]]()
                continue
        print_warning("Invalid choice.")
        pause()