# 试卷处理系统

该项目提供完整的试卷处理流程，包括扫描、文本识别、归档和浏览功能。

## 核心功能模块

1. **扫描模块 (scan.py)**
   - 通过扫描仪接口将纸质试卷扫描为PDF文件
   - 自动裁剪边缘空白区域
   - 支持多页连续扫描

2. **识别模块 (detect.py)**
   - 从扫描的试卷中提取文本内容
   - 自动识别学科类型和试卷标题
   - 分析并摘录错题信息
   - 将结果保存为结构化JSON文件

3. **归档模块 (archive.py)**
   - 将扫描的PDF试卷和对应的JSON文件
   - 按学科和日期分类存储
   - 自动清理文件名中的非法字符

4. **归档模块 (summary.py)**
   - 将归档的JSON文件汇总为一个parquet文件

5. **浏览模块 (web.py)**
   - 提供Web界面浏览归档的试卷
   - 支持按学科、日期筛选
   - 可直接查看PDF和图片文件

## 项目依赖
- `rapidocr`: 用于OCR文本识别
- `pymupdf`: 处理PDF文件
- `opencv-python`: 图像处理
- `win32com`: 扫描仪接口
- `fastapi`: Web界面后端

## 安装与运行
```bash
# 安装依赖
uv sync

# 启动扫描模块
uv run scan.py
# 启动识别模块
uv run detect.py [--paper-dir 扫描+识别试卷的暂存目录]

# 启动归档模块
uv run archive.py  [--paper-dir 扫描+识别试卷的暂存目录] [--archive-dir 归档目录] 小朋友名字
uv run summary.py  [--archive-dir 归档目录] 小朋友名字

# 启动浏览模块
uv run web.py
```