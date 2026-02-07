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

import os

from dotenv import load_dotenv

# 从项目根目录的 .env 文件加载环境变量（使用 Tavily/ARK 等配置前必须）
load_dotenv()

"""
for server
"""

# recommend to use DeepSeek-R1 model（国外站模型名 deepseek-r1-250528）
REASONING_MODEL = os.getenv('REASONING_MODEL') or "deepseek-r1-250528"
# default set to volc bot, if using tavily, change it into "tavily"
SEARCH_ENGINE = os.getenv('SEARCH_ENGINE') or "volc_bot"
# optional, if you select tavily as search engine, please configure this
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY') or "{YOUR_TAVILY_API_KEY}"
# optional, if you select volc bot as search engine, please configure this
SEARCH_BOT_ID = os.getenv('SEARCH_BOT_ID') or "{YOUR_SEARCH_BOT_ID}"
# optional, if you select you as search engine, please configure this
YOU_API_KEY = os.getenv('YOU_API_KEY') or "{YOUR_YOU_API_KEY}"
# optional, if you select ask_echo (BytePlus AskEcho Search Agent) as search engine
# API 文档: https://docs.byteplus.com/en/docs/askecho/Agent_API_Reference
# API Key 接入（推荐）: https://torchlight.byteintlapi.com/agent_api/agent/chat/completion
ASK_ECHO_API_KEY = os.getenv('ASK_ECHO_API_KEY') or ""
ASK_ECHO_AGENT_ID = os.getenv('ASK_ECHO_AGENT_ID') or ""
ASK_ECHO_BASE_URL = (os.getenv('ASK_ECHO_BASE_URL') or "").strip()  # 留空则用默认 torchlight.byteintlapi.com

"""
for webui
"""

# ark api key
ARK_API_KEY = os.getenv('ARK_API_KEY') or "{YOUR_ARK_API_KEY}"
# api server address for web ui（国外站：https://ark.ap-southeast.bytepluses.com/api/v3；国内站：https://ark.cn-beijing.volces.com/api/v3/bots）
API_ADDR = os.getenv("API_ADDR") or "https://ark.ap-southeast.bytepluses.com/api/v3"
# 国外站填模型名如 deepseek-r1-250528，国内站填 bot id
API_BOT_ID = os.getenv("API_BOT_ID") or "deepseek-r1-250528"
