import os
import base64
import io
from PIL import Image
import folder_paths
import numpy as np
import torch

class OpenAISaveImageNode:
    """保存 OpenAI 返回的图像数据到文件"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "b64_json": ("STRING", {"default": "", "multiline": True, "placeholder": "OpenAI API 返回的 base64 编码图像数据"}),
                "filename_prefix": ("STRING", {"default": "openai"}),
            },
            "optional": {
                "output_type": (["save", "image"], {"default": "save"}),
            }
        }

    RETURN_TYPES = ("STRING", "IMAGE",)
    RETURN_NAMES = ("filename", "image",)
    FUNCTION = "save_image"
    CATEGORY = "ToolBox/OpenAI"

    def save_image(self, b64_json, filename_prefix, output_type="save"):
        print(f"接收到 base64 数据，长度: {len(b64_json)}")
        
        try:
            # 解码 base64 数据
            image_data = base64.b64decode(b64_json)
            print(f"解码后的图像数据大小: {len(image_data)} 字节")
            
            # 使用 PIL 打开图像
            image = Image.open(io.BytesIO(image_data))
            print(f"解码图像成功，尺寸: {image.size}, 模式: {image.mode}")
            
            # 确保图像处于 RGB 模式
            if image.mode != 'RGB':
                print(f"转换图像从 {image.mode} 到 RGB 模式")
                image = image.convert('RGB')
                
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
            image.save(filepath)
            
            # 如果需要同时输出到 ComfyUI 工作流
            if output_type == "image":
                # 转换为 numpy 数组
                img_np = np.array(image).astype(np.float32) / 255.0
                
                # 转换为 PyTorch 张量 (CHW 格式)
                tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)
                print(f"输出张量形状: {tensor.shape}")
                return (filepath, tensor)
            
            # 仅保存文件
            return (filepath, None)
            
        except Exception as e:
            print(f"图像保存失败: {str(e)}")
            raise Exception(f"保存 OpenAI 图像失败: {str(e)}") 