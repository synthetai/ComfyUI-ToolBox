from .nodes.video_combine import VideoCombineNode
from .nodes.aws_s3_upload import AwsS3UploadNode
from .nodes.openai_image import CreateImageNode
from .nodes.openai_save_image import OpenAISaveImageNode
from .nodes.openai_save_to_file import OpenAI_SaveToFile
from .nodes.trim_audio_to_length import TrimAudioToLength
from .nodes.save_audio import SaveAudioNode, NODE_CLASS_MAPPINGS as SAVE_AUDIO_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as SAVE_AUDIO_DISPLAY_MAPPINGS
from .nodes.save_text_to_file import SaveTextToFileNode, NODE_CLASS_MAPPINGS as SAVE_TEXT_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as SAVE_TEXT_DISPLAY_MAPPINGS

# 1. 直接导入节点类和映射
from .nodes.create_image_edit_node import CreateImageEditNode
from .nodes.create_image_edit_node import NODE_CLASS_MAPPINGS as CREATE_IMAGE_EDIT_MAPPINGS
from .nodes.create_image_edit_node import NODE_DISPLAY_NAME_MAPPINGS as CREATE_IMAGE_EDIT_DISPLAY_MAPPINGS

# 新增的视频处理节点
from .nodes.smart_video_combiner import SmartVideoCombinerNode, NODE_CLASS_MAPPINGS as SMART_VIDEO_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as SMART_VIDEO_DISPLAY_MAPPINGS
from .nodes.video_subtitle_generator import VideoSubtitleGeneratorNode, NODE_CLASS_MAPPINGS as SUBTITLE_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as SUBTITLE_DISPLAY_MAPPINGS
from .nodes.image_to_video import ImageToVideoNode, NODE_CLASS_MAPPINGS as IMAGE_VIDEO_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as IMAGE_VIDEO_DISPLAY_MAPPINGS
from .nodes.video_audio_remover import VideoAudioRemoverNode, NODE_CLASS_MAPPINGS as AUDIO_REMOVER_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as AUDIO_REMOVER_DISPLAY_MAPPINGS
from .nodes.video_background_music import VideoBackgroundMusicNode, NODE_CLASS_MAPPINGS as BGM_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as BGM_DISPLAY_MAPPINGS

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
    "SaveTextToFileNode": SaveTextToFileNode,
    
    # 直接添加 CreateImageEditNode
    "CreateImageEditNode": CreateImageEditNode,
}

# 3. 添加从节点导入的其他映射
NODE_CLASS_MAPPINGS.update(CREATE_IMAGE_EDIT_MAPPINGS)
NODE_CLASS_MAPPINGS.update(SAVE_AUDIO_MAPPINGS)
NODE_CLASS_MAPPINGS.update(SAVE_TEXT_MAPPINGS)
NODE_CLASS_MAPPINGS.update(SMART_VIDEO_MAPPINGS)
NODE_CLASS_MAPPINGS.update(SUBTITLE_MAPPINGS)
NODE_CLASS_MAPPINGS.update(IMAGE_VIDEO_MAPPINGS)
NODE_CLASS_MAPPINGS.update(AUDIO_REMOVER_MAPPINGS)
NODE_CLASS_MAPPINGS.update(BGM_MAPPINGS)

# 4. 定义显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoCombineNode": "Video Combine",
    "AwsS3UploadNode": "AWS S3 Upload",
    "CreateImageNode": "Create Image (OpenAI)",
    "OpenAISaveImageNode": "Save Image (OpenAI)",
    "OpenAI_SaveToFile": "OpenAI SaveToFile",
    "TrimAudioToLength": "Trim Audio To Length",
    "SaveTextToFileNode": "Save Text To File",
    
    # 添加显示名称
    "CreateImageEditNode": "Edit Image (OpenAI)",
}

# 5. 添加从节点导入的其他显示名称映射
NODE_DISPLAY_NAME_MAPPINGS.update(CREATE_IMAGE_EDIT_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(SAVE_AUDIO_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(SAVE_TEXT_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(SMART_VIDEO_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(SUBTITLE_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(IMAGE_VIDEO_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(AUDIO_REMOVER_DISPLAY_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(BGM_DISPLAY_MAPPINGS)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY'] 