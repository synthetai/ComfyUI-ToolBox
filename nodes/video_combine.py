import os
import subprocess
import shutil
import tempfile
from datetime import datetime
import folder_paths

class VideoCombineNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_file": ("STRING", {"default": ""}),
                "audio_file": ("STRING", {"default": ""}),
                "filename_prefix": ("STRING", {"default": "output"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "combine_video_audio"
    CATEGORY = "ToolBox/Video Combine"

    def combine_video_audio(self, video_file, audio_file, filename_prefix):
        # 检查文件是否存在
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"视频文件不存在: {video_file}")
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
            
        # 获取ComfyUI的output目录
        output_dir = folder_paths.get_output_directory()
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        output_filename = f"{filename_prefix}_0001.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        # 检查音频和视频的时长
        video_duration = self._get_duration(video_file)
        audio_duration = self._get_duration(audio_file)
        
        if audio_duration <= video_duration:
            # 如果音频比视频短或相等，直接合并
            self._merge_audio_video(video_file, audio_file, output_path)
        else:
            # 如果音频比视频长，需要通过正向/反向播放来匹配音频长度
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 生成足够多的视频片段以匹配音频时长
                extended_video = self._extend_video(video_file, audio_duration, temp_dir)
                # 合并音频与扩展后的视频
                self._merge_audio_video(extended_video, audio_file, output_path)
                
        # 返回生成的文件绝对路径
        return os.path.abspath(output_path)
    
    def _get_duration(self, media_file):
        """获取媒体文件的时长（秒）"""
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            media_file
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    
    def _extend_video(self, video_file, target_duration, temp_dir):
        """通过正向和反向播放扩展视频至目标时长"""
        original_duration = self._get_duration(video_file)
        
        # 创建反向播放的视频
        reversed_video = os.path.join(temp_dir, "reversed.mp4")
        subprocess.run([
            "ffmpeg", "-i", video_file, "-vf", "reverse", 
            "-af", "areverse", reversed_video
        ], check=True)
        
        # 创建片段列表文件
        segments_file = os.path.join(temp_dir, "segments.txt")
        with open(segments_file, "w") as f:
            segments_count = 0
            current_duration = 0
            
            while current_duration < target_duration:
                if segments_count % 2 == 0:
                    # 正向片段
                    f.write(f"file '{video_file}'\n")
                    current_duration += original_duration
                else:
                    # 反向片段
                    f.write(f"file '{reversed_video}'\n")
                    current_duration += original_duration
                
                segments_count += 1
        
        # 合并所有片段
        extended_video = os.path.join(temp_dir, "extended.mp4")
        subprocess.run([
            "ffmpeg", "-f", "concat", "-safe", "0", 
            "-i", segments_file, "-c", "copy", extended_video
        ], check=True)
        
        # 裁剪到精确的时长
        final_extended = os.path.join(temp_dir, "final_extended.mp4")
        subprocess.run([
            "ffmpeg", "-i", extended_video, "-t", str(target_duration),
            "-c", "copy", final_extended
        ], check=True)
        
        return final_extended
    
    def _merge_audio_video(self, video_file, audio_file, output_file):
        """合并音频与视频"""
        subprocess.run([
            "ffmpeg", "-i", video_file, "-i", audio_file,
            "-map", "0:v", "-map", "1:a", 
            "-c:v", "copy", "-shortest", output_file
        ], check=True) 