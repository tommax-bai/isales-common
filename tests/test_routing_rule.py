"""Tests for campaign.routing_rules JSONB schema + RoleKind.RESTRUCTURE.

engine-multi-referee-and-restructure §1.10.
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from isales_common.enums import PromptScopeType, RoleKind
from isales_common.schemas.jsonb import (
    RestructureAction,
    RoutingRule,
    TransitionAction,
)


def test_rolekind_has_restructure():
    assert RoleKind.RESTRUCTURE == "restructure"
    assert {k.value for k in RoleKind} == {"main", "referee", "extractor", "restructure"}
    # PromptScopeType mirrors RoleKind so restructure prompts can be versioned.
    assert {k.value for k in RoleKind} == {p.value for p in PromptScopeType}


def test_transition_action_goal_achieved_requires_goal_type():
    ok = TransitionAction(to="goal_achieved", goal_type="appointment")
    assert ok.goal_type == "appointment"
    with pytest.raises(ValidationError):
        TransitionAction(to="goal_achieved")  # missing goal_type


def test_transition_action_goal_type_only_for_goal_achieved():
    with pytest.raises(ValidationError):
        TransitionAction(to="transfer", goal_type="appointment")
    # transfer / customer_decline without goal_type are fine
    assert TransitionAction(to="transfer").goal_type is None
    assert TransitionAction(to="customer_decline").goal_type is None


def test_restructure_action_source_enum():
    assert RestructureAction(source="last_reply").type == "restructure"
    assert RestructureAction(source="interrupt_remaining").source == "interrupt_remaining"
    with pytest.raises(ValidationError):
        RestructureAction(source="low_confidence")  # internal-only, not configurable


def test_routing_rule_discriminated_action():
    r = RoutingRule.model_validate(
        {
            "referee": "intent",
            "match": ["NEGATIVE"],
            "action": {"type": "restructure", "source": "last_reply"},
        }
    )
    assert isinstance(r.action, RestructureAction)

    r2 = RoutingRule.model_validate(
        {
            "referee": "main_judge",
            "match": ["goal_achieved"],
            "action": {"type": "transition", "to": "goal_achieved", "goal_type": "sale"},
        }
    )
    assert isinstance(r2.action, TransitionAction)
    assert r2.action.goal_type == "sale"


def test_routing_rule_requires_nonempty_match():
    with pytest.raises(ValidationError):
        RoutingRule(referee="x", match=[], action={"type": "transition", "to": "transfer"})


def test_routing_rules_list_roundtrip():
    rules = [
        {
            "referee": "main_judge",
            "match": ["transfer"],
            "action": {"type": "transition", "to": "transfer"},
        },
        {
            "referee": "intent",
            "match": ["NEGATIVE"],
            "action": {"type": "restructure", "source": "last_reply"},
        },
    ]
    adapter = TypeAdapter(list[RoutingRule])
    parsed = adapter.validate_python(rules)
    assert len(parsed) == 2
    # round-trips back to equal models (JSON dump adds explicit goal_type: null
    # on transition actions, so re-validate rather than compare raw dicts).
    assert adapter.validate_python(adapter.dump_python(parsed, mode="json")) == parsed
