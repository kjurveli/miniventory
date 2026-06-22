from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class PaintStatus(str, Enum):
    UNBUILT = "unbuilt"
    ASSEMBLED = "assembled"
    PRIMED = "primed"
    PAINTED = "painted"
    BASED = "based"

    @classmethod
    def choices(cls) -> list[str]:
        return [status.value for status in cls]


def new_id() -> str:
    return str(uuid4())


def normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for tag in tags:
        cleaned = tag.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalized.append(cleaned)
    return sorted(normalized)


@dataclass
class Army:
    name: str
    id: str = field(default_factory=new_id)
    faction: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = normalize_tags(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Army:
        return cls(
            id=data.get("id", new_id()),
            name=data["name"],
            faction=data.get("faction", ""),
            tags=normalize_tags(data.get("tags", [])),
            notes=data.get("notes", ""),
        )


@dataclass
class Unit:
    name: str
    army_id: str
    id: str = field(default_factory=new_id)
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tags"] = normalize_tags(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Unit:
        return cls(
            id=data.get("id", new_id()),
            name=data["name"],
            army_id=data["army_id"],
            tags=normalize_tags(data.get("tags", [])),
            notes=data.get("notes", ""),
        )


@dataclass
class Miniature:
    name: str
    unit_id: str
    id: str = field(default_factory=new_id)
    tags: list[str] = field(default_factory=list)
    status: PaintStatus = PaintStatus.UNBUILT
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["tags"] = normalize_tags(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Miniature:
        status_value = data.get("status", PaintStatus.UNBUILT.value)
        try:
            status = PaintStatus(status_value)
        except ValueError:
            status = PaintStatus.UNBUILT
        return cls(
            id=data.get("id", new_id()),
            name=data["name"],
            unit_id=data["unit_id"],
            tags=normalize_tags(data.get("tags", [])),
            status=status,
            notes=data.get("notes", ""),
        )


@dataclass
class Collection:
    armies: list[Army] = field(default_factory=list)
    units: list[Unit] = field(default_factory=list)
    miniatures: list[Miniature] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "armies": [army.to_dict() for army in self.armies],
            "units": [unit.to_dict() for unit in self.units],
            "miniatures": [miniature.to_dict() for miniature in self.miniatures],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Collection:
        return cls(
            armies=[Army.from_dict(item) for item in data.get("armies", [])],
            units=[Unit.from_dict(item) for item in data.get("units", [])],
            miniatures=[
                Miniature.from_dict(item) for item in data.get("miniatures", [])
            ],
        )

    def all_tags(self) -> list[str]:
        tags: set[str] = set()
        for entity in (*self.armies, *self.units, *self.miniatures):
            tags.update(entity.tags)
        return sorted(tags)