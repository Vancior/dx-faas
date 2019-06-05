import cv2
import math
import networkx as nx
import numpy as np
import random
import sys
from functools import reduce
from pprint import pprint


def parse_brite(fd):
    def _read_nodes(count):
        # id, x, y, indegree, outdegree, asid, type
        nodes = []
        for i in range(count):
            nodes.append(fd.readline().split('\t'))
        return nodes

    def _read_edges(count):
        # id, from, to, length, delay, bw, asfrom, asto, type
        edges = []
        for i in range(count):
            edges.append(fd.readline().split('\t'))
        return edges

    while True:
        line = fd.readline().split(' ')
        if line[0] == 'Nodes:':
            nodes = _read_nodes(int(line[2]))
        elif line[0] == 'Edges:':
            edges = _read_edges(int(line[2]))
            break

    def _p(array, indexes):
        for i in indexes:
            array[i] = int(float(array[i]))

    for i in nodes:
        _p(i, [0, 1, 2, 3, 4, 5])
    for i in edges:
        _p(i, [0, 1, 2, 3, 4, 5, 6, 7])
    return nodes, edges


def step2(nodes):
    result = set()
    degree_sum = 0
    for n in nodes:
        degree_sum += n[3]
    avg = degree_sum / len(nodes)
    for idx, n in enumerate(nodes):
        if n[3] > avg:
            result.add(idx)
    return result


def step3(nodes, edges, b_set):
    graph = nx.Graph()
    for e in edges:
        graph.add_edge(e[1], e[2])

    parent_table = {}
    visited = {}
    bb_set = b_set.copy()
    queue = [list(b_set)[0]]

    while len(queue) > 0:
        v = queue.pop(0)
        visited[v] = True
        parent = parent_table.get(v)
        if v in bb_set and parent is not None and parent not in bb_set:
            p = parent
            while p not in bb_set:
                bb_set.add(p)
                p = parent_table.get(p)
        for n in nx.neighbors(graph, v):
            if n not in queue and visited.get(n) is not True:
                parent_table[n] = v
                queue.append(n)
            elif v in bb_set and parent_table.get(
                    n) is not None and parent_table.get(n) not in bb_set:
                parent_table[n] = v
    return bb_set


def visualize(nodes, edges, b_set, scale=1):
    plane = np.full((1010, 1010, 3), 255, dtype=np.uint8)

    for n in nodes:
        n[1] //= scale
        n[2] //= scale

    radius = 8
    # NOTE draw nodes
    e_set = set(list(range(len(nodes)))) - b_set
    for i in list(b_set):
        node = nodes[i]
        cv2.circle(plane, (node[1], node[2]), radius,
                   (255, 0, 0), lineType=cv2.LINE_AA, thickness=2)
    for i in list(e_set):
        node = nodes[i]
        cv2.circle(plane, (node[1], node[2]), radius, (0, 255, 0),
                   lineType=cv2.LINE_AA, thickness=2)

    # NOTE draw edges
    radius += 3
    for e in edges:
        _from = [nodes[e[1]][1], nodes[e[1]][2]]
        _to = [nodes[e[2]][1], nodes[e[2]][2]]
        x = _to[0] - _from[0]
        y = _to[1] - _from[1]
        length = math.sqrt(x * x + y * y)
        _from[0] += x * radius / length
        _from[1] += y * radius / length
        _to[0] -= x * radius / length
        _to[1] -= y * radius / length
        for i in [0, 1]:
            _from[i] = int(_from[i])
            _to[i] = int(_to[i])
        cv2.line(plane, tuple(_from), tuple(_to), (200, 200, 200),
                 thickness=1, lineType=cv2.LINE_AA)

    cv2.imshow('show', plane)
    if cv2.waitKey(0):
        pass


if __name__ == '__main__':
    brite_name = sys.argv[1]
    scale = 1
    if len(sys.argv) == 3:
        scale = int(sys.argv[2])
    nodes, edges = parse_brite(open(brite_name))
    # length = int(len(edges) * 0.7)
    # random.shuffle(edges)
    # edges = edges[:length]
    # pprint(nodes)
    # pprint(edges)
    b_set = step2(nodes)
    print(sorted(list(b_set)))
    b_set = step3(nodes, edges, b_set)
    print(sorted(list(b_set)))
    visualize(nodes, edges, b_set, scale)
