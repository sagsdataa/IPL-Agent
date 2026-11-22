from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# SUPPORTED CAPABILITIES
# ============================================================

CapabilityName = Literal[
    "knowledge_search",
    "analytics_query",
]


RouteName = Literal[
    "knowledge",
    "analytics",
    "hybrid",
    "unsupported",
]


# ============================================================
# ENTITY REFERENCE
# ============================================================

class EntityReference(BaseModel):

    entity_type: str

    canonical_name: str

    mention: str | None = None


# ============================================================
# INDIVIDUAL PLANNED TASK
# ============================================================

class PlannedTask(BaseModel):

    task_id: str

    capability: CapabilityName

    question: str

    depends_on: list[str] = Field(
        default_factory=list
    )

    entities: list[EntityReference] = Field(
        default_factory=list
    )

    #metadata: dict[str, Any] = Field(
    #    default_factory=dict
    #)


# ============================================================
# COMPLETE CAPABILITY PLAN
# ============================================================

class CapabilityPlan(BaseModel):

    route: RouteName

    original_question: str

    tasks: list[PlannedTask] = Field(
        default_factory=list
    )

    entities: list[EntityReference] = Field(
        default_factory=list
    )

    unsupported_reason: str | None = None