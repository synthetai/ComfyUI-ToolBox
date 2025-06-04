import os
import random
import shutil
import tempfile
import subprocess
import folder_paths
import glob
import re
from moviepy import VideoFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
import gc

class SmartVideoCombinerNode:
    """
    智能视频合成节点 - 将多个视频文件智能切片并合成为单个视频
    根据音频时长自动调整视频长度，支持多种拼接模式和过渡效果
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_paths": ("STRING", {"default": "", "multiline": True, "placeholder": "视频文件路径，每行一个"}),
                "audio_file": ("STRING", {"default": ""}),
                "filename_prefix": ("STRING", {"default": "smart_combined"}),
                "max_clip_duration": ("FLOAT", {"default": 5.0, "min": 1.0, "max": 30.0, "step": 0.5}),
                "aspect_ratio": (["16:9", "9:16", "1:1", "4:3", "3:4"], {"default": "16:9"}),
                "concat_mode": (["sequential", "random"], {"default": "random"}),
            },
            "optional": {
                "transition_mode": (["none", "fade_in", "fade_out", "shuffle"], {"default": "none"}),
                "video_width": ("INT", {"default": 1920, "min": 480, "max": 4096, "step": 16}),
                "video_height": ("INT", {"default": 1080, "min": 480, "max": 4096, "step": 16}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "combine_videos"
    CATEGORY = "ToolBox/Video"

    def combine_videos(self, video_paths, audio_file, filename_prefix, max_clip_duration,
                      aspect_ratio, concat_mode, transition_mode="none", 
                      video_width=1920, video_height=1080):
        """智能合成多个视频文件"""
        
        # 检查音频文件
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        # 解析视频路径
        video_list = [path.strip() for path in video_paths.strip().split('\n') if path.strip()]
        if not video_list:
            raise ValueError("请提供至少一个视频文件路径")
        
        # 验证视频文件存在
        for video_path in video_list:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 获取音频时长
        audio_clip = AudioFileClip(audio_file)
        audio_duration = audio_clip.duration
        audio_clip.close()
        
        print(f"音频时长: {audio_duration:.2f}秒")
        print(f"最大片段时长: {max_clip_duration}秒")
        
        # 解析目标分辨率
        if aspect_ratio == "16:9":
            target_width, target_height = 1920, 1080
        elif aspect_ratio == "9:16":
            target_width, target_height = 1080, 1920
        elif aspect_ratio == "1:1":
            target_width, target_height = 1080, 1080
        elif aspect_ratio == "4:3":
            target_width, target_height = 1440, 1080
        elif aspect_ratio == "3:4":
            target_width, target_height = 1080, 1440
        else:
            target_width, target_height = video_width, video_height
        
        # 获取输出目录
        output_dir = folder_paths.get_output_directory()
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        output_filename = self._generate_filename(output_dir, filename_prefix)
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            # 创建视频片段
            subclips = self._create_subclips(video_list, max_clip_duration, concat_mode)
            
            # 处理并合成视频片段
            final_video_path = self._process_and_combine_clips(
                subclips, audio_file, audio_duration, target_width, target_height,
                transition_mode, output_path
            )
            
            return (os.path.abspath(final_video_path),)
            
        except Exception as e:
            print(f"视频合成失败: {str(e)}")
            raise Exception(f"视频合成失败: {str(e)}")

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

    def _create_subclips(self, video_list, max_clip_duration, concat_mode):
        """创建视频子片段"""
        subclips = []
        
        for video_path in video_list:
            # 获取视频信息
            clip = VideoFileClip(video_path)
            clip_duration = clip.duration
            clip_w, clip_h = clip.size
            clip.close()
            
            # 按最大时长切片
            start_time = 0
            while start_time < clip_duration:
                end_time = min(start_time + max_clip_duration, clip_duration)
                
                if clip_duration - start_time >= max_clip_duration:
                    subclips.append({
                        'file_path': video_path,
                        'start_time': start_time,
                        'end_time': end_time,
                        'width': clip_w,
                        'height': clip_h,
                        'duration': end_time - start_time
                    })
                
                start_time = end_time
                
                if concat_mode == "sequential":
                    break
        
        # 随机打乱顺序
        if concat_mode == "random":
            random.shuffle(subclips)
        
        print(f"创建了 {len(subclips)} 个视频片段")
        return subclips

    def _process_and_combine_clips(self, subclips, audio_file, audio_duration, 
                                 target_width, target_height, transition_mode, output_path):
        """处理并合成视频片段"""
        
        processed_clips = []
        current_duration = 0
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 处理每个片段
            for i, subclip in enumerate(subclips):
                if current_duration >= audio_duration:
                    break
                
                print(f"处理片段 {i+1}/{len(subclips)}")
                
                # 加载并裁剪视频片段
                clip = VideoFileClip(subclip['file_path']).subclipped(
                    subclip['start_time'], subclip['end_time']
                )
                
                # 调整视频尺寸
                clip = self._resize_clip(clip, target_width, target_height)
                
                # 应用过渡效果
                if transition_mode != "none":
                    clip = self._apply_transition(clip, transition_mode)
                
                # 保存临时文件
                temp_file = os.path.join(temp_dir, f"clip_{i:04d}.mp4")
                clip.write_videofile(temp_file, logger=None, fps=30, codec='libx264')
                
                processed_clips.append(temp_file)
                current_duration += clip.duration
                
                clip.close()
                del clip
                gc.collect()
            
            # 如果视频时长不够，循环添加片段
            if current_duration < audio_duration:
                print(f"视频时长不足，循环添加片段")
                base_clips = processed_clips.copy()
                while current_duration < audio_duration:
                    for clip_file in base_clips:
                        if current_duration >= audio_duration:
                            break
                        processed_clips.append(clip_file)
                        # 简单估算时长增加
                        current_duration += 5  # 假设每个片段5秒
            
            # 合成最终视频
            self._merge_clips_with_audio(processed_clips, audio_file, output_path)
            
            return output_path
            
        finally:
            # 清理临时文件
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _resize_clip(self, clip, target_width, target_height):
        """调整视频片段尺寸"""
        clip_w, clip_h = clip.size
        
        if clip_w == target_width and clip_h == target_height:
            return clip
        
        clip_ratio = clip_w / clip_h
        target_ratio = target_width / target_height
        
        if abs(clip_ratio - target_ratio) < 0.01:  # 比例接近，直接缩放
            return clip.resized(new_size=(target_width, target_height))
        else:
            # 比例不同，添加黑边
            if clip_ratio > target_ratio:
                scale_factor = target_width / clip_w
            else:
                scale_factor = target_height / clip_h
            
            new_width = int(clip_w * scale_factor)
            new_height = int(clip_h * scale_factor)
            
            background = ColorClip(
                size=(target_width, target_height), 
                color=(0, 0, 0)
            ).with_duration(clip.duration)
            
            clip_resized = clip.resized(new_size=(new_width, new_height)).with_position("center")
            
            return CompositeVideoClip([background, clip_resized])

    def _apply_transition(self, clip, transition_mode):
        """应用过渡效果"""
        if transition_mode == "fade_in":
            return clip.fadein(1.0)
        elif transition_mode == "fade_out":
            return clip.fadeout(1.0)
        elif transition_mode == "shuffle":
            # 随机选择效果
            effects = ["fade_in", "fade_out"]
            chosen_effect = random.choice(effects)
            return self._apply_transition(clip, chosen_effect)
        
        return clip

    def _merge_clips_with_audio(self, clip_files, audio_file, output_path):
        """合并视频片段并添加音频"""
        
        # 加载所有视频片段
        video_clips = [VideoFileClip(clip_file) for clip_file in clip_files]
        
        # 合并视频
        final_video = concatenate_videoclips(video_clips)
        
        # 添加音频
        audio_clip = AudioFileClip(audio_file)
        final_video = final_video.with_audio(audio_clip)
        
        # 确保视频时长与音频匹配
        if final_video.duration > audio_clip.duration:
            final_video = final_video.subclipped(0, audio_clip.duration)
        
        # 输出最终视频
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            logger=None
        )
        
        # 清理资源
        for clip in video_clips:
            clip.close()
        final_video.close()
        audio_clip.close()

# 节点注册
NODE_CLASS_MAPPINGS = {
    "SmartVideoCombinerNode": SmartVideoCombinerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SmartVideoCombinerNode": "Smart Video Combiner"
} 