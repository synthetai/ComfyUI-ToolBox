import os
import json
import requests
import io
import base64
import numpy as np
import torch
from PIL import Image
import folder_paths
import time

class CreateImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "A text description of the desired image(s)"}),
            },
            "optional": {
                "model": (["dall-e-2", "dall-e-3", "gpt-image-1"], {"default": "gpt-image-1"}),
                "size": (["auto", "1024x1024", "1792x1024", "1024x1792", "1536x1024", "1024x1536", "512x512", "256x256"], {"default": "1024x1024"}),
                "quality": (["auto", "standard", "hd", "high", "medium", "low"], {"default": "auto"}),
                "style": (["vivid", "natural"], {"default": "vivid"}),
                "background": (["auto", "transparent", "opaque"], {"default": "auto"}),
                "moderation": (["auto", "low"], {"default": "auto"}),
                "response_format": (["url", "b64_json"], {"default": "b64_json"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "output_compression": ("INT", {"default": 100, "min": 0, "max": 100, "step": 1}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10}),
                "user": ("STRING", {"default": "", "multiline": False, "placeholder": "A unique identifier representing your end-user"})
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "generate_image"
    CATEGORY = "ToolBox/OpenAI"

    def generate_image(self, api_key, prompt, model="dall-e-3", size="1024x1024", quality="auto", style="vivid", 
                      background="auto", moderation="auto", response_format="b64_json", output_format="png", 
                      output_compression=100, n=1, user=""):
        # 验证输入参数
        if not api_key:
            raise ValueError("必须提供 OpenAI API 密钥")
        
        if not prompt:
            raise ValueError("必须提供提示词")
        
        # 检查提示词长度限制
        if model == "gpt-image-1" and len(prompt) > 32000:
            raise ValueError(f"GPT-Image-1 模型的提示词最大长度为 32000 字符，当前长度为 {len(prompt)}")
        elif model == "dall-e-2" and len(prompt) > 1000:
            raise ValueError(f"DALL-E-2 模型的提示词最大长度为 1000 字符，当前长度为 {len(prompt)}")
        elif model == "dall-e-3" and len(prompt) > 4000:
            raise ValueError(f"DALL-E-3 模型的提示词最大长度为 4000 字符，当前长度为 {len(prompt)}")
        
        # 验证模型特定参数
        if model == "dall-e-3" and n > 1:
            print(f"警告: DALL-E-3 模型仅支持每次生成一张图像 (n=1)，已将 n 设置为 1")
            n = 1
            
        # 验证参数组合
        if background == "transparent" and output_format not in ["png", "webp"]:
            print(f"警告: 透明背景仅支持 PNG 和 WebP 格式，已将输出格式更改为 PNG")
            output_format = "png"
            
        if model != "gpt-image-1" and (background != "auto" or output_format != "png" or output_compression != 100):
            print(f"警告: background, output_format 和 output_compression 参数仅支持 GPT-Image-1 模型")
            
        # 验证尺寸与模型的兼容性
        valid_sizes = {
            "gpt-image-1": ["auto", "1024x1024", "1536x1024", "1024x1536"],
            "dall-e-2": ["256x256", "512x512", "1024x1024"],
            "dall-e-3": ["1024x1024", "1792x1024", "1024x1792"]
        }
        
        if size != "auto" and size not in valid_sizes.get(model, []):
            print(f"警告: 尺寸 {size} 与模型 {model} 不兼容，将使用默认尺寸")
            if model == "gpt-image-1":
                size = "1024x1024"
            elif model == "dall-e-2":
                size = "1024x1024"
            elif model == "dall-e-3":
                size = "1024x1024"
        
        # 验证质量与模型的兼容性
        valid_qualities = {
            "gpt-image-1": ["auto", "high", "medium", "low"],
            "dall-e-2": ["auto", "standard"],
            "dall-e-3": ["auto", "standard", "hd"]
        }
        
        if quality != "auto" and quality not in valid_qualities.get(model, []):
            print(f"警告: 质量 {quality} 与模型 {model} 不兼容，将使用默认质量")
            quality = "auto"
            
        # 设置 API 请求参数
        api_url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 构建请求 JSON 数据
        request_data = {
            "prompt": prompt,
            "model": model,
        }
        
        # 添加非默认参数
        if n != 1:
            request_data["n"] = n
            
        if size != "auto":
            request_data["size"] = size
            
        if quality != "auto":
            request_data["quality"] = quality
            
        if model == "dall-e-3" and style != "vivid":
            request_data["style"] = style
            
        if model == "gpt-image-1":
            if background != "auto":
                request_data["background"] = background
                
            if moderation != "auto":
                request_data["moderation"] = moderation
                
            if output_format != "png":
                request_data["output_format"] = output_format
                
            if output_compression != 100 and output_format in ["webp", "jpeg"]:
                request_data["output_compression"] = output_compression
        
        if model in ["dall-e-2", "dall-e-3"] and response_format != "url":
            request_data["response_format"] = response_format
            
        # 如果用户提供了 user 标识符，则添加
        if user:
            request_data["user"] = user
            
        print(f"正在请求 OpenAI 生成图像，提示词：{prompt}")
        print(f"使用参数: 模型={model}, 尺寸={size}, 质量={quality}")
        
        # 重试机制
        max_retries = 3
        retry_delay = 2  # 秒
        
        for retry in range(max_retries):
            try:
                # 发送 API 请求
                response = requests.post(api_url, headers=headers, json=request_data)
                
                # 检查 HTTP 状态码
                if response.status_code != 200:
                    error_info = response.json() if response.text else {"error": {"message": "未知错误"}}
                    error_message = error_info.get("error", {}).get("message", f"HTTP 错误 {response.status_code}")
                    
                    # 对于可能的限流或服务器错误进行重试
                    if response.status_code in [429, 500, 502, 503, 504] and retry < max_retries - 1:
                        wait_time = retry_delay * (retry + 1)
                        print(f"请求失败 ({response.status_code}): {error_message}. 等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"OpenAI API 错误 ({response.status_code}): {error_message}")
                
                response_data = response.json()
                
                # 检查响应数据
                if "data" not in response_data or len(response_data["data"]) == 0:
                    raise Exception("API 返回的响应中未包含图像数据")
                
                # 处理 API 返回结果
                if model == "gpt-image-1":
                    # GPT-Image-1 总是返回 base64 编码的图像
                    if "b64_json" not in response_data["data"][0]:
                        raise Exception("API 返回的响应未包含 base64 编码的图像数据")
                    
                    image_b64 = response_data["data"][0]["b64_json"]
                    image_data = base64.b64decode(image_b64)
                    image = Image.open(io.BytesIO(image_data))
                elif response_format == "b64_json":
                    # 如果返回的是 base64 编码的图像
                    if "b64_json" not in response_data["data"][0]:
                        raise Exception("API 返回的响应未包含 base64 编码的图像数据")
                    
                    image_b64 = response_data["data"][0]["b64_json"]
                    image_data = base64.b64decode(image_b64)
                    image = Image.open(io.BytesIO(image_data))
                else:
                    # 如果返回的是图像 URL
                    if "url" not in response_data["data"][0]:
                        raise Exception("API 返回的响应未包含图像 URL")
                    
                    image_url = response_data["data"][0]["url"]
                    print(f"获取到图像 URL: {image_url}")
                    image_response = requests.get(image_url)
                    
                    if image_response.status_code != 200:
                        raise Exception(f"下载图像失败 (HTTP {image_response.status_code})")
                    
                    image = Image.open(io.BytesIO(image_response.content))
                
                # 如果有修改后的提示词，则打印出来
                if "revised_prompt" in response_data["data"][0]:
                    revised_prompt = response_data["data"][0]["revised_prompt"]
                    print(f"OpenAI 修改后的提示词: {revised_prompt}")
                
                # 转换为 ComfyUI 支持的图像格式
                if image.mode == 'RGBA' and background == 'transparent':
                    # 如果是透明背景的 RGBA 图像，需要特殊处理
                    # 创建一个白色背景
                    white_bg = Image.new('RGBA', image.size, (255, 255, 255, 255))
                    # 将原图与白色背景合成
                    composite = Image.alpha_composite(white_bg, image)
                    # 转换为 RGB
                    image_rgb = composite.convert('RGB')
                    # 将 numpy 数组转换为 PyTorch 张量
                    image_array = np.array(image_rgb).astype(np.float32) / 255.0
                    image_tensor = torch.from_numpy(image_array).permute(2, 0, 1)
                    print("图像生成成功!")
                    return ([image_tensor],)
                else:
                    # 正常转换为 RGB
                    image = image.convert("RGB")
                    # 将 numpy 数组转换为 PyTorch 张量
                    image_array = np.array(image).astype(np.float32) / 255.0
                    image_tensor = torch.from_numpy(image_array).permute(2, 0, 1)
                    print("图像生成成功!")
                    return ([image_tensor],)
                
            except Exception as e:
                # 最后一次重试失败，或者是不需要重试的错误
                if retry == max_retries - 1:
                    print(f"图像生成失败，所有重试都失败: {str(e)}")
                    raise Exception(f"OpenAI 图像生成失败: {str(e)}")
                else:
                    print(f"图像生成出错，将重试 ({retry+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay * (retry + 1)) 