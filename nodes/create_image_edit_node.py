"""
CreateImageEditNode  ——  调用 OpenAI Images Edit 接口
放到  ComfyUI/custom_nodes/  目录，重启即可加载
"""

import os
import base64
import io
from typing import List, Dict, Any

import requests
from PIL import Image
import numpy as np
import torch

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 使用环境变量更安全


class CreateImageEditNode:
    """POST https://api.openai.com/v1/images/edits"""

    CATEGORY = "ToolBox/OpenAI"
    RETURN_TYPES = ("IMAGE",)        # 返回一张图（多张时只取第 1 张，自己修改即可）
    FUNCTION = "run"
    VERSION = "0.1.0"
    DESCRIPTION = """
Edit or extend images using OpenAI's API (DALL-E-2 and GPT-Image-1 models).
You can set how many image inputs the node has,
with the **inputcount** parameter and clicking "Update inputs" button.
"""

    # 最大支持 10 张输入，跟 n 的上限保持一致
    MAX_IMAGES = 10

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Dict[str, Any]]:
        inputs: Dict[str, Dict[str, Any]] = {
            "required": {
                "image_1": ("IMAGE",),                      # 至少 1 张
                "prompt": ("STRING", {"multiline": True}),
                "inputcount": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": cls.MAX_IMAGES,
                        "step": 1,
                        "display": "slider",
                    },
                ),
            },
            "optional": {
                "mask": ("MASK",),
                "model": (["dall-e-2", "gpt-image-1"], {"default": "dall-e-2"}),
                "n": ("INT", {"default": 1, "min": 1, "max": 10}),
                "quality": (
                    ["auto", "high", "medium", "low", "standard"],
                    {"default": "auto"},
                ),
                "response_format": (["url", "b64_json"], {"default": "url"}),
                "size": (
                    ["256x256", "512x512", "1024x1024", "1536x1024", "1024x1536", "auto"],
                    {"default": "1024x1024"},
                ),
                "user": ("STRING", {"multiline": False}),
            },
        }

        # 其余可选 image_i
        for i in range(2, cls.MAX_IMAGES + 1):
            inputs["optional"][f"image_{i}"] = ("IMAGE",)

        return inputs

    @staticmethod
    def _pil_to_bytes(pil_img: Image.Image) -> bytes:
        """PIL → bytes (PNG)"""
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return buf.getvalue()

    def _encode_images(self, images: List[Image.Image]) -> List[str]:
        """把 PIL 图转 base64 字符串，符合 openai 要求"""
        return [base64.b64encode(self._pil_to_bytes(img)).decode("utf-8") for img in images]

    def run(self, image_1, prompt, inputcount=1, **kwargs):
        # ---------- 收集所有 image_n ----------
        images = []
        images.append(self._tensor_to_pil(image_1))
        
        for i in range(2, self.MAX_IMAGES + 1):
            key = f"image_{i}"
            if key in kwargs and kwargs[key] is not None:
                images.append(self._tensor_to_pil(kwargs[key]))

        if not images:
            raise ValueError("至少需要一张 image_x 输入")

        # ---------- 构造请求 ----------
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }

        body = {
            "prompt": prompt,
            "n": kwargs.get("n", 1),
            "response_format": kwargs.get("response_format", "url"),
            "size": kwargs.get("size", "1024x1024"),
            "model": kwargs.get("model", "dall-e-2"),
            "quality": kwargs.get("quality", "auto"),
        }

        if "user" in kwargs and kwargs["user"]:
            body["user"] = kwargs["user"]

        # OpenAI 编辑接口要求 base64-encoded images => images 字段
        body["image"] = self._encode_images(images) if len(images) > 1 else self._encode_images(images)[0]

        # mask（可选）
        if "mask" in kwargs and kwargs["mask"] is not None:
            mask_pil = self._tensor_to_pil(kwargs["mask"])
            body["mask"] = base64.b64encode(self._pil_to_bytes(mask_pil)).decode("utf-8")

        # ---------- 调用 OpenAI ----------
        url = "https://api.openai.com/v1/images/edits"
        resp = requests.post(url, headers=headers, json=body, timeout=240)
        resp.raise_for_status()

        data = resp.json()

        # 只取第 1 张；如要全部返回，可把 RETURN_TYPES 改成 ("IMAGE",)*n
        first_item = data["data"][0]
        if body["response_format"] == "url":
            # 下载图片
            img_bytes = requests.get(first_item["url"], timeout=240).content
            img = Image.open(io.BytesIO(img_bytes))
        else:  # "b64_json"
            img = Image.open(io.BytesIO(base64.b64decode(first_item["b64_json"])))
            
        # 转换为 ComfyUI 格式的张量
        img_tensor = self._pil_to_tensor(img)
        return (img_tensor,)
    
    def _tensor_to_pil(self, image_tensor):
        """将 ComfyUI 图像张量转换为 PIL 图像"""
        if len(image_tensor.shape) == 4:
            # 使用第一张图
            image_tensor = image_tensor[0]
            
        # 确保正确的格式 [3,H,W] -> [H,W,3]
        i = 255. * image_tensor.cpu().numpy()
        img = Image.fromarray(np.clip(i.transpose(1, 2, 0), 0, 255).astype(np.uint8))
        return img
    
    def _pil_to_tensor(self, img):
        """将 PIL 图像转换为 ComfyUI 图像张量"""
        img_np = np.array(img).astype(np.float32) / 255.0
        # [H,W,3] -> [3,H,W] 
        img_np = img_np.transpose(2, 0, 1)
        return torch.from_numpy(img_np).unsqueeze(0) # 添加批次维度 [1,3,H,W]

# 确保节点能被 ComfyUI 注册
NODE_CLASS_MAPPINGS = {
    "CreateImageEditNode": CreateImageEditNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CreateImageEditNode": "Edit Image (OpenAI)",
}
