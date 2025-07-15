import json
from pathlib import Path
from fabric.core import Service, Property, Signal
from loguru import logger

from util.singleton import Singleton
from config.storage import STORAGE_DIRECTORY
from config.todo import TODO_JSON_PATH

import uuid


class ToDoItem:
    def __init__(
        self,
        text: str,
        completed: bool,
        id: str | None = None,
    ):
        self.id = id if id is not None else str(uuid.uuid4())
        self.text = text
        self.completed = completed

    def to_json_obj(self) -> dict:
        return {
            "text": self.text,
            "completed": self.completed,
        }
    
    @classmethod
    def from_json_obj(cls, id: str, json_obj):
        return cls(
            id=id,
            text=json_obj["text"],
            completed=json_obj["completed"],
        )


class ToDoItemParent(ToDoItem):
    def __init__(
        self,
        text: str,
        completed: bool,
        children: list = [], # list[ToDoItem]
        id: str | None = None,
    ):
        super().__init__(text, completed, id)
        self.children = {}
        for child in children:
            self.children[child.id] = child

    def to_json_obj(self) -> dict:
        obj = super().to_json_obj()
        obj["children"] = {
            id: child.to_json_obj() for id, child in self.children.items() 
        }
        return obj
    
    @classmethod
    def from_json_obj(cls, id: str, json_obj):
        return cls(
            id=id,
            text=json_obj["text"],
            completed=json_obj["completed"],
            children=[
                cls.from_json_obj(id, child_obj) 
                for id, child_obj in json_obj["children"].items()
            ]
        )


class ToDoService(Service, Singleton):
    @Signal("changed")
    def changed(self) -> None: ...

    @Property(list[ToDoItem], flags="readable")
    def to_do_list(self) -> list[ToDoItem]:
        return [
            ToDoItem.from_json_obj(id, json_obj)
            for id, json_obj in self._to_do_list.items()
        ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._path: Path = None
        self._to_do_list: dict = None

        self.init_to_do_file()

    @logger.catch
    def init_to_do_file(self):
        self._path = Path(STORAGE_DIRECTORY + TODO_JSON_PATH)

        try:
            if not self._path.exists():
                json.dump(dict(), self._path.open("w"))

            json_file = self._path.open("r+")
        except Exception as e:
            logger.error(
                f"Could not initialize TODO json file. Encountered error {e}"
            )
        else:
            with json_file:
                self._to_do_list = json.load(json_file)

    def is_initialized(self) -> bool:
        """Details whether this service is in a usable state."""
        return self._path is not None and self._to_do_list is not None
    
    def commit_changes(self) -> None:
        self.emit("changed")
        self.write_to_disk()

    @logger.catch
    def write_to_disk(self) -> None:
        if self.is_initialized():
            json.dump(self._to_do_list, self._path.open("w"))

    def add_to_do_item(self, item: ToDoItemParent):
        self._to_do_list[item.id] = item.to_json_obj()
        self.commit_changes()

    def delete_to_do_item(self, item: ToDoItemParent):
        self._to_do_list.pop(item.id)
        self.commit_changes()

    def add_child_to_item(self, item: ToDoItemParent, child: ToDoItem):
        self._to_do_list[item.id]["children"][child.id] = child.to_json_obj()
        self.commit_changes()

    def mark_item_completed(self, item: ToDoItemParent):
        self._to_do_list[item.id]["completed"] = True
        # if the parent item is completed, then logically all the children
        # must also be completed. So mark all children complete as well
        children = self._to_do_list[item.id]["children"]
        for id in children.keys():
            children[id]["completed"] = True

        self.commit_changes()

    def mark_child_completed(self, item: ToDoItemParent, child: ToDoItem, write: bool = True):
        self._to_do_list[item.id]["children"][child.id]["completed"] = True
        self.commit_changes()

    def mark_item_not_completed(self, item: ToDoItemParent):
        self._to_do_list[item.id]["completed"] = False
        self.commit_changes()

    def mark_child_not_completed(self, item: ToDoItemParent, child: ToDoItem):
        self._to_do_list[item.id]["children"][child.id]["completed"] = False
        # if the parent is marked complete, make sure to mark it incomplete
        # if marking a child incomplete.
        if self._to_do_list[item.id]["completed"]:
            self._to_do_list[item.id]["completed"] = False

        self.commit_changes()