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
import time

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
            
            # 检查图像通道数并进行适当处理
            tensor = img_tensor[0].cpu()
            
            # 打印出张量信息便于调试
            print(f"图像 {i+1} 张量形状: {tensor.shape}, 类型: {tensor.dtype}")
            
            # 处理不同形状的张量
            try:
                # 检查张量形状和格式
                if len(tensor.shape) == 3:
                    # 判断哪一个维度是通道
                    if tensor.shape[0] == 3:  # [C,H,W] 格式
                        # CHW 格式，将 tensor 转换为 numpy 数组，并调整到 [0,255] 范围
                        img_np = (tensor.numpy() * 255).astype(np.uint8)
                        # 从 [C,H,W] 转换为 [H,W,C]
                        img_np = np.transpose(img_np, (1, 2, 0))
                        # 创建 PIL 图像
                        pil_image = Image.fromarray(img_np, 'RGB')
                    elif tensor.shape[0] == 1:  # [1,H,W] 格式
                        # 单通道格式，转为灰度图
                        img_np = (tensor.numpy()[0] * 255).astype(np.uint8)
                        pil_image = Image.fromarray(img_np, 'L').convert('RGB')
                    elif tensor.shape[2] == 3:  # [H,W,C] 格式
                        # HWC 格式的 RGB 图像
                        img_np = (tensor.numpy() * 255).astype(np.uint8)
                        pil_image = Image.fromarray(img_np, 'RGB')
                    elif tensor.shape[2] == 1:  # [H,W,1] 格式
                        # HWC 格式的单通道图像
                        img_np = (tensor.numpy()[:, :, 0] * 255).astype(np.uint8)
                        pil_image = Image.fromarray(img_np, 'L').convert('RGB')
                    else:
                        raise ValueError(f"不支持的 3D 张量形状: {tensor.shape}")
                elif len(tensor.shape) == 2:  # [H,W] 格式
                    # 2D 张量，直接是灰度图
                    img_np = (tensor.numpy() * 255).astype(np.uint8)
                    pil_image = Image.fromarray(img_np, 'L').convert('RGB')
                else:
                    raise ValueError(f"不支持的张量维度: {len(tensor.shape)}. 需要 2D 或 3D 张量")
                
                print(f"转换后 PIL 图像: 尺寸: {pil_image.size}, 模式: {pil_image.mode}")
                
                # 保存到临时文件
                img_path = os.path.join(temp_dir, f"image_{i}.png")
                pil_image.save(img_path)
                image_files.append(img_path)
            except Exception as e:
                print(f"处理图像 {i+1} 时出错: {str(e)}")
                raise ValueError(f"图像 {i+1} 处理失败: {str(e)}")
        
        # 处理掩码（如果有）
        mask_path = None
        if mask is not None:
            try:
                print(f"掩码张量形状: {mask.shape}, 类型: {mask.dtype}")
                
                # 转换掩码 tensor 到 PIL
                mask_tensor = mask
                
                # 处理不同形状的掩码张量
                if len(mask_tensor.shape) == 4:  # [B, C, H, W]
                    mask_tensor = mask_tensor[0]  # 取第一个批次
                
                if len(mask_tensor.shape) == 3 and mask_tensor.shape[0] > 1:  # [C>1, H, W]
                    print("掩码有多个通道，取第一个通道")
                    mask_tensor = mask_tensor[0:1]
                
                # 确保掩码是2D，挤压掉单一维度
                if len(mask_tensor.shape) == 3:  # [1, H, W]
                    mask_tensor = mask_tensor.squeeze(0)
                
                # 反转掩码值 (OpenAI 期望透明区域代表要编辑的部分)
                mask_np = ((1.0 - mask_tensor.cpu().numpy()) * 255).astype(np.uint8)
                
                # 创建PIL掩码图像
                mask_pil = Image.fromarray(mask_np, mode='L')
                print(f"转换后掩码图像: 尺寸: {mask_pil.size}, 模式: {mask_pil.mode}")
                
                # 确保掩码尺寸与第一张图像相同
                first_img = Image.open(image_files[0])
                if mask_pil.size != first_img.size:
                    print(f"调整掩码尺寸从 {mask_pil.size} 到 {first_img.size}")
                    mask_pil = mask_pil.resize(first_img.size)
                
                # 保存掩码
                mask_path = os.path.join(temp_dir, "mask.png")
                mask_pil.save(mask_path)
                
            except Exception as e:
                print(f"处理掩码时出错: {str(e)}")
                print("将继续处理，但不使用掩码")
        
        # 准备 API 请求
        url = "https://api.openai.com/v1/images/edits"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        # 准备文件数据
        files = {}
        
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
        
        # 创建 multipart/form-data 表单数据
        form_data = {
            'prompt': prompt,
            'model': model,
            'n': str(n),
            'size': size,
            'response_format': response_format
        }
        
        if quality != "auto":
            form_data['quality'] = quality
            
        if user:
            form_data['user'] = user
        
        print(f"正在调用 OpenAI 编辑图像 API，模型: {model}")
        print(f"请求参数: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
        
        # 重试机制
        max_retries = 3
        retry_delay = 2  # 秒
        
        for retry in range(max_retries):
            try:
                # 发送请求
                print(f"发送 API 请求到 {url}...")
                response = requests.post(
                    url, 
                    headers=headers,
                    data=form_data,
                    files=files,
                    timeout=60
                )
                
                print(f"收到响应，状态码: {response.status_code}")
                
                # 检查 HTTP 状态码
                if response.status_code != 200:
                    error_info = {}
                    try:
                        error_info = response.json() if response.text else {"error": {"message": "未知错误"}}
                    except:
                        pass
                    
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
                
                result = response.json()
                print(f"响应数据结构: {list(result.keys())}")
                print(f"API 返回成功，返回 {len(result.get('data', []))} 张图像")
                
                # 处理返回的图像
                images_out = []
                response_data = ""
                
                for item in result.get("data", []):
                    if response_format == "url":
                        # 下载图像
                        print(f"从 URL 下载图像: {item['url'][:60]}...")
                        img_response = requests.get(item["url"], timeout=30)
                        if img_response.status_code == 200:
                            img = Image.open(io.BytesIO(img_response.content))
                            print(f"下载图像成功，尺寸: {img.size}, 模式: {img.mode}")
                            # 保存响应数据（第一张图的 URL）
                            if not response_data:
                                response_data = item["url"]
                        else:
                            print(f"图像下载失败: HTTP {img_response.status_code}")
                            continue
                    else:  # b64_json
                        print(f"解码 base64 图像数据，长度: {len(item['b64_json'])}")
                        img = Image.open(io.BytesIO(base64.b64decode(item["b64_json"])))
                        print(f"解码图像成功，尺寸: {img.size}, 模式: {img.mode}")
                        # 保存响应数据（第一张图的 base64）
                        if not response_data:
                            response_data = item["b64_json"]
                    
                    # 确保图像处于 RGB 模式
                    if img.mode != 'RGB':
                        print(f"转换图像从 {img.mode} 到 RGB 模式")
                        img = img.convert('RGB')
                    
                    # 转换为 ComfyUI 格式的张量
                    img_np = np.array(img).astype(np.float32) / 255.0
                    img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)
                    
                    # 验证张量格式
                    if img_tensor.dim() != 4 or img_tensor.shape[1] != 3:
                        print(f"警告: 张量形状不符合 ComfyUI 要求，调整中...")
                        # 确保是 [批次, 通道, 高度, 宽度] 格式
                        if img_tensor.dim() == 3 and img_tensor.shape[0] == 3:  # [C,H,W] 格式
                            img_tensor = img_tensor.unsqueeze(0)  # 添加批次维度变成 [1,C,H,W]
                    
                    print(f"最终张量形状: {img_tensor.shape}, 类型: {img_tensor.dtype}")
                    images_out.append(img_tensor)
                
                # 清理临时文件
                for f in files.values():
                    if isinstance(f, tuple) and hasattr(f[1], 'close'):
                        f[1].close()
                
                for file_path in image_files:
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"清理文件 {file_path} 失败: {str(e)}")
                
                if mask_path:
                    try:
                        os.remove(mask_path)
                    except Exception as e:
                        print(f"清理掩码文件失败: {str(e)}")
                
                # 如果没有返回图像，抛出异常
                if not images_out:
                    raise Exception("API 请求成功但未返回任何图像")
                
                # 合并所有图像为一个批量
                batch = torch.cat(images_out, dim=0)
                print(f"成功生成 {batch.shape[0]} 张图像，返回批次张量形状: {batch.shape}")
                
                # 返回图像批量和响应信息
                return (batch, response_data)
                
            except Exception as e:
                # 最后一次重试失败，或者是不需要重试的错误
                if retry == max_retries - 1:
                    print(f"图像编辑失败，所有重试都失败: {str(e)}")
                    
                    # 清理资源
                    for f in files.values():
                        if isinstance(f, tuple) and hasattr(f[1], 'close'):
                            try:
                                f[1].close()
                            except:
                                pass
                    
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
                else:
                    print(f"图像编辑出错，将重试 ({retry+1}/{max_retries}): {str(e)}")
                    time.sleep(retry_delay * (retry + 1))

# 注册节点
NODE_CLASS_MAPPINGS = {
    "CreateImageEditNode": CreateImageEditNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CreateImageEditNode": "Edit Image (OpenAI)"
} 