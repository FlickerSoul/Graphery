from .Node import Node, NodeSet
from .Edge import Edge, EdgeSet
import json
from typing import Iterable, Union, Optional, Mapping


class Graph:
    """
    The graph object
    """
    def __init__(self, nodes: Iterable[Node], edges: Iterable[Edge]):
        if isinstance(nodes, NodeSet):
            self.node_set = nodes
        else:
            self.node_set = NodeSet(nodes)

        if isinstance(edges, EdgeSet):
            self.edge_set = edges
        else:
            self.edge_set = EdgeSet(edges)

        self.high_light_classes = []

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        get a node by the node id
        @param node_id:
        @return: the node instance or None
        """
        return self.node_set[node_id]

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """
        get an edge by the edge id
        @param edge_id:
        @return: the edge instance or None
        """
        return self.edge_set[edge_id]

    def has_node(self, node: Union[str, Node]) -> bool:
        """
        Check if an node is in this graph
        @param node: a Node instance or the id of a node
        @return: boolean indicating the result
        """
        return self.node_set[node]

    def has_edge(self, edge: Union[str, Edge]) -> bool:
        """
        Check if an edge is in this graph
        @param edge: an Edge instance or the id of an edge
        @return: boolean indicating the result
        """
        return self.edge_set[edge]

    @staticmethod
    def graph_generator(graph_json: str = ''):
        """
        generate a graph instance from json
        template:
        {
            elements: {
                nodes: [
                    {
                        data: { id: 'a', ..., displayed: { /* the properties that should tracked and displayed */}},
                        ...
                    },
                    ...
                ],
                edges: [
                    {
                        data: { id: 'ab', source: 'a', target: 'b', ...,
                                displayed: { /* the properties that should tracked and displayed */}
                              },
                        ...
                    },
                    ...
                ]
            },
            layout: { // omitted },
            style: [ { selector: '***', style: {'label': 'data(id)', ...}, ... ]
        }

        @param graph_json:
        @return: a graph instance built from the given json
        """
        try:
            graph_dict = json.loads(graph_json)
            # TODO do not support json5
        except json.JSONDecodeError as e:
            logging.exception(e)
            raise e

        if 'elements' in graph_dict:
            element_dict = graph_dict['elements']
            if isinstance(element_dict, Mapping):
                parsed_node_set = []
                parsed_edge_set = []
                if 'nodes' in element_dict:
                    parsed_node_set = NodeSet.generate_node_set(element_dict['nodes'])
                if 'edges' in element_dict:
                    parsed_edge_set = EdgeSet.generate_edge_set(element_dict['edges'], parsed_node_set)

                return Graph(parsed_node_set, parsed_edge_set)
            else:
                raise NotImplementedError('The other json format is not supported for now')

