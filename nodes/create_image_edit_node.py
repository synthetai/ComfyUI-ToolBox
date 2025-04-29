"""
CreateImageEditNode - 调用 OpenAI Images Edit API
支持动态添加多个图像输入
"""

import os
import base64
import io
import json
import requests
import numpy as np
import torch
from PIL import Image
import folder_paths

class CreateImageEditNode:
    """调用 OpenAI 图像编辑 API，支持动态输入"""
    
    CATEGORY = "ToolBox/OpenAI"
    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("image", "response",)
    FUNCTION = "edit_image"
    VERSION = "1.0"
    DESCRIPTION = """使用 OpenAI API 编辑图像。
支持 DALL-E-2 和 GPT-Image-1 模型。
通过调整 inputcount 并点击 Update inputs 按钮可添加多个图像输入。
注意：DALL-E-2 只支持单张图像输入，GPT-Image-1 支持多张图像。
"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "image_1": ("IMAGE",),
                "prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "图像编辑提示词"}),
                "inputcount": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
            },
            "optional": {
                "mask": ("MASK",),
                "model": (["dall-e-2", "gpt-image-1"], {"default": "dall-e-2"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10}),
                "size": (["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536", "auto"], {"default": "1024x1024"}),
                "quality": (["auto", "standard", "hd", "high", "medium", "low"], {"default": "auto"}),
                "response_format": (["url", "b64_json"], {"default": "url"}),
                "user": ("STRING", {"default": "", "multiline": False}),
            }
        }
    
    def edit_image(self, api_key, image_1, prompt, inputcount=1, mask=None, model="dall-e-2", 
                  n=1, size="1024x1024", quality="auto", response_format="url", user="", **kwargs):
        """
        调用 OpenAI 图像编辑 API 编辑图像
        """
        if not api_key:
            raise ValueError("必须提供 OpenAI API 密钥")
        
        if not prompt:
            raise ValueError("必须提供提示词")
        
        # 创建临时目录
        temp_dir = os.path.join(folder_paths.get_temp_directory(), "openai_edit")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 收集所有图像
        images = [image_1]
        for i in range(2, inputcount + 1):
            img_key = f"image_{i}"
            if img_key in kwargs and kwargs[img_key] is not None:
                images.append(kwargs[img_key])
        
        # 处理模型兼容性
        if model == "dall-e-2" and len(images) > 1:
            print(f"警告: DALL-E-2 模型仅支持一张输入图像，将只使用第一张图像")
            images = images[:1]
        
        # 保存图像到临时文件
        image_files = []
        for i, img_tensor in enumerate(images):
            # 确保只使用第一张图（如果是批处理）
            if img_tensor.shape[0] > 1:
                img_tensor = img_tensor[0:1]
            
            # 将 tensor 转换为 numpy 数组，并调整到 [0,255] 范围
            img_np = (img_tensor[0].cpu().numpy() * 255).astype(np.uint8)
            
            # 从 [C,H,W] 转换为 [H,W,C]
            img_np = np.transpose(img_np, (1, 2, 0))
            
            # 创建 PIL 图像
            pil_image = Image.fromarray(img_np)
            
            # 保存到临时文件
            img_path = os.path.join(temp_dir, f"image_{i}.png")
            pil_image.save(img_path)
            image_files.append(img_path)
        
        # 处理掩码（如果有）
        mask_path = None
        if mask is not None:
            # 转换掩码 tensor 到 PIL
            if len(mask.shape) > 2:
                mask = mask.squeeze()
            
            # 反转掩码值 (OpenAI 期望透明区域代表要编辑的部分)
            mask_np = ((1.0 - mask.cpu().numpy()) * 255).astype(np.uint8)
            mask_pil = Image.fromarray(mask_np, mode='L')
            
            # 确保掩码尺寸与第一张图像相同
            first_img = Image.open(image_files[0])
            if mask_pil.size != first_img.size:
                mask_pil = mask_pil.resize(first_img.size)
            
            # 保存掩码
            mask_path = os.path.join(temp_dir, "mask.png")
            mask_pil.save(mask_path)
        
        # 准备 API 请求
        url = "https://api.openai.com/v1/images/edits"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # 准备表单数据
        files = {}
        data = {
            "prompt": prompt,
            "n": n,
            "size": size,
            "response_format": response_format,
            "model": model,
        }
        
        if quality != "auto":
            data["quality"] = quality
            
        if user:
            data["user"] = user
        
        # 添加图像文件
        if model == "gpt-image-1":
            # 对于 GPT-Image-1，使用 image[] 数组
            for i, img_path in enumerate(image_files):
                files[f'image[{i}]'] = (f'image_{i}.png', open(img_path, 'rb'), 'image/png')
        else:
            # 对于 DALL-E-2，使用单个 image
            files['image'] = ('image.png', open(image_files[0], 'rb'), 'image/png')
        
        # 添加掩码（如果有）
        if mask_path:
            files['mask'] = ('mask.png', open(mask_path, 'rb'), 'image/png')
        
        # 发送请求
        try:
            print(f"正在调用 OpenAI 编辑图像 API，模型: {model}")
            response = requests.post(
                url, 
                headers=headers,
                data=data,
                files=files,
                timeout=60
            )
            
            # 检查响应
            if response.status_code != 200:
                error_msg = f"API 错误: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = f"API 错误: {error_data['error']['message']}"
                except:
                    pass
                raise Exception(error_msg)
            
            result = response.json()
            print(f"API 返回成功，返回 {len(result.get('data', []))} 张图像")
            
            # 处理返回的图像
            images_out = []
            response_data = ""
            
            for item in result.get("data", []):
                if response_format == "url":
                    # 下载图像
                    img_response = requests.get(item["url"], timeout=30)
                    if img_response.status_code == 200:
                        img = Image.open(io.BytesIO(img_response.content))
                        # 保存响应数据（第一张图的 URL）
                        if not response_data:
                            response_data = item["url"]
                    else:
                        print(f"图像下载失败: HTTP {img_response.status_code}")
                        continue
                else:  # b64_json
                    img = Image.open(io.BytesIO(base64.b64decode(item["b64_json"])))
                    # 保存响应数据（第一张图的 base64）
                    if not response_data:
                        response_data = item["b64_json"]
                
                # 转换为 ComfyUI 格式的张量
                img_np = np.array(img.convert("RGB")).astype(np.float32) / 255.0
                img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)
                images_out.append(img_tensor)
            
            # 清理临时文件
            for file_path in image_files:
                try:
                    os.remove(file_path)
                except:
                    pass
            
            if mask_path:
                try:
                    os.remove(mask_path)
                except:
                    pass
            
            # 如果没有返回图像，抛出异常
            if not images_out:
                raise Exception("API 请求成功但未返回任何图像")
            
            # 合并所有图像为一个批量
            batch = torch.cat(images_out, dim=0)
            
            # 返回图像批量和响应信息
            return (batch, response_data)
            
        except Exception as e:
            print(f"处理失败: {str(e)}")
            # 清理临时文件
            for file_path in image_files:
                try:
                    os.remove(file_path)
                except:
                    pass
            
            if mask_path:
                try:
                    os.remove(mask_path)
                except:
                    pass
            
            # 返回空图像和错误信息
            error_tensor = torch.zeros((1, 3, 512, 512), dtype=torch.float32)
            return (error_tensor, f"error: {str(e)}")

# 注册节点
NODE_CLASS_MAPPINGS = {
    "CreateImageEditNode": CreateImageEditNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CreateImageEditNode": "Edit Image (OpenAI)"
} 