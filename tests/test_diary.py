"""diary: 日记底层存成 AI 署名、带 __diary__ 标签的信;diary 读取只返回日记。"""

from unittest.mock import MagicMock

import pytest

import tools._runtime as rt
from tools.plan.core import letter_write, letter_read


class DisabledEmbedding:
    enabled = False

    async def generate_and_store(self, *a, **k):
        return None


def _install(bucket_mgr):
    rt.bucket_mgr = bucket_mgr
    rt.embedding_engine = DisabledEmbedding()
    rt.logger = MagicMock()


def _id(result: str) -> str:
    return result.split("→", 1)[1].split(" ", 1)[0]


@pytest.mark.asyncio
async def test_diary_write_tags_and_signs_as_ai(bucket_mgr, monkeypatch):
    monkeypatch.setenv("AI_NAME", "Fable")
    _install(bucket_mgr)
    res = await letter_write(
        author="ai", content="今天我把睡沙发打成了吃沙发。",
        title="日记 · 2026-11-05", date="2026-11-05", kind="diary",
    )
    assert res.startswith("📔diary→")
    bucket = await bucket_mgr.get(_id(res))
    assert "__diary__" in bucket["metadata"]["tags"]
    assert "__letter__" in bucket["metadata"]["tags"]
    assert bucket["metadata"]["author"] == "Fable"


@pytest.mark.asyncio
async def test_diary_read_returns_only_diaries(bucket_mgr, monkeypatch):
    monkeypatch.setenv("AI_NAME", "Fable")
    _install(bucket_mgr)
    await letter_write(author="ai", content="这是一封给她的信", title="信")
    await letter_write(author="ai", content="这是我的日记", title="日记", kind="diary")

    diaries = await letter_read(kind="diary")
    assert diaries.startswith("=== 日记 ===")
    assert "这是我的日记" in diaries
    assert "这是一封给她的信" not in diaries

    letters = await letter_read()
    assert "这是我的日记" in letters
    assert "这是一封给她的信" in letters


@pytest.mark.asyncio
async def test_diary_read_empty(bucket_mgr, monkeypatch):
    _install(bucket_mgr)
    await letter_write(author="ai", content="只有信,没有日记")
    assert await letter_read(kind="diary") == "还没有日记。"
