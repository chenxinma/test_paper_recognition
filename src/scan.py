import os
from datetime import datetime

import win32com.client
import fitz  # PyMuPDF # pyright: ignore[reportMissingTypeStubs]
from io import BytesIO

import cv2
import numpy as np

def crop_image_edges(image_data: bytes) -> bytes:
    """改进版边缘检测，适用于偏黄纸张"""
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 分离BGR通道（纸张偏黄时蓝色通道对比度最高）
    b, g, r = cv2.split(img)
    
    # 增强蓝色通道对比度
    enhanced = cv2.normalize(b, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX) # pyright: ignore[reportCallIssue, reportArgumentType]
    
    # 自适应阈值处理
    thresh = cv2.adaptiveThreshold(enhanced, 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY_INV, 21, 10)
    
    # 形态学操作去除噪点
    kernel = np.ones((5,5), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # 查找轮廓
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, 
                                 cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # 合并所有轮廓的边界
        x, y, w, h = cv2.boundingRect(np.vstack(contours))
        
        # 添加安全边距
        height, width = img.shape[:2]
        margin = int(min(width, height) * 0.05)  # 5%边距
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(width - x, w + 2 * margin)
        h = min(height - y, h + 2 * margin)
        
        # 裁剪并返回
        cropped = img[y:y+h, x:x+w]
        _, buffer = cv2.imencode('.png', cropped)
        return buffer.tobytes()
    
    return image_data


def scan_paper() -> None:
    """
    使用TWAIN接口扫描试卷并保存为PDF
    """
    # 初始化扫描仪
    # Create WIA dialog and scanner device manager
    # wia_dialog = win32com.client.Dispatch("WIA.CommonDialog")
    # # Show scanner selection dialog
    # device = wia_dialog.ShowSelectDevice() 

    # 初始化 WIA 设备管理器
    wia_manager = win32com.client.Dispatch("WIA.DeviceManager")

    # 选择第一个可用的扫描仪设备（需提前确认设备存在）
    if wia_manager.DeviceInfos.Count < 1:
        print("未找到扫描仪设备。")
        exit()
    device_info = wia_manager.DeviceInfos(1)
    device = device_info.Connect()

    scanner_item = device.Items(1)  # 通常第一个Item是扫描源
    scanner_item.Properties("6146").Value = 1     # 色彩模式: 1=彩色, 2=灰度, 4=黑白
    scanner_item.Properties("6147").Value = 300    # 水平分辨率 (DPI)
    scanner_item.Properties("6148").Value = 300    # 垂直分辨率 (DPI)
    # scanner_item.Properties("6151").Value = 0      # 扫描区域左边界 (单位: 毫米*100)
    # scanner_item.Properties("6152").Value = 0      # 扫描区域上边界
    # scanner_item.Properties("6153").Value = 215900 # 宽度 (A4纸宽度 215.9mm * 1000)
    # scanner_item.Properties("6154").Value = 279400 # 高度 (A4纸高度 279.4mm * 1000)

    if not device:
        print("未选择扫描仪")
        return
    # 存储扫描的页面
    scanned_pages: list[bytes] = []
    try:
        while True:
            # 开始扫描
            # 获取扫描结果

            # scanned_image = wia_dialog.ShowAcquireImage( 
            #     DeviceType=1,     # 1 = Scanner
            #     Intent=0,         # 0 = Color, 1 = Grayscale, 2 = Text
            #     FormatID="{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}",  # PNG format
            #     AlwaysSelectDevice=False,
            #     UseCommonUI=False,
            #     CancelError=True
            # )
            # 执行扫描（静默模式）
            scanned_image = scanner_item.Transfer("{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}")  # PNG格式
            
            # 添加到页面列表
            scanned_pages.append(crop_image_edges(scanned_image.FileData.BinaryData)) # pyright: ignore[reportAny]
            
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
