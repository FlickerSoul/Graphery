from .Base import Comparable, HasProperty, Stylable, ElementSet
from typing import Iterable, Mapping, Union

from .Errors import GraphJsonFormatError


class Node(Comparable, HasProperty, Stylable):
    _PREFIX = 'v'

    def __init__(self, identity: str, name: str = None,
                 styles: Union[str, Mapping] = None, classes: Iterable = None):
        """
        create an node with an identity
        @param identity:
        @param name:
        @param styles: the styles applied to this node
        @param classes: the classes applied to this node
        """
        Comparable.__init__(self, identity, name)
        HasProperty.__init__(self)
        Stylable.__init__(self, styles, classes)

    def __str__(self):
        return 'Node(id: %s)' % self.identity

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def return_node(identity: Union[str, 'Node'], styles=None, classes=None):
        if isinstance(identity, str):
            return Node(identity=identity, styles=styles, classes=classes)
        elif isinstance(identity, Node):
            return identity
        else:
            raise TypeError(f'identity must be a string or a node instance. You gave {type(identity)}')


class NodeSet(ElementSet):
    def __init__(self, nodes: Iterable[Node]):
        """
        Create an edge set with a pile of elements.
        @param nodes:
        """
        super(NodeSet, self).__init__(nodes, Node)

    @staticmethod
    def generate_node_set(nodes: Iterable[Mapping]) -> 'NodeSet':
        stored_nodes = []
        for node in nodes:
            if not (isinstance(node, Mapping) and 'data' in node):
                raise GraphJsonFormatError(f'invalid format for Node {node}')

            data_field = node['data']
            if not ('id' in data_field):
                raise GraphJsonFormatError(f'The node {node} entry must contain a `id` field')

            stored_node = Node(data_field['id'])
            if 'displayed' in data_field:
                stored_node.update_properties(data_field['displayed'])
            stored_nodes.append(stored_node)

        return NodeSet(stored_nodes)


class MutableNodeSet(NodeSet):
    def __init__(self, nodes: Iterable[Node] = ()):
        super().__init__(nodes)

    def add_node(self, node: Node):
        if not isinstance(node, self.element_type):
            raise TypeError(f'The Mutable Node Set Only Accept {self.element_type}')
        self.elements.append(node)

    def remove_node(self, node: Node):
        if not isinstance(node, self.element_type):
            raise TypeError(f'Why do you want to remove {type(node)} from Nodes?')
        self.elements.remove(node)

    def add_nodes(self, edges: Iterable[Node]) -> None:
        for element in edges:
            self.add_node(element)

    def remove_nodes(self, edges: Iterable[Node]) -> None:
        for element in edges:
            self.remove_node(element)
