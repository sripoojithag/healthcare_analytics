"""
Unit Tests for Phase 8: Data Structures & Algorithms (Priority Queue & Graph Traversal).
"""

import pytest
from src.dsa.priority_queue import ClinicalTriagePriorityQueue, ClinicalReviewItem
from src.dsa.graph import ClinicalComorbidityGraph, build_uci_diabetes_comorbidity_graph


class TestClinicalTriagePriorityQueue:
    """Tests for the heap-based clinical triage priority queue."""

    def test_empty_queue_initial_state(self):
        pq = ClinicalTriagePriorityQueue()
        assert pq.is_empty() is True
        assert pq.size() == 0
        assert pq.peek() is None
        assert pq.dequeue_safe() is None
        with pytest.raises(IndexError, match="Cannot dequeue from an empty"):
            pq.dequeue()

    def test_single_enqueue_dequeue(self):
        pq = ClinicalTriagePriorityQueue()
        item = pq.enqueue(
            encounter_id="ENC-001",
            patient_id="PT-001",
            risk_score=0.75,
            time_in_hospital=4,
            num_medications=12,
            primary_diagnosis="Diabetes",
        )
        assert pq.is_empty() is False
        assert pq.size() == 1
        assert pq.peek() == item

        popped = pq.dequeue()
        assert popped.encounter_id == "ENC-001"
        assert popped.risk_score == 0.75
        assert pq.is_empty() is True

    def test_priority_ordering_highest_risk_first(self):
        pq = ClinicalTriagePriorityQueue()
        pq.enqueue("E-LOW", "P-1", risk_score=0.20)
        pq.enqueue("E-HIGH", "P-2", risk_score=0.89)
        pq.enqueue("E-MED", "P-3", risk_score=0.55)

        first = pq.dequeue()
        second = pq.dequeue()
        third = pq.dequeue()

        assert first.encounter_id == "E-HIGH"
        assert second.encounter_id == "E-MED"
        assert third.encounter_id == "E-LOW"

    def test_tie_breaking_rules(self):
        pq = ClinicalTriagePriorityQueue()
        # Same risk (0.70), different stay
        pq.enqueue("E-STAY-SHORT", "P-1", risk_score=0.70, time_in_hospital=2, num_medications=10)
        pq.enqueue("E-STAY-LONG", "P-2", risk_score=0.70, time_in_hospital=8, num_medications=10)

        assert pq.dequeue().encounter_id == "E-STAY-LONG"
        assert pq.dequeue().encounter_id == "E-STAY-SHORT"

        # Same risk (0.70) and stay (5), different medication count
        pq.enqueue("E-FEW-MEDS", "P-3", risk_score=0.70, time_in_hospital=5, num_medications=5)
        pq.enqueue("E-MANY-MEDS", "P-4", risk_score=0.70, time_in_hospital=5, num_medications=25)

        assert pq.dequeue().encounter_id == "E-MANY-MEDS"
        assert pq.dequeue().encounter_id == "E-FEW-MEDS"

        # Identical risk, stay, and meds -> deterministic FIFO order
        pq.enqueue("E-FIRST", "P-5", risk_score=0.60, time_in_hospital=4, num_medications=10)
        pq.enqueue("E-SECOND", "P-6", risk_score=0.60, time_in_hospital=4, num_medications=10)

        assert pq.dequeue().encounter_id == "E-FIRST"
        assert pq.dequeue().encounter_id == "E-SECOND"

    def test_invalid_input_handling(self):
        pq = ClinicalTriagePriorityQueue()
        with pytest.raises(ValueError):
            pq.enqueue("", "PT-01", risk_score=0.5)

        with pytest.raises(ValueError):
            pq.enqueue("ENC-01", "", risk_score=0.5)

        # Clamping of out-of-range risk scores
        item_high = pq.enqueue("E-HIGH", "P-1", risk_score=1.5)
        assert item_high.risk_score == 1.0

        item_low = pq.enqueue("E-LOW", "P-2", risk_score=-0.5)
        assert item_low.risk_score == 0.0

    def test_to_sorted_list_and_clear(self):
        pq = ClinicalTriagePriorityQueue()
        pq.enqueue("E1", "P1", risk_score=0.3)
        pq.enqueue("E2", "P2", risk_score=0.9)
        pq.enqueue("E3", "P3", risk_score=0.6)

        sorted_list = pq.to_sorted_list()
        assert len(sorted_list) == 3
        assert [x.encounter_id for x in sorted_list] == ["E2", "E3", "E1"]
        # Ensure heap was not mutated by to_sorted_list
        assert pq.size() == 3

        pq.clear()
        assert pq.is_empty() is True
        assert pq.size() == 0


