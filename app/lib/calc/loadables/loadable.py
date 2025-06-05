
from abc import ABC, abstractmethod
from typing import List, Any, Optional, Type
import json
from json import JSONDecodeError
from pathlib import Path

import logging


class Itemable(ABC):
    """
    Item of the Loadable class. See below.
    """
    @abstractmethod
    def to_dict(self):
        pass


class Loadable(ABC):

    """
    Abstract class providing centralized interface for Loadables.
    There is items property which contain loaded items of type item_type
    Each item shold be a child of Itemable providing to_dict method for
    proper serialization process.
    Loadable contains load() and save() methods which do the work
    It ensures children to override necessary settings for proper work
    """

    @property
    @abstractmethod
    def data_path(self) -> Path:
        """
        Should be overriden with actual Loadable child
        :return: Returns a path to file where serialized data is located
        """
        pass

    @property
    @abstractmethod
    def item_type(self) -> Type:
        """
        Type of the items members
        :return: Itemable child
        """
        pass

    @property
    @abstractmethod
    def item_tag(self) -> str:
        """
        This is a tag that is present in serialized data
        :return:
        """
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
                # Ability to regenerate storage. For future releases
                raise e
        self.items = [self.item_type(**item) for item in struct[self.item_tag]]
        logging.info(f'Succesfully loaded {self.item_tag}')
        return self

    def save(self, path: Path = None, force: bool = False):
        struct = {
            self.item_tag: [item.to_dict() for item in self.items]
        }
        filemode = 'w' if force else 'x'
        with open(self.data_path if path is None else path, mode=filemode, encoding='utf8') as f:
            f.write(json.dumps(struct, ensure_ascii=False, indent=2))
        logging.info(f'Succesfully saved {self.item_tag}')
        logging.info(f'Reloading {self.item_tag} from recently saved file')
        return self.load(path)
