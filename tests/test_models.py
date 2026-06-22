import unittest

from miniventory.models import (
    Army,
    Collection,
    Miniature,
    PaintStatus,
    Unit,
    normalize_tags,
)


class NormalizeTagsTests(unittest.TestCase):
    def test_lowercases_and_deduplicates(self) -> None:
        self.assertEqual(
            normalize_tags(["Loyalist", "loyalist", " Troops "]),
            ["loyalist", "troops"],
        )

    def test_ignores_empty_strings(self) -> None:
        self.assertEqual(normalize_tags(["", "  ", "valid"]), ["valid"])

    def test_empty_list(self) -> None:
        self.assertEqual(normalize_tags([]), [])


class PaintStatusTests(unittest.TestCase):
    def test_choices_returns_all_values(self) -> None:
        self.assertEqual(
            PaintStatus.choices(),
            ["unbuilt", "assembled", "primed", "painted", "based"],
        )


class ArmyTests(unittest.TestCase):
    def test_to_dict_normalizes_tags(self) -> None:
        army = Army(name="Ultramarines", tags=["Loyalist", "loyalist"])
        self.assertEqual(army.to_dict()["tags"], ["loyalist"])

    def test_from_dict_round_trip(self) -> None:
        army = Army(
            id="army-1",
            name="Orks",
            faction="Xenos",
            tags=["xenos"],
            notes="Waaagh!",
        )
        restored = Army.from_dict(army.to_dict())
        self.assertEqual(restored.id, army.id)
        self.assertEqual(restored.name, army.name)
        self.assertEqual(restored.faction, army.faction)
        self.assertEqual(restored.tags, army.tags)
        self.assertEqual(restored.notes, army.notes)

    def test_from_dict_generates_id_when_missing(self) -> None:
        army = Army.from_dict({"name": "Test"})
        self.assertTrue(army.id)


class UnitTests(unittest.TestCase):
    def test_from_dict_round_trip(self) -> None:
        unit = Unit(id="unit-1", name="Boyz", army_id="army-1", tags=["troops"])
        restored = Unit.from_dict(unit.to_dict())
        self.assertEqual(restored.id, unit.id)
        self.assertEqual(restored.army_id, unit.army_id)


class MiniatureTests(unittest.TestCase):
    def test_to_dict_uses_status_value(self) -> None:
        miniature = Miniature(name="Marine", unit_id="u1", status=PaintStatus.PAINTED)
        self.assertEqual(miniature.to_dict()["status"], "painted")

    def test_from_dict_invalid_status_defaults_to_unbuilt(self) -> None:
        miniature = Miniature.from_dict(
            {"name": "Marine", "unit_id": "u1", "status": "not-a-status"}
        )
        self.assertEqual(miniature.status, PaintStatus.UNBUILT)

    def test_from_dict_round_trip(self) -> None:
        miniature = Miniature(
            id="mini-1",
            name="Sergeant",
            unit_id="unit-1",
            status=PaintStatus.BASED,
            tags=["character"],
            notes="Leader",
        )
        restored = Miniature.from_dict(miniature.to_dict())
        self.assertEqual(restored.status, PaintStatus.BASED)
        self.assertEqual(restored.tags, ["character"])


class CollectionTests(unittest.TestCase):
    def test_to_dict_and_from_dict(self) -> None:
        army = Army(id="a1", name="Necrons")
        unit = Unit(id="u1", name="Warriors", army_id="a1")
        miniature = Miniature(id="m1", name="Warrior 1", unit_id="u1")
        collection = Collection(armies=[army], units=[unit], miniatures=[miniature])

        restored = Collection.from_dict(collection.to_dict())
        self.assertEqual(len(restored.armies), 1)
        self.assertEqual(len(restored.units), 1)
        self.assertEqual(len(restored.miniatures), 1)

    def test_all_tags_collects_from_all_entities(self) -> None:
        collection = Collection(
            armies=[Army(name="A", tags=["army-tag"])],
            units=[Unit(name="U", army_id="x", tags=["unit-tag"])],
            miniatures=[Miniature(name="M", unit_id="y", tags=["mini-tag"])],
        )
        self.assertEqual(collection.all_tags(), ["army-tag", "mini-tag", "unit-tag"])

    def test_all_tags_empty_collection(self) -> None:
        self.assertEqual(Collection().all_tags(), [])


if __name__ == "__main__":
    unittest.main()