import os
import boto3
from botocore.exceptions import ClientError
import folder_paths

class AwsS3UploadNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "bucket": ("STRING", {"default": ""}),
                "access_key": ("STRING", {"default": ""}),
                "secret_key": ("STRING", {"default": ""}),
                "region": ("STRING", {"default": "us-east-1"}),
                "parent_directory": ("STRING", {"default": ""}),
                "file_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "sub_dir_name": ("STRING", {"default": ""}),
                "url_type": (["public", "presigned"], {"default": "public"}),
                "custom_domain": ("STRING", {"default": "", "tooltip": "自定义域名（仅用于public类型），留空则使用标准S3域名"}),
                "presigned_expiry": ("INT", {"default": 3600, "min": 60, "max": 604800, "step": 60, "tooltip": "预签名URL过期时间（秒），仅用于presigned类型"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING",)
    RETURN_NAMES = ("s3_file_path", "access_url",)
    FUNCTION = "upload_to_s3"
    CATEGORY = "ToolBox/AWS S3"

    def upload_to_s3(self, bucket, access_key, secret_key, region, parent_directory, file_path, 
                     sub_dir_name="", url_type="public", custom_domain="", presigned_expiry=3600):
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 确保文件路径是绝对路径
        file_path = os.path.abspath(file_path)
        print(f"准备上传文件: {file_path}")
        
        # 获取文件名
        file_name = os.path.basename(file_path)
        
        # 处理父目录，确保没有前导和尾随斜杠
        parent_directory = parent_directory.strip('/')
        
        # 处理子目录，确保没有前导和尾随斜杠
        sub_dir_name = sub_dir_name.strip('/') if sub_dir_name else ""
        
        # 构建S3对象键（路径）
        s3_key = file_name
        
        # 根据不同情况构建完整路径
        if parent_directory and sub_dir_name:
            # 如果父目录和子目录都有值
            s3_key = f"{parent_directory}/{sub_dir_name}/{file_name}"
        elif parent_directory:
            # 只有父目录有值
            s3_key = f"{parent_directory}/{file_name}"
        elif sub_dir_name:
            # 只有子目录有值
            s3_key = f"{sub_dir_name}/{file_name}"
            
        print(f"最终S3存储路径: {s3_key}")
        print(f"使用AWS区域: {region}")
        
        try:
            # 创建S3客户端，指定区域
            s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # 上传文件
            print(f"正在上传到S3: bucket={bucket}, key={s3_key}, region={region}")
            s3_client.upload_file(file_path, bucket, s3_key)
            
            # 构建S3 URL
            s3_path = f"s3://{bucket}/{s3_key}"
            print(f"文件上传成功: {s3_path}")
            
            # 根据URL类型生成访问URL
            if url_type == "presigned":
                # 生成预签名URL（适用于私有桶）
                try:
                    public_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket, 'Key': s3_key},
                        ExpiresIn=presigned_expiry
                    )
                    print(f"生成预签名URL (过期时间: {presigned_expiry}秒): {public_url}")
                except Exception as e:
                    print(f"生成预签名URL失败: {str(e)}")
                    # 如果预签名URL生成失败，回退到标准S3 URL
                    public_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
                    print(f"回退到标准S3 URL: {public_url}")
            else:
                # 生成公开访问URL（适用于公开桶）
                if custom_domain.strip():
                    # 使用自定义域名
                    domain = custom_domain.strip().rstrip('/') + '/'
                    public_url = f"{domain}{s3_key}"
                    print(f"使用自定义域名生成URL: {public_url}")
                else:
                    # 使用标准S3域名
                    public_url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
                    print(f"使用标准S3域名生成URL: {public_url}")
            
            # 返回S3路径和访问URL
            return (s3_path, public_url,)
            
        except ClientError as e:
            error_message = f"S3上传失败: {str(e)}"
            print(error_message)
            raise Exception(error_message)
        except Exception as e:
            error_message = f"发生未知错误: {str(e)}"
            print(error_message)
            raise Exception(error_message) 