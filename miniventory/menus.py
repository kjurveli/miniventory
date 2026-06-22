from __future__ import annotations

from miniventory import display, ui
from miniventory.models import Army, Miniature, PaintStatus, Unit, normalize_tags
from miniventory.store import CollectionStore


class MenuContext:
    def __init__(self, store: CollectionStore) -> None:
        self.store = store
        self.active_tags: list[str] = []


def format_army(store: CollectionStore, army: Army) -> str:
    unit_count = len(store.list_units(army_id=army.id))
    miniature_count = sum(
        len(store.list_miniatures(unit_id=unit.id))
        for unit in store.list_units(army_id=army.id)
    )
    tags = ", ".join(army.tags) if army.tags else "no tags"
    faction = army.faction or "unspecified faction"
    return (
        f"{army.name} ({faction}) — "
        f"{unit_count} unit(s), {miniature_count} miniature(s) [{tags}]"
    )


def format_unit(store: CollectionStore, unit: Unit) -> str:
    army = store.get_army(unit.army_id)
    army_name = army.name if army else "unknown army"
    miniature_count = len(store.list_miniatures(unit_id=unit.id))
    tags = ", ".join(unit.tags) if unit.tags else "no tags"
    return f"{unit.name} — {army_name}, {miniature_count} miniature(s) [{tags}]"


def format_miniature(store: CollectionStore, miniature: Miniature) -> str:
    unit = store.get_unit(miniature.unit_id)
    unit_name = unit.name if unit else "unknown unit"
    tags = ", ".join(miniature.tags) if miniature.tags else "no tags"
    return f"{miniature.name} — {unit_name}, {miniature.status.value} [{tags}]"


def show_collection_overview(ctx: MenuContext) -> None:
    ui.clear_screen()
    ui.print_filter_banner(ctx.active_tags)
    ui.console.print(display.render_overview_panel(ctx.store, ctx.active_tags))
    ui.pause()


# --- Army menus ---


def list_armies(ctx: MenuContext) -> None:
    ui.clear_screen()
    ui.print_filter_banner(ctx.active_tags)
    armies = ctx.store.list_armies(tags=ctx.active_tags or None)
    if not armies:
        ui.print_info("No armies yet.")
    else:
        ui.console.print(display.render_armies_table(ctx.store, armies))
    ui.pause()


def add_army(ctx: MenuContext) -> None:
    ui.clear_screen()
    ui.print_panel("Add Army")
    name = ui.prompt_text("Name")
    faction = ui.prompt_optional_text("Faction")
    tags = ui.prompt_tags(current=[])
    notes = ui.prompt_optional_text("Notes")
    army = Army(name=name, faction=faction, tags=tags, notes=notes)
    ctx.store.add_army(army)
    ui.print_success(f"Added army: {army.name}")
    ui.pause()


def edit_army(ctx: MenuContext) -> None:
    armies = ctx.store.list_armies(tags=ctx.active_tags or None)
    army = ui.select_from_list("Select army to edit", armies, lambda item: item.name)
    if army is None:
        return

    ui.clear_screen()
    ui.print_panel(f"Edit Army: {army.name}")
    army.name = ui.prompt_text("Name", army.name)
    army.faction = ui.prompt_optional_text("Faction", army.faction)
    army.tags = ui.prompt_tags(current=army.tags)
    army.notes = ui.prompt_optional_text("Notes", army.notes)
    ctx.store.update_army(army)
    ui.print_success("Army updated.")
    ui.pause()


def delete_army(ctx: MenuContext) -> None:
    armies = ctx.store.list_armies(tags=ctx.active_tags or None)
    army = ui.select_from_list("Select army to delete", armies, lambda item: item.name)
    if army is None:
        return
    if ui.prompt_yes_no(f"Delete '{army.name}' and all its units/miniatures?", False):
        ctx.store.delete_army(army.id)
        ui.print_success("Army deleted.")
    else:
        ui.print_warning("Cancelled.")
    ui.pause()


def armies_menu(ctx: MenuContext) -> None:
    ui.run_menu(
        "Armies",
        {
            "List armies": lambda: list_armies(ctx),
            "Add army": lambda: add_army(ctx),
            "Edit army": lambda: edit_army(ctx),
            "Delete army": lambda: delete_army(ctx),
        },
    )


# --- Unit menus ---


def list_units(ctx: MenuContext) -> None:
    ui.clear_screen()
    ui.print_filter_banner(ctx.active_tags)
    units = ctx.store.list_units(tags=ctx.active_tags or None)
    if not units:
        ui.print_info("No units yet.")
    else:
        ui.console.print(display.render_units_table(ctx.store, units))
    ui.pause()


