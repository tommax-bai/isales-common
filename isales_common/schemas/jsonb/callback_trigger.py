"""Type alias for ``callback_config.trigger`` (JSONB, JsonLogic expression).

Spec: webhook-callback § trigger 表达式使用 JsonLogic.

JsonLogic shape is ``{op: <operand_or_list>}``. Validating the full grammar is
the JsonLogic library's job; here we only enforce "is a non-empty dict".
"""

from __future__ import annotations

from typing import Any

CallbackTrigger = dict[str, Any]
