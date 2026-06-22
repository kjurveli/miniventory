import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

from miniventory import ui
from miniventory.menus import (
    MenuContext,
    _clear_tag_filter,
    add_army,
    add_miniature,
    add_unit,
    armies_menu,
    browse_by_tags,
    delete_army,
    delete_miniature,
    delete_unit,
    edit_army,
    edit_miniature,
    edit_unit,
    list_armies,
    list_miniatures,
    list_units,
    main_menu,
    set_tag_filter,
    show_collection_overview,
    tags_menu,
)
from miniventory.models import Army, Miniature, PaintStatus, Unit
from miniventory.store import CollectionStore


class MenuIntegrationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "collection.json"
        self.store = CollectionStore(self.path)
        self.ctx = MenuContext(self.store)
        self.input_queue: list[str] = []

        self._original_console = ui.console
        ui.console = Console(file=io.StringIO(), force_terminal=True, width=120)
        ui.console.input = self._dequeue_input  # type: ignore[method-assign]

        self._pause_patch = patch.object(ui, "pause")
        self._pause_patch.start()
        self._clear_patch = patch.object(ui, "clear_screen")
        self._clear_patch.start()

    def tearDown(self) -> None:
        self._clear_patch.stop()
        self._pause_patch.stop()
        ui.console = self._original_console
        self.temp_dir.cleanup()

    def _dequeue_input(self, _prompt: str = "") -> str:
        if not self.input_queue:
            self.fail(f"Unexpected input prompt: {_prompt!r}")
        return self.input_queue.pop(0)

    def queue(self, *inputs: str) -> None:
        self.input_queue.extend(inputs)

    def seed_army_unit_miniature(self) -> tuple[Army, Unit, Miniature]:
        army = Army(name="Ultramarines", faction="Space Marines", tags=["loyalist"])
        self.store.add_army(army)
        unit = Unit(name="Intercessors", army_id=army.id, tags=["troops"])
        self.store.add_unit(unit)
        miniature = Miniature(
            name="Sergeant",
            unit_id=unit.id,
            status=PaintStatus.PAINTED,
            tags=["character"],
        )
        self.store.add_miniature(miniature)
        return army, unit, miniature


class ArmyMenuIntegrationTests(MenuIntegrationTestCase):
    def test_add_army_full_flow(self) -> None:
        self.queue("Ultramarines", "Space Marines", "loyalist", "First company")
        add_army(self.ctx)

        self.assertEqual(len(self.store.collection.armies), 1)
        army = self.store.collection.armies[0]
        self.assertEqual(army.name, "Ultramarines")
        self.assertEqual(army.faction, "Space Marines")
        self.assertEqual(army.tags, ["loyalist"])
        self.assertEqual(army.notes, "First company")

    def test_add_army_retries_when_name_empty(self) -> None:
        self.queue("", "Orks", "", "", "")
        add_army(self.ctx)
        self.assertEqual(self.store.collection.armies[0].name, "Orks")

    def test_edit_army_updates_fields(self) -> None:
        army = Army(name="Old Name", faction="Old", tags=["old"], notes="old notes")
        self.store.add_army(army)
        self.queue("1", "New Name", "New Faction", "new-tag", "new notes")
        edit_army(self.ctx)

        updated = self.store.get_army(army.id)
        assert updated is not None
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(updated.faction, "New Faction")
        self.assertEqual(updated.tags, ["new-tag"])
        self.assertEqual(updated.notes, "new notes")

    def test_edit_army_cancelled(self) -> None:
        self.store.add_army(Army(name="Stay"))
        self.queue("0")
        edit_army(self.ctx)
        self.assertEqual(self.store.collection.armies[0].name, "Stay")

    def test_delete_army_confirmed(self) -> None:
        army, unit, _ = self.seed_army_unit_miniature()
        self.queue("1", "y")
        delete_army(self.ctx)
        self.assertIsNone(self.store.get_army(army.id))
        self.assertIsNone(self.store.get_unit(unit.id))

    def test_delete_army_cancelled(self) -> None:
        self.store.add_army(Army(name="Keep"))
        self.queue("1", "n")
        delete_army(self.ctx)
        self.assertEqual(len(self.store.collection.armies), 1)

    def test_delete_army_no_selection(self) -> None:
        self.store.add_army(Army(name="Keep"))
        self.queue("0")
        delete_army(self.ctx)
        self.assertEqual(len(self.store.collection.armies), 1)

    def test_list_armies_empty(self) -> None:
        list_armies(self.ctx)
        self.assertEqual(self.store.collection.armies, [])

    def test_list_armies_with_data(self) -> None:
        self.seed_army_unit_miniature()
        list_armies(self.ctx)
        self.assertEqual(len(self.store.collection.armies), 1)

    def test_armies_menu_add_then_back(self) -> None:
        self.queue(
            "2",  # Add army
            "Necrons",
            "Xenos",
            "metal",
            "",
            "0",  # Back
        )
        armies_menu(self.ctx)
        self.assertEqual(self.store.collection.armies[0].name, "Necrons")


