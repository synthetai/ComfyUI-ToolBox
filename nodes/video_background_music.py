import os
import subprocess
import requests
import tempfile
import folder_paths
from urllib.parse import urlparse
import re
import shutil

class VideoBackgroundMusicNode:
    """
    视频背景音乐节点 - 为视频添加背景音乐
    支持保留原视频声音和字幕，可自定义背景音乐音量
    支持URL下载和本地文件输入
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename_prefix": ("STRING", {
                    "default": "bgm_video", 
                    "multiline": False,
                    "tooltip": "增加背景音乐后的视频文件名前缀"
                }),
                "bgm_volume": ("FLOAT", {
                    "default": 0.3, 
                    "min": 0.0, 
                    "max": 1.0, 
                    "step": 0.1,
                    "tooltip": "背景音乐音量大小（0.0-1.0）"
                }),
            },
            "optional": {
                "output_dir": ("STRING", {
                    "default": "", 
                    "multiline": False,
                    "tooltip": "自定义输出目录，留空则使用ComfyUI默认output目录"
                }),
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
                "audio_url": ("STRING", {
                    "default": "", 
                    "multiline": False,
                    "tooltip": "背景音乐文件的HTTP下载链接"
                }),
                "audio_path": ("STRING", {
                    "default": "", 
                    "multiline": False,
                    "tooltip": "本地背景音乐文件路径"
                }),
                "original_audio_volume": ("FLOAT", {
                    "default": 1.0, 
                    "min": 0.0, 
                    "max": 2.0, 
                    "step": 0.1,
                    "tooltip": "原视频音频音量大小（0.0-2.0）"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "add_background_music"
    CATEGORY = "ToolBox/Video"
    DESCRIPTION = "为视频添加背景音乐，保留原视频声音和字幕，支持URL下载和本地文件处理"

    def __init__(self):
        self.base_output_dir = folder_paths.get_output_directory()

    def _get_output_directory(self, output_dir):
        """获取输出目录"""
        if output_dir.strip() == "":
            # 如果用户未定义，则使用 ComfyUI 的 output 目录
            return self.base_output_dir
        elif os.path.isabs(output_dir):
            # 如果是绝对路径，直接使用
            return output_dir
        else:
            # 相对路径基于 ComfyUI 的 output 目录
            return os.path.join(self.base_output_dir, output_dir)

    def download_file(self, url, output_path, file_type="文件"):
        """下载文件到指定路径"""
        try:
            print(f"开始下载{file_type}: {url}")
            
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
            
            print(f"{file_type}下载完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"下载{file_type}失败: {str(e)}")
            return False

    def get_media_duration(self, media_path):
        """获取媒体文件时长"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', media_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"ffprobe失败: {result.stderr}")
                return 0
            
            import json
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
            
        except Exception as e:
            print(f"获取媒体时长失败: {str(e)}")
            return 0

    def get_next_filename(self, output_dir, prefix, extension=".mp4"):
        """生成下一个可用的文件名"""
        counter = 1
        while True:
            filename = f"{prefix}_{counter:04d}{extension}"
            full_path = os.path.join(output_dir, filename)
            if not os.path.exists(full_path):
                return filename, full_path
            counter += 1

    def get_file_extension(self, file_path):
        """获取文件扩展名"""
        _, ext = os.path.splitext(file_path)
        return ext if ext else ".mp4"

    def add_background_music_to_video(self, video_path, audio_path, output_path, 
                                     bgm_volume=0.3, original_audio_volume=1.0):
        """使用FFmpeg为视频添加背景音乐"""
        try:
            print(f"开始为视频添加背景音乐")
            print(f"视频文件: {video_path}")
            print(f"背景音乐: {audio_path}")
            print(f"输出文件: {output_path}")
            print(f"背景音乐音量: {bgm_volume}")
            print(f"原音频音量: {original_audio_volume}")
            
            # 获取视频和音频的时长
            video_duration = self.get_media_duration(video_path)
            audio_duration = self.get_media_duration(audio_path)
            
            if video_duration <= 0:
                raise ValueError("无法获取视频时长")
            if audio_duration <= 0:
                raise ValueError("无法获取音频时长")
            
            print(f"视频时长: {video_duration:.2f}秒")
            print(f"音频时长: {audio_duration:.2f}秒")
            
            # 构建FFmpeg命令
            cmd = [
                'ffmpeg', '-y',  # -y 覆盖输出文件
                '-i', video_path,  # 输入视频
                '-i', audio_path,  # 输入背景音乐
            ]
            
            # 音频处理滤镜
            if audio_duration < video_duration:
                # 如果背景音乐比视频短，循环播放背景音乐
                audio_filter = f"[1:a]aloop=loop=-1:size=2e+09,atrim=duration={video_duration},volume={bgm_volume}[bgm]"
            else:
                # 如果背景音乐比视频长或相等，截取到视频长度
                audio_filter = f"[1:a]atrim=duration={video_duration},volume={bgm_volume}[bgm]"
            
            # 原音频音量调整
            if original_audio_volume != 1.0:
                original_audio_filter = f"[0:a]volume={original_audio_volume}[orig]"
                mix_filter = "[orig][bgm]amix=inputs=2:duration=first:dropout_transition=3[mixed]"
                filter_complex = f"{original_audio_filter};{audio_filter};{mix_filter}"
            else:
                mix_filter = "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[mixed]"
                filter_complex = f"{audio_filter};{mix_filter}"
            
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '0:v',  # 映射视频流
                '-map', '[mixed]',  # 映射混合音频流
                '-c:v', 'copy',  # 复制视频流，不重新编码
                '-c:a', 'aac',  # 音频编码为AAC
                '-b:a', '192k',  # 音频比特率
                '-shortest',  # 以最短流为准
                output_path
            ])
            
            print("执行FFmpeg命令...")
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                print(f"背景音乐添加完成: {output_path}")
                return True
            else:
                print(f"FFmpeg错误: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("背景音乐添加超时")
            return False
        except Exception as e:
            print(f"添加背景音乐时出错: {str(e)}")
            return False

    def add_background_music(self, filename_prefix, bgm_volume=0.3, output_dir="", 
                           video_url="", video_path="", audio_url="", audio_path="", 
                           original_audio_volume=1.0):
        try:
            # 验证输入参数
            if not video_url.strip() and not video_path.strip():
                raise ValueError("必须提供 video_url 或 video_path 中的一个")
            
            if video_url.strip() and video_path.strip():
                raise ValueError("不能同时提供 video_url 和 video_path，请只选择一个")
            
            if not audio_url.strip() and not audio_path.strip():
                raise ValueError("必须提供 audio_url 或 audio_path 中的一个")
            
            if audio_url.strip() and audio_path.strip():
                raise ValueError("不能同时提供 audio_url 和 audio_path，请只选择一个")

            # 获取输出目录
            output_directory = self._get_output_directory(output_dir)
            os.makedirs(output_directory, exist_ok=True)
            
            # 确定输入视频文件路径
            input_video_path = None
            temp_video_file = None
            
            if video_url.strip():
                # 从URL下载视频
                parsed_url = urlparse(video_url.strip())
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("无效的视频URL格式")
                
                # 尝试从URL获取文件扩展名
                url_path = parsed_url.path
                extension = self.get_file_extension(url_path)
                
                # 创建临时下载文件
                temp_video_file = os.path.join(
                    output_directory, 
                    f"temp_video_{filename_prefix}_{os.getpid()}{extension}"
                )
                
                if not self.download_file(video_url.strip(), temp_video_file, "视频"):
                    raise RuntimeError("视频下载失败")
                
                input_video_path = temp_video_file
                
            else:
                # 使用本地视频文件
                video_path = video_path.strip()
                if not os.path.exists(video_path):
                    raise FileNotFoundError(f"视频文件不存在: {video_path}")
                
                input_video_path = video_path

            # 确定输入音频文件路径
            input_audio_path = None
            temp_audio_file = None
            
            if audio_url.strip():
                # 从URL下载音频
                parsed_url = urlparse(audio_url.strip())
                if not parsed_url.scheme or not parsed_url.netloc:
                    raise ValueError("无效的音频URL格式")
                
                # 尝试从URL获取文件扩展名
                url_path = parsed_url.path
                extension = self.get_file_extension(url_path)
                if extension in [".mp4", ".avi", ".mov", ".mkv"]:
                    extension = ".mp3"  # 音频文件使用音频扩展名
                
                # 创建临时下载文件
                temp_audio_file = os.path.join(
                    output_directory, 
                    f"temp_audio_{filename_prefix}_{os.getpid()}{extension}"
                )
                
                if not self.download_file(audio_url.strip(), temp_audio_file, "音频"):
                    raise RuntimeError("音频下载失败")
                
                input_audio_path = temp_audio_file
                
            else:
                # 使用本地音频文件
                audio_path = audio_path.strip()
                if not os.path.exists(audio_path):
                    raise FileNotFoundError(f"音频文件不存在: {audio_path}")
                
                input_audio_path = audio_path

            # 获取输入视频的扩展名
            video_extension = self.get_file_extension(input_video_path)
            
            # 生成输出文件名和路径
            output_filename, output_path = self.get_next_filename(
                output_directory, filename_prefix, video_extension
            )
            
            # 添加背景音乐
            if self.add_background_music_to_video(
                input_video_path, input_audio_path, output_path, 
                bgm_volume, original_audio_volume
            ):
                # 验证输出文件是否生成
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"背景音乐添加成功，输出文件: {output_path}")
                    
                    # 清理临时文件
                    if temp_video_file and os.path.exists(temp_video_file):
                        try:
                            os.remove(temp_video_file)
                        except:
                            pass
                    
                    if temp_audio_file and os.path.exists(temp_audio_file):
                        try:
                            os.remove(temp_audio_file)
                        except:
                            pass
                    
                    return (os.path.abspath(output_path),)
                else:
                    raise RuntimeError("输出文件生成失败")
            else:
                raise RuntimeError("背景音乐添加处理失败")
                
        except Exception as e:
            # 清理临时文件
            if 'temp_video_file' in locals() and temp_video_file and os.path.exists(temp_video_file):
                try:
                    os.remove(temp_video_file)
                except:
                    pass
            
            if 'temp_audio_file' in locals() and temp_audio_file and os.path.exists(temp_audio_file):
                try:
                    os.remove(temp_audio_file)
                except:
                    pass
            
            print(f"处理失败: {str(e)}")
            raise


# 节点映射
NODE_CLASS_MAPPINGS = {
    "VideoBackgroundMusicNode": VideoBackgroundMusicNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoBackgroundMusicNode": "Video Background Music"
} 