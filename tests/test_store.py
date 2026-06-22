import json
import tempfile
import unittest
from pathlib import Path

from miniventory.models import Army, Miniature, PaintStatus, Unit
from miniventory.store import CollectionStore


class CollectionStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "collection.json"
        self.store = CollectionStore(self.path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_save_and_load_round_trip(self) -> None:
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

        reloaded = CollectionStore(self.path)
        reloaded.load()

        self.assertEqual(len(reloaded.collection.armies), 1)
        self.assertEqual(len(reloaded.collection.units), 1)
        self.assertEqual(len(reloaded.collection.miniatures), 1)
        self.assertEqual(reloaded.collection.miniatures[0].status, PaintStatus.PAINTED)

    def test_delete_army_cascades(self) -> None:
        army = Army(name="Orks", tags=["xenos"])
        self.store.add_army(army)
        unit = Unit(name="Boyz", army_id=army.id)
        self.store.add_unit(unit)
        self.store.add_miniature(Miniature(name="Gretchin", unit_id=unit.id))

        self.store.delete_army(army.id)

        self.assertEqual(self.store.collection.armies, [])
        self.assertEqual(self.store.collection.units, [])
        self.assertEqual(self.store.collection.miniatures, [])

    def test_filter_by_tags(self) -> None:
        army = Army(name="Necrons", tags=["xenos", "metal"])
        self.store.add_army(army)
        unit = Unit(name="Warriors", army_id=army.id, tags=["troops", "metal"])
        self.store.add_unit(unit)
        self.store.add_miniature(
            Miniature(name="Warrior 1", unit_id=unit.id, tags=["batch-1"])
        )

        results = self.store.filter_by_tags(["metal"])

        self.assertEqual(len(results["armies"]), 1)
        self.assertEqual(len(results["units"]), 1)
        self.assertEqual(len(results["miniatures"]), 0)

    def test_json_file_is_written(self) -> None:
        self.store.add_army(Army(name="Test Army"))
        self.assertTrue(self.path.exists())
        with self.path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIn("armies", data)


if __name__ == "__main__":
    unittest.main()