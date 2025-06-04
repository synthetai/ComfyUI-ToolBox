import os
import random
import tempfile
import folder_paths
import glob
import re
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip, afx
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import Image, ImageFont, ImageDraw
import numpy as np

class VideoSubtitleGeneratorNode:
    """
    视频字幕生成节点 - 为视频添加字幕、背景音乐等效果
    支持SRT字幕文件、自定义字体样式、多种字幕位置等
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_file": ("STRING", {"default": ""}),
                "audio_file": ("STRING", {"default": ""}),
                "filename_prefix": ("STRING", {"default": "subtitle_video"}),
                "subtitle_enabled": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "subtitle_file": ("STRING", {"default": ""}),
                "subtitle_text": ("STRING", {"default": "", "multiline": True, "placeholder": "直接输入字幕文本（每行一句，格式：开始时间-结束时间 文本内容）"}),
                "font_size": ("INT", {"default": 40, "min": 12, "max": 200, "step": 2}),
                "font_color": ("STRING", {"default": "white"}),
                "bg_color": ("STRING", {"default": "transparent"}),
                "stroke_color": ("STRING", {"default": "black"}),
                "stroke_width": ("INT", {"default": 2, "min": 0, "max": 10, "step": 1}),
                "subtitle_position": (["bottom", "top", "center", "custom"], {"default": "bottom"}),
                "custom_position": ("FLOAT", {"default": 85.0, "min": 0.0, "max": 100.0, "step": 1.0}),
                "bgm_file": ("STRING", {"default": ""}),
                "bgm_volume": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 1.0, "step": 0.1}),
                "voice_volume": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "generate_subtitle_video"
    CATEGORY = "ToolBox/Video"

    def generate_subtitle_video(self, video_file, audio_file, filename_prefix, subtitle_enabled,
                              subtitle_file="", subtitle_text="", font_size=40, font_color="white",
                              bg_color="transparent", stroke_color="black", stroke_width=2,
                              subtitle_position="bottom", custom_position=85.0,
                              bgm_file="", bgm_volume=0.3, voice_volume=1.0):
        """生成带字幕的视频"""
        
        # 验证输入文件
        if not os.path.exists(video_file):
            raise FileNotFoundError(f"视频文件不存在: {video_file}")
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        # 获取输出目录
        output_dir = folder_paths.get_output_directory()
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        output_filename = self._generate_filename(output_dir, filename_prefix)
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            # 加载视频（移除音频）
            video_clip = VideoFileClip(video_file).without_audio()
            video_width, video_height = video_clip.size
            
            print(f"视频尺寸: {video_width}x{video_height}")
            
            # 加载主音频
            audio_clip = AudioFileClip(audio_file)
            if voice_volume != 1.0:
                audio_clip = audio_clip.with_effects([afx.MultiplyVolume(voice_volume)])
            
            # 处理字幕
            if subtitle_enabled:
                if subtitle_file and os.path.exists(subtitle_file):
                    # 使用SRT字幕文件
                    video_clip = self._add_srt_subtitles(
                        video_clip, subtitle_file, font_size, font_color, 
                        bg_color, stroke_color, stroke_width, subtitle_position, 
                        custom_position, video_width, video_height
                    )
                elif subtitle_text.strip():
                    # 使用文本字幕
                    video_clip = self._add_text_subtitles(
                        video_clip, subtitle_text, font_size, font_color,
                        bg_color, stroke_color, stroke_width, subtitle_position,
                        custom_position, video_width, video_height
                    )
            
            # 处理背景音乐
            if bgm_file and os.path.exists(bgm_file):
                bgm_clip = AudioFileClip(bgm_file)
                # 调整背景音乐音量和时长
                bgm_clip = bgm_clip.with_effects([
                    afx.MultiplyVolume(bgm_volume),
                    afx.AudioFadeOut(3),
                    afx.AudioLoop(duration=video_clip.duration)
                ])
                # 合成音频
                audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
            
            # 为视频添加音频
            video_clip = video_clip.with_audio(audio_clip)
            
            # 输出最终视频
            video_clip.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            
            # 清理资源
            video_clip.close()
            
            return (os.path.abspath(output_path),)
            
        except Exception as e:
            print(f"字幕视频生成失败: {str(e)}")
            raise Exception(f"字幕视频生成失败: {str(e)}")

    def _generate_filename(self, output_dir, prefix):
        """生成不重复的文件名"""
        pattern = os.path.join(output_dir, f"{prefix}_????.mp4")
        existing_files = glob.glob(pattern)
        
        if not existing_files:
            return f"{prefix}_0001.mp4"
        
        max_number = 0
        for file in existing_files:
            match = re.search(r'_(\d{4})\.mp4$', file)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
        
        new_number = max_number + 1
        return f"{prefix}_{new_number:04d}.mp4"

    def _add_srt_subtitles(self, video_clip, subtitle_file, font_size, font_color,
                          bg_color, stroke_color, stroke_width, subtitle_position,
                          custom_position, video_width, video_height):
        """添加SRT字幕文件"""
        
        def make_textclip(text):
            return TextClip(
                text=text,
                font_size=font_size,
                color=font_color,
                bg_color=None if bg_color == "transparent" else bg_color,
                stroke_color=stroke_color,
                stroke_width=stroke_width
            )
        
        # 加载字幕
        subtitles = SubtitlesClip(
            subtitles=subtitle_file,
            encoding="utf-8",
            make_textclip=make_textclip
        )
        
        # 创建字幕片段列表
        text_clips = []
        for item in subtitles.subtitles:
            clip = self._create_text_clip(
                item, font_size, font_color, bg_color, stroke_color, stroke_width,
                subtitle_position, custom_position, video_width, video_height
            )
            text_clips.append(clip)
        
        # 合成视频和字幕
        if text_clips:
            return CompositeVideoClip([video_clip, *text_clips])
        
        return video_clip

    def _add_text_subtitles(self, video_clip, subtitle_text, font_size, font_color,
                           bg_color, stroke_color, stroke_width, subtitle_position,
                           custom_position, video_width, video_height):
        """添加文本字幕"""
        
        # 解析字幕文本 (格式: "0.0-5.0 这是第一句字幕")
        text_clips = []
        lines = [line.strip() for line in subtitle_text.strip().split('\n') if line.strip()]
        
        for line in lines:
            try:
                # 解析时间和文本
                if ' ' not in line:
                    continue
                    
                time_part, text_part = line.split(' ', 1)
                if '-' not in time_part:
                    continue
                    
                start_time, end_time = time_part.split('-')
                start_time = float(start_time)
                end_time = float(end_time)
                
                # 创建字幕片段
                subtitle_item = ((start_time, end_time), text_part)
                clip = self._create_text_clip(
                    subtitle_item, font_size, font_color, bg_color, stroke_color, stroke_width,
                    subtitle_position, custom_position, video_width, video_height
                )
                text_clips.append(clip)
                
            except (ValueError, IndexError) as e:
                print(f"跳过无效字幕行: {line} (错误: {e})")
                continue
        
        # 合成视频和字幕
        if text_clips:
            return CompositeVideoClip([video_clip, *text_clips])
        
        return video_clip

    def _create_text_clip(self, subtitle_item, font_size, font_color, bg_color,
                         stroke_color, stroke_width, subtitle_position, custom_position,
                         video_width, video_height):
        """创建单个字幕片段"""
        
        time_info, text = subtitle_item
        start_time, end_time = time_info
        duration = end_time - start_time
        
        # 处理文本换行
        wrapped_text = self._wrap_text(text, video_width * 0.9, font_size)
        
        # 创建文本片段
        text_clip = TextClip(
            text=wrapped_text,
            font_size=font_size,
            color=font_color,
            bg_color=None if bg_color == "transparent" else bg_color,
            stroke_color=stroke_color,
            stroke_width=stroke_width
        )
        
        # 设置时间
        text_clip = text_clip.with_start(start_time).with_end(end_time).with_duration(duration)
        
        # 设置位置
        if subtitle_position == "bottom":
            text_clip = text_clip.with_position(("center", video_height * 0.9 - text_clip.h))
        elif subtitle_position == "top":
            text_clip = text_clip.with_position(("center", video_height * 0.05))
        elif subtitle_position == "center":
            text_clip = text_clip.with_position(("center", "center"))
        elif subtitle_position == "custom":
            margin = 10
            max_y = video_height - text_clip.h - margin
            min_y = margin
            custom_y = (video_height - text_clip.h) * (custom_position / 100)
            custom_y = max(min_y, min(custom_y, max_y))
            text_clip = text_clip.with_position(("center", custom_y))
        
        return text_clip

    def _wrap_text(self, text, max_width, font_size):
        """智能文本换行"""
        # 简单的按字符数换行
        chars_per_line = int(max_width / (font_size * 0.6))  # 估算每行字符数
        
        if len(text) <= chars_per_line:
            return text
        
        # 按词分割（中英文兼容）
        words = []
        current_word = ""
        
        for char in text:
            if char in [' ', '，', '。', '！', '？', ',', '.', '!', '?']:
                if current_word:
                    words.append(current_word)
                    current_word = ""
                words.append(char)
            else:
                current_word += char
        
        if current_word:
            words.append(current_word)
        
        # 组装行
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + word) <= chars_per_line:
                current_line += word
            else:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = word if word not in [' '] else ""
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(current_line.strip())
        
        return '\n'.join([line for line in lines if line])

# 节点注册
NODE_CLASS_MAPPINGS = {
    "VideoSubtitleGeneratorNode": VideoSubtitleGeneratorNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoSubtitleGeneratorNode": "Video Subtitle Generator"
} 