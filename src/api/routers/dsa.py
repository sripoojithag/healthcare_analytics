"""
DSA Microservices Router: Clinical Triage Priority Queue & Co-morbidity Graph Traversal.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.schemas import (
    GraphShortestPathRequest,
    GraphShortestPathResponse,
    GraphTraverseRequest,
    GraphTraverseResponse,
    TriageEnqueueRequest,
    TriageItemResponse,
    TriageQueueStatusResponse,
)
from src.dsa.graph import ClinicalComorbidityGraph, build_uci_diabetes_comorbidity_graph
from src.dsa.priority_queue import ClinicalReviewItem, ClinicalTriagePriorityQueue
from src.security.audit import audit_store
from src.security.rbac import AuthenticatedUser, require_role

router = APIRouter(prefix="/dsa", tags=["Data Structures & Algorithms"])

# Singleton instances for demonstration state
_triage_queue = ClinicalTriagePriorityQueue()
_comorbidity_graph = build_uci_diabetes_comorbidity_graph()


def _seed_initial_triage_queue():
    """Populates queue with representative high-risk cases if empty."""
    if _triage_queue.is_empty():
        _triage_queue.enqueue(
            encounter_id="ENC-109482",
            patient_id="PT-***8234",
            risk_score=0.8845,
            time_in_hospital=11,
            num_medications=28,
            primary_diagnosis="Circulatory",
            metadata={"urgency": "Immediate", "alert": "High Polypharmacy"},
        )
        _triage_queue.enqueue(
            encounter_id="ENC-204193",
            patient_id="PT-***9120",
            risk_score=0.7420,
            time_in_hospital=7,
            num_medications=19,
            primary_diagnosis="Diabetes",
            metadata={"urgency": "Elevated", "alert": "A1C Uncontrolled"},
        )
        _triage_queue.enqueue(
            encounter_id="ENC-330194",
            patient_id="PT-***4521",
            risk_score=0.7420,
            time_in_hospital=9,  # Tie breaker: same risk, longer stay
            num_medications=22,
            primary_diagnosis="Renal",
            metadata={"urgency": "Elevated", "alert": "Long Inpatient Stay"},
        )
        _triage_queue.enqueue(
            encounter_id="ENC-410928",
            patient_id="PT-***1123",
            risk_score=0.4120,
            time_in_hospital=3,
            num_medications=8,
            primary_diagnosis="Respiratory",
            metadata={"urgency": "Routine", "alert": "Standard Discharge"},
        )


_seed_initial_triage_queue()


# --- Priority Queue Endpoints ---

@router.get("/triage/status", response_model=TriageQueueStatusResponse)
def get_triage_queue_status(
    limit: int = Query(default=10, ge=1, le=100),
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """
    Returns current triage review queue size, root top-priority patient, and top items.
    Accessible to all authenticated roles.
    """
    top = _triage_queue.peek()
    sorted_items = _triage_queue.to_sorted_list()

    return TriageQueueStatusResponse(
        total_queued=_triage_queue.size(),
        is_empty=_triage_queue.is_empty(),
        top_patient=TriageItemResponse(**top.to_dict()) if top else None,
        queue_preview=[TriageItemResponse(**it.to_dict()) for it in sorted_items[:limit]],
    )


@router.post("/triage/enqueue", response_model=TriageItemResponse, status_code=status.HTTP_201_CREATED)
def enqueue_triage_encounter(
    payload: TriageEnqueueRequest,
    user: AuthenticatedUser = Depends(require_role("analyst")),
):
    """
    Pushes an inpatient encounter onto the priority review queue.
    Requires Analyst or Admin role.
    """
    try:
        item = _triage_queue.enqueue(
            encounter_id=payload.encounter_id,
            patient_id=payload.patient_id,
            risk_score=payload.risk_score,
            time_in_hospital=payload.time_in_hospital,
            num_medications=payload.num_medications,
            primary_diagnosis=payload.primary_diagnosis,
            metadata={"notes": payload.notes} if payload.notes else {},
        )
        audit_store.log(
            user_id=user.user_id,
            role=user.role.value,
            action="TRIAGE_ENQUEUE",
            resource=f"/api/v1/dsa/triage/enqueue/{payload.encounter_id}",
            status="SUCCESS",
            details={"risk_score": payload.risk_score},
        )
        return TriageItemResponse(**item.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/triage/dequeue", response_model=TriageItemResponse)
def dequeue_triage_encounter(
    user: AuthenticatedUser = Depends(require_role("analyst")),
):
    """
    Pops the highest priority patient from the review heap.
    Requires Analyst or Admin role.
    """
    if _triage_queue.is_empty():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Triage queue is empty; no patients awaiting review.",
        )

    item = _triage_queue.dequeue()
    audit_store.log(
        user_id=user.user_id,
        role=user.role.value,
        action="TRIAGE_DEQUEUE",
        resource=f"/api/v1/dsa/triage/dequeue/{item.encounter_id}",
        status="SUCCESS",
    )
    return TriageItemResponse(**item.to_dict())


@router.get("/triage/peek", response_model=Optional[TriageItemResponse])
def peek_triage_encounter(
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """
    Inspects the root top-priority patient in O(1) time without dequeueing.
    """
    item = _triage_queue.peek()
    if not item:
        return None
    return TriageItemResponse(**item.to_dict())


# --- Graph Traversal Endpoints ---

@router.get("/graph/schema")
def get_graph_schema(
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """
    Returns the co-morbidity clinical graph topology, nodes, and edges.
    """
    return _comorbidity_graph.to_dict()


@router.post("/graph/traverse", response_model=GraphTraverseResponse)
def traverse_comorbidity_graph(
    payload: GraphTraverseRequest,
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """
    Executes BFS or DFS traversal on the clinical diagnostic graph.
    Demonstrates cycle-safe traversal and disconnected subgraph exploration.
    """
    try:
        if payload.algorithm == "bfs":
            path = _comorbidity_graph.bfs(
                start_node=payload.start_node,
                visit_all_components=payload.visit_all_components,
            )
        else:
            path = _comorbidity_graph.dfs(
                start_node=payload.start_node,
                visit_all_components=payload.visit_all_components,
                iterative=True,
            )

        return GraphTraverseResponse(
            start_node=payload.start_node,
            algorithm=payload.algorithm.upper(),
            traversal_path=path,
            total_visited=len(path),
            time_complexity="O(V + E)",
            space_complexity="O(V)",
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/graph/shortest-path", response_model=GraphShortestPathResponse)
def get_shortest_path(
    payload: GraphShortestPathRequest,
    user: AuthenticatedUser = Depends(require_role("viewer")),
):
    """
    Calculates shortest unweighted diagnostic path between two co-morbidities using BFS.
    """
    path = _comorbidity_graph.find_shortest_path(
        start_node=payload.start_node,
        target_node=payload.target_node,
    )
    if path is None:
        return GraphShortestPathResponse(
            start_node=payload.start_node,
            target_node=payload.target_node,
            path=None,
            hops=None,
            path_found=False,
        )

    return GraphShortestPathResponse(
        start_node=payload.start_node,
        target_node=payload.target_node,
        path=path,
        hops=max(0, len(path) - 1),
        path_found=True,
    )
