"""
AI Software Company — LangGraph Orchestrator
Full 8-agent workflow with conditional edges, human gates, feedback loop.
"""

import os
import json
import asyncio
import argparse
from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

# LangGraph
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

# Load env
from dotenv import load_dotenv
load_dotenv()


# ============================================================
# STATE DEFINITIONS
# ============================================================

class FeatureStatus(str, Enum):
    BACKLOG = "backlog"
    IN_DESIGN = "in_design"
    IN_DEV = "in_dev"
    IN_QA = "in_qa"
    DEPLOYED = "deployed"
    SUNSET = "sunset"

@dataclass
class Analytics:
    daily_active: int = 0
    churn_rate: float = 0.0
    revenue_mrr: float = 0.0
    cost_per_user: float = 0.0
    top_funnel_drop: str = ""

@dataclass
class ProjectState:
    company: Dict[str, Any] = field(default_factory=dict)
    product: Dict[str, Any] = field(default_factory=dict)
    api_contracts: Dict[str, Any] = field(default_factory=dict)
    design_system: Dict[str, Any] = field(default_factory=dict)
    analytics: Analytics = field(default_factory=Analytics)
    infrastructure: Dict[str, Any] = field(default_factory=dict)
    agent_memory: Dict[str, Any] = field(default_factory=dict)

    trigger: str = ""
    current_agent: str = ""
    human_approval_needed: List[str] = field(default_factory=list)
    loop_count: int = 0
    max_loops: int = 50


# ============================================================
# AGENT LOADER
# ============================================================

class AgentRunner:
    """Loads agent prompts and runs LLM calls."""

    def __init__(self, agent_name: str):
        self.name = agent_name
        self.prompt_path = f"agents/{agent_name}/system_prompt.md"
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.2,
            max_tokens=4096,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    def load_prompt(self) -> str:
        with open(self.prompt_path, "r") as f:
            return f.read()

    def run(self, state: ProjectState) -> Dict[str, Any]:
        """Execute agent with current state context."""
        system_prompt = self.load_prompt()

        # Build context
        context = {
            "company": state.company,
            "product": state.product,
            "analytics": asdict(state.analytics),
            "infrastructure": state.infrastructure,
            "agent_memory": state.agent_memory,
            "trigger": state.trigger
        }

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
Current shared state:
{json.dumps(context, indent=2, default=str)}

Your task: Execute your role based on the current state.
Output strict JSON matching your defined output format.
""")
        ]

        try:
            response = self.llm.invoke(messages)
            output = self._parse_output(response.content)

            # Store in agent memory
            state.agent_memory[agent_name] = {
                "last_output": output,
                "timestamp": datetime.now().isoformat()
            }

            return output
        except Exception as e:
            return {"error": str(e), "agent": agent_name}

    def _parse_output(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM output, handling markdown fences."""
        # Strip markdown fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return {"raw_output": content, "error": "Failed to parse JSON"}


# ============================================================
# LANGGRAPH WORKFLOW
# ============================================================

