"""Unit tests for isales_common.cli.cred_migrate (parse + key mapping).

DB-backed import/export 留给 isales-api 集成测试 (需要 PG ON CONFLICT)；
这里仅覆盖 env 文件解析 + ENV_KEY_MAP 一致性 + main argparse 路径。
"""
from __future__ import annotations

from pathlib import Path

from isales_common.cli.cred_migrate import (
    ENV_KEY_MAP,
    REVERSE_KEY_MAP,
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
    def test_volcengine_keys_present(self):
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_APP_KEY"] == ("volcengine", "app_key")
        assert ENV_KEY_MAP["ISALES_VOLCENGINE_APP_TOKEN"] == ("volcengine", "app_token")

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
