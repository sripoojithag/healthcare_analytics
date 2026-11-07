"""
Clinical Co-morbidity & Diagnostic Relationship Graph (BFS & DFS Traversal).

Use Case:
In diabetic inpatient analysis, patients rarely present with an isolated condition.
Primary diagnoses frequently link with secondary co-morbidities (e.g., Type 2 Diabetes
ICD-9 250 strongly correlates with Circulatory disorders 410-427, Renal complications
580-589, and Peripheral Neuropathy). 

A graph abstraction models:
- Vertices (V): Diagnostic categories / ICD-9 chapters.
- Edges (E): Observed clinical transitions and co-occurring conditions.

Graph Traversal Algorithms:
1. Breadth-First Search (BFS):
   - Level-order exploration discovering the nearest / direct co-morbidities first.
   - Guaranteed shortest path (in terms of clinical hops) in unweighted co-morbidity networks.
   - Uses a FIFO queue (collections.deque).
   - Handles cycles via a 'visited' set.
   - Disconnected graph support: can optionally restart across all unvisited components.

2. Depth-First Search (DFS):
   - Deep disease progression pathway exploration.
   - Uses a LIFO call stack (or explicit stack).
   - Cycle detection via recursion state tracking (3-color state: unvisited, visiting, visited).
   - Handles disconnected components by iterating over remaining vertices.

Time Complexity:
- BFS: O(V + E) — visits every reachable vertex and examines every incident edge once.
- DFS: O(V + E) — traverses every vertex and explores each edge once.
- Shortest Path: O(V + E) — BFS-based unweighted path reconstruction.
- Connected Components: O(V + E) — single-pass component decomposition.

Space Complexity:
- O(V) auxiliary space for visited set, queue/call stack, and predecessor map.
"""

from collections import deque
from typing import Any, Dict, List, Optional, Set, Tuple


