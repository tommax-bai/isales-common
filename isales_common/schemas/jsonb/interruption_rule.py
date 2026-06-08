"""Schema for ``campaign.interruption_rules`` (JSONB, a composable rule tree).

Spec: interruption-detection § "可组合规则树打断判定" + "打断规则树配置与装配".
Change: engine-interruption-rule-tree (port of voxen ``core/interruption/``).

A composable boolean tree decides whether a user's ASR partial text counts as a
barge-in. Leaves test the text (and elapsed speech duration); composites combine
them with and/or/not. NULL column → engine synthesizes a backward-compatible
default tree from the legacy ``interruption_whitelist`` / ``interruption_min_
duration_ms`` columns (design D4); this schema only describes an *explicit* tree.

This schema enforces shape only. Depth / node-count limits are enforced by
:func:`validate_interruption_rule` (called by the api write path); the regex
pattern length cap is a field constraint.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import Field

from isales_common.schemas._base import AppModel

#: Max nesting depth of the rule tree (api-enforced, design Q1).
MAX_RULE_DEPTH = 8
#: Max total node count of the rule tree (api-enforced, design Q1).
MAX_RULE_NODES = 64
#: Max length of a single regex pattern (mitigates ReDoS, design D7).
MAX_REGEX_LEN = 128


# --- leaf rules ---------------------------------------------------------------


class KeywordRule(AppModel):
    """Text (trailing punctuation trimmed) hits any phrase in ``values``.

    ``match="contains"`` (default, voxen-style substring) or ``"exact"`` (whole
    stripped text equals a phrase — the legacy ``interruption_whitelist``
    semantics the default tree reproduces).
    """

    type: Literal["keyword"] = "keyword"
    values: list[str] = Field(min_length=1)
    match: Literal["contains", "exact"] = "contains"


class LengthRule(AppModel):
    """``len(text.strip())`` (rune/char count) ≥ ``value``."""

    type: Literal["length"] = "length"
    value: int = Field(ge=1)


class DurationRule(AppModel):
    """Elapsed ms since user speech_start ≥ ``value_ms`` (iSales semantic).

    Deliberately NOT voxen's ``timeInterval`` (which anchors on first rule eval
    and is never re-armed); anchored on the user's speech_start so it re-arms per
    user utterance (design D3).
    """

    type: Literal["duration"] = "duration"
    value_ms: int = Field(ge=0)


class RegexRule(AppModel):
    """``re.search(pattern, text)`` matches."""

    type: Literal["regex"] = "regex"
    pattern: str = Field(min_length=1, max_length=MAX_REGEX_LEN)


class SplitByDelimiterRule(AppModel):
    """Text contains any of ``delimiters``."""

    type: Literal["split_by_delimiter"] = "split_by_delimiter"
    delimiters: list[str] = Field(min_length=1)


class NoneRule(AppModel):
    """Always false (interruption disabled)."""

    type: Literal["none"] = "none"


# --- composite rules ----------------------------------------------------------


class AndRule(AppModel):
    """All children true (short-circuit on first false)."""

    type: Literal["and"] = "and"
    rules: list[InterruptionRule] = Field(min_length=1)


class OrRule(AppModel):
    """Any child true (short-circuit on first true)."""

    type: Literal["or"] = "or"
    rules: list[InterruptionRule] = Field(min_length=1)


class NotRule(AppModel):
    """Inverts a single child rule."""

    type: Literal["not"] = "not"
    rule: InterruptionRule


#: Discriminated union over ``type`` (recursive: and/or/not nest InterruptionRule).
InterruptionRule = Annotated[
    Union[
        KeywordRule,
        LengthRule,
        DurationRule,
        RegexRule,
        SplitByDelimiterRule,
        NoneRule,
        AndRule,
        OrRule,
        NotRule,
    ],
    Field(discriminator="type"),
]

AndRule.model_rebuild()
OrRule.model_rebuild()
NotRule.model_rebuild()


def _depth_and_nodes(rule: object) -> tuple[int, int]:
    """Return (depth, node_count) for a parsed rule-tree model."""
    if isinstance(rule, (AndRule, OrRule)):
        children = [_depth_and_nodes(r) for r in rule.rules]
        depth = 1 + max((d for d, _ in children), default=0)
        nodes = 1 + sum(n for _, n in children)
        return depth, nodes
    if isinstance(rule, NotRule):
        d, n = _depth_and_nodes(rule.rule)
        return 1 + d, 1 + n
    return 1, 1


def validate_interruption_rule(rule: object) -> None:
    """Enforce depth / node-count limits on a parsed rule tree.

    Shape (types, fields, regex length) is enforced by the models themselves;
    this adds the whole-tree limits. Raises ``ValueError`` on violation. Called
    by the api write path (design D7).
    """
    depth, nodes = _depth_and_nodes(rule)
    if depth > MAX_RULE_DEPTH:
        raise ValueError(f"interruption rule tree too deep: {depth} > {MAX_RULE_DEPTH}")
    if nodes > MAX_RULE_NODES:
        raise ValueError(f"interruption rule tree too many nodes: {nodes} > {MAX_RULE_NODES}")
