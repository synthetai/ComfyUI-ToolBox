import os
import base64
import io
from PIL import Image, ImageOps
import folder_paths
import numpy as np
import torch

class OpenAI_SaveToFile:
    """保存多个图像到文件并支持动态输入"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename_prefix": ("STRING", {"default": "openai"}),
                "output_dir": ("STRING", {"default": "", "placeholder": "自定义输出目录，留空则使用 ComfyUI 默认输出目录"}),
                "inputcount": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "image_1": ("IMAGE",),
            },
            "optional": {
                "b64_json": ("STRING", {"default": "", "multiline": True, "placeholder": "可选: OpenAI API 返回的 base64 编码图像数据"}),
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filenames",)
    FUNCTION = "save_images"
    CATEGORY = "ToolBox/OpenAI"

    def save_images(self, filename_prefix, output_dir, inputcount, image_1=None, b64_json="", prompt=None, extra_pnginfo=None, **kwargs):
        saved_paths = []
        
        # 确定输出目录
        if output_dir and output_dir.strip():
            # 使用用户指定的目录
            output_dir = output_dir.strip()
            if not os.path.isabs(output_dir):
                # 如果提供的是相对路径，则相对于 ComfyUI 根目录
                output_dir = os.path.join(os.path.dirname(folder_paths.base_path), output_dir)
            print(f"使用自定义输出目录: {output_dir}")
        else:
            # 使用 ComfyUI 默认输出目录
            output_dir = folder_paths.get_output_directory()
            print(f"使用默认输出目录: {output_dir}")
            
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 处理各个输入图像
        for i in range(1, inputcount + 1):
            image_key = f"image_{i}"
            if image_key in kwargs or (i == 1 and image_1 is not None):
                image_tensor = kwargs.get(image_key, image_1) if i > 1 else image_1
                
                # 生成文件名
                counter = 1
                while True:
                    filename = f"{filename_prefix}_{i}_{counter:05d}.png"
                    filepath = os.path.join(output_dir, filename)
                    if not os.path.exists(filepath):
                        break
                    counter += 1
                
                # 保存图像
                print(f"正在保存图像 {i} 到: {filepath}")
                i = 255. * image_tensor.cpu().numpy().squeeze()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                img.save(filepath)
                saved_paths.append(filepath)
        
        # 如果提供了 base64 数据，也保存它
        if b64_json and len(b64_json.strip()) > 0:
            try:
                # 解码 base64 数据
                image_data = base64.b64decode(b64_json)
                print(f"解码后的图像数据大小: {len(image_data)} 字节")
                
                # 使用 PIL 打开图像
                pil_image = Image.open(io.BytesIO(image_data))
                print(f"解码图像成功，尺寸: {pil_image.size}, 模式: {pil_image.mode}")
                
                # 生成文件名
                counter = 1
                while True:
                    filename = f"{filename_prefix}_b64_{counter:05d}.png"
                    filepath = os.path.join(output_dir, filename)
                    if not os.path.exists(filepath):
                        break
                    counter += 1
                    
                # 保存图像
                print(f"保存 base64 图像到: {filepath}")
                pil_image.save(filepath)
                saved_paths.append(filepath)
            except Exception as e:
                print(f"base64 图像处理失败: {str(e)}")
        
        return (", ".join(saved_paths),)

NODE_CLASS_MAPPINGS = {
    "OpenAI_SaveToFile": OpenAI_SaveToFile
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OpenAI_SaveToFile": "OpenAI SaveToFile"
} 