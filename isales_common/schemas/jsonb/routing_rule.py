"""Schema for ``campaign.routing_rules`` (JSONB array element).

Spec: ai-pipeline § "路由规则引擎（decider）"; data-model § "campaign.routing_rules
路由规则 schema". engine-multi-referee-and-restructure D3.

A routing rule binds one referee (by ``label``) to a set of category values and
an action. The engine's decider walks the ordered list and the first rule whose
referee returned a category in ``match`` wins (first-match-wins). No match →
``continue`` (back to LISTENING) — ``continue`` is implicit, never an explicit
rule.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from isales_common.schemas._base import AppModel

#: Transition targets a rule may drive the state machine to. Mirrors the
#: existing referee-driven transitions (goal-achievement / human-handoff specs).
TransitionTarget = Literal["goal_achieved", "transfer", "customer_decline"]

#: Where restructure draws its InterruptText from (D5). ``low_confidence`` is an
#: internal trigger, not a user-configurable source, so it is excluded here.
RestructureSource = Literal["last_reply", "interrupt_remaining"]


class TransitionAction(AppModel):
    """Drive the state machine to a terminal-ish state."""

    type: Literal["transition"] = "transition"
    to: TransitionTarget
    # Required iff to == "goal_achieved" (carries the goal_type the worker
    # records); MUST be null otherwise.
    goal_type: str | None = None

    @model_validator(mode="after")
    def _goal_type_only_for_goal_achieved(self) -> TransitionAction:
        if self.to == "goal_achieved" and not self.goal_type:
            raise ValueError("goal_type is required when to='goal_achieved'")
        if self.to != "goal_achieved" and self.goal_type is not None:
            raise ValueError("goal_type is only valid when to='goal_achieved'")
        return self


class RestructureAction(AppModel):
    """Switch to the restructure stream, re-voicing InterruptText."""

    type: Literal["restructure"] = "restructure"
    source: RestructureSource


RoutingAction = TransitionAction | RestructureAction


class RoutingRule(AppModel):
    """One ordered routing rule: referee category → action."""

    referee: str = Field(min_length=1, max_length=64, description="referee role_config.label")
    match: list[str] = Field(min_length=1, description="category values that fire this rule")
    action: RoutingAction = Field(discriminator="type")
