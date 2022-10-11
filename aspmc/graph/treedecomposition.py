"""
Tree Decomposition module that introduces a tree decomposition class, a bag class and ways to construct tree decompositions.
"""

import networkx as nx
import subprocess
import inspect
import os
import queue
import logging
import time

src_path = os.path.abspath(os.path.realpath(inspect.getfile(inspect.currentframe())))
src_path = os.path.realpath(os.path.join(src_path, '../../external'))

logger = logging.getLogger("aspmc")

class Bag(object):
    """A class for bags of tree decompositions.

    Args:
        idx (:obj:`int`): The unique ID of this bag in the tree decomposition.
        vertices (:obj:`set`): The vertices in this bag.
        children (:obj:`list`): The children (also bags) of this bag in the tree decomposition.

    Attributes:
        idx (:obj:`int`): The unique ID of this bag in the tree decomposition.
        vertices (:obj:`set`): The vertices in this bag.
        children (:obj:`list`): The children (also bags) of this bag in the tree decomposition.
    """
    def __init__(self, idx, vertices, children):
        self.idx = idx
        self.vertices = vertices
        self.children = children

class TreeDecomposition(object):
    """A class for tree decompositions.

    Allows manipulation and iteration in post order.

    Args:
        bags (:obj:`int`): The number of bags this tree decomposition has.
        width (:obj:`int`): The width of this tree decomposition.
        vertices (:obj:`int`): The number of vertices in this tree decomposition.
        tree (:obj:`nx.Graph`): The graph representing the actual tree decomposition. 
            Must have a node attribute "bag" that contains all the vertices in the bag of the node.
        root (:obj:`int`, optional): Which node should be the root of the tree. Defaults to 1. 
        The root is only set if this argument is not `None`.


    Attributes:
        bags (:obj:`int`): The number of bags this tree decomposition has.
        width (:obj:`int`): The width of this tree decomposition.
        vertices (:obj:`int`): The number of vertices in this tree decomposition.
        tree (:obj:`nx.Graph`): The graph representing the actual tree decomposition. 
            Has a node attribute "bag" that contains the bag object for the node. 
            (Requires that `set_root` has been run already. This is typically done in the constructor if `root` is not `None`.)
        root (:obj:`int`): Which node is the root of the tree. 
    """
    def __init__(self, bags, width, vertices, tree, root = 1):
        self.bags = bags
        self.width = width
        self.vertices = vertices
        self.tree = tree
        self.root = None
        if root is not None:
            self.set_root(root)

    def get_root(self):
        """Return the bag of the root node.

        Returns:
            :obj:`Bag`: The bag of the root node.
        """
        return self.tree.nodes[self.root]["bag"]

    def get_bag(self, node):
        """Return the bag of given node.

        Args:
            node (:obj:`int`): The id of the node in the tree decomposition.

        Returns:
            :obj:`Bag`: The bag of the node.
        """
        return self.tree.nodes[node]["bag"]

    def set_root(self, root):
        """Sets the root of the tree decomposition.
        Updates the "bag" attributes of the tree so that the bags have the correct children.

        Args:
            root (:obj:`int`): The id of the root to be.

        Returns:
            None
        """
        first = self.root is None
        self.root = root
        stack = queue.LifoQueue()
        stack.put((-1, self.root, self.tree.neighbors(self.root)))
        while not stack.empty():
            parent, cur, neighbors = stack.get()
            try:
                neigh = next(neighbors)
                if neigh == parent:
                    neigh = next(neighbors)
                stack.put((parent, cur, neighbors))
                stack.put((cur, neigh, self.tree.neighbors(neigh)))
            except:
                if first:
                    vertices = self.tree.nodes[cur]["bag"]
                else:
                    vertices = self.tree.nodes[cur]["bag"].vertices
                self.tree.nodes[cur]["bag"] = Bag(cur, vertices, [ self.tree.nodes[x]["bag"] for x in self.tree.neighbors(cur) if x != parent ])

    def find_centroid(self):
        import sys
        if self.root is None:
            self.set_root(1)
        if self.bags == 1:
            return 1
        stack = queue.LifoQueue()
        stack.put((-1, self.root, self.tree.neighbors(self.root), 0))
        while not stack.empty():
            finished = True
            while finished:
                finished = False
                parent, cur, neighbors, count = stack.get()
                try:
                    neigh = next(neighbors)
                    if neigh == parent:
                        neigh = next(neighbors)
                    stack.put((parent, cur, neighbors, count))
                    stack.put((cur, neigh, self.tree.neighbors(neigh), 0))
                except StopIteration:
                    finished = True
                    here_count = len(self.get_bag(cur).vertices.difference(self.get_bag(parent).vertices))
                    here_count += count
                    pp, pc, pn, pcount = stack.get()
                    if here_count + pcount > self.vertices//2:
                        return pc
                    stack.put((pp, pc, pn, pcount + here_count))


    def __iter__(self):
        if self.root is None:
            self.set_root(1)
        stack = queue.LifoQueue()
        stack.put((-1, self.root, self.tree.neighbors(self.root)))
        while not stack.empty():
            parent, cur, neighbors = stack.get()
            try:
                neigh = next(neighbors)
                if neigh == parent:
                    neigh = next(neighbors)
                stack.put((parent, cur, neighbors))
                stack.put((cur, neigh, self.tree.neighbors(neigh)))
            except:
                yield cur

    def __str__(self):
        res = f"s tw {self.bags} {self.width} {self.vertices}\n"
        for bag in self.bag_iter():
            res += f"b {bag.idx} {' '.join([ str(v) for v in bag.vertices ])}\n"
        for bag in self.bag_iter():
            for neigh in bag.children:
                res += f"{bag.idx} {neigh.idx}\n"
        return res

    def bag_iter(self, order = "post-order"): 
        """Iterate over all the bags in post order.

        Args:
            order (:obj:`string`, optional): Which order the bags should be iterated over. 
            Currently supported are "post-order" and "pre-order". Defaults to "post-order".

        Returns:
            :obj:`iterator`: Yields over the bags in the specified order.
        """    
        if order == "post-order":
            for bag in self:
                yield self.tree.nodes[bag]["bag"]
        elif order == "pre-order":
            if self.root is None:
                self.set_root(1)
            stack = queue.LifoQueue()
            stack.put((-1, self.root, self.tree.neighbors(self.root)))
            yield self.get_bag(self.root)
            while not stack.empty():
                parent, cur, neighbors = stack.get()
                try:
                    neigh = next(neighbors)
                    if neigh == parent:
                        neigh = next(neighbors)
                    stack.put((parent, cur, neighbors))
                    stack.put((cur, neigh, self.tree.neighbors(neigh)))
                    yield self.get_bag(neigh)
                except:
                    continue
        else:
            logger.error(f"Unsupported order {order}.")
            exit(-1)

    def find_containing(self, vertices):
        """Find a bag containing all the vertices in `vertices`.

        Args:
            vertices (:obj:`set`): The vertices that should be contained in the desired bag.

        Returns:
            :obj:`Bag`: A bag containg all the vertices in `vertices` or `None` if there is no such bag.
        """
        for t in self:
            if self.tree.nodes[t]["bag"].vertices.issuperset(vertices):
                return t

    def remove(self, vertices):
        """Remove the vertices in `vertices` from all bags.

        Args:
            vertices (:obj:`set`): The vertices that should be removed.

        Returns:
            None
        """
        for t in self:
            self.tree.nodes[t]["bag"].vertices.difference_update(vertices)
                
    def draw(self):
        """Visualizes this tree decompisition by showing a plot of it. 
        Mostly useful for debugging.

        Returns:
            None
        """
        import matplotlib.pyplot as plt
        from networkx.drawing.nx_pydot import graphviz_layout
        labels = { v : str((v, self.tree.nodes[v]["bag"])) for v in self.tree.nodes }
        pos = graphviz_layout(self.tree, prog="dot")
        nx.draw(self.tree, pos)
        nx.draw_networkx_labels(self.tree, pos, labels)
        plt.tight_layout()
        plt.axis("off")
        plt.show()


                


