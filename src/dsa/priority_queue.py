"""
Clinical Triage Review Priority Queue (Heap-Based Implementation).

Use Case:
In clinical decision support and hospital discharge planning, case managers
and clinical reviewers have limited daily bandwidth. Inpatient encounters must
be triaged dynamically so the highest-risk patients receive pre-discharge reviews
first.

Priority Ranking & Tie-breaking Rules:
1. Primary: Predicted 30-day readmission risk score (higher score = higher priority).
2. Secondary tie-breaker: Length of hospital stay (longer stay = higher complexity).
3. Tertiary tie-breaker: Medication count (higher polypharmacy = higher risk).
4. Deterministic tie-breaker: Monotonic sequence ID (FIFO for identical clinical metrics;
   prevents direct object comparison collisions in heapq).

Time Complexity:
- Enqueue: O(log N) — binary heap push maintains the complete binary tree invariant.
- Dequeue: O(log N) — binary heap pop swaps root with last element and sifts down.
- Peek:    O(1)     — root element inspection at array index 0.
- Size/Empty: O(1)  — direct list length check.

Space Complexity:
- O(N) auxiliary space to store N queued clinical encounter items.
"""

import heapq
import itertools
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ClinicalReviewItem:
    """Represents a patient encounter awaiting clinical review."""
    encounter_id: str
    patient_id: str
    risk_score: float
    time_in_hospital: int = 0
    num_medications: int = 0
    primary_diagnosis: str = "Unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "encounter_id": self.encounter_id,
            "patient_id": self.patient_id,
            "risk_score": round(self.risk_score, 4),
            "time_in_hospital": self.time_in_hospital,
            "num_medications": self.num_medications,
            "primary_diagnosis": self.primary_diagnosis,
            "metadata": self.metadata,
        }


class ClinicalTriagePriorityQueue:
    """
    Max-Priority Queue implemented using a binary min-heap with negated priorities.
    Thread-safe logic can be wrapped at service boundaries.
    """

    def __init__(self) -> None:
        self._heap: List[tuple] = []
        self._counter = itertools.count()  # Monotonically increasing tie-breaker counter

    def enqueue(
        self,
        encounter_id: str,
        patient_id: str,
        risk_score: float,
        time_in_hospital: int = 0,
        num_medications: int = 0,
        primary_diagnosis: str = "Unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClinicalReviewItem:
        """
        Pushes a new patient encounter onto the triage heap.

        Args:
            encounter_id: Hospital encounter identifier.
            patient_id: Patient ID (masked or unmasked).
            risk_score: Predicted 30-day readmission risk probability (0.0 to 1.0).
            time_in_hospital: Days admitted to hospital.
            num_medications: Total medications administered.
            primary_diagnosis: Primary ICD-9 category or code.
            metadata: Optional dictionary of clinical notes or tags.

        Returns:
            The created ClinicalReviewItem.
        """
        if not encounter_id or not patient_id:
            raise ValueError("encounter_id and patient_id must be non-empty strings")

        # Clamp and validate risk_score
        clamped_score = max(0.0, min(1.0, float(risk_score)))
        stay_val = max(0, int(time_in_hospital))
        meds_val = max(0, int(num_medications))

        item = ClinicalReviewItem(
            encounter_id=str(encounter_id),
            patient_id=str(patient_id),
            risk_score=clamped_score,
            time_in_hospital=stay_val,
            num_medications=meds_val,
            primary_diagnosis=primary_diagnosis or "Unknown",
            metadata=metadata or {},
        )

        seq = next(self._counter)
        # Heap tuple: (-risk_score, -time_in_hospital, -num_medications, seq, item)
        # Using negative numbers turns Python's min-heap into a multi-tiered max-heap.
        priority_tuple = (
            -round(clamped_score, 4),
            -stay_val,
            -meds_val,
            seq,
            item,
        )
        heapq.heappush(self._heap, priority_tuple)
        return item

    def dequeue(self) -> ClinicalReviewItem:
        """
        Removes and returns the highest priority encounter from the triage heap.

        Raises:
            IndexError: If the queue is empty.
        """
        if not self._heap:
            raise IndexError("Cannot dequeue from an empty ClinicalTriagePriorityQueue")

        _, _, _, _, item = heapq.heappop(self._heap)
        return item

    def dequeue_safe(self) -> Optional[ClinicalReviewItem]:
        """
        Removes and returns highest priority encounter, or None if empty.
        """
        if not self._heap:
            return None
        return self.dequeue()

    def peek(self) -> Optional[ClinicalReviewItem]:
        """
        Inspects the highest priority encounter without removing it.
        Returns None if queue is empty.
        """
        if not self._heap:
            return None
        return self._heap[0][4]

    def is_empty(self) -> bool:
        """Returns True if the queue has no elements."""
        return len(self._heap) == 0

    def size(self) -> int:
        """Returns current number of queued encounters."""
        return len(self._heap)

    def clear(self) -> None:
        """Clears all queued encounters."""
        self._heap.clear()

    def to_sorted_list(self) -> List[ClinicalReviewItem]:
        """
        Returns a sorted snapshot of all elements in priority order without mutating the heap.
        Time Complexity: O(N log N)
        """
        # Shallow copy heap list and pop in order
        heap_copy = list(self._heap)
        sorted_items = []
        while heap_copy:
            _, _, _, _, item = heapq.heappop(heap_copy)
            sorted_items.append(item)
        return sorted_items
