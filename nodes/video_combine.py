import os
import subprocess
import shutil
import tempfile
from datetime import datetime
import folder_paths
import glob
import re
from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, vfx

class VideoCombineNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_file": ("STRING", {"default": ""}),
                "audio_file": ("STRING", {"default": ""}),
                "filename_prefix": ("STRING", {"default": "output"}),
                "audio_handling": (["cut off audio", "bounce video", "loop video"], {"default": "bounce video"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "combine_video_audio"
    CATEGORY = "ToolBox/Video Combine"

    def combine_video_audio(self, video_file, audio_file, filename_prefix, audio_handling):
        # 检查文件是否存在
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"视频文件不存在: {video_file}")
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
            
        # 获取ComfyUI的output目录
        output_dir = folder_paths.get_output_directory()
        # 确保output_dir是绝对路径
        output_dir = os.path.abspath(output_dir)
        print(f"输出目录: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成不会重复的文件名
        output_filename = self._generate_filename(output_dir, filename_prefix)
        output_path = os.path.join(output_dir, output_filename)
        print(f"输出文件路径: {output_path}")
        
        # 检查音频和视频的时长
        video_duration = self._get_duration(video_file)
        audio_duration = self._get_duration(audio_file)
        
        if audio_duration <= video_duration:
            # 如果音频比视频短或相等，直接合并
            self._merge_audio_video(video_file, audio_file, output_path)
        else:
            # 根据选择的处理方式处理长音频
            if audio_handling == "cut off audio":
                # 截断音频与视频时长保持一致
                self._merge_audio_video_with_truncated_audio(video_file, audio_file, output_path)
            elif audio_handling == "bounce video":
                # 使用正/反向交替播放扩展视频
                with tempfile.TemporaryDirectory() as temp_dir:
                    extended_video = self._extend_video_alternate(video_file, audio_duration, temp_dir)
                    self._merge_audio_video(extended_video, audio_file, output_path)
            elif audio_handling == "loop video":
                # 循环播放视频
                with tempfile.TemporaryDirectory() as temp_dir:
                    extended_video = self._extend_video_loop(video_file, audio_duration, temp_dir)
                    self._merge_audio_video(extended_video, audio_file, output_path)
        
        # 使用最终的绝对路径
        final_path = os.path.abspath(output_path)
        
        # 检查文件是否已经成功生成
        if os.path.exists(final_path):
            print(f"文件已成功生成: {final_path}")
        else:
            print(f"警告: 文件未找到: {final_path}")
                
        # 调试信息
        print(f"最终返回路径: {final_path}")
        
        # ComfyUI节点需要返回元组，即使只有一个值
        # 这是关键修改，确保返回的是元组而不是单个字符串
        return (final_path,)
    
    def _generate_filename(self, output_dir, prefix):
        """生成不会重复的递增编号文件名"""
        # 查找同一前缀的所有文件
        pattern = os.path.join(output_dir, f"{prefix}_????.mp4")
        existing_files = glob.glob(pattern)
        
        # 如果没有同名文件，从0001开始
        if not existing_files:
            return f"{prefix}_0001.mp4"
        
        # 找出最大的编号
        max_number = 0
        for file in existing_files:
            match = re.search(r'_(\d{4})\.mp4$', file)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
        
        # 新编号是最大编号+1
        new_number = max_number + 1
        return f"{prefix}_{new_number:04d}.mp4"
    
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
    
    def _extend_video_alternate(self, video_file, target_duration, temp_dir):
        """通过正向和反向播放交替扩展视频至目标时长"""
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
    
    def _extend_video_loop(self, video_file, target_duration, temp_dir):
        """通过循环播放扩展视频至目标时长"""
        original_duration = self._get_duration(video_file)
        
        # 创建片段列表文件
        segments_file = os.path.join(temp_dir, "segments.txt")
        with open(segments_file, "w") as f:
            current_duration = 0
            
            while current_duration < target_duration:
                # 循环添加相同视频
                f.write(f"file '{video_file}'\n")
                current_duration += original_duration
        
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
    
    def _merge_audio_video_with_truncated_audio(self, video_file, audio_file, output_file):
        """合并视频与截断后的音频"""
        # 获取视频时长
        video_duration = self._get_duration(video_file)
        
        # 直接使用ffmpeg将视频和截断的音频合并为一个文件
        # 使用-shortest参数确保输出时长与视频相同，音频将被截断
        subprocess.run([
            "ffmpeg", "-y", "-i", video_file, "-i", audio_file,
            "-map", "0:v", "-map", "1:a", 
            "-c:v", "copy", "-c:a", "aac",
            "-shortest", output_file
        ], check=True)
    
    def _merge_audio_video(self, video_file, audio_file, output_file):
        """合并音频与视频"""
        subprocess.run([
            "ffmpeg", "-y", "-i", video_file, "-i", audio_file,
            "-map", "0:v", "-map", "1:a", 
            "-c:v", "copy", "-c:a", "aac", output_file
        ], check=True) 