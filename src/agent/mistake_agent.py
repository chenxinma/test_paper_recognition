import os
from dotenv import load_dotenv
from typing import Any, Annotated
from typing_extensions import TypedDict

import cv2

import filetype  # pyright: ignore[reportMissingTypeStubs]

from pydantic import Field
from pydantic import SecretStr
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from paper_typing import PaperFile

class Mistake(TypedDict):
    question: Annotated[str, Field(description="错题题目摘录，注意：只需要题目，不要包含答案。")]
    reason: Annotated[str, Field(description="推测可能的错误原因，例如：可能是笔误，可能是计算错误，可能是题目理解错误等。")]

class Response(TypedDict):
    mistakes_count: int
    mistakes: list[Mistake]

def initialize_agent() -> Agent[None, Response]:
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
                  result_type=Response,
                  system_prompt=(
                      """根据试卷的批改结果列出所有错题，
打勾视为正确，画叉或有红字标注的视为错误(红字标注 优、良、中、差等地不计算在内。)，如果未作批改的题目可以忽略。
"""))

    return agent

mistakes_agent = initialize_agent()

async def mistakes_update_paper_info(info:dict[str, Any], s_file: PaperFile) -> None: # pyright: ignore[reportExplicitAny]
    messages: list[BinaryContent] = []
    if isinstance(s_file, list):
        for img in s_file:
            b = BinaryContent(data=cv2.imencode('.png', img)[1].tobytes(), media_type='image/png')
            messages.append(b)
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
            messages.append(b)

    paper_mistakes = await mistakes_agent.run(messages)
    info.update(paper_mistakes.data)
