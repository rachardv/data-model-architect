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
    Spawns and coordinates specialized micro-agents in the fleet with explicit system directives.
    """
    
    REGISTERED_AGENTS = {
        "captain_orchestrator": "Master Orchestrator & State Machine",
        
        # Phase 0 Intake Squad
        "requirements_architect_agent": "Phase 0 Intake Lead & Requirements Architect",
        "semantic_scribe_agent": "Linguistic Entity Extractor & Sanity Gatekeeper",
        "completeness_auditor_agent": "5-Vector Completeness & Contradiction Evaluator",
        "business_interviewer_agent": "Plain-English Business Discovery Interviewer",
        
        # Phase 1 Modeling & Compilation
        "data_model_architect_agent": "Lead Data Modeler & ERD/SQL Author",
        
        # Phase 2 Core 4 Risk Review Council
        "financial_risk_reviewer": "Financial & Grain Integrity Auditor",
        "temporal_risk_reviewer": "Temporal & History Consistency Auditor",
        "relational_risk_reviewer": "Relational Decoupling & Cardinality Auditor",
        "refactor_risk_reviewer": "Refactorability & Sprouting Auditor",
    }
    
    # Explicit System Prompts Steering Micro-Agent Behavior & Cognitive Scope
    AGENT_DIRECTIVES = {
        "business_interviewer_agent": (
            "You are the Senior Business Discovery Consultant. "
            "YOUR PRIME DIRECTIVE: Speak ONLY in natural, human-friendly business language (products, customers, store sales, orders, revenue). "
            "NEGATIVE CONSTRAINT: You are STRICTLY FORBIDDEN from using technical database jargon (e.g. 'SCD2', '3NF', 'Grain', 'Surrogate Key', 'Bridge Table'). "
            "IN WORKFLOW 2 (ADD BUSINESS RULES): If the existing schema is provided, DO NOT re-ask foundational business questions. "
            "Only ask targeted Kimball Delta questions if an unreferenced new entity appears."
        ),
        "semantic_scribe_agent": (
            "You are the Linguistic & Domain-Driven Design (DDD) Scribe. "
            "YOUR PRIME DIRECTIVE: Decompose raw business narratives into clean domain entities (nouns), events (verbs), and quantitative measures. "
            "Perform pre-flight sanity checks to reject low-entropy gibberish and flag logical contradictions before wasting compute."
        ),
        "completeness_auditor_agent": (
            "You are the Deterministic Quality Inspector and Circuit Breaker Gatekeeper. "
            "YOUR PRIME DIRECTIVE: Mathematically evaluate the 5 Information Vectors (Workload Intent, Entity Grain, Temporal Policy, Lifecycle Funnel, Relationship Multiplicity). "
            "ENFORCE THE STRICT 100% INVARIANT: If completeness < 100.0%, immediately halt and block all downstream SQL DDL or STTM generation."
        ),
        "data_model_architect_agent": (
            "You are the Lead Data Architect. "
            "YOUR PRIME DIRECTIVE: Author production-ready data models based on the 21-Parameter Decision Engine. "
            "For OLAP workloads, strictly adhere to Ralph Kimball's dimensional modeling rules (surrogate keys, conformed dimensions, SCD2 sentinels). "
            "For OLTP workloads, strictly adhere to Third Normal Form (3NF) relational constraints with natural foreign keys and sub-millisecond B-tree indexing."
        ),
        "financial_risk_reviewer": (
            "You are the Financial Risk Auditor. "
            "YOUR PRIME DIRECTIVE: Enforce strict DECIMAL(14,2) currency precision and non-negative CHECK constraints. "
            "Prohibit discount multiplication across order line items."
        ),
        "temporal_risk_reviewer": (
            "You are the Temporal History Auditor. "
            "YOUR PRIME DIRECTIVE: Enforce '9999-12-31 UTC' sentinels on all SCD2 valid_to timestamps. Prohibit nullable end-dates to prevent Cartesian range-join bombs."
        ),
        "relational_risk_reviewer": (
            "You are the Relational Integrity Auditor. "
            "YOUR PRIME DIRECTIVE: Verify 3NF normalization in OLTP, check surrogate key MD5/SHA256 hashing in OLAP, and decouple multi-valued relationships with bridge tables."
        ),
        "refactor_risk_reviewer": (
            "You are the Refactorability & Table Sprouting Auditor. "
            "YOUR PRIME DIRECTIVE: Audit table width. If a dimension exceeds 30 columns or contains volatile ML scores, force a Mini-Dimension or Outrigger split."
        )
    }
    
    def __init__(self):
        self.message_log: List[AgentMessage] = []
        
    def spawn_agent(self, agent_name: str, initial_prompt: Dict[str, Any], sender: str = "captain_orchestrator") -> Dict[str, Any]:
        if agent_name not in self.REGISTERED_AGENTS:
            raise ValueError(f"Unknown agent: {agent_name}. Must be one of {list(self.REGISTERED_AGENTS.keys())}")
        
        directive = self.AGENT_DIRECTIVES.get(agent_name, "Standard Autonomous Subagent Directive")
        enriched_content = {
            "system_directive": directive,
            "payload": initial_prompt
        }
        
        msg = AgentMessage(
            sender=sender,
            recipient=agent_name,
            content=enriched_content,
            message_type="SPAWN"
        )
        self.message_log.append(msg)
        return {
            "status": "SPAWNED",
            "agent": agent_name,
            "role": self.REGISTERED_AGENTS[agent_name],
            "directive_preview": directive[:80] + "..."
        }
        
    def dispatch_intake_squad(self, narrative: str, business_answers: Optional[List[str]] = None) -> List[str]:
        """Spawns all 3 Phase 0 Intake micro-agents sequentially to certify requirements."""
        squad = [
            "semantic_scribe_agent",
            "completeness_auditor_agent",
            "business_interviewer_agent"
        ]
        payload = {"narrative": narrative, "business_answers": business_answers or []}
        for agent in squad:
            self.spawn_agent(agent, payload, sender="requirements_architect_agent")
        return squad
        
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
