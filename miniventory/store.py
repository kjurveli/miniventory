from __future__ import annotations

import json
from pathlib import Path

from miniventory.models import Army, Collection, Miniature, Unit, normalize_tags


class CollectionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.collection = Collection()

    def load(self) -> Collection:
        if not self.path.exists():
            self.collection = Collection()
            return self.collection

        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        self.collection = Collection.from_dict(data)
        return self.collection

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(self.collection.to_dict(), handle, indent=2)
            handle.write("\n")
        temp_path.replace(self.path)

    # --- Army operations ---

    def add_army(self, army: Army) -> Army:
        self.collection.armies.append(army)
        self.save()
        return army

    def update_army(self, army: Army) -> Army:
        for index, existing in enumerate(self.collection.armies):
            if existing.id == army.id:
                self.collection.armies[index] = army
                self.save()
                return army
        raise KeyError(f"Army not found: {army.id}")

    def delete_army(self, army_id: str) -> None:
        unit_ids = {unit.id for unit in self.collection.units if unit.army_id == army_id}
        self.collection.armies = [
            army for army in self.collection.armies if army.id != army_id
        ]
        self.collection.units = [
            unit for unit in self.collection.units if unit.army_id != army_id
        ]
        self.collection.miniatures = [
            miniature
            for miniature in self.collection.miniatures
            if miniature.unit_id not in unit_ids
        ]
        self.save()

    def get_army(self, army_id: str) -> Army | None:
        return next(
            (army for army in self.collection.armies if army.id == army_id),
            None,
        )

    def list_armies(self, tags: list[str] | None = None) -> list[Army]:
        if not tags:
            return list(self.collection.armies)
        required = set(normalize_tags(tags))
        return [
            army
            for army in self.collection.armies
            if required.issubset(set(army.tags))
        ]

    # --- Unit operations ---

    def add_unit(self, unit: Unit) -> Unit:
        if self.get_army(unit.army_id) is None:
            raise ValueError(f"Army not found: {unit.army_id}")
        self.collection.units.append(unit)
        self.save()
        return unit

    def update_unit(self, unit: Unit) -> Unit:
        if self.get_army(unit.army_id) is None:
            raise ValueError(f"Army not found: {unit.army_id}")
        for index, existing in enumerate(self.collection.units):
            if existing.id == unit.id:
                self.collection.units[index] = unit
                self.save()
                return unit
        raise KeyError(f"Unit not found: {unit.id}")

    def delete_unit(self, unit_id: str) -> None:
        self.collection.units = [
            unit for unit in self.collection.units if unit.id != unit_id
        ]
        self.collection.miniatures = [
            miniature
            for miniature in self.collection.miniatures
            if miniature.unit_id != unit_id
        ]
        self.save()

    def get_unit(self, unit_id: str) -> Unit | None:
        return next(
            (unit for unit in self.collection.units if unit.id == unit_id),
            None,
        )

    def list_units(
        self, army_id: str | None = None, tags: list[str] | None = None
    ) -> list[Unit]:
        units = self.collection.units
        if army_id:
            units = [unit for unit in units if unit.army_id == army_id]
        if tags:
            required = set(normalize_tags(tags))
            units = [unit for unit in units if required.issubset(set(unit.tags))]
        return list(units)

    # --- Miniature operations ---

    def add_miniature(self, miniature: Miniature) -> Miniature:
        if self.get_unit(miniature.unit_id) is None:
            raise ValueError(f"Unit not found: {miniature.unit_id}")
        self.collection.miniatures.append(miniature)
        self.save()
        return miniature

    def update_miniature(self, miniature: Miniature) -> Miniature:
        if self.get_unit(miniature.unit_id) is None:
            raise ValueError(f"Unit not found: {miniature.unit_id}")
        for index, existing in enumerate(self.collection.miniatures):
            if existing.id == miniature.id:
                self.collection.miniatures[index] = miniature
                self.save()
                return miniature
        raise KeyError(f"Miniature not found: {miniature.id}")

    def delete_miniature(self, miniature_id: str) -> None:
        self.collection.miniatures = [
            miniature
            for miniature in self.collection.miniatures
            if miniature.id != miniature_id
        ]
        self.save()

    def get_miniature(self, miniature_id: str) -> Miniature | None:
        return next(
            (
                miniature
                for miniature in self.collection.miniatures
                if miniature.id == miniature_id
            ),
            None,
        )

    def list_miniatures(
        self, unit_id: str | None = None, tags: list[str] | None = None
    ) -> list[Miniature]:
        miniatures = self.collection.miniatures
        if unit_id:
            miniatures = [
                miniature for miniature in miniatures if miniature.unit_id == unit_id
            ]
        if tags:
            required = set(normalize_tags(tags))
            miniatures = [
                miniature
                for miniature in miniatures
                if required.issubset(set(miniature.tags))
            ]
        return list(miniatures)

    def filter_by_tags(self, tags: list[str]) -> dict[str, list]:
        normalized = normalize_tags(tags)
        return {
            "armies": self.list_armies(tags=normalized),
            "units": self.list_units(tags=normalized),
            "miniatures": self.list_miniatures(tags=normalized),
        }