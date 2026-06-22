import tempfile
import unittest
from pathlib import Path

from miniventory.menus import (
    MenuContext,
    format_army,
    format_miniature,
    format_unit,
)
from miniventory.models import Army, Miniature, PaintStatus, Unit
from miniventory.store import CollectionStore


class MenuContextTests(unittest.TestCase):
    def test_active_tags_start_empty(self) -> None:
        store = CollectionStore(Path("unused.json"))
        ctx = MenuContext(store)
        self.assertEqual(ctx.active_tags, [])


class FormatHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = CollectionStore(Path(self.temp_dir.name) / "collection.json")
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

    def test_format_army_includes_counts_and_tags(self) -> None:
        text = format_army(self.store, self.army)
        self.assertIn("Ultramarines", text)
        self.assertIn("Space Marines", text)
        self.assertIn("1 unit(s)", text)
        self.assertIn("1 miniature(s)", text)
        self.assertIn("loyalist", text)

    def test_format_unit_includes_army_and_counts(self) -> None:
        text = format_unit(self.store, self.unit)
        self.assertIn("Intercessors", text)
        self.assertIn("Ultramarines", text)
        self.assertIn("troops", text)

    def test_format_miniature_includes_unit_status_and_tags(self) -> None:
        text = format_miniature(self.store, self.miniature)
        self.assertIn("Sergeant", text)
        self.assertIn("Intercessors", text)
        self.assertIn("painted", text)
        self.assertIn("character", text)

    def test_format_unit_unknown_army(self) -> None:
        orphan = Unit(name="Lost", army_id="missing")
        text = format_unit(self.store, orphan)
        self.assertIn("unknown army", text)

    def test_format_miniature_unknown_unit(self) -> None:
        orphan = Miniature(name="Lost", unit_id="missing")
        text = format_miniature(self.store, orphan)
        self.assertIn("unknown unit", text)


if __name__ == "__main__":
    unittest.main()