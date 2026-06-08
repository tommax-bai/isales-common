"""Tests for the pipeline schemas (engine-multi-referee-and-restructure)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from isales_common.schemas.jsonb import RoutingRule
from isales_common.schemas.pipeline import (
    ExtractorSpec,
    MainSpec,
    PipelineConfig,
    RefereeSpec,
    RestructureSpec,
)


def _slot(**over):
    base = {"role_config_id": 1, "prompt_version_id": 2, "system_prompt": "hi"}
    base.update(over)
    return base


@pytest.mark.parametrize("cls", [MainSpec, ExtractorSpec])
def test_slot_spec_defaults(cls):
    spec = cls(**_slot())
    assert spec.model == "mock"
    assert spec.temperature == 1.0
    assert spec.top_p == 1.0


@pytest.mark.parametrize("cls", [RefereeSpec, RestructureSpec])
def test_labelled_slot_defaults(cls):
    spec = cls(**_slot(label="x"))
    assert spec.model == "mock"
    assert spec.label == "x"


def test_referee_spec_requires_label():
    with pytest.raises(ValidationError):
        RefereeSpec(**_slot())


def test_pipeline_config_roundtrip():
    cfg = PipelineConfig(
        main=MainSpec(**_slot(model="doubao", temperature=0.7)),
        referees=[
            RefereeSpec(**_slot(role_config_id=3, model="qwen-turbo", label="intent")),
            RefereeSpec(**_slot(role_config_id=5, model="qwen-turbo", label="reject")),
        ],
        restructure=RestructureSpec(**_slot(role_config_id=6, label="rewrite")),
        extractor=ExtractorSpec(**_slot(role_config_id=4, model="qwen-plus")),
        routing_rules=[
            RoutingRule(
                referee="intent",
                match=["NEGATIVE"],
                action={"type": "restructure", "source": "last_reply"},
            ),
        ],
        max_continuous_restructure=3,
        short_reply_active=True,
    )
    dumped = cfg.model_dump()
    assert dumped["main"]["model"] == "doubao"
    assert [r["label"] for r in dumped["referees"]] == ["intent", "reject"]
    assert dumped["restructure"]["label"] == "rewrite"
    assert dumped["max_continuous_restructure"] == 3
    assert PipelineConfig.model_validate(dumped) == cfg


def test_pipeline_config_defaults():
    cfg = PipelineConfig(
        main=MainSpec(**_slot()),
        extractor=ExtractorSpec(**_slot()),
    )
    assert cfg.referees == []
    assert cfg.restructure is None
    assert cfg.routing_rules == []
    assert cfg.max_continuous_restructure == 2
    assert cfg.short_reply_active is False


def test_pipeline_config_rejects_extra_fields():
    with pytest.raises(ValidationError):
        PipelineConfig(
            main=MainSpec(**_slot()),
            extractor=ExtractorSpec(**_slot()),
            referee=RefereeSpec(**_slot(label="x")),  # old singular field — rejected
        )
