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

import logging
import os
from typing import AsyncIterable, Union

from arkitect.core.component.llm.model import (
    ArkChatCompletionChunk,
    ArkChatRequest,
    ArkChatResponse,
)
from arkitect.launcher.local.serve import launch_serve
from arkitect.launcher.vefaas import bot_wrapper
from arkitect.telemetry.trace import task
from volcenginesdkarkruntime import AsyncArk
from search_engine.tavily import TavilySearchEngine
from search_engine.volc_bot import VolcBotSearchEngine
from search_engine.you import YouSearchEngine
from search_engine.ask_echo import AskEchoSearchEngine
from deep_search import DeepSearch, ExtraConfig

from utils import get_last_message

from config import (
    REASONING_MODEL,
    SEARCH_ENGINE,
    ARK_API_KEY,
    TAVILY_API_KEY,
    SEARCH_BOT_ID,
    YOU_API_KEY,
    ASK_ECHO_API_KEY,
    ASK_ECHO_AGENT_ID,
    ASK_ECHO_BASE_URL,
)

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s][%(levelname)s] %(message)s"
)
LOGGER = logging.getLogger(__name__)


@task()
async def main(
        request: ArkChatRequest,
) -> AsyncIterable[Union[ArkChatCompletionChunk, ArkChatResponse]]:
    # using last_user_message as query
    last_user_message = get_last_message(request.messages, "user")
    # settings from request (metadata may contain search_engine choice)
    metadata = request.metadata or {}
    selected_engine = metadata.get("search_engine", SEARCH_ENGINE)
    # 前端显示名别名映射为实际引擎 id（如 BytePlusAskEchoSearchAgent -> ask_echo）
    if selected_engine == "BytePlusAskEchoSearchAgent":
        selected_engine = "ask_echo"
    # set search_engine dynamically
    if selected_engine == "tavily":
        search_engine = TavilySearchEngine(api_key=TAVILY_API_KEY)
    elif selected_engine == "you":
        search_engine = YouSearchEngine(api_key=YOU_API_KEY)
    elif selected_engine == "ask_echo":
        search_engine = AskEchoSearchEngine(
            api_key=ASK_ECHO_API_KEY,
            agent_id=ASK_ECHO_AGENT_ID,
            base_url=ASK_ECHO_BASE_URL or None,
        )
    else:
        search_engine = VolcBotSearchEngine(bot_id=SEARCH_BOT_ID)
    max_search_words = metadata.get('max_search_words', 5)
    max_planning_rounds = metadata.get('max_planning_rounds', 5)

    deep_research = DeepSearch(
        search_engine=search_engine,
        planning_endpoint_id=REASONING_MODEL,
        summary_endpoint_id=REASONING_MODEL,
        extra_config=ExtraConfig(
            # optional, the max search words for each planning rounds
            max_search_words=max_search_words,
            # optional, the max rounds to run planning
            max_planning_rounds=max_planning_rounds,
        )
    )

    if request.stream:
        async for c in deep_research.astream_deep_research(request=request, question=last_user_message.content):
            yield c
    else:
        rsp = await deep_research.arun_deep_research(request=request, question=last_user_message.content)
        yield rsp


@bot_wrapper()
@task(custom_attributes={"input": None, "output": None})
async def handler(
        request: ArkChatRequest,
) -> AsyncIterable[Union[ArkChatCompletionChunk, ArkChatResponse]]:
    async for resp in main(request):
        yield resp


if __name__ == "__main__":
    port = os.getenv("_FAAS_RUNTIME_PORT")
    launch_serve(
        package_path="server",
        port=int(port) if port else 7859,
        health_check_path="/v1/ping",
        endpoint_path="/api/v3/bots/chat/completions",
        trace_on=False,
        clients={
            "ark": (
                AsyncArk,
                {
                    "region": "ap-southeast-1",
                    "base_url": "https://ark.ap-southeast.volces.com/api/v3",
                    "api_key": ARK_API_KEY,
                },
            ),
        },
    )