class UnitMenuIntegrationTests(MenuIntegrationTestCase):
    def test_add_unit_full_flow(self) -> None:
        self.store.add_army(Army(name="Ultramarines"))
        self.queue("1", "Intercessors", "troops", "Battleline")
        add_unit(self.ctx)

        self.assertEqual(len(self.store.collection.units), 1)
        unit = self.store.collection.units[0]
        self.assertEqual(unit.name, "Intercessors")
        self.assertEqual(unit.tags, ["troops"])
        self.assertEqual(unit.notes, "Battleline")

    def test_add_unit_cancelled_when_no_army_selected(self) -> None:
        self.store.add_army(Army(name="Solo"))
        self.queue("0")
        add_unit(self.ctx)
        self.assertEqual(self.store.collection.units, [])

    def test_add_unit_skipped_when_no_armies_exist(self) -> None:
        add_unit(self.ctx)
        self.assertEqual(self.store.collection.units, [])

    def test_edit_unit_without_changing_army(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("1", "Assault Intercessors", "n", "fast", "Updated notes")
        edit_unit(self.ctx)

        unit = self.store.collection.units[0]
        self.assertEqual(unit.name, "Assault Intercessors")
        self.assertEqual(unit.tags, ["fast"])

    def test_edit_unit_changes_army(self) -> None:
        army_a = Army(name="Army A")
        army_b = Army(name="Army B")
        self.store.add_army(army_a)
        self.store.add_army(army_b)
        self.store.add_unit(Unit(name="Mobile", army_id=army_a.id))
        self.queue("1", "Mobile", "y", "2", "", "")
        edit_unit(self.ctx)

        unit = self.store.collection.units[0]
        self.assertEqual(unit.army_id, army_b.id)

    def test_delete_unit_confirmed(self) -> None:
        _, unit, miniature = self.seed_army_unit_miniature()
        self.queue("1", "y")
        delete_unit(self.ctx)
        self.assertIsNone(self.store.get_unit(unit.id))
        self.assertIsNone(self.store.get_miniature(miniature.id))

    def test_delete_unit_cancelled(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("1", "n")
        delete_unit(self.ctx)
        self.assertEqual(len(self.store.collection.units), 1)

    def test_list_units_empty(self) -> None:
        list_units(self.ctx)
        self.assertEqual(self.store.collection.units, [])

    def test_list_units_with_data(self) -> None:
        self.seed_army_unit_miniature()
        list_units(self.ctx)
        self.assertEqual(len(self.store.collection.units), 1)

    def test_edit_unit_cancelled(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("0")
        edit_unit(self.ctx)
        self.assertEqual(self.store.collection.units[0].name, "Intercessors")

    def test_delete_unit_no_selection(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("0")
        delete_unit(self.ctx)
        self.assertEqual(len(self.store.collection.units), 1)


class MiniatureMenuIntegrationTests(MenuIntegrationTestCase):
    def test_add_miniature_full_flow(self) -> None:
        army = Army(name="Ultramarines")
        self.store.add_army(army)
        self.store.add_unit(Unit(name="Intercessors", army_id=army.id))
        self.queue("1", "Marine 1", "4", "batch-1", "Note")
        add_miniature(self.ctx)

        miniature = self.store.collection.miniatures[0]
        self.assertEqual(miniature.name, "Marine 1")
        self.assertEqual(miniature.status, PaintStatus.PAINTED)
        self.assertEqual(miniature.tags, ["batch-1"])

    def test_add_miniature_cancelled(self) -> None:
        army = Army(name="Ultramarines")
        self.store.add_army(army)
        self.store.add_unit(Unit(name="Intercessors", army_id=army.id))
        self.queue("0")
        add_miniature(self.ctx)
        self.assertEqual(self.store.collection.miniatures, [])

    def test_edit_miniature_changes_unit_and_status(self) -> None:
        army = Army(name="Ultramarines")
        self.store.add_army(army)
        unit_a = Unit(name="Unit A", army_id=army.id)
        unit_b = Unit(name="Unit B", army_id=army.id)
        self.store.add_unit(unit_a)
        self.store.add_unit(unit_b)
        self.store.add_miniature(
            Miniature(name="Marine", unit_id=unit_a.id, status=PaintStatus.UNBUILT)
        )
        self.queue("1", "Veteran", "y", "2", "5", "veteran", "")
        edit_miniature(self.ctx)

        miniature = self.store.collection.miniatures[0]
        self.assertEqual(miniature.name, "Veteran")
        self.assertEqual(miniature.unit_id, unit_b.id)
        self.assertEqual(miniature.status, PaintStatus.BASED)
        self.assertEqual(miniature.tags, ["veteran"])

    def test_edit_miniature_keeps_defaults(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("1", "Sergeant", "n", "", "", "")
        edit_miniature(self.ctx)

        miniature = self.store.collection.miniatures[0]
        self.assertEqual(miniature.name, "Sergeant")
        self.assertEqual(miniature.status, PaintStatus.PAINTED)

    def test_delete_miniature_confirmed(self) -> None:
        _, _, miniature = self.seed_army_unit_miniature()
        self.queue("1", "y")
        delete_miniature(self.ctx)
        self.assertIsNone(self.store.get_miniature(miniature.id))

    def test_delete_miniature_cancelled(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("1", "n")
        delete_miniature(self.ctx)
        self.assertEqual(len(self.store.collection.miniatures), 1)

    def test_list_miniatures_empty(self) -> None:
        list_miniatures(self.ctx)
        self.assertEqual(self.store.collection.miniatures, [])

    def test_list_miniatures_with_data(self) -> None:
        self.seed_army_unit_miniature()
        list_miniatures(self.ctx)
        self.assertEqual(len(self.store.collection.miniatures), 1)

    def test_edit_miniature_cancelled(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("0")
        edit_miniature(self.ctx)
        self.assertEqual(self.store.collection.miniatures[0].name, "Sergeant")

    def test_delete_miniature_no_selection(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("0")
        delete_miniature(self.ctx)
        self.assertEqual(len(self.store.collection.miniatures), 1)


class TagMenuIntegrationTests(MenuIntegrationTestCase):
    def test_set_tag_filter(self) -> None:
        self.queue("Loyalist, Troops")
        set_tag_filter(self.ctx)
        self.assertEqual(self.ctx.active_tags, ["loyalist", "troops"])

    def test_set_tag_filter_blank_keeps_current_tags(self) -> None:
        self.ctx.active_tags = ["old"]
        self.queue("")
        set_tag_filter(self.ctx)
        self.assertEqual(self.ctx.active_tags, ["old"])

    def test_set_tag_filter_blank_clears_when_no_current_tags(self) -> None:
        self.queue("")
        set_tag_filter(self.ctx)
        self.assertEqual(self.ctx.active_tags, [])

    def test_clear_tag_filter(self) -> None:
        self.ctx.active_tags = ["loyalist"]
        _clear_tag_filter(self.ctx)
        self.assertEqual(self.ctx.active_tags, [])

    def test_browse_by_tags_empty_collection(self) -> None:
        browse_by_tags(self.ctx)
        self.assertEqual(self.store.collection.all_tags(), [])

    def test_browse_by_tags_select_number(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("1")
        browse_by_tags(self.ctx)

    def test_browse_by_tags_comma_separated(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("loyalist, troops")
        browse_by_tags(self.ctx)

    def test_browse_by_tags_cancel(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("0")
        browse_by_tags(self.ctx)

    def test_browse_by_tags_invalid_selection(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("99")
        browse_by_tags(self.ctx)

    def test_tags_menu_set_filter_and_clear(self) -> None:
        self.seed_army_unit_miniature()
        self.queue(
            "1",  # Set active filter
            "loyalist",
            "3",  # Clear active filter
            "0",  # Back
        )
        tags_menu(self.ctx)
        self.assertEqual(self.ctx.active_tags, [])


class MainMenuIntegrationTests(MenuIntegrationTestCase):
    def test_show_collection_overview(self) -> None:
        self.seed_army_unit_miniature()
        show_collection_overview(self.ctx)
        self.assertEqual(len(self.store.collection.armies), 1)

    def test_main_menu_exit(self) -> None:
        self.queue("0")
        main_menu(self.ctx)

    def test_main_menu_collection_overview_then_exit(self) -> None:
        self.seed_army_unit_miniature()
        self.queue("1", "0")
        main_menu(self.ctx)

    def test_main_menu_invalid_choice_then_exit(self) -> None:
        self.queue("9", "0")
        main_menu(self.ctx)

    def test_main_menu_armies_submenu_then_exit(self) -> None:
        self.queue("2", "0", "0")
        main_menu(self.ctx)

    def test_main_menu_full_crud_flow(self) -> None:
        self.queue(
            "2",  # Armies
            "2",  # Add army
            "Orks",
            "Xenos",
            "green",
            "",
            "0",  # Back from armies
            "3",  # Units
            "2",  # Add unit
            "1",
            "Boyz",
            "troops",
            "",
            "0",  # Back from units
            "4",  # Miniatures
            "2",  # Add miniature
            "1",
            "Gretchin",
            "1",
            "",
            "",
            "0",  # Back from miniatures
            "0",  # Exit
        )
        main_menu(self.ctx)

        self.assertEqual(len(self.store.collection.armies), 1)
        self.assertEqual(len(self.store.collection.units), 1)
        self.assertEqual(len(self.store.collection.miniatures), 1)
        self.assertEqual(self.store.collection.armies[0].name, "Orks")
        self.assertEqual(self.store.collection.units[0].name, "Boyz")
        self.assertEqual(self.store.collection.miniatures[0].name, "Gretchin")

    def test_list_views_with_active_tag_filter(self) -> None:
        army_loyal = Army(name="Loyal", tags=["loyalist"])
        army_chaos = Army(name="Heretic", tags=["chaos"])
        self.store.add_army(army_loyal)
        self.store.add_army(army_chaos)
        self.ctx.active_tags = ["loyalist"]

        list_armies(self.ctx)
        list_units(self.ctx)
        list_miniatures(self.ctx)

        self.assertEqual(len(self.store.list_armies(tags=["loyalist"])), 1)


class KeyboardInterruptIntegrationTests(MenuIntegrationTestCase):
    def test_main_menu_keyboard_interrupt_exits(self) -> None:
        with patch.object(ui.console, "input", side_effect=KeyboardInterrupt):
            main_menu(self.ctx)

    def test_browse_by_tags_keyboard_interrupt_propagates(self) -> None:
        self.seed_army_unit_miniature()
        with patch.object(ui.console, "input", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                browse_by_tags(self.ctx)

    def test_run_menu_keyboard_interrupt_exits_process(self) -> None:
        with patch.object(ui.console, "input", side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit):
                armies_menu(self.ctx)


class UiLoopIntegrationTests(MenuIntegrationTestCase):
    def test_prompt_yes_no_retries_invalid_answer(self) -> None:
        self.store.add_army(Army(name="Test"))
        self.queue("1", "maybe", "yes")
        delete_army(self.ctx)
        self.assertEqual(self.store.collection.armies, [])

    def test_prompt_choice_retries_invalid_then_accepts_default(self) -> None:
        army = Army(name="A")
        self.store.add_army(army)
        self.store.add_unit(Unit(name="U", army_id=army.id))
        self.queue("1", "Mini", "9", "", "", "")
        add_miniature(self.ctx)
        self.assertEqual(self.store.collection.miniatures[0].status, PaintStatus.UNBUILT)

    def test_run_menu_invalid_choice_then_back(self) -> None:
        self.queue("9", "0")
        armies_menu(self.ctx)


if __name__ == "__main__":
    unittest.main()