class TestClinicalComorbidityGraph:
    """Tests for the clinical co-morbidity graph traversal algorithms."""

    def test_empty_graph(self):
        g = ClinicalComorbidityGraph()
        assert len(g.nodes) == 0
        assert g.edge_count == 0
        assert g.bfs("Diabetes") == []
        assert g.dfs("Diabetes") == []
        assert g.has_cycle() is False
        assert g.get_connected_components() == []

    def test_node_and_edge_addition(self):
        g = ClinicalComorbidityGraph(directed=False)
        g.add_edge("Diabetes", "Circulatory", weight=0.85)

        assert "Diabetes" in g.nodes
        assert "Circulatory" in g.nodes
        assert g.edge_count == 1
        assert g.get_neighbors("Diabetes")["Circulatory"] == 0.85
        assert g.get_neighbors("Circulatory")["Diabetes"] == 0.85

    def test_bfs_traversal(self):
        g = ClinicalComorbidityGraph(directed=False)
        g.add_edge("A", "B")
        g.add_edge("A", "C")
        g.add_edge("B", "D")
        g.add_edge("C", "E")

        bfs_result = g.bfs("A")
        assert bfs_result[0] == "A"
        # B and C are level 1
        assert set(bfs_result[1:3]) == {"B", "C"}
        # D and E are level 2
        assert set(bfs_result[3:5]) == {"D", "E"}

    def test_dfs_traversal_recursive_and_iterative(self):
        g = ClinicalComorbidityGraph(directed=False)
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("A", "D")

        rec_dfs = g.dfs("A", iterative=False)
        it_dfs = g.dfs("A", iterative=True)

        assert rec_dfs[0] == "A"
        assert set(rec_dfs) == {"A", "B", "C", "D"}
        assert it_dfs[0] == "A"
        assert set(it_dfs) == {"A", "B", "C", "D"}

    def test_cycle_handling_without_infinite_loop(self):
        # Create triangular cycle: A - B - C - A
        g = ClinicalComorbidityGraph(directed=False)
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        g.add_edge("C", "A")

        # Must terminate and visit all 3 nodes
        bfs_res = g.bfs("A")
        assert len(bfs_res) == 3
        assert set(bfs_res) == {"A", "B", "C"}

        dfs_res = g.dfs("A")
        assert len(dfs_res) == 3
        assert set(dfs_res) == {"A", "B", "C"}

        assert g.has_cycle() is True

    def test_directed_graph_cycle_detection(self):
        # Acyclic directed: A -> B -> C
        g_dag = ClinicalComorbidityGraph(directed=True)
        g_dag.add_edge("A", "B")
        g_dag.add_edge("B", "C")
        assert g_dag.has_cycle() is False

        # Add back edge: C -> A
        g_dag.add_edge("C", "A")
        assert g_dag.has_cycle() is True

    def test_disconnected_graph_handling(self):
        g = ClinicalComorbidityGraph(directed=False)
        # Component 1
        g.add_edge("Diabetes", "Circulatory")
        # Component 2 (Isolated)
        g.add_edge("Ophthalmology", "Retinopathy")
        # Component 3 (Single node)
        g.add_node("Isolated_Derm")

        # Without visit_all_components
        comp1_bfs = g.bfs("Diabetes", visit_all_components=False)
        assert set(comp1_bfs) == {"Diabetes", "Circulatory"}

        # With visit_all_components
        all_bfs = g.bfs("Diabetes", visit_all_components=True)
        assert set(all_bfs) == {"Diabetes", "Circulatory", "Ophthalmology", "Retinopathy", "Isolated_Derm"}

        # Connected components partitioning
        components = g.get_connected_components()
        assert len(components) == 3
        assert any(set(c) == {"Diabetes", "Circulatory"} for c in components)
        assert any(set(c) == {"Ophthalmology", "Retinopathy"} for c in components)
        assert any(set(c) == {"Isolated_Derm"} for c in components)

    def test_shortest_path_bfs(self):
        g = ClinicalComorbidityGraph(directed=False)
        g.add_edge("Diabetes", "Renal")
        g.add_edge("Diabetes", "Circulatory")
        g.add_edge("Circulatory", "Respiratory")
        g.add_edge("Respiratory", "Digestive")
        # Isolated node
        g.add_node("Unreachable")

        path = g.find_shortest_path("Diabetes", "Respiratory")
        assert path == ["Diabetes", "Circulatory", "Respiratory"]

        # Same start and target
        assert g.find_shortest_path("Diabetes", "Diabetes") == ["Diabetes"]

        # No path to unreachable node
        assert g.find_shortest_path("Diabetes", "Unreachable") is None

        # Non-existent node
        assert g.find_shortest_path("Diabetes", "NonExistent") is None

    def test_uci_diabetes_factory_graph(self):
        uci_g = build_uci_diabetes_comorbidity_graph()
        assert "Diabetes" in uci_g.nodes
        assert "Circulatory" in uci_g.nodes
        assert "Respiratory" in uci_g.nodes
        assert uci_g.edge_count > 5

        # Shortest path from Diabetes to Digestive
        path = uci_g.find_shortest_path("Diabetes", "Digestive")
        assert path is not None
        assert path[0] == "Diabetes"
        assert path[-1] == "Digestive"
