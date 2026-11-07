"""
Audit Logging Module for Healthcare Data Governance
Records security, access, and ingestion operations without persisting sensitive patient data (PHI).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import threading

@dataclass
class AuditRecord:
    timestamp: str
    user_id: str
    role: str
    action: str
    resource: str
    status: str  # "SUCCESS", "DENIED", "FAILED"
    client_ip: Optional[str] = "127.0.0.1"
    details: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "role": self.role,
            "action": self.action,
            "resource": self.resource,
            "status": self.status,
            "client_ip": self.client_ip,
            "details": self.details
        }


class AuditLogStore:
    """Thread-safe in-memory audit trail."""
    def __init__(self, max_records: int = 1000):
        self._records: List[AuditRecord] = []
        self._lock = threading.Lock()
        self._max_records = max_records

    def log(
        self,
        user_id: str,
        role: str,
        action: str,
        resource: str,
        status: str,
        client_ip: Optional[str] = "127.0.0.1",
        details: Optional[Dict[str, Any]] = None
    ) -> AuditRecord:
        record = AuditRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=user_id,
            role=role,
            action=action,
            resource=resource,
            status=status,
            client_ip=client_ip,
            details=details or {}
        )
        with self._lock:
            self._records.append(record)
            if len(self._records) > self._max_records:
                self._records.pop(0)
        return record

    def get_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in reversed(self._records[-limit:])]

    def clear(self):
        with self._lock:
            self._records.clear()


audit_store = AuditLogStore()
