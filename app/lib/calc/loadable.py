
from abc import ABC, abstractmethod
from typing import List, Any, Optional, Type
from pathlib import Path
from json import JSONDecodeError
import json
import logging


class Itemable(ABC):

    @abstractmethod
    def to_dict(self):
        pass


class Loadable(ABC):

    @property
    @abstractmethod
    def data_path(self) -> Path:
        pass

    @property
    @abstractmethod
    def item_type(self) -> Type:
        pass

    @property
    @abstractmethod
    def item_tag(self) -> str:
        pass

    _items: Optional[List[Itemable]]
    _defined_status: bool

    @property
    def items(self) -> Optional[List[Any]]:
        return self._items

    @items.setter
    def items(self, value):
        self._items = value
        self._defined_status = True

    def __init__(self):
        self._items = None
        self._defined_status = False

    def load(self, path: Path = None):
        with open(self.data_path if path is None else path, mode='r', encoding='utf-8') as f:
            try:
                struct = json.load(f)
            except (JSONDecodeError, OSError) as e:
                logging.exception(e)
                # TODO Regenerate file
                raise e
        self.items = [self.item_type(**item) for item in struct[self.item_tag]]
        logging.info(f'Succesfully loaded {self.item_tag}')
        return self

    def save(self, path=None, force=False) -> None:
        struct = {
            self.item_tag: [item.to_dict() for item in self.items]
        }
        filemode = 'w' if force else 'x'
        with open(self.data_path if path is None else path, mode=filemode, encoding='utf8') as f:
            f.write(json.dumps(struct, ensure_ascii=False, indent=2))
        logging.info(f'Succesfully saved {self.item_tag}')
