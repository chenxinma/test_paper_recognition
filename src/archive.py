import os
import json
import shutil
import re
from typing import Any
from datetime import datetime
import click

def process_files(paper_dir: str, target_dir: str):
    # 遍历 paper 目录下的所有文件
    for root, _, files in os.walk(paper_dir):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in ['.jpg', '.jpeg', '.png', '.pdf']:
                file_base_name = os.path.splitext(file)[0]
                json_file_path = os.path.join(root, f'{file_base_name}.json')

                # 检查同名的 json 文件是否存在
                if not os.path.exists(json_file_path):
                    continue

                # 读取 json 文件内容
                with open(json_file_path, 'r', encoding='utf-8') as json_file:
                    data: dict[str, Any] = json.load(json_file) # pyright: ignore[reportExplicitAny]

                # 从 json 数据中提取所需信息
                subject:str = data.get('subject', '未知学科')
                ym = datetime.now().strftime('%Y-%m')
                title:str = data.get('title', '未知标题')

                # 清理标题中的非法字符
                safe_title = re.sub(r'[<>:"/\\|?*]', '', title)

                # 构建目标目录
                subject_dir = os.path.join(target_dir, subject)
                ym_dir = os.path.join(subject_dir, ym)
                os.makedirs(ym_dir, exist_ok=True)

                # 构建新的文件名
                new_file_name = f'{safe_title}{file_ext}'
                new_file_path = os.path.join(ym_dir, new_file_name)
                new_json_path = os.path.join(ym_dir, f'{safe_title}.json')  # 新增JSON路径

                # 移动并重命名文件
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                shutil.move(os.path.join(root, file), new_file_path)
                if os.path.exists(new_json_path):
                    os.remove(new_json_path)
                shutil.move(json_file_path, new_json_path)  # 新增移动JSON文件

@click.command()
@click.option('--paper-dir', default='./papers', help='指定 paper 目录')
@click.option('--target-dir', default='Y://', help='指定目标目录')
@click.argument('name')
def main(paper_dir: str, target_dir: str, name: str):
    target_directory = os.path.join(target_dir, name) 
    process_files(paper_dir, target_directory)

if __name__ == "__main__":
    main()
