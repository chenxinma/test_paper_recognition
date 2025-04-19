import os
import hashlib
import json

import pandas as pd
import click

def calculate_md5(file_path:str):
    """
    计算文件的 MD5 哈希值
    :param file_path: 文件路径
    :return: MD5 哈希值
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def process_json_files(directory:str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    处理指定目录下的所有 JSON 文件
    :param directory: 指定目录
    :return: 包含处理结果的 DataFrame
    """
    data = []
    mistakes = []
    # 遍历指定目录及子目录下的所有文件
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                # 计算文件的 MD5 哈希值
                file_id = calculate_md5(file_path)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        subject = json_data.get('subject', '')
                        title = json_data.get('title', '')
                        mistakes_count = json_data.get('mistakes_count', 0)
                        data.append({
                            'id': file_id,
                            'subject': subject,
                            'title': title,
                            'mistakes_count': mistakes_count,
                            'file_path': file_path
                        })
                        _mistakes = json_data.get('mistakes', [])
                        for mistake in _mistakes:
                            mistake['id'] = file_id
                            mistakes.append(mistake)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    return pd.DataFrame(data), pd.DataFrame(mistakes)

def save_to_parquet(df:pd.DataFrame, output_path: str):
    """
    将 DataFrame 保存为 Parquet 文件
    :param df: 包含处理结果的 DataFrame
    :param output_path: 输出文件路径
    """
    df.to_parquet(output_path, index=False)

@click.command()
@click.option('--source-dir', default='Y:/', help='统计源目录')
def main(source_dir: str):
    # 指定要遍历的目录
    input_directory = source_dir
    # 指定输出的 Parquet 文件路径
    output_file = os.path.join(input_directory, 'summary.parquet')
    mistakes_file = os.path.join(input_directory,'mistakes.parquet')
    # 处理 JSON 文件并保存到 Parquet 文件
    df_summary, df_mistakes = process_json_files(input_directory)
    save_to_parquet(df_summary, output_file)
    save_to_parquet(df_mistakes, mistakes_file)
    
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    main()
