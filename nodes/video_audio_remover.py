import os
import subprocess
import requests
import tempfile
import folder_paths
from urllib.parse import urlparse
import re

class VideoAudioRemoverNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "filename_prefix": ("STRING", {
                    "default": "no_audio_video", 
                    "multiline": False,
                    "tooltip": "输出视频文件名前缀，例如：no_audio_video_0001.mp4"
                }),
            },
            "optional": {
                "video_url": ("STRING", {
                    "default": "", 
                    "multiline": False,
                    "tooltip": "视频文件的HTTP下载链接"
                }),
                "video_path": ("STRING", {
                    "default": "", 
                    "multiline": False,
                    "tooltip": "本地视频文件路径"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "remove_audio"
    CATEGORY = "ToolBox/Video"
    DESCRIPTION = "从视频中移除音频轨道，支持URL下载和本地文件处理"

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    def download_video(self, url, output_path):
        """下载视频文件到指定路径"""
        try:
            print(f"开始下载视频: {url}")
            
            # 发送HTTP请求下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件总大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            print(f"下载进度: {progress:.1f}%")
            
            print(f"视频下载完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"下载视频失败: {str(e)}")
            return False

    def has_audio_track(self, video_path):
        """检查视频是否包含音频轨道"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-select_streams', 'a', 
                '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', 
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # 如果有输出内容，说明存在音频轨道
            return len(result.stdout.strip()) > 0
            
        except Exception as e:
            print(f"检查音频轨道时出错: {str(e)}")
            # 如果检查失败，假设有音频轨道并尝试移除
            return True

    def remove_audio_from_video(self, input_path, output_path):
        """使用FFmpeg从视频中移除音频"""
        try:
            print(f"开始移除音频: {input_path}")
            
            cmd = [
                'ffmpeg', '-y',  # -y 覆盖输出文件
                '-i', input_path,
                '-c:v', 'copy',  # 复制视频流，不重新编码
                '-an',  # 移除音频流
                '-avoid_negative_ts', 'make_zero',  # 避免负时间戳
                output_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"音频移除完成: {output_path}")
                return True
            else:
                print(f"FFmpeg错误: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("音频移除超时")
            return False
        except Exception as e:
            print(f"移除音频时出错: {str(e)}")
            return False

    def get_next_filename(self, prefix, extension=".mp4"):
        """生成下一个可用的文件名"""
        counter = 1
        while True:
            filename = f"{prefix}_{counter:04d}{extension}"
            full_path = os.path.join(self.output_dir, filename)
            if not os.path.exists(full_path):
                return filename, full_path
            counter += 1

    def get_video_extension(self, file_path):
        """获取视频文件扩展名"""
        _, ext = os.path.splitext(file_path)
        return ext if ext else ".mp4"

    def remove_audio(self, filename_prefix, video_url="", video_path=""):
        try:
            # 验证输入参数
            if not video_url.strip() and not video_path.strip():
                raise ValueError("必须提供 video_url 或 video_path 中的一个")
            
            if video_url.strip() and video_path.strip():
                raise ValueError("不能同时提供 video_url 和 video_path，请只选择一个")

            # 确定输入视频文件路径
            input_video_path = None
            temp_downloaded_file = None
            
            if video_url.strip():
                # 从URL下载视频
                parsed_url = urlparse(video_url.strip())
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("无效的视频URL格式")
                
                # 尝试从URL获取文件扩展名
                url_path = parsed_url.path
                extension = self.get_video_extension(url_path)
                
                # 创建临时下载文件
                temp_downloaded_file = os.path.join(
                    self.output_dir, 
                    f"temp_download_{filename_prefix}_{os.getpid()}{extension}"
                )
                
                if not self.download_video(video_url.strip(), temp_downloaded_file):
                    raise RuntimeError("视频下载失败")
                
                input_video_path = temp_downloaded_file
                
            else:
                # 使用本地文件
                video_path = video_path.strip()
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"视频文件不存在: {video_path}")
                
                input_video_path = video_path

            # 获取输入视频的扩展名
            video_extension = self.get_video_extension(input_video_path)
            
            # 检查视频是否包含音频轨道
            print("检查视频是否包含音频轨道...")
            has_audio = self.has_audio_track(input_video_path)
            
            if not has_audio:
                print("视频不包含音频轨道，直接复制文件")
                # 生成输出文件名和路径
                output_filename, output_path = self.get_next_filename(filename_prefix, video_extension)
                
                # 直接复制文件
                import shutil
                shutil.copy2(input_video_path, output_path)
                
                # 清理临时文件
                if temp_downloaded_file and os.path.exists(temp_downloaded_file):
                    try:
                        os.remove(temp_downloaded_file)
                    except:
                        pass
                
                print(f"处理完成，输出文件: {output_path}")
                return (output_path,)
            
            # 生成输出文件名和路径
            output_filename, output_path = self.get_next_filename(filename_prefix, video_extension)
            
            # 移除音频
            if self.remove_audio_from_video(input_video_path, output_path):
                # 验证输出文件是否生成
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"音频移除成功，输出文件: {output_path}")
                    
                    # 清理临时文件
                    if temp_downloaded_file and os.path.exists(temp_downloaded_file):
                        try:
                            os.remove(temp_downloaded_file)
                        except:
                            pass
                    
                    return (output_path,)
                else:
                    raise RuntimeError("输出文件生成失败")
            else:
                raise RuntimeError("音频移除处理失败")

        except Exception as e:
            # 清理临时文件
            if 'temp_downloaded_file' in locals() and temp_downloaded_file and os.path.exists(temp_downloaded_file):
                try:
                    os.remove(temp_downloaded_file)
                except:
                    pass
            
            error_msg = f"视频音频移除失败: {str(e)}"
            print(error_msg)
            raise RuntimeError(error_msg)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "VideoAudioRemoverNode": VideoAudioRemoverNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoAudioRemoverNode": "Video Audio Remover"
} 