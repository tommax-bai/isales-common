"""Nested models inside ``pipeline_trace.role_candidates`` /
``pipeline_trace.judge_results`` JSONB columns.

Spec: transcript § pipeline_trace 字段; ai-pipeline for stage roles.
"""

from __future__ import annotations

from typing import Any

from isales_common.schemas._base import AppModel


class RoleCandidate(AppModel):
    role_config_id: int
    prompt_version_id: int
    raw_output: str | None = None
    parsed_json: dict[str, Any] | None = None
    duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    error: str | None = None


class JudgeResult(AppModel):
    candidate_index: int
    role_config_id: int
    prompt_version_id: int
    passed: bool
    reason: str | None = None
    duration_ms: int | None = None


class PolishInput(AppModel):
    candidates: list[dict[str, Any]]
    selected_index: int | None = None
