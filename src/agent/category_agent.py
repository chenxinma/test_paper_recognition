import os
from dotenv import load_dotenv
from typing import Any

from pydantic import SecretStr
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from paper_typing import PaperFile
from .utils import parse_json

def initialize_agent() -> Agent:
    """
    创建 Agent 实例
    :return: Agent 实例
    """
    # 加载环境变量
    if not load_dotenv():
        print("环境变量加载失败")
        exit(1)

    base_url = os.getenv('LLM_BASE_URL', '')
    api_key = SecretStr(os.getenv('LLM_API_KEY', ''))
    _model = OpenAIModel('qwen-max', provider=OpenAIProvider(
                base_url=base_url,
                api_key=api_key.get_secret_value(),
             ))

    agent = Agent(_model, 
                  result_type=str,
                  system_prompt=(
                      f"""
                      根据OCR的结果给出的部分文本，判断这份试卷的学科是 语文、英语、数学中的哪一科？
                      并提取出试卷标题。
                      请严格按照json格式返回，格式如下：
```json
{{
    "subject": "学科名称",
    "title": "试卷标题"
}}
```
    """))
    return agent

categoryAgent = initialize_agent()

async def category_update_paper_info(info:dict[str, Any], _: PaperFile) -> None: # pyright: ignore[reportExplicitAny]
    paper_hint = await categoryAgent.run(info["texts"][:30]) # pyright: ignore[reportAny]
    # 使用新添加的 parse_json 函数处理返回的文本
    parsed_data = parse_json(paper_hint.data)
    info.update(parsed_data)
