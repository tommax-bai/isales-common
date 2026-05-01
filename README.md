# isales-common

iSales 平台的共享 Python 包：SQLAlchemy 模型、Pydantic schemas、AI Provider ABC、跨服务 Redis 消息契约、alembic 迁移与通用工具。

被 `isales-api` / `isales-engine` / `isales-scheduler` / `isales-worker` / `isales-telephony` 共同依赖。

## 模块概览

| 模块 | 内容 | 关联 spec |
|---|---|---|
| `isales_common.enums` | 全局枚举（CallStatus、LeadStatus、HangupCause 等） | data-model |
| `isales_common.models` | 19 张表的 SQLAlchemy 2.x ORM；单一 `Base` | data-model |
| `isales_common.schemas` | DTO 三件套（Create / Update / Read） | data-model |
| `isales_common.schemas.jsonb` | JSONB 字段的嵌套 Pydantic 模型 | data-model（JSONB 字段约束） |
| `isales_common.schemas.messages` | 跨服务 Redis 消息契约（含 `BaseMessage` + 版本管理） | message-contract |
| `isales_common.providers` | ASR / TTS / LLM Provider ABC + 内存 mock | provider-abc |
| `isales_common.utils` | phone / crypto / redis client / audio 常量 | — |
| `alembic/` | 单一来源迁移；初始 revision 建 19 张表 | data-model |

## 安装

本地开发：

```bash
pip install -e ".[dev]"
pre-commit install
```

下游服务（在各自 `pyproject.toml`）：

```toml
[project]
dependencies = [
  "isales-common @ git+ssh://git@github.com/tommax-bai/isales-common.git@v0.1.0",
]
```

或在多仓本地开发时用相对路径：

```bash
pip install -e ../isales-common
```

## 测试

```bash
pytest
```

`tests/` 覆盖 utils、enums、DTO schemas、JSONB schemas、Provider ABC 契约、跨服务消息 round-trip。

## 数据库迁移

`env.py` 从 `ISALES_DATABASE_URL` 环境变量读 DSN（驱动必须是 `postgresql+asyncpg`），覆盖 `alembic.ini` 中的占位。

```bash
export ISALES_DATABASE_URL="postgresql+asyncpg://user:pwd@localhost/isales"
alembic upgrade head     # 应用全部迁移
alembic downgrade base   # 回退到空库
alembic check            # 校验 ORM 与库结构无 drift
```

CI 会自动跑一次 upgrade → check → downgrade → upgrade 完整 roundtrip。

## 在下游服务中的典型引用

```python
# isales-engine: 拉一条派单消息并回 ASR 文本
from isales_common.schemas.messages import (
    DialRequest, ASRPartial, is_supported_version,
)

raw = await redis.brpop("dial:queue")
msg = DialRequest.model_validate_json(raw)
if not is_supported_version(msg.schema_version):
    await dead_letter(raw)            # 见 message-contract spec
    return
# … 用 msg.lead / msg.prompt_versions / msg.caller_id 启动通话
await redis.publish(
    f"call:{msg.lead.lead_id}:events",
    ASRPartial(call_record_id=cr_id, text="he", timestamp_ms=100).model_dump_json(),
)
```

```python
# isales-engine: 接 Provider ABC 写真实实现
from isales_common.providers import LLMProvider, LLMResponse, Message

class OpenAILLMProvider(LLMProvider):
    async def chat(self, messages, *, json_mode=False, temperature=1.0,
                   top_p=1.0, max_tokens=None) -> LLMResponse:
        ...  # 包装 OpenAI SDK，把异常翻译为 ProviderError 子类
```

```python
# 测试中替换 Provider
from isales_common.providers.testing import mock_llm_provider  # pytest fixture
```

## 版本与演进

- 当前版本：`v0.1.0`
- 消息 schema 版本：`CURRENT_SCHEMA_VERSION = 1`
- 演进规则见 `message-contract` spec § Requirement: 演进规则；破坏性变更 MUST 走 OpenSpec change proposal。
