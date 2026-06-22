from __future__ import annotations

from typing import Any

from rich.panel import Panel
from rich.table import Table

from miniventory.models import Army, Miniature, PaintStatus, Unit
from miniventory.store import CollectionStore
from miniventory import ui


STATUS_STYLES: dict[PaintStatus, str] = {
    PaintStatus.UNBUILT: "dim",
    PaintStatus.ASSEMBLED: "yellow",
    PaintStatus.PRIMED: "blue",
    PaintStatus.PAINTED: "green",
    PaintStatus.BASED: "bold green",
}


def status_label(status: PaintStatus) -> str:
    style = STATUS_STYLES.get(status, "")
    return f"[{style}]{status.value}[/]"


def _base_table(title: str) -> Table:
    table = Table(title=title, show_header=True, header_style="bold", expand=True)
    table.add_column("#", style="dim", width=4, justify="right")
    return table


def render_armies_table(store: CollectionStore, armies: list[Army]) -> Table:
    table = _base_table("Armies")
    table.add_column("Name", style="bold")
    table.add_column("Faction")
    table.add_column("Units", justify="right")
    table.add_column("Miniatures", justify="right")
    table.add_column("Tags")

    for index, army in enumerate(armies, start=1):
        unit_count = len(store.list_units(army_id=army.id))
        miniature_count = sum(
            len(store.list_miniatures(unit_id=unit.id))
            for unit in store.list_units(army_id=army.id)
        )
        table.add_row(
            str(index),
            army.name,
            army.faction or "[dim]—[/]",
            str(unit_count),
            str(miniature_count),
            ui.print_tags(army.tags),
        )
    return table


def render_units_table(store: CollectionStore, units: list[Unit]) -> Table:
    table = _base_table("Units")
    table.add_column("Name", style="bold")
    table.add_column("Army")
    table.add_column("Miniatures", justify="right")
    table.add_column("Tags")

    for index, unit in enumerate(units, start=1):
        army = store.get_army(unit.army_id)
        army_name = army.name if army else "[dim]unknown[/]"
        miniature_count = len(store.list_miniatures(unit_id=unit.id))
        table.add_row(
            str(index),
            unit.name,
            army_name,
            str(miniature_count),
            ui.print_tags(unit.tags),
        )
    return table


def render_miniatures_table(
    store: CollectionStore, miniatures: list[Miniature]
) -> Table:
    table = _base_table("Miniatures")
    table.add_column("Name", style="bold")
    table.add_column("Unit")
    table.add_column("Status")
    table.add_column("Tags")

    for index, miniature in enumerate(miniatures, start=1):
        unit = store.get_unit(miniature.unit_id)
        unit_name = unit.name if unit else "[dim]unknown[/]"
        table.add_row(
            str(index),
            miniature.name,
            unit_name,
            status_label(miniature.status),
            ui.print_tags(miniature.tags),
        )
    return table


def render_overview_panel(
    store: CollectionStore,
    active_tags: list[str] | None = None,
) -> Panel:
    collection = store.collection
    lines = [
        f"[bold]Armies:[/] {len(collection.armies)}",
        f"[bold]Units:[/] {len(collection.units)}",
        f"[bold]Miniatures:[/] {len(collection.miniatures)}",
        f"[bold]Data file:[/] [dim]{store.path}[/]",
        f"[bold]Tags:[/] {ui.print_tags(collection.all_tags())}",
    ]

    if active_tags:
        results = store.filter_by_tags(active_tags)
        lines.append("")
        lines.append("[bold yellow]Active filter results[/]")
        lines.append(f"  Armies: {len(results['armies'])}")
        lines.append(f"  Units: {len(results['units'])}")
        lines.append(f"  Miniatures: {len(results['miniatures'])}")

    return Panel(
        "\n".join(lines),
        title="Collection Overview",
        expand=False,
    )


def render_tag_results(
    store: CollectionStore,
    results: dict[str, list[Any]],
    tags: list[str],
) -> None:
    tag_display = ", ".join(f"[cyan]{tag}[/]" for tag in tags)
    ui.console.print()
    ui.console.print(
        Panel(
            f"Results for [bold]{tag_display}[/]",
            expand=False,
            border_style="cyan",
        )
    )

    sections = [
        ("Armies", results["armies"], render_armies_table),
        ("Units", results["units"], render_units_table),
        ("Miniatures", results["miniatures"], render_miniatures_table),
    ]

    for title, items, render_fn in sections:
        ui.console.print()
        if items:
            ui.console.print(render_fn(store, items))
        else:
            ui.console.print(f"[bold]{title}:[/] [dim](none)[/]")