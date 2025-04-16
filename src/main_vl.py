from openai import OpenAI
import os
import base64
from dotenv import load_dotenv
from pydantic import SecretStr
from openai.types.chat import ChatCompletionContentPartParam

import numpy as np
import cv2
import pymupdf # pyright: ignore[reportMissingTypeStubs]

# base 64 编码格式
class ImageUtils:
    @staticmethod
    def convert_img(page: pymupdf.Page):
        pix: pymupdf.Pixmap = page.get_pixmap(dpi=200) # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
        img = np.frombuffer(pix.samples, dtype=np.uint8) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        img = img.reshape([pix.h, pix.w, pix.n]) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return cv2.imencode('.jpg', img)[1]

    @staticmethod
    def encode_pdf(pdf_url:str):
        with pymupdf.open(pdf_url) as doc:
            for page in doc:
                img = ImageUtils.convert_img(page)
                yield base64.b64encode(img).decode("utf-8") # pyright: ignore[reportArgumentType]


def load_env_vars():
    if not load_dotenv():
        print("Could not load .env file or it is empty. Please check if the file exists and is readable.")
        exit(1)
    return os.getenv('LLM_BASE_URL', ''), SecretStr(os.getenv('LLM_API_KEY', ''))

def initialize_openai_client(base_url: str, api_key: SecretStr) -> OpenAI:
    return OpenAI(
        api_key=api_key.get_secret_value(),
        base_url=base_url,
    )

def main():
    base_url, api_key = load_env_vars()
    client = initialize_openai_client(base_url, api_key)

    # 将xxxx/eagle.png替换为你本地图像的绝对路径
    contents:list[ChatCompletionContentPartParam] = []
    for b_img in ImageUtils.encode_pdf("./papers/文档扫描_20250415215556583.pdf"):
        contents.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/jpg;base64,{b_img}"}
        })
    contents.append({"type": "text", "text": """根据试卷的批改结果列出所有错题，
    打勾视为正确，画叉或有红字标注的视为错误(红字标注 优、良、中、差等地不计算在内。)，如果未作批改的题目可以忽略。
    结果严格按照json格式输出，例如：
    ```json
    {
        "mistakes_count": 2,
        "mistakes": [
            {
                "question": "1. 请写出以下表达式的值：(1+2)^3",
                "reason": "{{推测可能的错误原因，例如：可能是笔误，可能是计算错误，可能是题目理解错误等。}}",
            },
            {
                "question": " 2. (2) 雷公公把藏了好久的大鼓重重地敲了起来。  ",
                "reason": "...."
            }
        ]
    }
    ```
    """})
    
    completion = client.chat.completions.create(
        model="qwen-vl-max-latest",
        messages=[
            {
                "role": "system",
                "content": [{"type":"text","text": "You are a helpful assistant."}]
            },
            {
                "role": "user",
                "content": contents,
            }
        ],
    )
    print(completion.choices[0].message.content)


if __name__ == "__main__":
    main()
