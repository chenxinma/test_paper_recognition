import os
import json
import asyncio
from typing import Any
from dotenv import load_dotenv

import cv2
import filetype
import pymupdf
import numpy as np
import asyncclick as click

from tqdm import tqdm
from ocr import orc_update_paper_info
from agent import category_update_paper_info, mistakes_update_paper_info
from paper_typing import PaperFile

import logfire

load_dotenv()
# configure logfire
logfire.configure(send_to_logfire='if-token-present')
logfire.instrument_openai()

handlers = [ 
    orc_update_paper_info, 
    category_update_paper_info,
    mistakes_update_paper_info
]

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


def process_pdf(pdf_url:str) -> list[cv2.typing.MatLike]:
    """
    处理 PDF 文件，进行 OCR 识别并返回结果
    :param engine: RapidOCR 引擎实例
    :param pdf_url: PDF 文件路径
    :return: OCR 识别结果
    """
    def convert_img(page: pymupdf.Page) -> cv2.typing.MatLike:
        pix: pymupdf.Pixmap = page.get_pixmap(dpi=200) # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
        img = np.frombuffer(pix.samples, dtype=np.uint8) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        img = img.reshape([pix.h, pix.w, pix.n]) # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img

    with pymupdf.open(pdf_url) as doc:
        # 提取第一页并转换为图片
        return [ convert_img(page) for page in doc ]


async def save_result_to_json(data, img_url:str): # pyright: ignore[reportUnknownParameterType,reportMissingParameterType]
    """
    将 OCR 识别结果保存为 JSON 文件
    :param result: OCR 识别结果
    :param img_url: 图片文件路径
    :param agent: 智能体实例
    """
    file_name = os.path.basename(img_url)
    result_file = os.path.splitext(file_name)[0] + ".json"
    result_file_path = os.path.join(os.path.dirname(img_url), result_file)
    
    with open(result_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@click.command()
@click.option('--paper-dir', default='./papers', help='指定 paper 目录')
async def main(paper_dir: str):

    # 指定试卷目录
    paper_directory = paper_dir  # 默认值保持向后兼容
    # 获取所有需要处理的 PNG 文件路径
    paper_files = get_files(paper_directory)
    # 遍历处理所有 PNG 文件
    for file_url in tqdm(paper_files):
        tqdm.write(f"正在处理 {file_url} ...")
        kind = filetype.guess(file_url) # pyright: ignore[reportUnknownMemberType]
        if kind is None:
            print('无法判断文件类型!')
            continue
        s_file: PaperFile | None = None
        if kind.extension == 'pdf':
            s_file = process_pdf(file_url)
        else:
            s_file = file_url
        
        data: dict[str, Any] = {}  # pyright: ignore[reportExplicitAny]
        try:
            last_func_name = None
            for updator_func in handlers:
                last_func_name = updator_func.__name__
                tqdm.write(f"正在使用 {updator_func.__name__} 进行更新...")
                await updator_func(data, s_file)

            await save_result_to_json(data, file_url)
        except Exception as e:
            tqdm.write(f"!!处理 {last_func_name} 时出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
