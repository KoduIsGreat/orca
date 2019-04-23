from orca.core.config import OrcaConfig
from orca.core.handler import walk


class Node(object):
    def __repr__(self):
        return "orca.core.graph.Node<{0}, {1}>".format(self.name, self.connections)

    def __init__(self, name, connections, task=None, came_from=None, is_root=True):
        self.name = name
        self.connections = connections
        self.came_from = came_from
        self.task = task
        self.is_root = is_root


class Graph(object):
    def __init__(self, nodes, root):
        self.nodes = nodes
        self.roots = root

    def to_dot(self, fp, visited_nodes=None, current_node=None):
        """converts the graph to a dot file using a DFS"""
        if visited_nodes is None:
            visited_nodes = {}
        if current_node is None:
            current_node = self.roots[0]  # defaults to first root if current node is not provided
        if current_node.name in visited_nodes:
            return

        visited_nodes[current_node.name] = True
        for conn in current_node.connections:
            fp.write("\t{0} -> {1}\n".format(current_node.name, conn.name))
            self.to_dot(fp, visited_nodes, conn)

        return visited_nodes


def loads(config: OrcaConfig) -> 'Graph':
    node_map = {}
    for task in walk(config.job, visit_all_tasks=True):
        to_name = task.get('task')
        to_node = node_map.get(to_name, None)
        if to_node is None:
            to_node = Node(to_name, [], task=task)
            node_map[to_name] = to_node

        inputs = task.get('inputs', {})

        for k, v in inputs.items():
            if str(v).startswith('task.'):
                split = str(v).split('.')
                upstream_task = split[1]
                from_node = node_map.get(upstream_task, None)
                if from_node is None:
                    from_node = Node(upstream_task, [])
                    node_map[from_node.name] = from_node

                to_node.is_root = not to_node.is_root
                from_node.connections.append(to_node)

    roots = [v for k, v in node_map.items() if v.is_root]

    return Graph(node_map, roots)




