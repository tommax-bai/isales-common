"""Unit tests for isales_common.cli.cred_migrate (parse + key mapping).

DB-backed import/export 留给 isales-api 集成测试 (需要 PG ON CONFLICT)；
这里仅覆盖 env 文件解析 + ENV_KEY_MAP 一致性 + main argparse 路径。
"""
from __future__ import annotations

from pathlib import Path

from isales_common.cli.cred_migrate import (
    ENV_KEY_MAP,
    REVERSE_KEY_MAP,
    SPEECH_FIELDS,
    parse_env_file,
)


class TestParseEnvFile:
    def test_basic_kv(self, tmp_path: Path):
        f = tmp_path / "test.env"
        f.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
        assert parse_env_file(f) == {"FOO": "bar", "BAZ": "qux"}

    def test_strips_double_quotes(self, tmp_path: Path):
        f = tmp_path / "test.env"
        f.write_text('FOO="bar baz"\n', encoding="utf-8")
        assert parse_env_file(f) == {"FOO": "bar baz"}

    def test_strips_single_quotes(self, tmp_path: Path):
        f = tmp_path / "test.env"
        f.write_text("FOO='bar baz'\n", encoding="utf-8")
        assert parse_env_file(f) == {"FOO": "bar baz"}

    def test_ignores_comments(self, tmp_path: Path):
        f = tmp_path / "test.env"
        f.write_text("# this is a comment\nFOO=bar\n#FOO=ignored\n", encoding="utf-8")
        assert parse_env_file(f) == {"FOO": "bar"}

    def test_ignores_empty_lines(self, tmp_path: Path):
        f = tmp_path / "test.env"
        f.write_text("\nFOO=bar\n\n\nBAZ=qux\n", encoding="utf-8")
        assert parse_env_file(f) == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_empty_value(self, tmp_path: Path):
        f = tmp_path / "test.env"
        f.write_text("FOO=\nBAR=value\n", encoding="utf-8")
        # 空值不入字典 (避免覆盖已设字段为空)
        assert parse_env_file(f) == {"BAR": "value"}

    def test_lowercase_keys_ignored(self, tmp_path: Path):
        """Regex 仅匹配 [A-Z]开头，不接 dotenv 常见的小写自定义键。"""
        f = tmp_path / "test.env"
        f.write_text("foo=bar\nFOO=baz\n", encoding="utf-8")
        assert parse_env_file(f) == {"FOO": "baz"}


class TestKeyMap:
    def test_volcengine_llm_keys_present(self):
        # split-model-and-speech-provider-config: volcengine = 火山方舟 Ark LLM,
        # 其 api_key 是 ark key (非语音 X-Api-Key)。
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_API_KEY"] == ("volcengine", "api_key")
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_LLM_MODEL"] == (
            "volcengine",
            "default_model",
        )

    def test_volcengine_speech_keys_present(self):
        # 语音密钥归 volcengine_speech provider_id, 与 LLM 互不串。
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_SPEECH_API_KEY"] == (
            "volcengine_speech",
            "api_key",
        )
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_APP_KEY"] == (
            "volcengine_speech",
            "app_key",
        )
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_APP_TOKEN"] == (
            "volcengine_speech",
            "app_token",
        )
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_TTS_RESOURCE_ID"] == (
            "volcengine_speech",
            "tts_resource_id",
        )

    def test_llm_and_speech_api_key_are_distinct_providers(self):
        # 两条产品线两套密钥: 同 field_name=api_key 但不同 provider_id。
        llm = ENV_KEY_MAP["ISALES_VOLCENGINE_API_KEY"]
        speech = ENV_KEY_MAP["ISALES_VOLCENGINE_SPEECH_API_KEY"]
        assert llm[1] == speech[1] == "api_key"
        assert llm[0] == "volcengine"
        assert speech[0] == "volcengine_speech"
        assert llm != speech

    def test_dashscope_keys_present(self):
        assert ENV_KEY_MAP["ISALES_DASHSCOPE_API_KEY"] == ("dashscope", "api_key")

    def test_reverse_map_is_inverse(self):
        for env_key, (provider_id, field_name) in ENV_KEY_MAP.items():
            assert REVERSE_KEY_MAP[(provider_id, field_name)] == env_key

    def test_no_duplicate_destinations(self):
        # 不同 ENV_KEY 不应映射到同一 (provider, field) 对，否则
        # REVERSE_KEY_MAP 会丢失。
        destinations = list(ENV_KEY_MAP.values())
        assert len(destinations) == len(set(destinations))


class TestSpeechFields:
    def test_speech_fields_cover_migrated_columns(self):
        # split-speech 搬运的语音字段全集 (provider_id 改写, cipher 不动)。
        assert SPEECH_FIELDS == frozenset(
            {
                "api_key",
                "app_key",
                "app_token",
                "tts_resource_id",
                "asr_resource_id",
                "asr_endpoint",
                "tts_endpoint",
            }
        )

    def test_speech_fields_exclude_llm_only_columns(self):
        # endpoint / default_model 属火山方舟 Ark LLM, MUST NOT 被搬到语音。
        assert "endpoint" not in SPEECH_FIELDS
        assert "default_model" not in SPEECH_FIELDS
