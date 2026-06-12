"""isales-cred-migrate — one-shot provider_credential migration tool.

Spec: provider-credential capability § "一次性迁移工具 isales-cred-migrate".

子命令:

  import-env  读 env 文件里的 ISALES_VOLCENGINE_APP_KEY 等已知字段 ->
              Fernet 加密 -> upsert 到 provider_credential 表 (provider_id,
              field_name) 对。默认 dry-run，仅打印 masked 计划；--apply
              真写。明文不打 stdout。

  export-env  读 provider_credential 表 -> 解密 -> 写出 env 兼容行
              (`ISALES_VOLCENGINE_APP_KEY=<plaintext>` 等)。仅 rollback
              路径用。

  split-speech  把现有单一 `volcengine` provider_id 下的豆包语音字段
              (app_key/app_token/*_resource_id/*_endpoint + 旧布局承载语音
              X-Api-Key 的 api_key) 整行搬到 `volcengine_speech` provider_id
              (split-model-and-speech-provider-config)。纯 provider_id 改写,
              cipher_text 不动。默认 dry-run;--apply 真写;--rollback 反向。
              迁移后单独把 ark LLM key 写入 volcengine.api_key。

环境变量:
  ISALES_FERNET_KEY     必须;Fernet 主密钥 (urlsafe base64, 32 byte)
  ISALES_DATABASE_URL   必须;PG asyncpg URL (postgresql+asyncpg://...)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from collections.abc import Iterable
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from isales_common.credentials import mask
from isales_common.models.provider_credential import ProviderCredential
from isales_common.utils.crypto import decrypt, encrypt


# (provider_id, field_name) 映射表 - 增加新 provider/字段时改这里。
#
# split-model-and-speech-provider-config: 火山两条产品线两套密钥拆成两个
# provider_id —— `volcengine` = 火山方舟 Ark LLM (api_key=ark + endpoint +
# default_model);`volcengine_speech` = 豆包语音 ASR/TTS (新版 api_key=
# X-Api-Key / 旧版 app_key+app_token / *_resource_id / *_endpoint)。二者
# 的 api_key 是**不同**的密钥 (ark UUID vs 语音 X-Api-Key),MUST NOT 混入
# 同一 provider_id。原 `ISALES_VOLCENGINE_API_KEY` 承载语音 X-Api-Key,
# 拆分后改承载 ark LLM key;语音 X-Api-Key 走新键 ISALES_VOLCENGINE_SPEECH_API_KEY。
ENV_KEY_MAP: dict[str, tuple[str, str]] = {
    # --- volcengine 火山方舟 Ark LLM (豆包大模型) ---
    "ISALES_VOLCENGINE_API_KEY": ("volcengine", "api_key"),  # ark key (UUID)
    "ISALES_VOLCENGINE_LLM_MODEL": ("volcengine", "default_model"),
    # --- volcengine_speech 豆包语音 ASR/TTS (bytedance openspeech) ---
    # 新版控制台单 API Key 鉴权 (豆包 V3 SSE TTS / V3 SAUC ASR, vendor docs
    # § 2.1 新版控制台). 老版 app_key/app_token 仍保留作 fallback 走旧版三件套.
    "ISALES_VOLCENGINE_SPEECH_API_KEY": ("volcengine_speech", "api_key"),
    "ISALES_VOLCENGINE_APP_KEY": ("volcengine_speech", "app_key"),
    "ISALES_VOLCENGINE_APP_TOKEN": ("volcengine_speech", "app_token"),
    "ISALES_VOLCENGINE_TTS_RESOURCE_ID": ("volcengine_speech", "tts_resource_id"),
    # ASR V3 SAUC resource id (volc.bigasr.sauc.duration / .concurrent /
    # volc.seedasr.sauc.duration / .concurrent). 跨 grant 切版本走这里.
    "ISALES_VOLCENGINE_ASR_RESOURCE_ID": ("volcengine_speech", "asr_resource_id"),
    "ISALES_VOLCENGINE_ASR_ENDPOINT": ("volcengine_speech", "asr_endpoint"),
    "ISALES_VOLCENGINE_TTS_ENDPOINT": ("volcengine_speech", "tts_endpoint"),
    "ISALES_DASHSCOPE_API_KEY": ("dashscope", "api_key"),
    "ISALES_DASHSCOPE_BASE_URL": ("dashscope", "endpoint"),
    "ISALES_DASHSCOPE_LLM_MODEL": ("dashscope", "default_model"),
}

# split-volcengine-speech: 在旧的单一 `volcengine` provider_id 下,这些
# field_name 实际属于豆包语音 (ASR/TTS) 产品线,迁移时整行搬到
# `volcengine_speech`。迁移后 `volcengine` 仅留 Ark LLM 字段 (api_key=ark
# + endpoint + default_model);其中 ark api_key 是**新值**,迁移后再单独
# 写入 (不在 SPEECH_FIELDS 搬运范围 —— 旧 `volcengine.api_key` 是语音键,
# 先被搬到 volcengine_speech,再把 ark key 写回 volcengine.api_key)。
SPEECH_FIELDS: frozenset[str] = frozenset(
    {
        "api_key",  # 旧布局: 语音新版 X-Api-Key (NOT ark LLM key)
        "app_key",
        "app_token",
        "tts_resource_id",
        "asr_resource_id",
        "asr_endpoint",
        "tts_endpoint",
    }
)

# 反向: (provider_id, field_name) -> ENV_KEY (用于 export-env)。
REVERSE_KEY_MAP: dict[tuple[str, str], str] = {v: k for k, v in ENV_KEY_MAP.items()}


_ENV_LINE_RX = re.compile(r"^\s*(?P<key>[A-Z][A-Z0-9_]*)\s*=\s*(?P<value>.*?)\s*$")


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a dotenv-style file. 忽略注释 / 空行 / 不含 = 的行。值不剥引号。"""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _ENV_LINE_RX.match(raw)
        if not m:
            continue
        value = m.group("value")
        # strip surrounding quotes 如果 value 是 "abc" 或 'abc'
        if (
            len(value) >= 2
            and ((value[0] == value[-1]) and value[0] in ('"', "'"))
        ):
            value = value[1:-1]
        if value:
            out[m.group("key")] = value
    return out


