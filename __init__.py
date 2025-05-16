from .nodes.video_combine import VideoCombineNode
from .nodes.aws_s3_upload import AwsS3UploadNode
from .nodes.openai_image import CreateImageNode
from .nodes.openai_save_image import OpenAISaveImageNode
from .nodes.openai_save_to_file import OpenAI_SaveToFile
from .nodes.trim_audio_to_length import TrimAudioToLength

# 1. 直接导入节点类和映射
from .nodes.create_image_edit_node import CreateImageEditNode
from .nodes.create_image_edit_node import NODE_CLASS_MAPPINGS as CREATE_IMAGE_EDIT_MAPPINGS
from .nodes.create_image_edit_node import NODE_DISPLAY_NAME_MAPPINGS as CREATE_IMAGE_EDIT_DISPLAY_MAPPINGS

# 告诉 ComfyUI 从哪里加载前端扩展
import os
WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")

# 2. 定义基本节点映射
NODE_CLASS_MAPPINGS = {
    "VideoCombineNode": VideoCombineNode,
    "AwsS3UploadNode": AwsS3UploadNode,
    "CreateImageNode": CreateImageNode,
    "OpenAISaveImageNode": OpenAISaveImageNode,
    "OpenAI_SaveToFile": OpenAI_SaveToFile,
    "TrimAudioToLength": TrimAudioToLength,
    
    # 直接添加 CreateImageEditNode
    "CreateImageEditNode": CreateImageEditNode,
}

# 3. 添加从节点导入的其他映射
NODE_CLASS_MAPPINGS.update(CREATE_IMAGE_EDIT_MAPPINGS)

# 4. 定义显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoCombineNode": "Video Combine",
    "AwsS3UploadNode": "AWS S3 Upload",
    "CreateImageNode": "Create Image (OpenAI)",
    "OpenAISaveImageNode": "Save Image (OpenAI)",
    "OpenAI_SaveToFile": "OpenAI SaveToFile",
    "TrimAudioToLength": "Trim Audio To Length",
    
    # 添加显示名称
    "CreateImageEditNode": "Edit Image (OpenAI)",
}

# 5. 添加从节点导入的其他显示名称映射
NODE_DISPLAY_NAME_MAPPINGS.update(CREATE_IMAGE_EDIT_DISPLAY_MAPPINGS) 