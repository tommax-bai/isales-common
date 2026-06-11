"""Tests for engine-tools-multidialogue-gating schema additions:
tool_config, route/tool routing actions, persona slots, gating campaign fields.
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from isales_common.enums import HangupCause, PromptScopeType, RoleKind
from isales_common.schemas.campaign import CampaignUpdate
from isales_common.schemas.jsonb import (
    HangupToolConfig,
    RoutePersonaAction,
    RouteToolAction,
    RoutingAction,
    RoutingRule,
    ToolConfig,
    TransferToolConfig,
)
from isales_common.schemas.messages.dial import (
    PersonaPromptVersionRef,
    PromptVersionsSnapshot,
)
from isales_common.schemas.pipeline import (
    ExtractorSpec,
    MainSpec,
    PersonaSpec,
    PipelineConfig,
)


def test_enums_gained_persona_and_referee_hangup():
    assert RoleKind.PERSONA == "persona"
    assert PromptScopeType.PERSONA == "persona"
    assert HangupCause.REFEREE_HANGUP == "referee_hangup"


def test_tool_config_discriminated_union():
    adapter = TypeAdapter(ToolConfig)
    h = adapter.validate_python({"type": "hangup", "closing_phrase": "再见"})
    assert isinstance(h, HangupToolConfig)
    assert h.closing_phrase == "再见"
    assert h.interrupt is False
    t = adapter.validate_python({"type": "transfer"})
    assert isinstance(t, TransferToolConfig)
    # transfer carries no phrase field — single-source campaign.transfer_phrases.
    assert not hasattr(t, "connecting_phrase")
    with pytest.raises(ValidationError):
        adapter.validate_python({"type": "nope"})


def test_routing_action_route_and_tool():
    adapter = TypeAdapter(RoutingAction)
    r = adapter.validate_python(
        {"type": "route", "to": "closing", "then_state": "WRAPPING_UP"}
    )
    assert isinstance(r, RoutePersonaAction)
    assert r.to == "closing"
    assert r.then_state == "WRAPPING_UP"
    tool = adapter.validate_python({"type": "tool", "tool": "hangup", "then_state": "END"})
    assert isinstance(tool, RouteToolAction)
    assert tool.tool == "hangup"
    # then_state optional
    assert adapter.validate_python({"type": "route", "to": "p1"}).then_state is None
    # invalid then_state rejected
    with pytest.raises(ValidationError):
        adapter.validate_python({"type": "route", "to": "p1", "then_state": "BOGUS"})


def test_route_closing_carries_goal_type():
    # fix-goal-achievement-pipeline: route:closing carries goal_type (modern form
    # of transition:goal_achieved), so the goal_achieved event records a label.
    adapter = TypeAdapter(RoutingAction)
    r = adapter.validate_python(
        {"type": "route", "to": "closing", "then_state": "WRAPPING_UP",
         "goal_type": "intent_confirmed"}
    )
    assert isinstance(r, RoutePersonaAction)
    assert r.goal_type == "intent_confirmed"


def test_route_goal_type_rejected_for_non_closing():
    # goal_type only valid on the builtin closing route — forbidden on personas.
    adapter = TypeAdapter(RoutingAction)
    with pytest.raises(ValidationError):
        adapter.validate_python({"type": "route", "to": "p1", "goal_type": "x"})


def test_routing_rule_with_tool_action():
    rule = RoutingRule.model_validate(
        {
            "referee": "main_judge",
            "match": ["hangup"],
            "action": {"type": "tool", "tool": "hangup", "then_state": "END"},
        }
    )
    assert isinstance(rule.action, RouteToolAction)


def test_legacy_transition_action_still_parses():
    # removal-tracked shim: legacy transition kept.
    rule = RoutingRule.model_validate(
        {
            "referee": "main_judge",
            "match": ["goal_achieved"],
            "action": {"type": "transition", "to": "goal_achieved", "goal_type": "appointment"},
        }
    )
    assert rule.action.type == "transition"


def test_campaign_persona_fanout_cap_clamped():
    assert CampaignUpdate(persona_fanout_cap=1).persona_fanout_cap == 1
    assert CampaignUpdate(persona_fanout_cap=3).persona_fanout_cap == 3
    with pytest.raises(ValidationError):
        CampaignUpdate(persona_fanout_cap=0)
    with pytest.raises(ValidationError):
        CampaignUpdate(persona_fanout_cap=4)


def test_campaign_update_tools_and_gating_fields():
    u = CampaignUpdate(
        tools={"bye": {"type": "hangup", "closing_phrase": "再见"}},
        referee_timeout_ms=500,
        referee_fail_open_route="main",
    )
    assert isinstance(u.tools["bye"], HangupToolConfig)
    assert u.referee_timeout_ms == 500
    with pytest.raises(ValidationError):
        CampaignUpdate(referee_timeout_ms=0)  # gt=0


def test_pipeline_config_personas_and_gating():
    cfg = PipelineConfig(
        main=MainSpec(role_config_id=1, prompt_version_id=1, system_prompt="m"),
        extractor=ExtractorSpec(role_config_id=2, prompt_version_id=2, system_prompt="e"),
        personas=[
            PersonaSpec(role_config_id=3, prompt_version_id=3, system_prompt="p", label="warm")
        ],
        tools={"bye": {"type": "hangup"}},
        persona_fanout_cap=2,
        referee_timeout_ms=600,
        referee_fail_open_route="main",
    )
    assert cfg.personas[0].label == "warm"
    assert isinstance(cfg.tools["bye"], HangupToolConfig)
    assert cfg.persona_fanout_cap == 2
    # defaults when omitted
    bare = PipelineConfig(
        main=MainSpec(role_config_id=1, prompt_version_id=1, system_prompt="m"),
        extractor=ExtractorSpec(role_config_id=2, prompt_version_id=2, system_prompt="e"),
    )
    assert bare.personas == []
    assert bare.persona_fanout_cap == 1
    assert bare.referee_fail_open_route == "main"


def test_dial_persona_llms_snapshot():
    snap = PromptVersionsSnapshot(
        persona_llms=[
            PersonaPromptVersionRef(role_config_id=3, prompt_version_id=9, label="warm")
        ]
    )
    assert snap.persona_llms[0].label == "warm"
    assert PromptVersionsSnapshot().persona_llms == []
