"""
AI Software Company — Tool Registry
All tools available to agents, with permission-based access control.
"""

import os
import subprocess
from typing import Dict, Callable, Any, List
from datetime import datetime


class ToolRegistry:
    _tools: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, func: Callable, description: str, required_permissions: List[str] = None):
        cls._tools[name] = {"func": func, "description": description, "permissions": required_permissions or []}

    @classmethod
    def get(cls, name: str) -> Callable:
        tool = cls._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return tool["func"]

    @classmethod
    def list_for_agent(cls, agent: str) -> Dict[str, Any]:
        from security import DEFAULT_PERMISSIONS
        perms = DEFAULT_PERMISSIONS.get(agent)
        if not perms:
            return {}
        return {name: {"description": t["description"]} for name, t in cls._tools.items() if all(p in perms.allowed_tools for p in t["permissions"])}


# --- State Tools ---

def read_project_state(section: str = "all") -> Dict[str, Any]:
    """Read from shared project state."""
    from memory import ProjectMemory
    memory = ProjectMemory()
    return memory.read(section)

def write_project_state(section: str, data: Dict[str, Any], agent: str = "unknown") -> bool:
    """Write to shared project state."""
    from memory import ProjectMemory
    memory = ProjectMemory()
    return memory.write(section, data, agent)

# --- Code Tools ---

def execute_code_sandbox(code: str, language: str = "typescript", timeout: int = 30) -> Dict[str, Any]:
    """Execute code in E2B sandbox."""
    # In production: use E2B SDK
    return {"success": True, "output": "Sandbox execution placeholder", "errors": [], "coverage": 0.0}

def run_test_suite(test_code: str, language: str = "typescript") -> Dict[str, Any]:
    """Run test suite."""
    return {"passed": True, "coverage": 0.85, "failures": [], "duration_ms": 1200}

# --- Deploy Tools ---

def execute_terraform_plan(config: str) -> Dict[str, Any]:
    """Run terraform plan."""
    return {"valid": True, "changes": [], "estimated_cost_impact": "$0"}

def run_deployment(environment: str, commit_sha: str) -> Dict[str, Any]:
    """Run deployment pipeline."""
    return {"success": True, "environment": environment, "commit": commit_sha, "url": f"https://{environment}.example.com"}

# --- Content Tools ---

def publish_content(content: Dict[str, Any]) -> Dict[str, Any]:
    """Publish marketing content."""
    return {"published": True, "url": f"https://blog.example.com/{content.get('slug', 'post')}"}

# --- Human Tools ---

def request_human_approval(decision_type: str, details: str) -> str:
    """Request human approval for critical decisions."""
    from security import HumanGate
    gate = HumanGate()
    return gate.request(decision_type, {"details": details}, "system")

# Register all tools
ToolRegistry.register("read_project_state", read_project_state, "Read from shared project state", ["read_state"])
ToolRegistry.register("write_project_state", write_project_state, "Write to shared project state", ["write_state"])
ToolRegistry.register("execute_code_sandbox", execute_code_sandbox, "Execute code in isolated sandbox", ["execute_code"])
ToolRegistry.register("run_test_suite", run_test_suite, "Run test suite", ["run_tests"])
ToolRegistry.register("execute_terraform_plan", execute_terraform_plan, "Run terraform plan", ["execute_terraform"])
ToolRegistry.register("run_deployment", run_deployment, "Run deployment pipeline", ["deploy"])
ToolRegistry.register("publish_content", publish_content, "Publish marketing content", ["publish_content"])
ToolRegistry.register("request_human_approval", request_human_approval, "Request human approval", ["human_approval"])
