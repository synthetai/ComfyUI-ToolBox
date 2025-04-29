from .nodes.video_combine import VideoCombineNode
from .nodes.aws_s3_upload import AwsS3UploadNode
from .nodes.openai_image import CreateImageNode
from .nodes.openai_save_image import OpenAISaveImageNode
from .nodes.openai_save_to_file import OpenAI_SaveToFile

# 导入自定义节点定义的 NODE_CLASS_MAPPINGS
from .nodes.create_image_edit_node import NODE_CLASS_MAPPINGS as CREATE_IMAGE_EDIT_NODE_MAPPINGS
from .nodes.create_image_edit_node import NODE_DISPLAY_NAME_MAPPINGS as CREATE_IMAGE_EDIT_DISPLAY_MAPPINGS

NODE_CLASS_MAPPINGS = {
    "VideoCombineNode": VideoCombineNode,
    "AwsS3UploadNode": AwsS3UploadNode,
    "CreateImageNode": CreateImageNode,
    "OpenAISaveImageNode": OpenAISaveImageNode,
    "OpenAI_SaveToFile": OpenAI_SaveToFile,
}

# 更新节点映射
NODE_CLASS_MAPPINGS.update(CREATE_IMAGE_EDIT_NODE_MAPPINGS)

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoCombineNode": "Video Combine",
    "AwsS3UploadNode": "AWS S3 Upload",
    "CreateImageNode": "Create Image (OpenAI)",
    "OpenAISaveImageNode": "Save Image (OpenAI)",
    "OpenAI_SaveToFile": "OpenAI SaveToFile",
}

# 更新显示名称映射
NODE_DISPLAY_NAME_MAPPINGS.update(CREATE_IMAGE_EDIT_DISPLAY_MAPPINGS) 