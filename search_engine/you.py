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

import asyncio
import logging
from abc import ABC
from typing import Literal, Optional, List, Any

import httpx

from .search_engine import SearchEngine, SearchResult, SearchReference

LOGGER = logging.getLogger(__name__)

YOU_SEARCH_BASE_URL = "https://ydc-index.io/v1/search"
DEFAULT_TIMEOUT = 30.0


class YouSearchEngine(SearchEngine, ABC):
    """You.com Search API 搜索引擎实现。"""

    def __init__(
        self,
        api_key: str,
        count: int = 10,
        freshness: Literal["day", "week", "month", "year"] = "week",
        safesearch: Literal["off", "moderate", "strict"] = "moderate",
        timeout: float = DEFAULT_TIMEOUT,
    ):
        super().__init__()
        self._api_key = api_key
        self._count = count
        self._freshness = freshness
        self._safesearch = safesearch
        self._timeout = timeout

    def search(self, queries: List[str]) -> List[SearchResult]:
        return asyncio.run(self.asearch(queries=queries))

    async def asearch(self, queries: List[str]) -> List[SearchResult]:
        tasks = [self._search_single(query) for query in queries]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        results: List[SearchResult] = []
        for i, r in enumerate(task_results):
            if isinstance(r, Exception):
                LOGGER.warning("You search failed for query %s: %s", queries[i], r)
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

    async def _search_single(self, query: str) -> SearchResult:
        params: dict[str, Any] = {
            "query": query,
            "count": self._count,
            "freshness": self._freshness,
            "safesearch": self._safesearch,
        }
        headers = {"X-API-Key": self._api_key}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(YOU_SEARCH_BASE_URL, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return self._format_result(data, query)

    @classmethod
    def _format_result(cls, api_response: dict, query: str) -> SearchResult:
        results = api_response.get("results") or {}
        web_items = results.get("web") or []
        news_items = results.get("news") or []
        formatted = ""
        refs: List[SearchReference] = []

        for i, item in enumerate(web_items, 1):
            title = item.get("title") or ""
            description = item.get("description") or ""
            snippets = item.get("snippets") or []
            url = item.get("url") or ""
            snippet_text = " ".join(snippets) if isinstance(snippets, list) and snippets else description
            content = snippet_text.strip() or description
            formatted += f"参考资料{i}: \n"
            formatted += f"标题: {title}\n"
            formatted += f"内容: {content}\n\n"
            refs.append(
                SearchReference(
                    site=None,
                    title=title,
                    url=url,
                    content=content,
                )
            )

        offset = len(web_items)
        for j, item in enumerate(news_items, 1):
            idx = offset + j
            title = item.get("title") or ""
            description = item.get("description") or ""
            url = item.get("url") or ""
            formatted += f"参考资料{idx}: \n"
            formatted += f"标题: {title}\n"
            formatted += f"内容: {description}\n\n"
            refs.append(
                SearchReference(
                    site=None,
                    title=title,
                    url=url,
                    content=description,
                )
            )

        if not formatted.strip():
            formatted = "未找到相关结果。"

        return SearchResult(
            query=query,
            summary_content=formatted.strip(),
            search_references=refs if refs else None,
        )
