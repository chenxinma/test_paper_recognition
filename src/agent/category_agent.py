import os
from dotenv import load_dotenv
from typing import Any, Annotated
from typing_extensions import TypedDict

import cv2
import filetype

from pydantic import SecretStr, Field
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from paper_typing import PaperFile

class Category(TypedDict):
    subject: Annotated[str, Field(description="学科名称")]
    title: Annotated[str, Field(description="试卷的标题")]

def initialize_agent() -> Agent[None, Category]:
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
    _model = OpenAIModel('qwen-vl-max-latest', provider=OpenAIProvider(
                base_url=base_url,
                api_key=api_key.get_secret_value(),
             ))

    agent = Agent(_model, 
                  result_type=Category,
                  model_settings={'temperature': 0.0, 'timeout': 600},
                  system_prompt=(
                      f"""
                      判断这份试卷的学科是 语文、英语、数学中的哪一科？并提取出试卷标题。
    """))
    return agent

categoryAgent = initialize_agent()

async def category_update_paper_info(info:dict[str, Any], s_file: PaperFile) -> None: # pyright: ignore[reportExplicitAny]
    if isinstance(s_file, list):
        b = BinaryContent(data=cv2.imencode('.png', s_file[0])[1].tobytes(), media_type='image/png')
    else:
        kind = filetype.guess(s_file)  # pyright: ignore[reportUnknownMemberType]
        if kind is None:
            print('无法判断文件类型!')
            return
        if kind.extension not in ['jpg', 'png', 'jpeg']:
            print('不支持文件类型!', s_file)
            return
        kind.mime
        
        with open(s_file, 'rb') as f:
            b = BinaryContent(data=f.read(), media_type=str(kind.mime)) # pyright: ignore[reportUnknownArgumentType]
        
    
    paper_hint = await categoryAgent.run([b])
    # 使用新添加的 parse_json 函数处理返回的文本
    info.update(paper_hint.data)
