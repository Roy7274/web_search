# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# Licensed under the 【火山方舟】原型应用软件自用许可协议
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://www.volcengine.com/docs/82379/1433703
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
BytePlus AskEcho Search Agent 搜索引擎实现。

参考: https://docs.byteplus.com/en/docs/askecho/Agent_API_Reference
API Key 接入（推荐）: https://torchlight.byteintlapi.com/agent_api/agent/chat/completion
"""

import asyncio
import logging
from abc import ABC
from typing import Any, List, Optional

import httpx

from .search_engine import SearchEngine, SearchResult, SearchReference

LOGGER = logging.getLogger(__name__)

# AskEcho Search Agent API（API Key 接入推荐）
# 文档: https://docs.byteplus.com/en/docs/askecho/Agent_API_Reference
ASK_ECHO_CHAT_URL = "https://torchlight.byteintlapi.com/agent_api/agent/chat/completion"
DEFAULT_TIMEOUT = 60.0


class AskEchoSearchEngine(SearchEngine, ABC):
    """使用 BytePlus AskEcho Search Agent 进行搜索。"""

    def __init__(
        self,
        api_key: str,
        agent_id: str,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__()
        self._api_key = (api_key or "").strip()
        self._agent_id = (agent_id or "").strip()
        raw = (base_url or "").strip().rstrip("/")
        self._chat_url = f"{raw}/agent_api/agent/chat/completion" if raw else ASK_ECHO_CHAT_URL
        self._timeout = timeout
        if not self._api_key:
            raise ValueError("AskEcho 必须配置 ASK_ECHO_API_KEY")


    def search(self, queries: List[str]) -> List[SearchResult]:
        return asyncio.run(self.asearch(queries=queries))

    async def asearch(self, queries: List[str]) -> List[SearchResult]:
        tasks = [self._single_search(query) for query in queries]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        results: List[SearchResult] = []
        for i, r in enumerate(task_results):
            if isinstance(r, Exception):
                LOGGER.warning("AskEcho search failed for query %s: %s", queries[i], r)
                results.append(
                    SearchResult(
                        query=queries[i],
                        summary_content=f"搜索失败: {str(r)}",
                        search_references=[],
                    )
                )
            else:
                results.append(r)
        return results

    async def _single_search(self, query: str) -> SearchResult:
        url = self._chat_url
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "bot_id": self._agent_id,
            "messages": [{"role": "user", "content": query}],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        LOGGER.info(f"AskEcho response for query '{query}': {data}")
        return self._format_result(data, query)

    @classmethod
    def _format_result(cls, data: dict, query: str) -> SearchResult:
        choices = data.get("choices") or []
        content = ""
        if choices and isinstance(choices[0], dict):
            msg = choices[0].get("message") or {}
            content = (msg.get("content") or "").strip()
        refs: List[SearchReference] = []
        for r in data.get("references") or []:
            if isinstance(r, dict):
                refs.append(
                    SearchReference(
                        site=r.get("site_name"),
                        url=r.get("url"),
                        content=r.get("summary"),
                        title=r.get("title"),
                    )
                )
        return SearchResult(
            query=query,
            summary_content=content or "未返回内容。",
            search_references=refs if refs else None,
        )
