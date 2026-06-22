import tempfile
import unittest
from pathlib import Path

from miniventory.models import Army, Miniature, PaintStatus, Unit
from miniventory.store import CollectionStore


class CollectionStoreExtendedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "collection.json"
        self.store = CollectionStore(self.path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _seed_collection(self) -> tuple[Army, Unit, Miniature]:
        army = Army(name="Ultramarines", tags=["loyalist"])
        self.store.add_army(army)
        unit = Unit(name="Intercessors", army_id=army.id, tags=["troops"])
        self.store.add_unit(unit)
        miniature = Miniature(
            name="Sergeant",
            unit_id=unit.id,
            tags=["character"],
            status=PaintStatus.PAINTED,
        )
        self.store.add_miniature(miniature)
        return army, unit, miniature

    def test_load_missing_file_returns_empty_collection(self) -> None:
        collection = self.store.load()
        self.assertEqual(collection.armies, [])
        self.assertEqual(collection.units, [])
        self.assertEqual(collection.miniatures, [])

    def test_update_army(self) -> None:
        army, _, _ = self._seed_collection()
        army.name = "Renamed"
        army.faction = "Space Marines"
        updated = self.store.update_army(army)
        self.assertEqual(updated.name, "Renamed")
        self.assertEqual(self.store.get_army(army.id).faction, "Space Marines")

    def test_update_army_not_found_raises(self) -> None:
        with self.assertRaises(KeyError):
            self.store.update_army(Army(id="missing", name="Ghost"))

    def test_get_army_returns_none_for_unknown_id(self) -> None:
        self.assertIsNone(self.store.get_army("does-not-exist"))

    def test_list_armies_with_tag_filter(self) -> None:
        self.store.add_army(Army(name="Loyal", tags=["loyalist"]))
        self.store.add_army(Army(name="Heretic", tags=["chaos"]))

        loyalists = self.store.list_armies(tags=["loyalist"])
        self.assertEqual([army.name for army in loyalists], ["Loyal"])

    def test_list_armies_requires_all_tags(self) -> None:
        self.store.add_army(Army(name="Tagged", tags=["a", "b"]))
        self.assertEqual(len(self.store.list_armies(tags=["a", "b"])), 1)
        self.assertEqual(len(self.store.list_armies(tags=["a", "c"])), 0)

    def test_add_unit_without_army_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.store.add_unit(Unit(name="Orphans", army_id="missing"))

    def test_update_unit(self) -> None:
        _, unit, _ = self._seed_collection()
        unit.name = "Assault Intercessors"
        self.store.update_unit(unit)
        self.assertEqual(self.store.get_unit(unit.id).name, "Assault Intercessors")

    def test_update_unit_not_found_raises(self) -> None:
        army = Army(name="Solo")
        self.store.add_army(army)
        with self.assertRaises(KeyError):
            self.store.update_unit(Unit(id="missing", name="Ghost", army_id=army.id))

    def test_update_unit_with_invalid_army_raises(self) -> None:
        _, unit, _ = self._seed_collection()
        unit.army_id = "missing"
        with self.assertRaises(ValueError):
            self.store.update_unit(unit)

    def test_delete_unit_cascades_miniatures(self) -> None:
        _, unit, _ = self._seed_collection()
        self.store.delete_unit(unit.id)
        self.assertEqual(self.store.collection.units, [])
        self.assertEqual(self.store.collection.miniatures, [])

    def test_list_units_by_army_and_tags(self) -> None:
        army_a = Army(name="A")
        army_b = Army(name="B")
        self.store.add_army(army_a)
        self.store.add_army(army_b)
        self.store.add_unit(Unit(name="A Unit", army_id=army_a.id, tags=["fast"]))
        self.store.add_unit(Unit(name="B Unit", army_id=army_b.id, tags=["slow"]))

        self.assertEqual(len(self.store.list_units(army_id=army_a.id)), 1)
        self.assertEqual(len(self.store.list_units(tags=["fast"])), 1)
        self.assertEqual(len(self.store.list_units(army_id=army_b.id, tags=["slow"])), 1)

    def test_add_miniature_without_unit_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.store.add_miniature(Miniature(name="Lost", unit_id="missing"))

    def test_update_miniature(self) -> None:
        _, unit, miniature = self._seed_collection()
        miniature.status = PaintStatus.BASED
        self.store.update_miniature(miniature)
        self.assertEqual(
            self.store.get_miniature(miniature.id).status,
            PaintStatus.BASED,
        )

    def test_update_miniature_not_found_raises(self) -> None:
        _, unit, _ = self._seed_collection()
        with self.assertRaises(KeyError):
            self.store.update_miniature(
                Miniature(id="missing", name="Ghost", unit_id=unit.id)
            )

    def test_delete_miniature(self) -> None:
        _, _, miniature = self._seed_collection()
        self.store.delete_miniature(miniature.id)
        self.assertEqual(self.store.collection.miniatures, [])

    def test_list_miniatures_by_unit_and_tags(self) -> None:
        army = Army(name="A")
        self.store.add_army(army)
        unit_a = Unit(name="Unit A", army_id=army.id)
        unit_b = Unit(name="Unit B", army_id=army.id)
        self.store.add_unit(unit_a)
        self.store.add_unit(unit_b)
        self.store.add_miniature(
            Miniature(name="M1", unit_id=unit_a.id, tags=["hero"])
        )
        self.store.add_miniature(Miniature(name="M2", unit_id=unit_b.id))

        self.assertEqual(len(self.store.list_miniatures(unit_id=unit_a.id)), 1)
        self.assertEqual(len(self.store.list_miniatures(tags=["hero"])), 1)

    def test_get_unit_and_miniature(self) -> None:
        _, unit, miniature = self._seed_collection()
        self.assertEqual(self.store.get_unit(unit.id).name, unit.name)
        self.assertEqual(self.store.get_miniature(miniature.id).name, miniature.name)
        self.assertIsNone(self.store.get_unit("missing"))
        self.assertIsNone(self.store.get_miniature("missing"))

    def test_list_armies_without_tag_filter_returns_all(self) -> None:
        self.store.add_army(Army(name="One"))
        self.store.add_army(Army(name="Two"))
        self.assertEqual(len(self.store.list_armies()), 2)
        self.assertEqual(len(self.store.list_armies(tags=None)), 2)

    def test_update_miniature_with_invalid_unit_raises(self) -> None:
        _, _, miniature = self._seed_collection()
        miniature.unit_id = "missing"
        with self.assertRaises(ValueError):
            self.store.update_miniature(miniature)


if __name__ == "__main__":
    unittest.main()