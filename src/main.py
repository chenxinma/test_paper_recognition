import os
import json
import asyncio
from dotenv import load_dotenv
from typing import Any

import cv2
import filetype # pyright: ignore[reportMissingTypeStubs]
import pymupdf # pyright: ignore[reportMissingTypeStubs]
import numpy as np

from rapidocr import RapidOCR # pyright: ignore[reportMissingTypeStubs]
from tqdm import tqdm

from pydantic import SecretStr
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

def parse_json(json_text:str) -> dict[str, str]:
    """
    处理返回的 JSON 格式文本，将其转换为 Python 字典。
    :param json_text: 包含 JSON 格式的文本
    :return: 转换后的 Python 字典，如果解析失败则返回空字典
    """
    try:
        # 去除可能存在的代码块标记
        cleaned_text = json_text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text) # pyright: ignore[reportAny]
    except json.JSONDecodeError:
        print("JSON 解析失败，请检查输入文本格式。")
        return {}

def initialize_agent():
    """初始化agent"""
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

def initialize_ocr_engine():
    """初始化 RapidOCR 引擎"""
    return RapidOCR()

def get_files(image_dir:str)-> list[str]:
    """
    遍历指定目录，获取所有 文件的路径，若存在同名的 json 文件则跳过该 文件
    :param image_dir: 图片目录路径
    :return: 文件路径列表
    """
    paper_files:list[str] = []
    for root, _, files in os.walk(image_dir):
        for file in files:
            if file.lower()[-4:] in [".png", ".jpg", ".jpeg", ".pdf"]:
                file_name = os.path.splitext(file)[0]
                json_file = file_name + ".json"
                json_file_path = os.path.join(root, json_file)
                # 检查同名 json 文件是否存在，若不存在则添加到列表
                if not os.path.exists(json_file_path):
                    paper_files.append(os.path.join(root, file))
    return paper_files

def process_image(engine:RapidOCR, img_url:str):
    """
    处理单张图片，进行 OCR 识别并返回结果
    :param engine: RapidOCR 引擎实例
    :param img_url: 图片文件路径
    :return: OCR 识别结果
    """
    return engine(img_url)

def process_pdf(engine:RapidOCR, pdf_url:str):
    """
    处理 PDF 文件，进行 OCR 识别并返回结果
    :param engine: RapidOCR 引擎实例
    :param pdf_url: PDF 文件路径
    :return: OCR 识别结果
    """
    def convert_img(page: pymupdf.Page):
        pix: pymupdf.Pixmap = page.get_pixmap(dpi=200) # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
        img = np.frombuffer(pix.samples, dtype=np.uint8) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        img = img.reshape([pix.h, pix.w, pix.n]) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img

    with pymupdf.open(pdf_url) as doc:
        # 提取第一页并转换为图片
        first_page = doc[0]
        img = convert_img(first_page)
        
    # 将numpy数组作为输入进行OCR识别
    return engine(img)

async def save_result_to_json(result, img_url:str, agent:Agent): # pyright: ignore[reportUnknownParameterType,reportMissingParameterType]
    """
    将 OCR 识别结果保存为 JSON 文件
    :param result: OCR 识别结果
    :param img_url: 图片文件路径
    :param agent: 智能体实例
    """
    file_name = os.path.basename(img_url)
    result_file = os.path.splitext(file_name)[0] + ".json"
    result_file_path = os.path.join(os.path.dirname(img_url), result_file)
    data: dict[str, Any] = { # pyright: ignore[reportExplicitAny]
        "texts": result.txts, # pyright: ignore[reportUnknownMemberType]
        "boxes": result.boxes.tolist() # pyright: ignore[reportUnknownMemberType]
    }
    paper_hint = await agent.run(data["texts"][:30]) # pyright: ignore[reportAny]
    # 使用新添加的 parse_json 函数处理返回的文本
    parsed_data = parse_json(paper_hint.data)
    data.update(parsed_data)
    with open(result_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def main():
    # 初始化 OCR 引擎
    engine = initialize_ocr_engine()
    agent = initialize_agent()
    # 指定试卷目录
    paper_directory = os.getenv('PAPER_DIR', './papers')  # 默认值保持向后兼容
    # 获取所有需要处理的 PNG 文件路径
    paper_files = get_files(paper_directory)
    # 遍历处理所有 PNG 文件
    for file_url in tqdm(paper_files):
        kind = filetype.guess(file_url) # pyright: ignore[reportUnknownMemberType]
        if kind is None:
            print('无法判断文件类型!')
            continue
        if kind.extension == 'pdf':
            result = process_pdf(engine, file_url)
        else:
            result = process_image(engine, file_url)
        await save_result_to_json(result, file_url, agent)

if __name__ == "__main__":
    asyncio.run(main())
