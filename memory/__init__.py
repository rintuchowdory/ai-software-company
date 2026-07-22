"""
AI Software Company — Shared Memory Layer
Hybrid: Vector DB (semantic search) + Structured DB (transactions) + Event Log (audit)
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


class VectorMemory:
    """Semantic search over project history."""

    def __init__(self, provider: str = "pinecone"):
        self.provider = provider
        self.dimension = 1536
        # self.client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        # self.index = self.client.Index(os.getenv("PINECONE_INDEX_NAME"))

    def embed_and_store(self, content: str, metadata: Dict[str, Any], namespace: str = "general") -> str:
        vector_id = hashlib.md5(f"{metadata.get('agent', 'unknown')}-{datetime.now().isoformat()}-{content[:50]}".encode()).hexdigest()
        # In production: generate embedding and upsert
        return vector_id

    def semantic_search(self, query: str, namespace: str = "general", top_k: int = 5) -> List[Dict[str, Any]]:
        # In production: query vector DB
        return []

    def get_relevant_context(self, agent_name: str, task: str, feature_id: Optional[str] = None) -> str:
        query = f"{agent_name} needs to: {task}"
        if feature_id:
            query += f" for feature {feature_id}"

        namespaces = ["general"]
        if agent_name in ["frontend", "backend"]:
            namespaces.extend(["code", "api_contracts"])
        elif agent_name == "designer":
            namespaces.extend(["design", "user_feedback"])
        elif agent_name == "qa":
            namespaces.extend(["bugs", "test_cases"])

        all_results = []
        for ns in namespaces:
            results = self.semantic_search(query, namespace=ns, top_k=3)
            all_results.extend(results)

        seen = set()
        context_parts = []
        for r in all_results:
            content = r.get("metadata", {}).get("content", "")
            if content not in seen:
                seen.add(content)
                context_parts.append(f"[{r.get('metadata', {}).get('type', 'note')}] {content[:500]}")

        return "\n\n".join(context_parts) if context_parts else "No relevant context found."


class StructuredStateStore:
    """Transactional state storage."""

    def __init__(self, backend: str = "redis"):
        self.backend = backend
        # self.redis = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, decode_responses=True)

    def get_state(self, section: str = "all") -> Dict[str, Any]:
        if section == "all":
            return self._load_full_state()
        return self._load_section(section)

    def update_state(self, section: str, data: Dict[str, Any], agent: str) -> bool:
        current = self._load_section(section)
        if current.get("_version") != data.get("_version"):
            raise ValueError("State conflict detected.")

        data["_version"] = current.get("_version", 0) + 1
        data["_last_updated"] = datetime.now().isoformat()
        data["_updated_by"] = agent

        self._write_section(section, data)
        self._append_event({
            "type": "state_update",
            "section": section,
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
            "diff": self._compute_diff(current, data)
        })
        return True

    def _load_full_state(self) -> Dict[str, Any]:
        return {s: self._load_section(s) for s in ["company", "product", "api_contracts", "design_system", "analytics", "infrastructure", "agent_memory"]}

    def _load_section(self, section: str) -> Dict[str, Any]:
        return {}

    def _write_section(self, section: str, data: Dict[str, Any]) -> None:
        pass

    def _compute_diff(self, old: Dict, new: Dict) -> Dict[str, Any]:
        diff = {}
        for key in set(old.keys()) | set(new.keys()):
            if old.get(key) != new.get(key):
                diff[key] = {"old": old.get(key), "new": new.get(key)}
        return diff

    def _append_event(self, event: Dict[str, Any]) -> None:
        pass


class EventLog:
    """Append-only audit trail."""

    def __init__(self):
        self.events = []

    def log(self, event_type: str, agent: str, details: Dict[str, Any], feature_id: Optional[str] = None) -> None:
        import uuid
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "agent": agent,
            "feature_id": feature_id,
            "details": details
        }
        self.events.append(event)

    def get_events(self, agent: Optional[str] = None, feature_id: Optional[str] = None, since: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.events
        if agent:
            results = [e for e in results if e["agent"] == agent]
        if feature_id:
            results = [e for e in results if e.get("feature_id") == feature_id]
        if since:
            results = [e for e in results if e["timestamp"] >= since]
        return results


class ProjectMemory:
    """Unified interface for agents."""

    def __init__(self):
        self.vector_db = VectorMemory()
        self.structured = StructuredStateStore()
        self.event_log = EventLog()

    def read(self, section: str = "all", agent: str = "unknown") -> Dict[str, Any]:
        self.event_log.log("state_read", agent, {"section": section})
        return self.structured.get_state(section)

    def write(self, section: str, data: Dict[str, Any], agent: str) -> bool:
        success = self.structured.update_state(section, data, agent)
        if success:
            self.event_log.log("state_write", agent, {"section": section})
            content = json.dumps(data, default=str)
            self.vector_db.embed_and_store(
                content=content[:4000],
                metadata={"agent": agent, "type": "state_update", "section": section, "timestamp": datetime.now().isoformat()}
            )
        return success

    def search(self, query: str, agent: str, namespace: str = "general") -> str:
        self.event_log.log("semantic_search", agent, {"query": query, "namespace": namespace})
        return self.vector_db.get_relevant_context(agent, query)

    def log(self, event_type: str, agent: str, details: Dict[str, Any]) -> None:
        self.event_log.log(event_type, agent, details)

    def get_history(self, agent: Optional[str] = None, since: Optional[str] = None) -> List[Dict]:
        return self.event_log.get_events(agent=agent, since=since)