class ClinicalComorbidityGraph:
    """
    Adjacency list representation of clinical diagnosis categories and co-morbidity relationships.
    Supports directed and undirected modes, cycle protection, and disconnected component traversal.
    """

    def __init__(self, directed: bool = False) -> None:
        self.directed = directed
        self._adj: Dict[str, Dict[str, float]] = {}  # node -> {neighbor: weight}

    @property
    def nodes(self) -> List[str]:
        """Returns all registered diagnosis nodes."""
        return list(self._adj.keys())

    @property
    def edge_count(self) -> int:
        """Returns total number of directed or undirected edges."""
        count = sum(len(neighbors) for neighbors in self._adj.values())
        return count if self.directed else count // 2

    def add_node(self, node: str) -> None:
        """Adds a diagnosis category node if not already present."""
        node_clean = str(node).strip()
        if not node_clean:
            raise ValueError("Node identifier must not be empty")
        if node_clean not in self._adj:
            self._adj[node_clean] = {}

    def add_edge(self, source: str, target: str, weight: float = 1.0) -> None:
        """
        Adds a directed or undirected edge representing co-morbidity between two conditions.
        """
        src = str(source).strip()
        tgt = str(target).strip()
        if not src or not tgt:
            raise ValueError("Source and target node identifiers must not be empty")

        self.add_node(src)
        self.add_node(tgt)

        self._adj[src][tgt] = float(weight)
        if not self.directed:
            self._adj[tgt][src] = float(weight)

    def get_neighbors(self, node: str) -> Dict[str, float]:
        """Returns adjacent nodes and edge weights for a given condition."""
        return self._adj.get(node, {})

    def bfs(self, start_node: str, visit_all_components: bool = False) -> List[str]:
        """
        Breadth-First Search traversal starting from start_node.

        Safely handles cycles using a visited set.
        If visit_all_components is True, restarts from unvisited nodes to cover disconnected subgraphs.

        Time Complexity: O(V + E)
        Space Complexity: O(V)
        """
        if not self._adj:
            return []

        start = str(start_node).strip()
        if start not in self._adj:
            raise KeyError(f"Start node '{start}' does not exist in graph")

        visited: Set[str] = set()
        traversal_order: List[str] = []
        queue: deque[str] = deque([start])
        visited.add(start)

        while queue:
            current = queue.popleft()
            traversal_order.append(current)

            for neighbor in self._adj.get(current, {}):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        # Handle disconnected components if requested
        if visit_all_components:
            for remaining_node in self._adj:
                if remaining_node not in visited:
                    visited.add(remaining_node)
                    queue.append(remaining_node)
                    while queue:
                        curr = queue.popleft()
                        traversal_order.append(curr)
                        for neighbor in self._adj.get(curr, {}):
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)

        return traversal_order

    def dfs(
        self,
        start_node: str,
        visit_all_components: bool = False,
        iterative: bool = False,
    ) -> List[str]:
        """
        Depth-First Search traversal starting from start_node.

        Safely handles cycles using a visited set.
        Supports both recursive and iterative stack implementations.

        Time Complexity: O(V + E)
        Space Complexity: O(V)
        """
        if not self._adj:
            return []

        start = str(start_node).strip()
        if start not in self._adj:
            raise KeyError(f"Start node '{start}' does not exist in graph")

        visited: Set[str] = set()
        traversal_order: List[str] = []

        if iterative:
            # Iterative DFS with explicit stack
            stack: List[str] = [start]
            while stack:
                current = stack.pop()
                if current not in visited:
                    visited.add(current)
                    traversal_order.append(current)
                    # Push neighbors (reversed for intuitive deterministic left-to-right order)
                    neighbors = sorted(list(self._adj.get(current, {}).keys()), reverse=True)
                    for neighbor in neighbors:
                        if neighbor not in visited:
                            stack.append(neighbor)
        else:
            # Recursive DFS
            def _dfs_recursive(node: str) -> None:
                visited.add(node)
                traversal_order.append(node)
                for neighbor in sorted(self._adj.get(node, {}).keys()):
                    if neighbor not in visited:
                        _dfs_recursive(neighbor)

            _dfs_recursive(start)

        # Handle disconnected components
        if visit_all_components:
            for remaining in sorted(self._adj.keys()):
                if remaining not in visited:
                    if iterative:
                        stack = [remaining]
                        while stack:
                            curr = stack.pop()
                            if curr not in visited:
                                visited.add(curr)
                                traversal_order.append(curr)
                                for nbr in sorted(list(self._adj.get(curr, {}).keys()), reverse=True):
                                    if nbr not in visited:
                                        stack.append(nbr)
                    else:
                        def _dfs_rem(n: str) -> None:
                            visited.add(n)
                            traversal_order.append(n)
                            for nbr in sorted(self._adj.get(n, {}).keys()):
                                if nbr not in visited:
                                    _dfs_rem(nbr)
                        _dfs_rem(remaining)

        return traversal_order

    def find_shortest_path(self, start_node: str, target_node: str) -> Optional[List[str]]:
        """
        Finds the shortest unweighted path (minimum diagnosis hops) between two conditions using BFS.

        Time Complexity: O(V + E)
        Space Complexity: O(V)

        Returns:
            List of node names representing the path from start_node to target_node,
            or None if no path exists.
        """
        start = str(start_node).strip()
        target = str(target_node).strip()

        if start not in self._adj or target not in self._adj:
            return None

        if start == target:
            return [start]

        visited: Set[str] = {start}
        predecessor: Dict[str, str] = {}
        queue: deque[str] = deque([start])

        found = False
        while queue:
            current = queue.popleft()
            if current == target:
                found = True
                break

            for neighbor in self._adj.get(current, {}):
                if neighbor not in visited:
                    visited.add(neighbor)
                    predecessor[neighbor] = current
                    queue.append(neighbor)

        if not found:
            return None

        # Reconstruct path by backtracking predecessors
        path = []
        curr: Optional[str] = target
        while curr is not None:
            path.append(curr)
            curr = predecessor.get(curr)

        path.reverse()
        return path

    def has_cycle(self) -> bool:
        """
        Detects whether the graph contains any cycle.

        For directed graphs: uses 3-color DFS state (0=white/unvisited, 1=gray/visiting, 2=black/done).
        For undirected graphs: uses parent tracking to avoid false positives on back-edges.

        Time Complexity: O(V + E)
        Space Complexity: O(V)
        """
        if not self._adj:
            return False

        if self.directed:
            # 0 = unvisited, 1 = in progress (ancestor), 2 = completed
            state: Dict[str, int] = {node: 0 for node in self._adj}

            def _dfs_cycle_directed(node: str) -> bool:
                state[node] = 1
                for neighbor in self._adj.get(node, {}):
                    if state[neighbor] == 1:
                        return True  # Found back-edge to ancestor in current DFS stack
                    if state[neighbor] == 0:
                        if _dfs_cycle_directed(neighbor):
                            return True
                state[node] = 2
                return False

            for n in self._adj:
                if state[n] == 0:
                    if _dfs_cycle_directed(n):
                        return True
            return False
        else:
            # Undirected graph cycle check
            visited: Set[str] = set()

            def _dfs_cycle_undirected(node: str, parent: Optional[str]) -> bool:
                visited.add(node)
                for neighbor in self._adj.get(node, {}):
                    if neighbor not in visited:
                        if _dfs_cycle_undirected(neighbor, node):
                            return True
                    elif neighbor != parent:
                        return True  # Visited neighbor that is not immediate parent = cycle
                return False

            for n in self._adj:
                if n not in visited:
                    if _dfs_cycle_undirected(n, None):
                        return True
            return False

    def get_connected_components(self) -> List[List[str]]:
        """
        Partitions the graph into isolated or connected components.
        For undirected graphs, each component is a maximal connected subgraph.

        Time Complexity: O(V + E)
        Space Complexity: O(V)
        """
        visited: Set[str] = set()
        components: List[List[str]] = []

        for node in sorted(self._adj.keys()):
            if node not in visited:
                comp_members = self.bfs(node, visit_all_components=False)
                visited.update(comp_members)
                components.append(comp_members)

        return components

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the graph topology for JSON API responses."""
        nodes_list = [{"id": n, "label": n} for n in self._adj]
        edges_list = []
        seen_edges: Set[Tuple[str, str]] = set()

        for src, neighbors in self._adj.items():
            for tgt, weight in neighbors.items():
                if not self.directed:
                    edge_key = tuple(sorted([src, tgt]))
                    if edge_key in seen_edges:
                        continue
                    seen_edges.add(edge_key)  # type: ignore

                edges_list.append({
                    "source": src,
                    "target": tgt,
                    "weight": weight,
                })

        return {
            "directed": self.directed,
            "node_count": len(self._adj),
            "edge_count": self.edge_count,
            "nodes": nodes_list,
            "edges": edges_list,
        }


def build_uci_diabetes_comorbidity_graph() -> ClinicalComorbidityGraph:
    """
    Factory constructing a representative clinical co-morbidity network
    derived from the UCI Diabetes Inpatient Dataset.

    Models primary disease nodes (Diabetes, Circulatory, Respiratory, Renal, etc.)
    and clinical transition associations.
    """
    g = ClinicalComorbidityGraph(directed=False)

    # Core high-frequency clinical co-morbidities
    g.add_edge("Diabetes", "Circulatory", weight=0.88)
    g.add_edge("Diabetes", "Renal", weight=0.74)
    g.add_edge("Circulatory", "Respiratory", weight=0.69)
    g.add_edge("Circulatory", "Hypertension", weight=0.85)
    g.add_edge("Diabetes", "Neurological", weight=0.55)
    g.add_edge("Respiratory", "Digestive", weight=0.42)
    g.add_edge("Digestive", "Genitourinary", weight=0.38)
    g.add_edge("Musculoskeletal", "Injury", weight=0.61)
    g.add_edge("Injury", "Circulatory", weight=0.33)

    # Disconnected component demonstrating graph robustness for rare / isolated conditions
    g.add_edge("Ophthalmology", "Retinopathy", weight=0.72)
    g.add_node("Dermatology_Isolated")  # Single isolated node

    return g
