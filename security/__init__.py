"""
AI Software Company — Security Model
Defense layers: Sandboxing, Input validation, Output validation, Rate limiting, Audit logging, Human gates, Least privilege
"""

import os
import re
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class Permission(str, Enum):
    READ_STATE = "read_state"
    WRITE_STATE = "write_state"
    EXECUTE_CODE = "execute_code"
    DEPLOY = "deploy"
    DELETE_DATA = "delete_data"
    MODIFY_CONTRACTS = "modify_contracts"
    ACCESS_SECRETS = "access_secrets"
    HUMAN_APPROVAL = "human_approval"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AgentPermissions:
    agent: str
    allowed_tools: List[str]
    allowed_state_sections: List[str]
    max_tokens_per_run: int
    max_runs_per_hour: int
    risk_level: RiskLevel
    requires_approval_for: List[Permission]

DEFAULT_PERMISSIONS = {
    "ceo": AgentPermissions("ceo", ["read_state", "write_state", "human_approval"],
                           ["company", "analytics", "agent_memory"], 8000, 10, RiskLevel.HIGH,
                           [Permission.DELETE_DATA, Permission.MODIFY_CONTRACTS]),
    "pm": AgentPermissions("pm", ["read_state", "write_state", "send_message"],
                          ["product", "company", "analytics"], 6000, 20, RiskLevel.MEDIUM,
                          [Permission.DELETE_DATA]),
    "designer": AgentPermissions("designer", ["read_state", "write_state"],
                                ["design_system", "product"], 4000, 30, RiskLevel.LOW, []),
    "frontend": AgentPermissions("frontend", ["read_state", "write_state", "execute_code"],
                                ["design_system", "product", "api_contracts"], 8000, 20, RiskLevel.MEDIUM,
                                [Permission.EXECUTE_CODE]),
    "backend": AgentPermissions("backend", ["read_state", "write_state", "execute_code"],
                               ["product", "api_contracts", "infrastructure"], 8000, 20, RiskLevel.HIGH,
                               [Permission.EXECUTE_CODE, Permission.MODIFY_CONTRACTS]),
    "qa": AgentPermissions("qa", ["read_state", "write_state", "execute_code", "run_tests"],
                          ["product", "api_contracts", "design_system"], 10000, 50, RiskLevel.MEDIUM, []),
    "devops": AgentPermissions("devops", ["read_state", "write_state", "deploy", "execute_terraform"],
                              ["infrastructure", "company"], 6000, 10, RiskLevel.CRITICAL,
                              [Permission.DEPLOY, Permission.ACCESS_SECRETS]),
    "marketing": AgentPermissions("marketing", ["read_state", "write_state", "publish_content"],
                                 ["product", "analytics", "company"], 4000, 20, RiskLevel.LOW, [])
}


class InputSanitizer:
    INJECTION_PATTERNS = [
        r"ignore previous instructions", r"ignore all (prior|previous)",
        r"you are now .*", r"system prompt", r"new role:",
        r"disregard", r"forget everything", r"DAN mode", r"jailbreak",
    ]

    DANGEROUS_CODE_PATTERNS = [
        r"eval\s*\(", r"exec\s*\(", r"os\.system", r"subprocess\.",
        r"__import__", r"rm -rf", r"drop table", r"delete from",
        r"<script", r"javascript:",
    ]

    @classmethod
    def sanitize_text(cls, text: str, source: str = "unknown") -> Dict[str, Any]:
        flags = []
        risk_score = 0.0

        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(f"injection_pattern: {pattern}")
                risk_score += 0.3

        for pattern in cls.DANGEROUS_CODE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(f"dangerous_code: {pattern}")
                risk_score += 0.5

        if len(text) > 50000:
            flags.append("excessive_length")
            risk_score += 0.2

        unusual_chars = sum(1 for c in text if ord(c) > 0x2000)
        if unusual_chars > len(text) * 0.1:
            flags.append("unusual_unicode")
            risk_score += 0.3

        return {"clean": risk_score < 0.5 and len(flags) < 2, "text": text, "flags": flags, "risk_score": min(risk_score, 1.0), "source": source}

    @classmethod
    def sanitize_agent_output(cls, output: Dict[str, Any], agent: str) -> Dict[str, Any]:
        flags = []

        def scan_value(value, path=""):
            if isinstance(value, str):
                result = cls.sanitize_text(value, source=f"{agent}:{path}")
                if not result["clean"]:
                    flags.extend(result["flags"])
            elif isinstance(value, dict):
                for k, v in value.items():
                    scan_value(v, f"{path}.{k}")
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    scan_value(v, f"{path}[{i}]")

        scan_value(output)
        return {"clean": len(flags) == 0, "flags": flags, "output": output}