def _engine_url() -> str:
    url = os.environ.get("ISALES_DATABASE_URL")
    if not url:
        sys.exit("error: ISALES_DATABASE_URL not set")
    return url


def _check_fernet() -> None:
    if not os.environ.get("ISALES_FERNET_KEY"):
        sys.exit(
            "error: ISALES_FERNET_KEY not set; generate via "
            "`python -c 'from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())'`"
        )


async def _import_env(env_path: Path, apply: bool) -> int:
    """读 env -> 加密 -> upsert。Return upsert count。"""
    env_values = parse_env_file(env_path)
    planned: list[tuple[str, str, str]] = []  # (provider_id, field_name, plaintext)
    for env_key, (provider_id, field_name) in ENV_KEY_MAP.items():
        if env_key in env_values:
            planned.append((provider_id, field_name, env_values[env_key]))

    if not planned:
        print(f"no known ISALES_* keys found in {env_path}", file=sys.stderr)
        return 0

    print(f"# import-env plan ({'apply' if apply else 'dry-run'}):")
    for provider_id, field_name, plaintext in planned:
        print(f"  {provider_id:12s} {field_name:18s} = {mask(plaintext)}")

    if not apply:
        print(f"\n(dry-run; pass --apply to write {len(planned)} row(s))")
        return 0

    engine = create_async_engine(_engine_url(), echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    upserted = 0
    async with session_factory() as session:
        for provider_id, field_name, plaintext in planned:
            cipher = encrypt(plaintext)
            stmt = pg_insert(ProviderCredential).values(
                provider_id=provider_id,
                field_name=field_name,
                cipher_text=cipher,
                updated_by="isales-cred-migrate",
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["provider_id", "field_name"],
                set_={"cipher_text": stmt.excluded.cipher_text, "updated_by": "isales-cred-migrate"},
            )
            await session.execute(stmt)
            upserted += 1
        await session.commit()
    await engine.dispose()
    print(f"\nupserted {upserted} row(s) into provider_credential")
    return upserted


async def _export_env(env_path: Path, apply: bool) -> int:
    """读 provider_credential -> 解密 -> 写 env 行。Return written count。"""
    engine = create_async_engine(_engine_url(), echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    lines: list[str] = []
    async with session_factory() as session:  # type: AsyncSession
        rows = (await session.execute(select(ProviderCredential))).scalars().all()
        for row in rows:
            env_key = REVERSE_KEY_MAP.get((row.provider_id, row.field_name))
            if env_key is None:
                continue
            plaintext = decrypt(row.cipher_text)
            lines.append(f"{env_key}={plaintext}")
    await engine.dispose()

    if not lines:
        print(f"no rows in provider_credential mappable to known ENV keys", file=sys.stderr)
        return 0

    print(f"# export-env plan ({'apply' if apply else 'dry-run'}):")
    for env_key, (provider_id, field_name) in ENV_KEY_MAP.items():
        if (provider_id, field_name) in {(p, f) for p, f, *_ in []}:
            pass  # placeholder for verbose mode
    # 仅展示 key 不展示明文
    for line in lines:
        key = line.split("=", 1)[0]
        print(f"  {key}")

    if not apply:
        print(f"\n(dry-run; pass --apply to write {len(lines)} line(s) to {env_path})")
        return 0

    # 写文件 (追加在文件末，保留原内容；用户负责清理重复字段)。
    with env_path.open("a", encoding="utf-8") as fh:
        fh.write("\n# --- isales-cred-migrate export-env (rollback only) ---\n")
        for line in lines:
            fh.write(line + "\n")
    print(f"\nwrote {len(lines)} line(s) to {env_path}")
    return len(lines)


async def _split_speech(apply: bool, rollback: bool) -> int:
    """把 `volcengine` 下的语音字段整行搬到 `volcengine_speech` (或反向回滚)。

    纯 provider_id 改写 —— cipher_text 不动 (同一 Fernet key, 解密仍有效),
    无需重新加密。幂等: 重复跑找不到源行即 no-op。dst 已有同名 field 时
    SKIP + 警告 (不破坏 UNIQUE(provider_id, field_name))。

    迁移顺序约束 (D5): 先跑本命令把语音 api_key 搬走, **再**把 ark LLM key
    写入 `volcengine.api_key` —— 否则 ark key 会被当语音键一起搬走。
    """
    src, dst = (
        ("volcengine_speech", "volcengine")
        if rollback
        else ("volcengine", "volcengine_speech")
    )
    engine = create_async_engine(_engine_url(), echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    moved = 0
    async with session_factory() as session:  # type: AsyncSession
        src_rows = (
            await session.execute(
                select(ProviderCredential).where(
                    ProviderCredential.provider_id == src
                )
            )
        ).scalars().all()
        dst_fields = {
            r.field_name
            for r in (
                await session.execute(
                    select(ProviderCredential).where(
                        ProviderCredential.provider_id == dst
                    )
                )
            ).scalars().all()
        }
        planned = [r for r in src_rows if r.field_name in SPEECH_FIELDS]

        verb = "rollback" if rollback else "split"
        print(f"# {verb}-speech plan ({'apply' if apply else 'dry-run'}): {src} -> {dst}")
        if not planned:
            print(f"  (no {src} speech-field rows found; nothing to move)")
        for row in planned:
            if row.field_name in dst_fields:
                print(
                    f"  SKIP {src}.{row.field_name} — {dst}.{row.field_name} "
                    "already exists (UNIQUE guard)"
                )
                continue
            try:
                preview = mask(decrypt(row.cipher_text))
            except Exception:  # noqa: BLE001  - preview only; never block move
                preview = "<undecryptable>"
            print(f"  MOVE {src}.{row.field_name:18s} -> {dst}.{row.field_name:18s} = {preview}")
            if apply:
                row.provider_id = dst
                moved += 1
        if apply:
            await session.commit()
    await engine.dispose()

    if not apply:
        print(
            f"\n(dry-run; pass --apply to move {len([r for r in planned if r.field_name not in dst_fields])} row(s))"
        )
        if not rollback:
            print(
                "after --apply, write the ark LLM key into volcengine.api_key "
                "(UI «模型配置» or ISALES_VOLCENGINE_API_KEY import-env)"
            )
        return 0
    print(f"\nmoved {moved} row(s) {src} -> {dst}")
    return moved


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="isales-cred-migrate",
        description="provider_credential 一次性迁移工具 (env <-> DB)",
    )
    subs = parser.add_subparsers(dest="cmd", required=True)

    p_imp = subs.add_parser("import-env", help="读 env -> 加密 -> upsert DB")
    p_imp.add_argument("--env-file", type=Path, required=True)
    p_imp.add_argument("--apply", action="store_true")

    p_exp = subs.add_parser("export-env", help="读 DB -> 解密 -> 写 env (rollback)")
    p_exp.add_argument("--env-file", type=Path, required=True)
    p_exp.add_argument("--apply", action="store_true")

    p_split = subs.add_parser(
        "split-speech",
        help="把 volcengine 语音字段搬到 volcengine_speech (provider_id 拆分)",
    )
    p_split.add_argument("--apply", action="store_true")
    p_split.add_argument(
        "--rollback",
        action="store_true",
        help="反向: volcengine_speech 语音字段搬回 volcengine",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)
    _check_fernet()

    if args.cmd == "import-env":
        asyncio.run(_import_env(args.env_file, args.apply))
    elif args.cmd == "export-env":
        asyncio.run(_export_env(args.env_file, args.apply))
    elif args.cmd == "split-speech":
        asyncio.run(_split_speech(args.apply, args.rollback))
    else:  # pragma: no cover  - argparse required=True 已守
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
