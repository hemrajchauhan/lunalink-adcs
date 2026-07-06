"""Generic JSON-backed repository.

All persistent collections (bodies, satellites, missions) are lists of records
in a JSON file under ``lunalink/data``. This base class owns the file I/O and
the common list operations; concrete repositories only supply the file name
and the (de)serialisation of one record.
"""
from pathlib import Path
import json

DATA_DIR = Path(__file__).parents[2] / "data"


class JsonRepository:
    """List-of-records store. Subclasses set :attr:`FILENAME` and implement
    :meth:`decode` (dict -> object) and :meth:`encode` (object -> dict).
    Objects are expected to expose a ``name`` attribute (the record key).
    """

    FILENAME: str = ""

    def __init__(self):
        self.path = DATA_DIR / self.FILENAME

    # -- record (de)serialisation, supplied by subclasses ------------------
    def decode(self, record: dict):
        raise NotImplementedError

    def encode(self, obj) -> dict:
        raise NotImplementedError

    # -- persistence --------------------------------------------------------
    def load_all(self) -> list:
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, ValueError):
            return []
        return [self.decode(record) for record in data]

    def save_all(self, objects: list) -> None:
        data = [self.encode(obj) for obj in objects]
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    # -- common list operations ----------------------------------------------
    def get_by_name(self, name: str):
        return next((o for o in self.load_all() if o.name == name), None)

    def add(self, obj) -> None:
        objects = self.load_all()
        objects.append(obj)
        self.save_all(objects)

    def upsert(self, obj, original_name: str | None = None) -> None:
        """Replace the record called ``original_name`` (or ``obj.name``) with
        ``obj``; append if no such record exists."""
        key = original_name or obj.name
        objects = self.load_all()
        for index, existing in enumerate(objects):
            if existing.name == key:
                objects[index] = obj
                break
        else:
            objects.append(obj)
        self.save_all(objects)

    def delete(self, name: str) -> None:
        self.save_all([o for o in self.load_all() if o.name != name])
