import os
import numpy as np
import soundfile as sf
from scipy.io import wavfile
import folder_paths
import json

class SaveAudioNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "filename_prefix": ("STRING", {"default": "audio/ComfyUI"}),
                "quality": (["V0", "V1", "V2", "V3", "V4"], {"default": "V0"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("audio_file",)
    FUNCTION = "save_audio"
    CATEGORY = "ToolBox/Audio"
    OUTPUT_NODE = True

    def save_audio(self, audio, filename_prefix, quality="V0"):
        # 获取输出目录
        output_dir = folder_paths.get_output_directory()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 确保filename_prefix的目录存在
        prefix_dir = os.path.dirname(filename_prefix)
        if prefix_dir:
            prefix_path = os.path.join(output_dir, prefix_dir)
            os.makedirs(prefix_path, exist_ok=True)
        
        # 查找下一个可用的文件名
        counter = 1
        filename_base = os.path.basename(filename_prefix)
        while True:
            filename = f"{filename_base}_{counter:04d}.mp3"
            if prefix_dir:
                rel_filepath = os.path.join(prefix_dir, filename)
            else:
                rel_filepath = filename
            
            filepath = os.path.join(output_dir, rel_filepath)
            if not os.path.exists(filepath):
                break
            counter += 1
        
        try:
            # 确定质量设置
            quality_settings = {
                "V0": {"bitrate": 320000},
                "V1": {"bitrate": 256000},
                "V2": {"bitrate": 224000},
                "V3": {"bitrate": 192000},
                "V4": {"bitrate": 128000}
            }
            
            bitrate = quality_settings.get(quality, {"bitrate": 320000})["bitrate"]
            
            # 将音频数据保存为MP3文件
            # 使用指定的比特率保存
            print(f"保存音频文件: {filepath}，质量: {quality}，比特率: {bitrate//1000}kbps")
            sf.write(filepath, audio, 44100, format='mp3', subtype=f'PCM_{bitrate}')
            
            # 创建相对路径用于预览
            preview_path = os.path.relpath(filepath, os.path.abspath(output_dir))
            
            # 返回音频文件的绝对路径
            return (os.path.abspath(filepath),)
            
        except Exception as e:
            error_message = f"保存音频文件时发生错误: {str(e)}"
            print(error_message)
            raise Exception(error_message)
    
    @classmethod
    def IS_CHANGED(cls, audio, filename_prefix, quality="V0"):
        # 返回时间戳，确保每次都会保存
        import time
        return time.time()

# 配置节点的UI显示
WEB_DIRECTORY = "../web"

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ToolboxSaveAudio": SaveAudioNode
}

# 节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "ToolboxSaveAudio": "Save Audio (MP3)"
} 