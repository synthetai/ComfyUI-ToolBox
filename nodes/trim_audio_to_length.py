import os
import subprocess
import glob
import re
import folder_paths

class TrimAudioToLength:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_path": ("STRING", {"default": ""}),
                "target_duration": ("FLOAT", {"default": 10.0, "min": 0.1, "max": 3600.0, "step": 0.1}),
                "filename_prefix": ("STRING", {"default": "trimmed_audio"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("file_path",)
    FUNCTION = "trim_audio"
    CATEGORY = "ToolBox/Audio"

    def trim_audio(self, audio_path, target_duration, filename_prefix):
        # 检查文件是否存在
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")
            
        # 获取ComfyUI的output目录
        output_dir = folder_paths.get_output_directory()
        # 确保output_dir是绝对路径
        output_dir = os.path.abspath(output_dir)
        print(f"输出目录: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取原始音频的文件扩展名
        _, file_extension = os.path.splitext(audio_path)
        
        # 生成不会重复的文件名
        output_filename = self._generate_filename(output_dir, filename_prefix, file_extension)
        output_path = os.path.join(output_dir, output_filename)
        print(f"输出文件路径: {output_path}")
        
        # 获取音频时长
        original_duration = self._get_duration(audio_path)
        
        # 如果目标时长超过了原始时长，发出警告但继续处理
        if target_duration > original_duration:
            print(f"警告: 目标时长 ({target_duration}秒) 超过了原始音频时长 ({original_duration}秒)。将返回原始音频。")
            # 复制原始音频到输出路径
            self._copy_audio(audio_path, output_path)
        else:
            # 裁剪音频到目标时长
            self._trim_audio(audio_path, output_path, target_duration)
        
        # 使用最终的绝对路径
        final_path = os.path.abspath(output_path)
        
        # 检查文件是否已经成功生成
        if os.path.exists(final_path):
            print(f"文件已成功生成: {final_path}")
        else:
            print(f"警告: 文件未找到: {final_path}")
                
        # 调试信息
        print(f"最终返回路径: {final_path}")
        
        # 返回绝对路径的元组
        return (final_path,)
    
    def _generate_filename(self, output_dir, prefix, extension):
        """生成不会重复的递增编号文件名"""
        # 确保扩展名以.开头
        if not extension.startswith('.'):
            extension = '.' + extension
            
        # 查找同一前缀的所有文件
        pattern = os.path.join(output_dir, f"{prefix}_????{extension}")
        existing_files = glob.glob(pattern)
        
        # 如果没有同名文件，从0001开始
        if not existing_files:
            return f"{prefix}_0001{extension}"
        
        # 找出最大的编号
        max_number = 0
        for file in existing_files:
            match = re.search(r'_(\d{4})' + re.escape(extension) + r'$', file)
            if match:
                number = int(match.group(1))
                max_number = max(max_number, number)
        
        # 新编号是最大编号+1
        new_number = max_number + 1
        return f"{prefix}_{new_number:04d}{extension}"
    
    def _get_duration(self, audio_file):
        """获取音频文件的时长（秒）"""
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            audio_file
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    
    def _trim_audio(self, input_file, output_file, target_duration):
        """裁剪音频到指定时长"""
        subprocess.run([
            "ffmpeg", "-y", "-i", input_file, "-t", str(target_duration),
            "-c:a", "copy", output_file
        ], check=True)
        
    def _copy_audio(self, input_file, output_file):
        """复制音频文件"""
        subprocess.run([
            "ffmpeg", "-y", "-i", input_file, "-c:a", "copy", output_file
        ], check=True) 