def from_file(path):
    """Reads a tree decomposition from a file.

    Args:
        path (:obj:`string`): The path to the file containing the tree decomposition.

    Returns:
        :obj:`TreeDecomposition`: The tree decomposition specified in the file.
    """
    with open(path, "r") as input:
        for line in input:
            line = line.split()
            if len(line) == 0: 
                continue
            if line[0] == 's':
                bags = int(line[2])
                width = int(line[3])
                vertices = int(line[4])
                tree = nx.Graph()
                tree.add_nodes_from(range(1,bags + 1))
            elif line[0] == 'b':
                tree.nodes[int(line[1])]["bag"] = set([ int(x) for x in line[2:] ])
            else:
                tree.add_edge(int(line[0]), int(line[1]))
    return TreeDecomposition(bags, width, vertices, tree)

def from_stream(stream):
    """Reads a tree decomposition from a stream.

    Args:
        stream (:obj:`string`): The stream with the tree decomposition. Must be binary.

    Returns:
        :obj:`TreeDecomposition`: The tree decomposition specified in the stream.
    """
    for line in stream.read().decode().split('\n'):
        line = line.split()
        if len(line) == 0: 
            continue
        if line[0] == 's':
            bags = int(line[2])
            width = int(line[3])
            vertices = int(line[4])
            tree = nx.Graph()
            tree.add_nodes_from(range(1,bags + 1))
        elif line[0] == 'b':
            tree.nodes[int(line[1])]["bag"] = set([ int(x) for x in line[2:] ])
        else:
            tree.add_edge(int(line[0]), int(line[1]))
    return TreeDecomposition(bags, width, vertices, tree)

