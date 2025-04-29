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

class CreateImageEditNode:
    """OpenAI 图像编辑节点，可以编辑或扩展已有图像"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": "", "multiline": False}),
                "inputcount": ("INT", {"default": 1, "min": 1, "max": 4, "step": 1}),
                "image_1": ("IMAGE",),
                "prompt": ("STRING", {"default": "", "multiline": True, "placeholder": "A text description of the desired image(s)"}),
            },
            "optional": {
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "mask": ("MASK",),
                "model": (["gpt-image-1", "dall-e-2"], {"default": "gpt-image-1"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10}),
                "size": (["auto", "1024x1024", "1536x1024", "1024x1536", "512x512", "256x256"], {"default": "1024x1024"}),
                "quality": (["auto", "standard", "high", "medium", "low"], {"default": "auto"}),
                "response_format": (["url", "b64_json"], {"default": "b64_json"}),
                "user": ("STRING", {"default": "", "multiline": False, "placeholder": "A unique identifier representing your end-user"})
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("image", "b64_json",)
    FUNCTION = "edit_image"
    CATEGORY = "ToolBox/OpenAI"
    DESCRIPTION = """
Edit or extend images using OpenAI's API (DALL-E-2 and GPT-Image-1 models).
You can set how many image inputs the node has (1-4),
with the **inputcount** parameter and clicking "Update inputs".
Note: DALL-E-2 only supports a single input image.
"""

    def edit_image(self, api_key, inputcount, image_1, prompt, mask=None, model="gpt-image-1", n=1, size="1024x1024", 
                   quality="auto", response_format="b64_json", user="", **kwargs):
        print(f"图像编辑, prompt: {prompt}")
        
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
        
        # 验证size参数与模型的兼容性
        valid_sizes = {
            "gpt-image-1": ["auto", "1024x1024", "1536x1024", "1024x1536"],
            "dall-e-2": ["256x256", "512x512", "1024x1024"]
        }
        
        if size not in valid_sizes.get(model, []):
            print(f"警告: 尺寸 {size} 与模型 {model} 不兼容，将使用默认尺寸")
            size = "1024x1024"
            
        # 验证模型特定参数
        if model == "dall-e-2" and n > 1:
            print(f"注意: 当前 n={n}，DALL-E-2 可以生成多张图像")
            
        # 创建临时文件以保存图像
        temp_dir = os.path.join(folder_paths.get_temp_directory(), "openai_edit")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 准备存储所有图像路径
        image_paths = []
        
        # 收集所有提供的图像
        images = [image_1]
        for i in range(2, inputcount + 1):
            if f"image_{i}" in kwargs and kwargs[f"image_{i}"] is not None and kwargs[f"image_{i}"].shape[0] > 0:
                images.append(kwargs[f"image_{i}"])
        
        # 对于 DALL-E-2，只能使用一张输入图像
        if model == "dall-e-2" and len(images) > 1:
            print(f"警告: DALL-E-2 模型仅支持一张输入图像，将只使用第一张图像")
            images = images[:1]
        
        # 对于 GPT-Image-1，最多支持 4 张输入图像
        if model == "gpt-image-1" and len(images) > 4:
            print(f"警告: GPT-Image-1 模型最多支持 4 张输入图像，将只使用前 4 张图像")
            images = images[:4]
        
        print(f"使用 {len(images)} 张输入图像")
        
        # 处理所有输入图像
        for i, img in enumerate(images):
            # 确保图像是一个批次中的第一张
            if img.shape[0] > 1:
                print(f"警告: 图像 {i+1} 包含多个批次，仅使用第一个")
            
            # 获取当前图像张量
            image_tensor = img[0]
            
            # 将 tensor 转换为 numpy 数组 [0,1] -> [0,255]
            image_np = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
            
            # 从 [C,H,W] 转换为 [H,W,C]
            image_np = np.transpose(image_np, (1, 2, 0))
            
            # 创建 PIL 图像
            pil_image = Image.fromarray(image_np)
            print(f"输入图像 {i+1}: 尺寸: {pil_image.size}, 模式: {pil_image.mode}")
            
            # 保存图像
            image_path = os.path.join(temp_dir, f"source_image_{i}.png")
            print(f"保存源图像 {i+1} 到临时文件: {image_path}")
            pil_image.save(image_path)
            image_paths.append(image_path)
        
        # 如果提供了掩码，则处理掩码（仅适用于第一张图像）
        mask_path = None
        if mask is not None:
            if mask.shape[0] > 1:
                print(f"警告: 收到批量掩码，仅使用第一个掩码应用于第一张图像")
                mask_tensor = mask[0]
            else:
                mask_tensor = mask[0]
            
            # 确保掩码是 2D
            if len(mask_tensor.shape) > 2:
                mask_tensor = mask_tensor.squeeze()
            
            # 将掩码转换为 PIL 图像 (反转值，因为 OpenAI 要求透明区域表示要编辑的区域)
            mask_np = ((1.0 - mask_tensor.cpu().numpy()) * 255).astype(np.uint8)
            
            # 创建 RGBA 图像作为掩码
            mask_image = Image.fromarray(mask_np, mode='L')
            
            # 获取第一张图像
            first_pil_image = Image.open(image_paths[0])
            
            # 确保掩码与原图像尺寸相同
            if mask_image.size != first_pil_image.size:
                print(f"调整掩码尺寸从 {mask_image.size} 到 {first_pil_image.size}")
                mask_image = mask_image.resize(first_pil_image.size, Image.LANCZOS)
            
            # 创建 RGBA 图像，将原始 RGB 通道和 alpha 通道结合
            rgba_mask = Image.new("RGBA", first_pil_image.size)
            rgba_mask.paste(first_pil_image, (0, 0))
            
            # 应用掩码作为 alpha 通道
            r, g, b, a = rgba_mask.split()
            rgba_mask = Image.merge("RGBA", (r, g, b, mask_image))
            
            mask_path = os.path.join(temp_dir, "mask_image.png")
            print(f"保存掩码图像到临时文件: {mask_path}")
            rgba_mask.save(mask_path)
        
        # 设置 API 请求 URL
        api_url = "https://api.openai.com/v1/images/edits"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # 准备多部分表单数据
        files = {
            'prompt': (None, prompt),
            'model': (None, model),
            'n': (None, str(n)),
            'size': (None, size),
            'response_format': (None, response_format),
        }
        
        # 添加图像文件
        if model == "gpt-image-1":
            # 对于 GPT-Image-1，可以添加多张图像
            for i, img_path in enumerate(image_paths):
                files[f'image[{i}]'] = (f'image_{i}.png', open(img_path, 'rb'), 'image/png')
        else:
            # 对于 DALL-E-2，只能添加一张图像
            files['image'] = ('image.png', open(image_paths[0], 'rb'), 'image/png')
        
        # 添加掩码（如果有）- 掩码仅适用于第一张图像
        if mask_path:
            files['mask'] = ('mask.png', open(mask_path, 'rb'), 'image/png')
        
        # 添加其他非默认参数
        if quality != "auto":
            files['quality'] = (None, quality)
            
        if user:
            files['user'] = (None, user)
        
        print(f"正在发送请求到 OpenAI 编辑图像 API，模型: {model}")
        
        # 重试机制
        max_retries = 3
        retry_delay = 2
        
        for retry in range(max_retries):
            try:
                print(f"发送 API 请求到 {api_url}...")
                response = requests.post(api_url, headers=headers, files=files)
                print(f"收到响应，状态码: {response.status_code}")
                
                # 检查 HTTP 状态码
                if response.status_code != 200:
                    error_info = response.json() if response.text else {"error": {"message": "未知错误"}}
                    error_message = error_info.get("error", {}).get("message", f"HTTP 错误 {response.status_code}")
                    print(f"API 错误: {error_message}")
                    
                    # 对于可能的限流或服务器错误进行重试
                    if response.status_code in [429, 500, 502, 503, 504] and retry < max_retries - 1:
                        wait_time = retry_delay * (retry + 1)
                        print(f"请求失败 ({response.status_code}): {error_message}. 等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"OpenAI API 错误 ({response.status_code}): {error_message}")
                
                response_data = response.json()
                print(f"响应数据结构: {list(response_data.keys())}")
                
                # 检查响应数据
                if "data" not in response_data or len(response_data["data"]) == 0:
                    raise Exception("API 返回的响应中未包含图像数据")
                
                print(f"数据项数量: {len(response_data['data'])}")
                
                # 处理返回的所有图像
                result_tensors = []
                first_b64_json = ""
                
                for i, data_item in enumerate(response_data["data"]):
                    # 保存 base64 数据以便返回（仅返回第一张图像的数据）
                    if i == 0 and response_format == "b64_json":
                        if "b64_json" in data_item:
                            first_b64_json = data_item["b64_json"]
                        else:
                            print("警告: 响应中未找到 b64_json 数据")
                    
                    # 处理图像数据
                    image_data = None
                    if response_format == "b64_json" and "b64_json" in data_item:
                        # 处理 base64 编码的图像
                        image_b64 = data_item["b64_json"]
                        print(f"图像 {i+1}: Base64 图像数据长度: {len(image_b64)}")
                        image_data = base64.b64decode(image_b64)
                    elif "url" in data_item:
                        # 如果返回的是图像 URL
                        image_url = data_item["url"]
                        print(f"图像 {i+1}: 获取到图像 URL: {image_url}")
                        
                        try:
                            image_response = requests.get(image_url, timeout=30)
                            print(f"图像 {i+1}: 下载图像，状态码: {image_response.status_code}")
                            
                            if image_response.status_code != 200:
                                print(f"警告: 图像 {i+1} 下载失败 (HTTP {image_response.status_code})")
                                continue
                            
                            image_data = image_response.content
                            
                            # 如果是第一张图像且尚未设置 first_b64_json，则设置它
                            if i == 0 and not first_b64_json:
                                first_b64_json = base64.b64encode(image_data).decode('utf-8')
                        except Exception as e:
                            print(f"图像 {i+1} 下载错误: {str(e)}")
                            continue
                    else:
                        print(f"警告: 图像 {i+1} 数据格式不受支持")
                        continue
                    
                    # 处理图像
                    try:
                        result_image = Image.open(io.BytesIO(image_data))
                        print(f"图像 {i+1}: 尺寸: {result_image.size}, 模式: {result_image.mode}")
                        
                        # 确保图像处于 RGB 模式
                        if result_image.mode != 'RGB':
                            print(f"图像 {i+1}: 转换图像从 {result_image.mode} 到 RGB 模式")
                            result_image = result_image.convert('RGB')
                        
                        # 转换为 numpy 数组
                        img_np = np.array(result_image).astype(np.float32) / 255.0
                        
                        # 转换为 PyTorch 张量并设置正确的维度顺序 (CHW)
                        tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)
                        result_tensors.append(tensor)
                    except Exception as e:
                        print(f"图像 {i+1} 处理错误: {str(e)}")
                
                # 清理临时文件
                try:
                    for img_path in image_paths:
                        os.remove(img_path)
                    if mask_path:
                        os.remove(mask_path)
                except Exception as e:
                    print(f"清理临时文件失败: {str(e)}")
                
                # 确保至少有一张图像被成功处理
                if not result_tensors:
                    raise Exception("没有成功处理任何图像")
                
                # 将所有张量连接为一个批次
                batch_tensor = torch.cat(result_tensors, dim=0)
                print(f"最终输出批次张量形状: {batch_tensor.shape}")
                
                # 返回格式与 ComfyUI 兼容 - 同时返回图像张量和 base64 数据
                return (batch_tensor, first_b64_json)
                
            except Exception as e:
                # 最后一次重试失败，或者是不需要重试的错误
                if retry == max_retries - 1:
                    print(f"图像编辑失败，所有重试都失败: {str(e)}")
                    
                    # 清理临时文件
                    try:
                        for img_path in image_paths:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                        if mask_path and os.path.exists(mask_path):
                            os.remove(mask_path)
                    except:
                        pass
                    
                    # 返回空图像和错误消息
                    empty_image = torch.zeros((1, 3, 512, 512), dtype=torch.float32)
                    return (empty_image, f"error: {str(e)}")
                else:
                    print(f"图像编辑出错，将重试 ({retry+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay * (retry + 1)) 