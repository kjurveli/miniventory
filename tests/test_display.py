import io
import tempfile
import unittest
from pathlib import Path

from rich.console import Console

from miniventory import display, ui
from miniventory.models import Army, Miniature, PaintStatus, Unit
from miniventory.store import CollectionStore


class DisplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "collection.json"
        self.store = CollectionStore(self.path)
        self.army = Army(name="Ultramarines", faction="Space Marines", tags=["loyalist"])
        self.store.add_army(self.army)
        self.unit = Unit(name="Intercessors", army_id=self.army.id, tags=["troops"])
        self.store.add_unit(self.unit)
        self.miniature = Miniature(
            name="Sergeant",
            unit_id=self.unit.id,
            status=PaintStatus.PAINTED,
            tags=["character"],
        )
        self.store.add_miniature(self.miniature)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_status_label_includes_markup_for_each_status(self) -> None:
        self.assertIn("unbuilt", display.status_label(PaintStatus.UNBUILT))
        self.assertIn("painted", display.status_label(PaintStatus.PAINTED))
        self.assertIn("green", display.status_label(PaintStatus.PAINTED))

    def test_render_armies_table_has_expected_rows_and_columns(self) -> None:
        table = display.render_armies_table(self.store, self.store.collection.armies)
        self.assertEqual(table.row_count, 1)
        self.assertEqual(len(table.columns), 6)
        self.assertEqual(table.columns[1].header, "Name")

    def test_render_units_table_shows_army_name(self) -> None:
        table = display.render_units_table(self.store, self.store.collection.units)
        self.assertEqual(table.row_count, 1)
        rendered = self._render_table(table)
        self.assertIn("Ultramarines", rendered)
        self.assertIn("Intercessors", rendered)

    def test_render_miniatures_table_shows_status_and_unit(self) -> None:
        table = display.render_miniatures_table(
            self.store, self.store.collection.miniatures
        )
        rendered = self._render_table(table)
        self.assertIn("Sergeant", rendered)
        self.assertIn("Intercessors", rendered)
        self.assertIn("painted", rendered)

    def test_render_overview_panel_without_filter(self) -> None:
        panel = display.render_overview_panel(self.store)
        self.assertEqual(panel.title, "Collection Overview")
        rendered = self._render_panel(panel)
        self.assertIn("Armies:", rendered)
        self.assertIn("Miniatures:", rendered)
        self.assertNotIn("Active filter results", rendered)

    def test_render_overview_panel_with_active_filter(self) -> None:
        panel = display.render_overview_panel(self.store, active_tags=["loyalist"])
        rendered = self._render_panel(panel)
        self.assertIn("Active filter results", rendered)

    def test_render_tag_results_prints_all_sections(self) -> None:
        output = io.StringIO()
        test_console = Console(file=output, force_terminal=True, width=120)
        original = ui.console
        ui.console = test_console
        try:
            results = self.store.filter_by_tags(["loyalist"])
            display.render_tag_results(self.store, results, ["loyalist"])
        finally:
            ui.console = original

        rendered = output.getvalue()
        self.assertIn("Results for", rendered)
        self.assertIn("Ultramarines", rendered)
        self.assertIn("Units:", rendered)
        self.assertIn("none", rendered)

    def _render_table(self, table) -> str:
        output = io.StringIO()
        Console(file=output, force_terminal=True, width=120).print(table)
        return output.getvalue()

    def _render_panel(self, panel) -> str:
        output = io.StringIO()
        Console(file=output, force_terminal=True, width=120).print(panel)
        return output.getvalue()


if __name__ == "__main__":
    unittest.main()