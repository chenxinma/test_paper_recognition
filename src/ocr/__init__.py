from typing import Any

from rapidocr import RapidOCR # pyright: ignore[reportMissingTypeStubs]
from paper_typing import PaperFile

def initialize_ocr_engine():
    """初始化 RapidOCR 引擎"""
    return RapidOCR()

engine = initialize_ocr_engine()

async def orc_update_paper_info(info:dict[str, Any], s_file: PaperFile) -> None: # pyright: ignore[reportExplicitAny]
    if isinstance(s_file, list):
        result = engine(s_file[0])
    else:
        result = engine(s_file)
    
    data: dict[str, Any] = { # pyright: ignore[reportExplicitAny]
        "texts": result.txts, # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
        "boxes": 
            result.boxes.tolist() if result.boxes is not None else [] # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
    }
    info.update(data)