def from_graph(graph, solver = "flow-cutter", timeout = "1"):
    """Constructs a tree decomposition from a graph.

    Args:
        solver (:obj:`string`, optional): The solver to generate the tree decomposition. 
        Currently supported is "flow-cutter". Defaults to "flow-cutter".
        timeout (:obj:`string`, optional): After how much time to kill the solver in seconds. Defaults to "1".

    Returns:
        :obj:`TreeDecomposition`: The tree decomposition output by the solver.
    """
    timeout = float(timeout)
    start = time.time()
    node_map = dict()
    map_node = dict()
    idx = 1
    for node in graph.nodes:
        node_map[node] = idx
        map_node[idx] = node
        idx += 1
    if solver == "flow-cutter":
        p = subprocess.Popen([os.path.join(src_path, "flow-cutter/flow_cutter_pace17")], stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds = True)
    else:
        logger.error(f"Unknown td-solver {solver}")    
    # with open("debug.gr", "wb") as debug_gr:
    #    debug_gr.write(f"p tw {len(graph.nodes)} {len(graph.edges)}\n".encode())
    #    for (v,vp) in graph.edges:
    #        debug_gr.write(f"{node_map[v]} {node_map[vp]}\n".encode())
    p.stdin.write(f"p tw {len(graph.nodes)} {len(graph.edges)}\n".encode())
    for (v,vp) in graph.edges:
        p.stdin.write(f"{node_map[v]} {node_map[vp]}\n".encode())
    p.stdin.flush()
    p.stdin.close()
    first = False
    while p.poll() is None and not first:
        line = p.stdout.readline().decode()
        first = line.startswith("c status")
    time_left = timeout - (time.time() - start)
    try:
        p.wait(time_left)
    except subprocess.TimeoutExpired:
        p.terminate()
    for line in p.stdout.read().decode().split('\n'):
        line = line.split()
        if len(line) == 0: 
            continue
        if line[0] == 's':
            bags = int(line[2])
            width = int(line[3])
            vertices = int(line[4])
            tree = nx.Graph()
            tree.add_nodes_from(range(1,bags + 1))
        elif line[0] == 'b':
            tree.nodes[int(line[1])]["bag"] = set([ map_node[int(x)] for x in line[2:] ])
        elif line[0] == 'c':
            continue
        else:
            tree.add_edge(int(line[0]), int(line[1]))
    p.stdout.close()
    p.wait()
    return TreeDecomposition(bags, width, vertices, tree)

def from_hypergraph(hypergraph, solver = "flow-cutter", timeout = "1"):
    """Constructs a tree decomposition from a hypergraph.

    Args:
        solver (:obj:`string`, optional): The solver to generate the tree decomposition. 
        Currently supported is "flow-cutter". Defaults to "flow-cutter".
        timeout (:obj:`string`, optional): After how much time to kill the solver in seconds. Defaults to "1".

    Returns:
        :obj:`TreeDecomposition`: The tree decomposition output by the solver.
    """
    if solver == "flow-cutter":
        return from_graph(hypergraph.to_graph(), solver = solver, timeout = timeout)
    else:
        logger.error(f"Unknown td-solver {solver}")   