class OutputValidator:
    @staticmethod
    def validate_code_output(code: str, language: str = "typescript") -> Dict[str, Any]:
        flags = []
        dangerous = [
            (r"eval\s*\(", "eval() forbidden"),
            (r"exec\s*\(", "exec() forbidden"),
            (r"process\.env", "env access forbidden"),
            (r"fs\.readFileSync.*\.env", ".env read forbidden"),
            (r"require\(["']child_process", "child_process forbidden"),
        ]
        for pattern, message in dangerous:
            if re.search(pattern, code):
                flags.append(message)
        return {"safe": len(flags) == 0, "flags": flags, "code": code}


class RateLimiter:
    def __init__(self):
        self.usage = {}

    def check(self, agent: str, estimated_tokens: int) -> Dict[str, Any]:
        perms = DEFAULT_PERMISSIONS.get(agent)
        if not perms:
            return {"allowed": False, "reason": "Unknown agent", "remaining": 0}

        current_hour = datetime.now().strftime("%Y-%m-%d-%H")
        if agent not in self.usage:
            self.usage[agent] = {}
        if current_hour not in self.usage[agent]:
            self.usage[agent][current_hour] = {"runs": 0, "tokens": 0}

        usage = self.usage[agent][current_hour]

        if usage["runs"] >= perms.max_runs_per_hour:
            return {"allowed": False, "reason": f"Run limit: {usage['runs']}/{perms.max_runs_per_hour}", "remaining": 0}

        usage["runs"] += 1
        usage["tokens"] += estimated_tokens

        return {"allowed": True, "reason": "", "remaining": perms.max_runs_per_hour - usage["runs"]}


class HumanGate:
    CRITICAL_DECISIONS = ["deploy_to_production", "feature_kill", "budget_increase", "destructive_migration", "security_patch", "data_deletion", "go_with_risk"]

    def __init__(self):
        self.pending_approvals = {}

    def request(self, decision_type: str, context: Dict[str, Any], requester: str) -> str:
        import hashlib
        approval_id = hashlib.sha256(f"{decision_type}-{requester}-{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        self.pending_approvals[approval_id] = {
            "type": decision_type, "context": context, "requester": requester,
            "status": "pending", "requested_at": datetime.now().isoformat(),
            "approved_at": None, "approved_by": None, "comment": None
        }
        return approval_id

    def approve(self, approval_id: str, approved_by: str, comment: str = "") -> bool:
        if approval_id not in self.pending_approvals:
            return False
        self.pending_approvals[approval_id].update({"status": "approved", "approved_at": datetime.now().isoformat(), "approved_by": approved_by, "comment": comment})
        return True

    def reject(self, approval_id: str, rejected_by: str, reason: str) -> bool:
        if approval_id not in self.pending_approvals:
            return False
        self.pending_approvals[approval_id].update({"status": "rejected", "approved_at": datetime.now().isoformat(), "approved_by": rejected_by, "comment": reason})
        return True

    def is_approved(self, approval_id: str) -> bool:
        return self.pending_approvals.get(approval_id, {}).get("status") == "approved"


class SecurityGate:
    def __init__(self):
        self.sanitizer = InputSanitizer()
        self.validator = OutputValidator()
        self.rate_limiter = RateLimiter()
        self.human_gate = HumanGate()

    def check_input(self, text: str, source: str = "unknown") -> Dict[str, Any]:
        return self.sanitizer.sanitize_text(text, source)

    def check_output(self, output: Dict[str, Any], agent: str) -> Dict[str, Any]:
        results = {"passed": True, "checks": {}, "human_approval_required": None}

        sanitize_result = self.sanitizer.sanitize_agent_output(output, agent)
        results["checks"]["sanitize"] = sanitize_result
        if not sanitize_result["clean"]:
            results["passed"] = False

        if "files" in output:
            for file in output["files"]:
                if file.get("language") in ["typescript", "javascript", "python"]:
                    code_result = self.validator.validate_code_output(file.get("code", ""))
                    results["checks"][f"code_{file.get('path', 'unknown')}"] = code_result
                    if not code_result["safe"]:
                        results["passed"] = False

        perms = DEFAULT_PERMISSIONS.get(agent)
        if perms:
            for action in output.keys():
                permission_map = {"deploy": Permission.DEPLOY, "feature_kill": Permission.DELETE_DATA,
                                "api_contract_update": Permission.MODIFY_CONTRACTS, "database_changes": Permission.MODIFY_CONTRACTS}
                perm = permission_map.get(action)
                if perm and perm in perms.requires_approval_for:
                    approval_id = self.human_gate.request(action, {"agent": agent, "output": output}, agent)
                    results["human_approval_required"] = approval_id
                    results["passed"] = False

        return results

    def check_rate_limit(self, agent: str, estimated_tokens: int) -> Dict[str, Any]:
        return self.rate_limiter.check(agent, estimated_tokens)
