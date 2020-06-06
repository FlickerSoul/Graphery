from abc import ABCMeta, abstractmethod
from typing import Union, Iterable, Mapping, TypeVar, Generic, Type
import json
import logging


class Highlightable(metaclass=ABCMeta):
    """
    Highlight interface
    """
    @abstractmethod
    def highlight(self, cls: str):
        """
        make this object highlighted
        @param cls: the color of which this object should be highlighted
        @raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def unhighlight(self, cls: str):
        """
        unhighlight this object
        @param cls: the color of which this object should be highlighted
        @raise: NotImplementedError
        """
        raise NotImplementedError


class Comparable(metaclass=ABCMeta):
    """
    Comparable interface allows you compare objects with their identity.
    """
    PREFIX = ''

    def __init__(self, identity: Union[int, str], name=None):
        """
        Identity interface. Subclass should pass in an identity that should be comparable
        But it is restricted to `int` and `str` for now.
        @param identity: unique id for this object
        @param name: displayed name for this object
        """
        self.identity = identity
        self.name = name if not name else Comparable.PREFIX + str(identity)

    def __eq__(self, other: 'Comparable'):
        if not isinstance(other, Comparable):
            return False
        return self.identity == other.identity

    def __ne__(self, other: 'Comparable'):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.identity)

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
        self.properties = {}

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
    def __init__(self, style: Union[str, Mapping] = None, classes: Iterable[str] = None):
        self.styles = {}
        self.classes = []

        if isinstance(style, str):
            try:
                self.styles.update(json.loads(style))
            except json.JSONDecodeError as e:
                logging.exception('Cannot decode Json')
                raise e
            except Exception as e:
                logging.exception('Unknown Exception')
                raise e
        elif isinstance(style, Mapping):
            self.styles.update(style)

        if isinstance(classes, Mapping):
            self.classes.extend(classes)


T = TypeVar('T')


class ElementSet(metaclass=ABCMeta, Generic[T]):
    def __init__(self, elements: Iterable[T], element_type: Type[Comparable]):
        self.elements = []
        self.element_type = element_type
        if isinstance(elements, Iterable) and all(isinstance(element, self.element_type) for element in elements):
            self.elements.extend(*elements)
        else:
            raise KeyError('nodes are not all %s type' % self.element_type)

    def __getitem__(self, item):
        for element in self.elements:
            if element.identity == item:
                return element

        return None

    def __contains__(self, item):
        if isinstance(item, self.element_type):
            return item in self.elements
        if isinstance(item, str):
            return any(element.identity == item for element in self.elements)
            # TODO what about searching for names?
        return False
