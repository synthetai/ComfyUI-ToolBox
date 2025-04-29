from .nodes.video_combine import VideoCombineNode
from .nodes.aws_s3_upload import AwsS3UploadNode
from .nodes.openai_image import CreateImageNode
from .nodes.openai_save_image import OpenAISaveImageNode
from .nodes.create_image_edit_node import CreateImageEditNode
from .nodes.openai_save_to_file import OpenAI_SaveToFile

NODE_CLASS_MAPPINGS = {
    "VideoCombineNode": VideoCombineNode,
    "AwsS3UploadNode": AwsS3UploadNode,
    "CreateImageNode": CreateImageNode,
    "OpenAISaveImageNode": OpenAISaveImageNode,
    "CreateImageEditNode": CreateImageEditNode,
    "OpenAI_SaveToFile": OpenAI_SaveToFile
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoCombineNode": "Video Combine",
    "AwsS3UploadNode": "AWS S3 Upload",
    "CreateImageNode": "Create Image (OpenAI)",
    "OpenAISaveImageNode": "Save Image (OpenAI)",
    "CreateImageEditNode": "Edit Image (OpenAI)",
    "OpenAI_SaveToFile": "OpenAI SaveToFile"
} 