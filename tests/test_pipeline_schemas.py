"""Tests for the dual-LLM pipeline schemas (pipeline-stream-and-referee)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from isales_common.schemas.pipeline import (
    ExtractorSpec,
    MainSpec,
    PipelineConfig,
    RefereeSpec,
)


def _slot(**over):
    base = {"role_config_id": 1, "prompt_version_id": 2, "system_prompt": "hi"}
    base.update(over)
    return base


@pytest.mark.parametrize("cls", [MainSpec, RefereeSpec, ExtractorSpec])
def test_slot_spec_defaults(cls):
    spec = cls(**_slot())
    assert spec.model == "mock"
    assert spec.temperature == 1.0
    assert spec.top_p == 1.0


@pytest.mark.parametrize("cls", [MainSpec, RefereeSpec, ExtractorSpec])
def test_slot_spec_roundtrip(cls):
    spec = cls(**_slot(model="qwen-turbo", temperature=0.3, top_p=0.9))
    dumped = spec.model_dump()
    assert dumped["model"] == "qwen-turbo"
    assert cls.model_validate(dumped) == spec


def test_pipeline_config_roundtrip():
    cfg = PipelineConfig(
        main=MainSpec(**_slot(model="doubao", temperature=0.7)),
        referee=RefereeSpec(**_slot(role_config_id=3, model="qwen-turbo")),
        extractor=ExtractorSpec(**_slot(role_config_id=4, model="qwen-plus")),
        short_reply_active=True,
    )
    dumped = cfg.model_dump()
    assert dumped["main"]["model"] == "doubao"
    assert dumped["referee"]["model"] == "qwen-turbo"
    assert dumped["extractor"]["model"] == "qwen-plus"
    assert dumped["short_reply_active"] is True
    assert PipelineConfig.model_validate(dumped) == cfg


def test_pipeline_config_short_reply_defaults_false():
    cfg = PipelineConfig(
        main=MainSpec(**_slot()),
        referee=RefereeSpec(**_slot()),
        extractor=ExtractorSpec(**_slot()),
    )
    assert cfg.short_reply_active is False


def test_pipeline_config_rejects_extra_fields():
    with pytest.raises(ValidationError):
        PipelineConfig(
            main=MainSpec(**_slot()),
            referee=RefereeSpec(**_slot()),
            extractor=ExtractorSpec(**_slot()),
            judges=[],  # old field — must be rejected (extra=forbid)
        )