def add_unit(ctx: MenuContext) -> None:
    armies = ctx.store.collection.armies
    army = ui.select_from_list("Select army", armies, lambda item: item.name)
    if army is None:
        return

    ui.clear_screen()
    ui.print_panel(f"Add Unit to {army.name}")
    name = ui.prompt_text("Name")
    tags = ui.prompt_tags(current=[])
    notes = ui.prompt_optional_text("Notes")
    unit = Unit(name=name, army_id=army.id, tags=tags, notes=notes)
    ctx.store.add_unit(unit)
    ui.print_success(f"Added unit: {unit.name}")
    ui.pause()


def edit_unit(ctx: MenuContext) -> None:
    units = ctx.store.list_units(tags=ctx.active_tags or None)
    unit = ui.select_from_list(
        "Select unit to edit", units, lambda item: format_unit(ctx.store, item)
    )
    if unit is None:
        return

    ui.clear_screen()
    ui.print_panel(f"Edit Unit: {unit.name}")
    unit.name = ui.prompt_text("Name", unit.name)

    armies = ctx.store.collection.armies
    current_army = ctx.store.get_army(unit.army_id)
    if armies:
        ui.print_info(f"Current army: {current_army.name if current_army else 'unknown'}")
        if ui.prompt_yes_no("Change army?", False):
            army = ui.select_from_list("Select army", armies, lambda item: item.name)
            if army is not None:
                unit.army_id = army.id

    unit.tags = ui.prompt_tags(current=unit.tags)
    unit.notes = ui.prompt_optional_text("Notes", unit.notes)
    ctx.store.update_unit(unit)
    ui.print_success("Unit updated.")
    ui.pause()


def delete_unit(ctx: MenuContext) -> None:
    units = ctx.store.list_units(tags=ctx.active_tags or None)
    unit = ui.select_from_list(
        "Select unit to delete", units, lambda item: format_unit(ctx.store, item)
    )
    if unit is None:
        return
    if ui.prompt_yes_no(f"Delete '{unit.name}' and its miniatures?", False):
        ctx.store.delete_unit(unit.id)
        ui.print_success("Unit deleted.")
    else:
        ui.print_warning("Cancelled.")
    ui.pause()


def units_menu(ctx: MenuContext) -> None:
    ui.run_menu(
        "Units",
        {
            "List units": lambda: list_units(ctx),
            "Add unit": lambda: add_unit(ctx),
            "Edit unit": lambda: edit_unit(ctx),
            "Delete unit": lambda: delete_unit(ctx),
        },
    )


# --- Miniature menus ---


def list_miniatures(ctx: MenuContext) -> None:
    ui.clear_screen()
    ui.print_filter_banner(ctx.active_tags)
    miniatures = ctx.store.list_miniatures(tags=ctx.active_tags or None)
    if not miniatures:
        ui.print_info("No miniatures yet.")
    else:
        ui.console.print(display.render_miniatures_table(ctx.store, miniatures))
    ui.pause()


def add_miniature(ctx: MenuContext) -> None:
    units = ctx.store.collection.units
    unit = ui.select_from_list(
        "Select unit", units, lambda item: format_unit(ctx.store, item)
    )
    if unit is None:
        return

    ui.clear_screen()
    ui.print_panel(f"Add Miniature to {unit.name}")
    name = ui.prompt_text("Name")
    status = ui.prompt_choice("Status", PaintStatus.choices(), PaintStatus.UNBUILT.value)
    tags = ui.prompt_tags(current=[])
    notes = ui.prompt_optional_text("Notes")
    miniature = Miniature(
        name=name,
        unit_id=unit.id,
        tags=tags,
        status=PaintStatus(status),
        notes=notes,
    )
    ctx.store.add_miniature(miniature)
    ui.print_success(f"Added miniature: {miniature.name}")
    ui.pause()


def edit_miniature(ctx: MenuContext) -> None:
    miniatures = ctx.store.list_miniatures(tags=ctx.active_tags or None)
    miniature = ui.select_from_list(
        "Select miniature to edit",
        miniatures,
        lambda item: format_miniature(ctx.store, item),
    )
    if miniature is None:
        return

    ui.clear_screen()
    ui.print_panel(f"Edit Miniature: {miniature.name}")
    miniature.name = ui.prompt_text("Name", miniature.name)

    units = ctx.store.collection.units
    current_unit = ctx.store.get_unit(miniature.unit_id)
    if units:
        ui.print_info(f"Current unit: {current_unit.name if current_unit else 'unknown'}")
        if ui.prompt_yes_no("Change unit?", False):
            unit = ui.select_from_list(
                "Select unit", units, lambda item: format_unit(ctx.store, item)
            )
            if unit is not None:
                miniature.unit_id = unit.id

    miniature.status = PaintStatus(
        ui.prompt_choice(
            "Status",
            PaintStatus.choices(),
            miniature.status.value,
        )
    )
    miniature.tags = ui.prompt_tags(current=miniature.tags)
    miniature.notes = ui.prompt_optional_text("Notes", miniature.notes)
    ctx.store.update_miniature(miniature)
    ui.print_success("Miniature updated.")
    ui.pause()


