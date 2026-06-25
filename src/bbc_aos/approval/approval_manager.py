"""BBC-AOS ApprovalManager

Governs risk-based human approvals, transition rules, and checkpoints.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from bbc_aos.approval.approval_exceptions import (
    InvalidTransitionException,
)
from bbc_aos.approval.approval_request import ApprovalRequest
from bbc_aos.approval.approval_result import ApprovalResult
from bbc_aos.approval.approval_policy import ApprovalPolicy
from bbc_aos.approval.approval_checkpoint import ApprovalCheckpoint
from bbc_aos.approval.approval_audit_log import ApprovalAuditLog

logger = logging.getLogger("bbc_aos.approval.approval_manager")


class ApprovalManager:
    """Manages active approval requests, transitions, and history stacks."""

    def __init__(self, audit_log: Optional[ApprovalAuditLog] = None) -> None:
        """Initializes ApprovalManager.

        Args:
            audit_log: Optional custom audit log registry.
        """
        self.requests: Dict[str, ApprovalRequest] = {}
        self.checkpoint_stack: List[ApprovalCheckpoint] = []
        self.audit_log: ApprovalAuditLog = audit_log or ApprovalAuditLog()

    def request_approval(
        self,
        trace_id: str,
        replay_id: str,
        risk_level: str,
        commit_payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates a new approval request and routes it based on risk.

        Args:
            trace_id: Active trace ID.
            replay_id: Active replay ID.
            risk_level: Target risk level (LOW/MEDIUM/HIGH/CRITICAL).
            commit_payload: Proposed CodeDiff commit dictionary.

        Returns:
            A serialized ApprovalResult dictionary.
        """
        # Save pre-change checkpoint
        self._save_checkpoint()

        # Generate deterministic approval_id
        input_str = f"{trace_id}_{replay_id}_{risk_level}"
        approval_id = f"app_{hashlib.sha256(input_str.encode('utf-8')).hexdigest()[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Determine initial status from policy
        status = ApprovalPolicy.get_initial_status(risk_level)

        # Create request
        req = ApprovalRequest(
            approval_id=approval_id,
            trace_id=trace_id,
            replay_id=replay_id,
            risk_level=risk_level,
            status=status,
            commit_payload=commit_payload,
            timestamp=timestamp,
        )
        self.requests[approval_id] = req

        # Generate deterministic approval hash
        app_hash = self._calculate_approval_hash(req)

        # Log audit log
        self.audit_log.append(
            trace_id=trace_id,
            replay_id=replay_id,
            approval_id=approval_id,
            approval_hash=app_hash,
            status=status,
            timestamp=timestamp,
            risk_level=risk_level,
        )

        res = ApprovalResult(
            approval_id=approval_id,
            approval_hash=app_hash,
            status=status,
            timestamp=timestamp,
        )
        logger.info(f"Created approval request '{approval_id}' with status '{status}'.")
        return res.to_dict()

    def approve(self, approval_id: str) -> Dict[str, Any]:
        """Approves a pending or escalated request.

        Args:
            approval_id: Unique approval request identifier.

        Returns:
            A serialized ApprovalResult dictionary.
        """
        req = self._get_request(approval_id)
        if req.status not in ("PENDING", "ESCALATED"):
            raise InvalidTransitionException(
                f"Cannot approve request '{approval_id}' in status '{req.status}'"
            )

        # Save checkpoint
        self._save_checkpoint()

        timestamp = datetime.now(timezone.utc).isoformat()
        req.status = "APPROVED"
        app_hash = self._calculate_approval_hash(req)

        self.audit_log.append(
            trace_id=req.trace_id,
            replay_id=req.replay_id,
            approval_id=approval_id,
            approval_hash=app_hash,
            status="APPROVED",
            timestamp=timestamp,
            risk_level=req.risk_level,
        )

        res = ApprovalResult(
            approval_id=approval_id,
            approval_hash=app_hash,
            status="APPROVED",
            timestamp=timestamp,
        )
        logger.info(f"Request '{approval_id}' approved.")
        return res.to_dict()

    def reject(self, approval_id: str) -> Dict[str, Any]:
        """Rejects a pending or escalated request.

        Args:
            approval_id: Unique approval request identifier.

        Returns:
            A serialized ApprovalResult dictionary.
        """
        req = self._get_request(approval_id)
        if req.status not in ("PENDING", "ESCALATED"):
            raise InvalidTransitionException(
                f"Cannot reject request '{approval_id}' in status '{req.status}'"
            )

        # Save checkpoint
        self._save_checkpoint()

        timestamp = datetime.now(timezone.utc).isoformat()
        req.status = "REJECTED"
        app_hash = self._calculate_approval_hash(req)

        self.audit_log.append(
            trace_id=req.trace_id,
            replay_id=req.replay_id,
            approval_id=approval_id,
            approval_hash=app_hash,
            status="REJECTED",
            timestamp=timestamp,
            risk_level=req.risk_level,
        )

        res = ApprovalResult(
            approval_id=approval_id,
            approval_hash=app_hash,
            status="REJECTED",
            timestamp=timestamp,
        )
        logger.info(f"Request '{approval_id}' rejected.")
        return res.to_dict()

    def timeout(self, approval_id: str) -> Dict[str, Any]:
        """Expires a pending request.

        Args:
            approval_id: Unique approval request identifier.

        Returns:
            A serialized ApprovalResult dictionary.
        """
        req = self._get_request(approval_id)
        if req.status != "PENDING":
            raise InvalidTransitionException(
                f"Cannot expire request '{approval_id}' in status '{req.status}'"
            )

        # Save checkpoint
        self._save_checkpoint()

        timestamp = datetime.now(timezone.utc).isoformat()
        req.status = "EXPIRED"
        app_hash = self._calculate_approval_hash(req)

        self.audit_log.append(
            trace_id=req.trace_id,
            replay_id=req.replay_id,
            approval_id=approval_id,
            approval_hash=app_hash,
            status="EXPIRED",
            timestamp=timestamp,
            risk_level=req.risk_level,
        )

        res = ApprovalResult(
            approval_id=approval_id,
            approval_hash=app_hash,
            status="EXPIRED",
            timestamp=timestamp,
        )
        logger.info(f"Request '{approval_id}' timed out / expired.")
        return res.to_dict()

    def escalate(self, approval_id: str) -> Dict[str, Any]:
        """Escalates a pending request.

        Args:
            approval_id: Unique approval request identifier.

        Returns:
            A serialized ApprovalResult dictionary.
        """
        req = self._get_request(approval_id)
        if req.status != "PENDING":
            raise InvalidTransitionException(
                f"Cannot escalate request '{approval_id}' in status '{req.status}'"
            )

        # Save checkpoint
        self._save_checkpoint()

        timestamp = datetime.now(timezone.utc).isoformat()
        req.status = "ESCALATED"
        app_hash = self._calculate_approval_hash(req)

        self.audit_log.append(
            trace_id=req.trace_id,
            replay_id=req.replay_id,
            approval_id=approval_id,
            approval_hash=app_hash,
            status="ESCALATED",
            timestamp=timestamp,
            risk_level=req.risk_level,
        )

        res = ApprovalResult(
            approval_id=approval_id,
            approval_hash=app_hash,
            status="ESCALATED",
            timestamp=timestamp,
        )
        logger.info(f"Request '{approval_id}' escalated.")
        return res.to_dict()

    def rollback_request(self, approval_id: str) -> Dict[str, Any]:
        """Rolls back requests mappings to the latest checkpoint.

        Args:
            approval_id: Target approval request ID.

        Returns:
            A status dictionary indicating success.
        """
        if not self.checkpoint_stack:
            raise InvalidTransitionException("No checkpoints available to rollback pending approvals")

        # Get request info before restoring checkpoint to log rollback audit
        req = self.requests.get(approval_id)
        if req:
            app_hash = self._calculate_approval_hash(req)
            timestamp = datetime.now(timezone.utc).isoformat()
            self.audit_log.append(
                trace_id=req.trace_id,
                replay_id=req.replay_id,
                approval_id=approval_id,
                approval_hash=app_hash,
                status="ROLLED_BACK",
                timestamp=timestamp,
                risk_level=req.risk_level,
            )

        # Pop latest checkpoint
        cp = self.checkpoint_stack.pop()
        cp.restore(self.requests)

        logger.info(f"Approval state rolled back via checkpoint '{cp.checkpoint_id}'.")
        return {
            "status": "ROLLED_BACK",
            "approval_id": approval_id,
        }

    def get_status(self, approval_id: str) -> Dict[str, Any]:
        """Gets the status details of a request.

        Args:
            approval_id: Unique approval request identifier.

        Returns:
            A status summary dictionary.
        """
        if approval_id in self.requests:
            return self.requests[approval_id].to_dict()

        # Try audit log
        events = self.audit_log.get_events()
        latest_event = None
        for event in reversed(events):
            if event.get("approval_id") == approval_id:
                latest_event = event
                break

        if latest_event:
            if latest_event["status"] == "ROLLED_BACK":
                raise KeyError(f"Approval request '{approval_id}' was rolled back.")
            return {
                "approval_id": approval_id,
                "trace_id": latest_event["trace_id"],
                "replay_id": latest_event["replay_id"],
                "risk_level": latest_event["risk_level"],
                "status": latest_event["status"],
                "timestamp": latest_event["timestamp"],
                "commit_payload": {},
            }

        raise KeyError(f"Approval request '{approval_id}' not found.")

    # ------------------------------------------------------------------
    # Helper Private Methods
    # ------------------------------------------------------------------

    def _get_request(self, approval_id: str) -> ApprovalRequest:
        """Retrieves request or raises KeyError."""
        if approval_id not in self.requests:
            raise KeyError(f"Approval request '{approval_id}' not found in active mappings.")
        return self.requests[approval_id]

    def _calculate_approval_hash(self, req: ApprovalRequest) -> str:
        """Generates deterministic approval hash."""
        input_str = f"{req.approval_id}_{req.trace_id}_{req.replay_id}_{req.status}_{req.risk_level}"
        return hashlib.sha256(input_str.encode("utf-8")).hexdigest()

    def _save_checkpoint(self) -> None:
        """Pushes an active requests snapshot onto the checkpoint stack."""
        timestamp = datetime.now(timezone.utc).isoformat()
        cp_id = f"cp_app_{len(self.checkpoint_stack)}"
        cp = ApprovalCheckpoint(checkpoint_id=cp_id, timestamp=timestamp)
        cp.capture(self.requests)
        self.checkpoint_stack.append(cp)
        # Cap stack size to 10
        if len(self.checkpoint_stack) > 10:
            self.checkpoint_stack.pop(0)
