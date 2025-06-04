import os
import random
import shutil
import tempfile
import subprocess
import folder_paths
import glob
import re
import itertools
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
import gc

class SmartVideoCombinerNode:
    """
    智能视频合成节点 - 从指定目录读取视频文件并智能切片合成为单个视频
    按照文件名顺序读取目录中的视频文件，根据音频时长自动调整视频长度
    支持多种视频格式、拼接模式和过渡效果
    
    功能特色：
    - 自动扫描指定目录中的视频文件
    - 按文件名排序确保合成顺序
    - 支持多种视频格式（mp4, avi, mov, mkv, flv, wmv等）
    - 智能切片和随机/顺序拼接模式
    - 多种过渡效果和视频比例支持
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_directory": ("STRING", {"default": "", "placeholder": "视频文件目录路径"}),
                "audio_file": ("STRING", {"default": ""}),
                "filename_prefix": ("STRING", {"default": "smart_combined"}),
                "max_clip_duration": ("FLOAT", {"default": 5.0, "min": 1.0, "max": 30.0, "step": 0.5}),
                "aspect_ratio": (["16:9", "9:16", "1:1", "4:3", "3:4"], {"default": "16:9"}),
                "concat_mode": (["sequential", "random"], {"default": "sequential"}),
            },
            "optional": {
                "transition_mode": (["none", "fade_in", "fade_out", "shuffle"], {"default": "none"}),
                "video_width": ("INT", {"default": 1920, "min": 480, "max": 4096, "step": 16}),
                "video_height": ("INT", {"default": 1080, "min": 480, "max": 4096, "step": 16}),
                "file_extensions": ("STRING", {"default": "mp4,avi,mov,mkv,flv,wmv", "placeholder": "支持的视频文件扩展名，用逗号分隔"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "combine_videos"
    CATEGORY = "ToolBox/Video"

    def combine_videos(self, video_directory, audio_file, filename_prefix, max_clip_duration,
                      aspect_ratio, concat_mode, transition_mode="none", 
                      video_width=1920, video_height=1080, file_extensions="mp4,avi,mov,mkv,flv,wmv"):
        """智能合成多个视频文件 - 按照原始逻辑实现"""
        
        # 检查视频目录
        if not os.path.exists(video_directory):
            raise FileNotFoundError(f"视频目录不存在: {video_directory}")
        
        if not os.path.isdir(video_directory):
            raise ValueError(f"路径不是一个目录: {video_directory}")
        
        # 检查音频文件
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        # 获取视频文件列表
        video_list = self._get_video_list(video_directory, file_extensions)
        if not video_list:
            raise ValueError(f"在目录 {video_directory} 中没有找到支持的视频文件")
        
        print(f"找到 {len(video_list)} 个视频文件:")
        for i, video_path in enumerate(video_list, 1):
            print(f"  {i}. {os.path.basename(video_path)}")
        
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
            # 按原始逻辑处理视频
            return self._combine_videos_original_logic(
                video_list, audio_file, audio_duration, target_width, target_height,
                max_clip_duration, concat_mode, transition_mode, output_path
            )
            
        except Exception as e:
            print(f"视频合成失败: {str(e)}")
            raise Exception(f"视频合成失败: {str(e)}")

    def _combine_videos_original_logic(self, video_paths, audio_file, audio_duration, 
                                     video_width, video_height, max_clip_duration, 
                                     concat_mode, transition_mode, combined_video_path):
        """按照原始代码逻辑实现视频合成"""
        
        output_dir = os.path.dirname(combined_video_path)
        
        # 1. 创建子片段列表
        subclipped_items = []
        for video_path in video_paths:
            clip = VideoFileClip(video_path)
            clip_duration = clip.duration
            clip_w, clip_h = clip.size
            self._close_clip(clip)
            
            start_time = 0
            while start_time < clip_duration:
                end_time = min(start_time + max_clip_duration, clip_duration)
                if clip_duration - start_time >= max_clip_duration:
                    subclipped_items.append({
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
        
        # 2. 随机打乱顺序（如果需要）
        if concat_mode == "random":
            random.shuffle(subclipped_items)
        
        print(f"创建了 {len(subclipped_items)} 个子片段")
        
        # 3. 逐个处理片段直到达到音频时长
        processed_clips = []
        video_duration = 0
        temp_files = []
        
        for i, subclipped_item in enumerate(subclipped_items):
            if video_duration >= audio_duration:
                break
                
            print(f"处理片段 {i+1}/{len(subclipped_items)}, 当前时长: {video_duration:.2f}s, 剩余: {audio_duration - video_duration:.2f}s")
            
            try:
                # 加载并处理片段
                print(f"  加载视频: {subclipped_item['file_path']}")
                print(f"  时间段: {subclipped_item['start_time']:.2f}s - {subclipped_item['end_time']:.2f}s")
                
                clip = VideoFileClip(subclipped_item['file_path']).subclip(
                    subclipped_item['start_time'], subclipped_item['end_time']
                )
                
                print(f"  片段时长: {clip.duration:.2f}s, 尺寸: {clip.size}")
                
                # 调整尺寸
                clip = self._resize_clip(clip, video_width, video_height)
                
                # 应用过渡效果
                if transition_mode != "none":
                    clip = self._apply_transition(clip, transition_mode)
                
                # 保存临时文件
                clip_file = os.path.join(output_dir, f"temp-clip-{i+1}.mp4")
                print(f"  保存临时文件: {clip_file}")
                
                clip.write_videofile(clip_file, logger=None, fps=30, codec='libx264')
                
                processed_clips.append({
                    'file_path': clip_file,
                    'duration': clip.duration
                })
                temp_files.append(clip_file)
                video_duration += clip.duration
                
                print(f"  处理完成，累计时长: {video_duration:.2f}s")
                
                self._close_clip(clip)
                
            except Exception as e:
                print(f"处理片段失败: {str(e)}")
                print(f"  视频文件: {subclipped_item['file_path']}")
                print(f"  时间段: {subclipped_item['start_time']:.2f}s - {subclipped_item['end_time']:.2f}s")
                import traceback
                traceback.print_exc()
                continue
        
        # 4. 如果时长不够，循环添加已处理的片段
        if video_duration < audio_duration and processed_clips:
            print(f"视频时长 ({video_duration:.2f}s) 短于音频时长 ({audio_duration:.2f}s)，开始循环添加片段")
            base_clips = processed_clips.copy()
            
            for clip in itertools.cycle(base_clips):
                if video_duration >= audio_duration:
                    break
                processed_clips.append(clip)
                video_duration += clip['duration']
            
            print(f"循环后视频时长: {video_duration:.2f}s，共 {len(processed_clips)} 个片段")
        
        # 5. 逐个合并视频片段（避免内存溢出）
        print("开始合并视频片段")
        if not processed_clips:
            raise ValueError("没有可用的视频片段")
        
        if len(processed_clips) == 1:
            print("只有一个片段，直接复制")
            shutil.copy(processed_clips[0]['file_path'], combined_video_path)
        else:
            # 逐个合并片段
            temp_merged_video = os.path.join(output_dir, "temp-merged-video.mp4")
            temp_merged_next = os.path.join(output_dir, "temp-merged-next.mp4")
            
            # 复制第一个片段作为基础
            shutil.copy(processed_clips[0]['file_path'], temp_merged_video)
            
            # 逐个合并剩余片段
            for i, clip_info in enumerate(processed_clips[1:], 1):
                print(f"合并片段 {i}/{len(processed_clips)-1}")
                
                try:
                    base_clip = VideoFileClip(temp_merged_video)
                    next_clip = VideoFileClip(clip_info['file_path'])
                    
                    merged_clip = concatenate_videoclips([base_clip, next_clip])
                    merged_clip.write_videofile(
                        temp_merged_next,
                        logger=None,
                        fps=30,
                        codec='libx264'
                    )
                    
                    self._close_clip(base_clip)
                    self._close_clip(next_clip)
                    self._close_clip(merged_clip)
                    
                    # 替换基础文件
                    if os.path.exists(temp_merged_video):
                        os.remove(temp_merged_video)
                    os.rename(temp_merged_next, temp_merged_video)
                    
                except Exception as e:
                    print(f"合并片段失败: {str(e)}")
                    continue
            
            # 重命名为最终文件
            os.rename(temp_merged_video, combined_video_path)
        
        # 6. 清理临时文件
        self._delete_files(temp_files)
        
        print("视频合成完成")
        return (os.path.abspath(combined_video_path),)

    def _close_clip(self, clip):
        """安全关闭clip资源"""
        if clip is None:
            return
            
        try:
            # 关闭主要资源
            if hasattr(clip, 'reader') and clip.reader is not None:
                clip.reader.close()
                
            # 关闭音频资源
            if hasattr(clip, 'audio') and clip.audio is not None:
                if hasattr(clip.audio, 'reader') and clip.audio.reader is not None:
                    clip.audio.reader.close()
                del clip.audio
                
            # 关闭mask资源
            if hasattr(clip, 'mask') and clip.mask is not None:
                if hasattr(clip.mask, 'reader') and clip.mask.reader is not None:
                    clip.mask.reader.close()
                del clip.mask
                
            # 处理复合clip中的子clip
            if hasattr(clip, 'clips') and clip.clips:
                for child_clip in clip.clips:
                    if child_clip is not clip:  # 避免循环引用
                        self._close_clip(child_clip)
                        
            # 清空clip列表
            if hasattr(clip, 'clips'):
                clip.clips = []
                
        except Exception as e:
            print(f"关闭clip失败: {str(e)}")
        
        del clip
        gc.collect()

    def _delete_files(self, files):
        """删除文件列表"""
        if isinstance(files, str):
            files = [files]
            
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                print(f"删除文件失败 {file}: {str(e)}")

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

    def _get_video_list(self, video_directory, file_extensions):
        """获取视频目录中的所有视频文件，按文件名排序"""
        # 解析支持的文件扩展名
        extensions = [ext.strip().lower() for ext in file_extensions.split(',')]
        
        video_files = []
        
        # 遍历目录中的所有文件
        try:
            for filename in os.listdir(video_directory):
                file_path = os.path.join(video_directory, filename)
                
                # 检查是否为文件
                if os.path.isfile(file_path):
                    # 检查文件扩展名
                    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
                    if file_ext in extensions:
                        video_files.append(file_path)
            
            # 自然排序（处理数字文件名）
            def natural_sort_key(filename):
                import re
                # 提取文件名中的数字部分进行排序
                parts = re.split(r'(\d+)', os.path.basename(filename).lower())
                # 将数字部分转换为整数，非数字部分保持字符串
                for i in range(len(parts)):
                    try:
                        parts[i] = int(parts[i])
                    except ValueError:
                        pass
                return parts
            
            video_files.sort(key=natural_sort_key)
            
        except Exception as e:
            print(f"读取视频目录失败: {str(e)}")
            return []
        
        return video_files

    def _resize_clip(self, clip, target_width, target_height):
        """调整视频片段尺寸"""
        clip_w, clip_h = clip.size
        
        if clip_w == target_width and clip_h == target_height:
            return clip
        
        clip_ratio = clip_w / clip_h
        target_ratio = target_width / target_height
        
        print(f"调整尺寸: 源 {clip_w}x{clip_h} (比例: {clip_ratio:.2f}) -> 目标 {target_width}x{target_height} (比例: {target_ratio:.2f})")
        
        if abs(clip_ratio - target_ratio) < 0.01:  # 比例接近，直接缩放
            return clip.resize((target_width, target_height))
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
            ).set_duration(clip.duration)
            
            clip_resized = clip.resize((new_width, new_height)).set_position("center")
            
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

# 节点注册
NODE_CLASS_MAPPINGS = {
    "SmartVideoCombinerNode": SmartVideoCombinerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SmartVideoCombinerNode": "Smart Video Combiner"
} 