def delete_miniature(ctx: MenuContext) -> None:
    miniatures = ctx.store.list_miniatures(tags=ctx.active_tags or None)
    miniature = ui.select_from_list(
        "Select miniature to delete",
        miniatures,
        lambda item: format_miniature(ctx.store, item),
    )
    if miniature is None:
        return
    if ui.prompt_yes_no(f"Delete '{miniature.name}'?", False):
        ctx.store.delete_miniature(miniature.id)
        ui.print_success("Miniature deleted.")
    else:
        ui.print_warning("Cancelled.")
    ui.pause()


def miniatures_menu(ctx: MenuContext) -> None:
    ui.run_menu(
        "Miniatures",
        {
            "List miniatures": lambda: list_miniatures(ctx),
            "Add miniature": lambda: add_miniature(ctx),
            "Edit miniature": lambda: edit_miniature(ctx),
            "Delete miniature": lambda: delete_miniature(ctx),
        },
    )


# --- Tag filtering ---


def set_tag_filter(ctx: MenuContext) -> None:
    ui.clear_screen()
    ui.print_panel(
        "Set Tag Filter",
        "Enter tags to filter lists. Leave blank to clear.",
    )
    tags = ui.prompt_tags(current=ctx.active_tags)
    ctx.active_tags = normalize_tags(tags)
    if ctx.active_tags:
        ui.print_success(f"Filter set: {', '.join(ctx.active_tags)}")
    else:
        ui.print_info("Tag filter cleared.")
    ui.pause()


def browse_by_tags(ctx: MenuContext) -> None:
    ui.clear_screen()
    all_tags = ctx.store.collection.all_tags()
    if not all_tags:
        ui.print_panel("Browse by Tags")
        ui.print_info("No tags in collection yet.")
        ui.pause()
        return

    ui.print_panel("Browse by Tags", "Select a tag or enter comma-separated tags")
    ui.print_numbered_list(all_tags, back_label="0. Cancel")

    try:
        selection = ui.console.input(
            "\nSelect a tag (or enter tags comma-separated): "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        ui.console.print()
        raise

    if selection == "0":
        return

    if selection.isdigit():
        index = int(selection) - 1
        if 0 <= index < len(all_tags):
            tags = [all_tags[index]]
        else:
            ui.print_warning("Invalid selection.")
            ui.pause()
            return
    else:
        tags = [part.strip() for part in selection.split(",") if part.strip()]

    results = ctx.store.filter_by_tags(tags)
    ui.clear_screen()
    display.render_tag_results(ctx.store, results, normalize_tags(tags))
    ui.pause()


def tags_menu(ctx: MenuContext) -> None:
    ui.run_menu(
        "Tags",
        {
            "Set active filter": lambda: set_tag_filter(ctx),
            "Browse by tag": lambda: browse_by_tags(ctx),
            "Clear active filter": lambda: _clear_tag_filter(ctx),
        },
    )


def _clear_tag_filter(ctx: MenuContext) -> None:
    ctx.active_tags = []
    ui.print_info("Tag filter cleared.")
    ui.pause()


def main_menu(ctx: MenuContext) -> None:
    while True:
        ui.clear_screen()
        ui.print_panel(
            "Miniventory",
            "Warhammer Miniature Tracker",
        )
        ui.print_filter_banner(ctx.active_tags)
        ui.print_info(f"Data file: {ctx.store.path}")
        ui.console.print(
            f"Collection: [bold]{len(ctx.store.collection.armies)}[/] armies, "
            f"[bold]{len(ctx.store.collection.units)}[/] units, "
            f"[bold]{len(ctx.store.collection.miniatures)}[/] miniatures"
        )
        ui.console.print()
        ui.print_numbered_list(
            [
                "Collection overview",
                "Armies",
                "Units",
                "Miniatures",
                "Tags",
            ],
            back_label="0. Exit",
        )

        try:
            choice = ui.console.input("\nChoice: ").strip()
        except (EOFError, KeyboardInterrupt):
            ui.console.print("\nGoodbye!")
            return

        actions = {
            "1": lambda: show_collection_overview(ctx),
            "2": lambda: armies_menu(ctx),
            "3": lambda: units_menu(ctx),
            "4": lambda: miniatures_menu(ctx),
            "5": lambda: tags_menu(ctx),
        }
        if choice == "0":
            ui.console.print("Goodbye!")
            return
        action = actions.get(choice)
        if action:
            action()
        else:
            ui.print_warning("Invalid choice.")
            ui.pause()