class WorkflowState(TypedDict):
    project_state: ProjectState
    current_step: str
    output_log: List[Dict[str, Any]]
    error: Optional[str]


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for the AI Software Company."""

    workflow = StateGraph(WorkflowState)

    # --- Node definitions ---

    def ceo_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("ceo")
        result = runner.run(ps)
        state["output_log"].append({"agent": "ceo", "output": result, "timestamp": datetime.now().isoformat()})

        if result.get("human_approval_required"):
            ps.human_approval_needed.extend(result["human_approval_required"])
        if "updated_okrs" in result:
            ps.company["okrs"] = result["updated_okrs"]

        return state

    def pm_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("pm")
        result = runner.run(ps)
        state["output_log"].append({"agent": "pm", "output": result, "timestamp": datetime.now().isoformat()})

        if "sprint_plan" in result:
            ps.company["active_sprint"] = result["sprint_plan"].get("sprint_id", "unknown")
            ps.product["current_sprint"] = result["sprint_plan"]

        return state

    def designer_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("designer")
        result = runner.run(ps)
        state["output_log"].append({"agent": "designer", "output": result, "timestamp": datetime.now().isoformat()})

        if "design_specs" in result:
            ps.product["design_specs"] = result["design_specs"]

        return state

    def frontend_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("frontend")
        result = runner.run(ps)
        state["output_log"].append({"agent": "frontend", "output": result, "timestamp": datetime.now().isoformat()})

        if "files" in result:
            ps.product["frontend_files"] = result["files"]
        if result.get("api_requests"):
            ps.agent_memory["frontend_api_requests"] = result["api_requests"]

        return state

    def backend_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("backend")
        result = runner.run(ps)
        state["output_log"].append({"agent": "backend", "output": result, "timestamp": datetime.now().isoformat()})

        if "api_contract_update" in result:
            contract = result["api_contract_update"]
            ps.api_contracts[contract["endpoint"]] = contract
        if "files" in result:
            ps.product["backend_files"] = result["files"]

        return state

    def qa_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("qa")
        result = runner.run(ps)
        state["output_log"].append({"agent": "qa", "output": result, "timestamp": datetime.now().isoformat()})
        ps.product["qa_results"] = result
        return state

    def devops_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("devops")
        result = runner.run(ps)
        state["output_log"].append({"agent": "devops", "output": result, "timestamp": datetime.now().isoformat()})

        if "deployment_plan" in result:
            ps.infrastructure["last_deployment"] = result["deployment_plan"]

        return state

    def marketing_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        runner = AgentRunner("marketing")
        result = runner.run(ps)
        state["output_log"].append({"agent": "marketing", "output": result, "timestamp": datetime.now().isoformat()})
        ps.product["marketing_campaigns"] = result.get("campaigns", [])
        return state

    def human_gate_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        critical = ["feature_kill", "budget_change", "prod_deploy", "go_with_risk"]
        needs_approval = [d for d in ps.human_approval_needed if d in critical]

        if needs_approval:
            state["error"] = f"Human approval required for: {needs_approval}"
            return state

        ps.human_approval_needed = []
        return state

    def feedback_loop_node(state: WorkflowState) -> WorkflowState:
        ps = state["project_state"]
        # Simulate analytics update from marketing
        ps.analytics.daily_active += 100
        ps.loop_count = 0
        return state

    # Add nodes
    workflow.add_node("ceo", ceo_node)
    workflow.add_node("pm", pm_node)
    workflow.add_node("designer", designer_node)
    workflow.add_node("frontend", frontend_node)
    workflow.add_node("backend", backend_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("devops", devops_node)
    workflow.add_node("marketing", marketing_node)
    workflow.add_node("human_gate", human_gate_node)
    workflow.add_node("feedback_loop", feedback_loop_node)

    # --- Edges ---
    workflow.set_entry_point("ceo")
    workflow.add_edge("ceo", "pm")
    workflow.add_edge("pm", "designer")
    workflow.add_edge("designer", "frontend")
    workflow.add_edge("designer", "backend")

    # Frontend <-> Backend negotiation
    def frontend_condition(state: WorkflowState) -> str:
        ps = state["project_state"]
        api_requests = ps.agent_memory.get("frontend_api_requests", [])
        if api_requests:
            return "negotiate"
        return "proceed_to_qa"

    workflow.add_conditional_edges(
        "frontend",
        frontend_condition,
        {"negotiate": "backend", "proceed_to_qa": "qa"}
    )

    workflow.add_edge("backend", "qa")

    # QA -> DevOps or PM
    def qa_condition(state: WorkflowState) -> str:
        ps = state["project_state"]
        qa_results = ps.product.get("qa_results", {})
        verdict = qa_results.get("release_recommendation", {}).get("verdict", "NO-GO")

        if verdict == "GO":
            return "deploy"
        elif verdict == "GO_WITH_RISK":
            ps.human_approval_needed.append("go_with_risk")
            return "human_gate"
        else:
            return "fix_bugs"

    workflow.add_conditional_edges(
        "qa",
        qa_condition,
        {"deploy": "devops", "human_gate": "human_gate", "fix_bugs": "pm"}
    )

    workflow.add_edge("human_gate", "devops")
    workflow.add_edge("devops", "marketing")
    workflow.add_edge("marketing", "feedback_loop")
    workflow.add_edge("feedback_loop", END)

    return workflow.compile(checkpointer=MemorySaver())


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_project() -> ProjectState:
    """Create initial project state for Week 1 MVP."""
    return ProjectState(
        company={
            "okrs": {"q3": "Ship MVP with user authentication and dashboard"},
            "budget_remaining": 4200.0,
            "active_sprint": "sprint-1",
            "runway_months": 6.0
        },
        product={
            "features": [],
            "backlog": [],
            "current_sprint": None
        },
        analytics=Analytics(
            daily_active=0,
            churn_rate=0.0,
            revenue_mrr=0.0,
            cost_per_user=0.0,
            top_funnel_drop=""
        ),
        design_system={
            "tokens": {
                "colors": {"primary": "#3b82f6", "danger": "#ef4444", "success": "#10b981"},
                "spacing": {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"},
                "typography": {"heading": "Inter 700", "body": "Inter 400", "mono": "JetBrains Mono"}
            },
            "components": {}
        },
        infrastructure={
            "deployments": [],
            "alerts": [],
            "cost_breakdown": {"compute": 0, "storage": 0, "bandwidth": 0, "llm_api": 0}
        }
    )


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def run_ai_company(trigger: str = "weekly_review", max_loops: int = 50) -> Dict[str, Any]:
    """Run one full cycle of the AI Software Company."""

    ps = initialize_project()
    ps.trigger = trigger
    ps.max_loops = max_loops

    workflow = create_workflow()

    initial_state = WorkflowState(
        project_state=ps,
        current_step="ceo",
        output_log=[],
        error=None
    )

    try:
        result = workflow.invoke(initial_state)
        return {
            "success": True,
            "final_state": result,
            "log": result["output_log"],
            "error": result.get("error"),
            "total_agents_ran": len(result["output_log"])
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "log": []
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Software Company Orchestrator")
    parser.add_argument("--trigger", default="weekly_review",
                       choices=["weekly_review", "new_feature", "bug_alert", "emergency"])
    parser.add_argument("--max-loops", type=int, default=50)
    parser.add_argument("--output", default="orchestrator_output.json",
                       help="Output file for results")

    args = parser.parse_args()

    print(f"\n🚀 Starting AI Software Company — Trigger: {args.trigger}")
    print("=" * 60)

    result = run_ai_company(trigger=args.trigger, max_loops=args.max_loops)

    # Save output
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, default=str)

    if result["success"]:
        print(f"\n✅ Workflow completed successfully!")
        print(f"   Agents ran: {result['total_agents_ran']}")
        print(f"   Output saved to: {args.output}")
    else:
        print(f"\n❌ Workflow failed: {result['error']}")

    print("\n📊 Agent execution log:")
    for entry in result.get("log", []):
        agent = entry["agent"].upper()
        print(f"   • {agent}: {list(entry['output'].keys()) if isinstance(entry['output'], dict) else 'error'}")
