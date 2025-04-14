# 试卷识别测试项目

该项目使用 `RapidOCR` 库对指定图片进行 OCR 识别，并将识别结果可视化保存。

## 项目依赖
- `rapidocr`：用于执行 OCR 识别任务。

## 项目结构
- `main.py`：主程序文件，负责调用 `RapidOCR` 进行图片识别并输出结果。
- `images/`：存放待识别的图片文件。
- `vis_result.jpg`：识别结果可视化后的图片文件。

## 运行步骤
1. 确保已经安装 `rapidocr` 库，可以使用以下命令进行安装：
```bash
pip install rapidocr