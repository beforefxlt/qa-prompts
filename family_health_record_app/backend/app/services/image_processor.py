from PIL import Image, ImageDraw
import io
from typing import Tuple

def desensitize_image(image_bytes: bytes, mask_top_percent: float = 0.15, mask_bottom_percent: float = 0.10) -> bytes:
    """
    对图像执行脱敏处理，遮盖顶部和底部的敏感区域。
    默认遮盖顶部 15% 和底部 10%。
    如果输入不是有效图片，直接返回原始字节。
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return image_bytes

    width, height = img.size
    draw = ImageDraw.Draw(img)

    # 遮盖顶部区域 (仅遮盖左侧 60%，保留右侧 40% 给日期识别)
    top_mask_end = int(height * mask_top_percent)
    right_edge_to_mask = int(width * 0.6)
    draw.rectangle([0, 0, right_edge_to_mask, top_mask_end], fill="black")

    # 遮盖底部区域
    bottom_mask_start = int(height * (1 - mask_bottom_percent))
    draw.rectangle([0, bottom_mask_start, width, height], fill="black")

    output = io.BytesIO()
    # 统一转换为 RGB 并保存为高质量 WebP
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(output, format="WEBP", quality=85)
    return output.getvalue()
