import os
import base64
import io
from PIL import Image, ImageOps
import folder_paths
import numpy as np
import torch

class OpenAISaveImageNode:
    """保存 OpenAI 返回的图像数据到文件并输出图像"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "b64_json": ("STRING", {"default": "", "multiline": True, "placeholder": "OpenAI API 返回的 base64 编码图像数据"}),
                "filename_prefix": ("STRING", {"default": "openai"}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE", "MASK",)
    RETURN_NAMES = ("filename", "image", "mask",)
    FUNCTION = "save_image"
    CATEGORY = "ToolBox/OpenAI"

    def save_image(self, b64_json, filename_prefix):
        print(f"接收到 base64 数据，长度: {len(b64_json)}")
        
        try:
            # 解码 base64 数据
            image_data = base64.b64decode(b64_json)
            print(f"解码后的图像数据大小: {len(image_data)} 字节")
            
            # 使用 PIL 打开图像
            pil_image = Image.open(io.BytesIO(image_data))
            print(f"解码图像成功，尺寸: {pil_image.size}, 模式: {pil_image.mode}")
            
            # 获取输出目录
            output_dir = folder_paths.get_output_directory()
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件名
            counter = 1
            while True:
                filename = f"{filename_prefix}_{counter:05d}.png"
                filepath = os.path.join(output_dir, filename)
                if not os.path.exists(filepath):
                    break
                counter += 1
                
            # 保存图像
            print(f"保存图像到: {filepath}")
            pil_image.save(filepath)
            
            # ----- 以下参考 LoadImageJMNodes 的方式重新从文件加载图像 -----
            
            # 加载刚刚保存的图像文件
            print(f"从文件加载图像: {filepath}")
            i = Image.open(filepath)
            i = ImageOps.exif_transpose(i)
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            
            # 处理 mask（如果有 alpha 通道）
            if 'A' in i.getbands():
                print(f"检测到 alpha 通道，提取为 mask")
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                print(f"未检测到 alpha 通道，创建空 mask")
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            
            print(f"输出图像张量形状: {image.shape}, mask 形状: {mask.shape}")
            return (filepath, image, mask.unsqueeze(0))
            
        except Exception as e:
            print(f"图像处理失败: {str(e)}")
            # 创建空张量作为备用
            empty_image = torch.zeros((1, 3, 64, 64), dtype=torch.float32)
            empty_mask = torch.zeros((1, 1, 64, 64), dtype=torch.float32)
            return (f"error: {str(e)}", empty_image, empty_mask) 