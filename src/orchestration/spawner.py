from typing import Dict, Any, List, Optional
import dataclasses

@dataclasses.dataclass
class AgentMessage:
    sender: str
    recipient: str
    content: Dict[str, Any]
    message_type: str = "INSTRUCTION"

class SubagentSpawner:
    """
    Autonomous agent spawner and inter-agent communication bus.
    Spawns and coordinates specialized subagents in the fleet.
    """
    
    REGISTERED_AGENTS = {
        "captain_orchestrator": "Master Orchestrator & State Machine",
        "requirements_architect_agent": "Phase 0 Intake & Triage Specialist",
        "data_model_architect_agent": "Lead Data Modeler & ERD/SQL Author",
        "financial_risk_reviewer": "Financial & Grain Integrity Auditor",
        "temporal_risk_reviewer": "Temporal & History Consistency Auditor",
        "relational_risk_reviewer": "Relational Decoupling & Cardinality Auditor",
        "refactor_risk_reviewer": "Refactorability & Sprouting Auditor",
    }
    
    def __init__(self):
        self.message_log: List[AgentMessage] = []
        
    def spawn_agent(self, agent_name: str, initial_prompt: Dict[str, Any]) -> Dict[str, Any]:
        if agent_name not in self.REGISTERED_AGENTS:
            raise ValueError(f"Unknown agent: {agent_name}. Must be one of {list(self.REGISTERED_AGENTS.keys())}")
        
        msg = AgentMessage(
            sender="captain_orchestrator",
            recipient=agent_name,
            content=initial_prompt,
            message_type="SPAWN"
        )
        self.message_log.append(msg)
        return {
            "status": "SPAWNED",
            "agent": agent_name,
            "role": self.REGISTERED_AGENTS[agent_name]
        }
        
    def dispatch_parallel_reviewers(self, schema_payload: Dict[str, Any]) -> List[str]:
        """Spawns all 4 Risk Reviewers concurrently."""
        reviewers = [
            "financial_risk_reviewer",
            "temporal_risk_reviewer",
            "relational_risk_reviewer",
            "refactor_risk_reviewer"
        ]
        for rev in reviewers:
            self.spawn_agent(rev, schema_payload)
        return reviewers
