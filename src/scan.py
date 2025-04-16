import os
from datetime import datetime

import win32com.client
import fitz  # PyMuPDF # pyright: ignore[reportMissingTypeStubs]
from io import BytesIO

def scan_paper() -> None:
    """
    使用TWAIN接口扫描试卷并保存为PDF
    """
    # 初始化扫描仪
    # Create WIA dialog and scanner device manager
    wia_dialog = win32com.client.Dispatch("WIA.CommonDialog")
    # Show scanner selection dialog
    device = wia_dialog.ShowSelectDevice() # pyright: ignore[reportAny]

    if not device:
        print("未选择扫描仪")
        return
    # 存储扫描的页面
    scanned_pages: list[bytes] = []
    try:
        while True:
            # 开始扫描
            # 获取扫描结果
            scanned_image = wia_dialog.ShowAcquireImage( # pyright: ignore[reportAny]
                DeviceType=1,     # 1 = Scanner
                Intent=0,         # 0 = Color, 1 = Grayscale, 2 = Text
                FormatID="{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}",  # PNG format
                AlwaysSelectDevice=False,
                UseCommonUI=False,
                CancelError=True
            )
            
            # 添加到页面列表
            scanned_pages.append(scanned_image.FileData.BinaryData) # pyright: ignore[reportAny]
            
            # 询问用户是否继续扫描下一页
            user_input = input(f"已扫描{len(scanned_pages)}页，是否继续扫描下一页？(y/n): ").lower()
            if user_input != 'y':
                break
                
    except Exception as e:
        print(f"扫描过程中发生错误: {e}")
    
    # 将扫描的页面保存为PDF
    if scanned_pages:
        save_as_pdf(scanned_pages)

def mm_to_points(mm: float) -> float:
    return mm / 25.4 * 72  # 毫米转点

def save_as_pdf(pages: list[bytes]) -> None:
    """
    将扫描的页面保存为PDF文件
    
    Args:
        pages: 扫描的页面列表
        output_path: 输出PDF文件路径
    """
    pdf:fitz.Document = fitz.open()
    
    for page in pages:
        # 将图像转换为字节流
        img_bytes = BytesIO(page)
        
        # 创建PDF页面
        rect = fitz.Rect(0, 0, mm_to_points(210), mm_to_points(297))
        pdf_page = pdf.new_page(width=rect.width, height=rect.height)  # A4尺寸 # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
        pdf_page.insert_image(rect, stream=img_bytes.getvalue()) # pyright: ignore[reportUnknownMemberType]
    
    # 保存PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join("./papers", f"scan_{len(pages):03d}_{timestamp}.pdf")
    pdf.save(output_path) # pyright: ignore[reportUnknownMemberType]
    pdf.close()
    print(f"PDF已保存至: {output_path}")


if __name__ == "__main__":
    scan_paper()