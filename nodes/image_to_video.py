import os
import tempfile
import shutil
import folder_paths
import glob
import re
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image
import numpy as np
import gc

class ImageToVideoNode:
    """
    图片转视频节点 - 将静态图片转换为动态视频
    支持缩放效果、自定义时长、分辨率检查等功能
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_paths": ("STRING", {"default": "", "multiline": True, "placeholder": "图片文件路径，每行一个"}),
                "filename_prefix": ("STRING", {"default": "image_video"}),
                "clip_duration": ("FLOAT", {"default": 3.0, "min": 0.5, "max": 30.0, "step": 0.1}),
                "output_width": ("INT", {"default": 1920, "min": 480, "max": 4096, "step": 16}),
                "output_height": ("INT", {"default": 1080, "min": 480, "max": 4096, "step": 16}),
            },
            "optional": {
                "zoom_effect": ("BOOLEAN", {"default": True}),
                "zoom_factor": ("FLOAT", {"default": 1.2, "min": 1.0, "max": 2.0, "step": 0.1}),
                "min_resolution": ("INT", {"default": 480, "min": 240, "max": 1920, "step": 16}),
                "combine_videos": ("BOOLEAN", {"default": True}),
                "fps": ("INT", {"default": 30, "min": 15, "max": 60, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "convert_images_to_video"
    CATEGORY = "ToolBox/Video"

    def convert_images_to_video(self, image_paths, filename_prefix, clip_duration, 
                               output_width, output_height, zoom_effect=True, 
                               zoom_factor=1.2, min_resolution=480, combine_videos=True, fps=30):
        """将图片转换为视频"""
        
        # 解析图片路径
        image_list = [path.strip() for path in image_paths.strip().split('\n') if path.strip()]
        if not image_list:
            raise ValueError("请提供至少一个图片文件路径")
        
        # 验证图片文件存在
        valid_images = []
        for image_path in image_list:
            if not os.path.exists(image_path):
                print(f"警告: 图片文件不存在: {image_path}")
                continue
                
            # 检查分辨率
            try:
                with Image.open(image_path) as img:
                    width, height = img.size
                    if width < min_resolution or height < min_resolution:
                        print(f"警告: 图片分辨率过低 {width}x{height} (最低要求: {min_resolution}x{min_resolution}): {image_path}")
                        continue
                    valid_images.append(image_path)
            except Exception as e:
                print(f"警告: 无法读取图片 {image_path}: {e}")
                continue
        
        if not valid_images:
            raise ValueError("没有有效的图片文件")
        
        print(f"找到 {len(valid_images)} 个有效图片文件")
        
        # 获取输出目录
        output_dir = folder_paths.get_output_directory()
        os.makedirs(output_dir, exist_ok=True)
        
        if combine_videos:
            # 合并所有图片为一个视频
            output_filename = self._generate_filename(output_dir, filename_prefix)
            output_path = os.path.join(output_dir, output_filename)
            
            self._create_combined_video(
                valid_images, output_path, clip_duration, output_width, output_height,
                zoom_effect, zoom_factor, fps
            )
            
            return (os.path.abspath(output_path),)
        else:
            # 为每个图片生成单独的视频
            video_paths = []
            for i, image_path in enumerate(valid_images):
                output_filename = self._generate_filename(output_dir, f"{filename_prefix}_{i+1:03d}")
                output_path = os.path.join(output_dir, output_filename)
                
                self._create_single_video(
                    image_path, output_path, clip_duration, output_width, output_height,
                    zoom_effect, zoom_factor, fps
                )
                
                video_paths.append(os.path.abspath(output_path))
            
            # 返回第一个视频路径（如果需要返回所有路径，需要修改返回类型）
            return (video_paths[0] if video_paths else "",)

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

    def _create_single_video(self, image_path, output_path, clip_duration, 
                           output_width, output_height, zoom_effect, zoom_factor, fps):
        """为单个图片创建视频"""
        
        try:
            # 创建图片剪辑
            clip = ImageClip(image_path).with_duration(clip_duration).with_position("center")
            
            # 调整图片尺寸
            clip = self._resize_image_clip(clip, output_width, output_height)
            
            # 应用缩放效果
            if zoom_effect:
                clip = self._apply_zoom_effect(clip, zoom_factor, clip_duration)
            
            # 创建最终视频
            final_clip = concatenate_videoclips([clip])
            
            # 输出视频
            final_clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                logger=None
            )
            
            # 清理资源
            clip.close()
            final_clip.close()
            
            print(f"图片视频已保存: {output_path}")
            
        except Exception as e:
            print(f"处理图片失败 {image_path}: {str(e)}")
            raise

    def _create_combined_video(self, image_paths, output_path, clip_duration, 
                             output_width, output_height, zoom_effect, zoom_factor, fps):
        """创建合并的视频"""
        
        try:
            clips = []
            
            for image_path in image_paths:
                print(f"处理图片: {image_path}")
                
                # 创建图片剪辑
                clip = ImageClip(image_path).with_duration(clip_duration).with_position("center")
                
                # 调整图片尺寸
                clip = self._resize_image_clip(clip, output_width, output_height)
                
                # 应用缩放效果
                if zoom_effect:
                    clip = self._apply_zoom_effect(clip, zoom_factor, clip_duration)
                
                clips.append(clip)
            
            # 按顺序连接所有剪辑
            final_clip = concatenate_videoclips(clips)
            
            # 输出视频
            final_clip.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                logger=None
            )
            
            # 清理资源
            for clip in clips:
                clip.close()
            final_clip.close()
            
            print(f"合并视频已保存: {output_path}")
            
        except Exception as e:
            print(f"创建合并视频失败: {str(e)}")
            raise

    def _resize_image_clip(self, clip, target_width, target_height):
        """调整图片剪辑尺寸"""
        
        # 获取原始尺寸
        clip_w, clip_h = clip.size
        
        # 计算缩放比例
        scale_w = target_width / clip_w
        scale_h = target_height / clip_h
        
        # 选择较小的缩放比例以保持宽高比
        scale = min(scale_w, scale_h)
        
        # 计算新尺寸
        new_width = int(clip_w * scale)
        new_height = int(clip_h * scale)
        
        # 调整图片尺寸
        resized_clip = clip.resized(new_size=(new_width, new_height))
        
        # 如果需要，添加黑边使其符合目标尺寸
        if new_width != target_width or new_height != target_height:
            from moviepy.editor import ColorClip, CompositeVideoClip
            
            # 创建黑色背景
            background = ColorClip(
                size=(target_width, target_height), 
                color=(0, 0, 0)
            ).with_duration(clip.duration)
            
            # 将调整后的图片居中放置在背景上
            resized_clip = resized_clip.with_position("center")
            
            # 合成最终剪辑
            return CompositeVideoClip([background, resized_clip])
        
        return resized_clip

    def _apply_zoom_effect(self, clip, zoom_factor, duration):
        """应用缩放效果"""
        
        def zoom_function(t):
            # 计算当前时间的缩放比例
            # 从1.0开始，逐渐缩放到zoom_factor
            progress = t / duration
            current_zoom = 1.0 + (zoom_factor - 1.0) * progress
            return current_zoom
        
        # 应用动态缩放
        zoomed_clip = clip.resized(zoom_function)
        
        return zoomed_clip

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageToVideoNode": ImageToVideoNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageToVideoNode": "Image to Video Converter"
} 