from __future__ import annotations
from abc import ABCMeta
from typing import Union, Iterable, Mapping, Type, MutableMapping, List, overload
import json
import logging

from .Errors import InvalidGraphStyleCollectionError, InvalidGraphClassCollectionError


class Comparable(metaclass=ABCMeta):
    """
    Comparable interface allows you compare objects with their identity.
    """
    _PREFIX = ''

    def __init__(self, identity: Union[int, str], name=None):
        """
        Identity interface. Subclass should pass in an identity that should be comparable
        But it is restricted to `int` and `str` for now.
        @param identity: unique id for this object
        @param name: displayed name for this object
        """
        # TODO read SUID if id is not present.
        # TODO think of an naming convention for id
        assert identity is not None
        self.identity = identity
        self.name = name if name else self._PREFIX + str(identity)

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.identity == other.identity
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((type(self), self.identity))

    def __gt__(self, other: 'Comparable'):
        if not isinstance(other, Comparable):
            raise ValueError('Cannot compare %s with %s' % (self, other))
        return self.identity > other.identity

    def __lt__(self, other: 'Comparable'):
        return not self.__gt__(other)

    def __ge__(self, other: 'Comparable'):
        return self.__gt__(other) or self.__eq__(other)

    def __le__(self, other: 'Comparable'):
        return self.__lt__(other) or self.__eq__(other)


class HasProperty(metaclass=ABCMeta):
    """
    Property interface allows you to manage defined property and access them through subscript;
    """
    def __init__(self):
        """
        create a property interface
        """
        self.properties = {}

    def update_properties(self, properties: Mapping):
        self.properties.update(properties)

    def __getitem__(self, item):
        """
        get property
        @param item:
        @return:
        """
        return self.properties[item]

    def __setitem__(self, key, value):
        """
        set a property with some value
        @param key:
        @param value:
        """
        self.properties[key] = value

    def __contains__(self, item):
        """
        Check whether this object has certain property
        @param item:
        @return boolean value indicating whether the property is in this object
        """
        return item in self.properties

    def __iter__(self):
        """
        loop through all the properties
        @return:
        """
        for key, value in self.properties:
            yield key, value

    def __len__(self):
        """
        @return: the number of properties of this object
        """
        return len(self.properties)


class Stylable(metaclass=ABCMeta):
    @staticmethod
    def is_valid_graph_styles(styles: Iterable[Mapping]) -> bool:
        if isinstance(styles, Iterable):
            for element in styles:
                if not isinstance(element, Mapping) or 'selector' not in element or 'style' not in element:
                    return False
            return True
        return False

    @staticmethod
    def is_valid_graph_classes(classes: Iterable[str]) -> bool:
        return isinstance(classes, Iterable) and all(isinstance(element, str) for element in classes)

    @overload
    def __init__(self, styles: Iterable[Mapping] = (), classes: Iterable[str] = None) -> None: ...

    @overload
    def __init__(self, styles: str = (), classes: Iterable[str] = None) -> None: ...

    def __init__(self, styles, classes):
        """
        interface that helps managing the state of an element
        @param styles:
        @param classes:
        """

        self.styles: List[MutableMapping[str, str]] = []
        self.classes = []

        if isinstance(styles, str):
            try:
                styles = json.loads(styles)
            except json.JSONDecodeError as e:
                logging.exception('Cannot decode Json')
                raise e
            except Exception as e:
                logging.exception('Unknown Exception')
                raise e

        if self.is_valid_graph_styles(styles):
            self.styles.extend(styles)
        else:
            raise InvalidGraphStyleCollectionError(f'cannot init {type(self)} due to graph style format error.')

        # TODO ???
        if self.is_valid_graph_classes(classes):
            self.classes.extend(classes)
        else:
            raise InvalidGraphClassCollectionError(f'cannot init {type(self)} due to graph class format error.')


class ElementSet:
    def __init__(self, elements: Iterable[Comparable], element_type: Type[Comparable]):
        """
        Element set base class
        @param elements:
        @param element_type:
        """
        self.elements = set()
        self.element_type = element_type
        if isinstance(elements, Iterable) and all(isinstance(element, self.element_type) for element in elements):
            self.elements.update(elements)
        else:
            raise KeyError('elements are not all %s type' % self.element_type)

    def _rm_element(self, element):
        if isinstance(element, self.element_type) and element in self.elements:
            self.elements.remove(element)

    def is_empty(self):
        return len(self.elements) == 0

    def __len__(self):
        """
        return the number of elements in this set
        @return:
        """
        return len(self.elements)

    def __getitem__(self, identity):
        """
        use subscript [] to get item
        @param identity:
        @return:
        """
        for element in self.elements:
            if element.identity == identity:
                return element

        return None

    def __iter__(self):
        """
        iterator that goes through the elements in the set
        @return:
        """
        for element in self.elements:
            yield element

    def __contains__(self, item):
        """
        whether this set contains a given item
        @param item:
        @return:
        """
        if isinstance(item, self.element_type):
            return item in self.elements
        if isinstance(item, str):
            # TODO what about searches for names?
            return any(element.identity == item for element in self.elements)
        return False

    def __str__(self):
        return str(self.elements)

    def __repr__(self):
        return self.__str__()
