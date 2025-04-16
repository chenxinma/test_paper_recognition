import json

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
        print("原始文本:", json_text)
        return {}
