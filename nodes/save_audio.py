import os
import numpy as np
import soundfile as sf
from scipy.io import wavfile
import folder_paths
from IPython.display import Audio, display
import json

class SaveAudioNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "filename_prefix": ("STRING", {"default": "audio"}),
            },
            "optional": {
                "play_audio": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("audio_file",)
    FUNCTION = "save_audio"
    CATEGORY = "ToolBox/Audio"

    def save_audio(self, audio, filename_prefix, play_audio=False):
        # 获取输出目录
        output_dir = folder_paths.get_output_directory()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 查找下一个可用的文件名
        counter = 1
        while True:
            filename = f"{filename_prefix}_{counter:04d}.mp3"
            filepath = os.path.join(output_dir, filename)
            if not os.path.exists(filepath):
                break
            counter += 1
        
        try:
            # 将音频数据保存为MP3文件
            # 注意：这里假设audio数据是numpy数组，采样率为44100Hz
            sf.write(filepath, audio, 44100, format='mp3')
            print(f"音频文件已保存: {filepath}")
            
            # 如果需要播放音频
            if play_audio:
                # 创建Audio对象并播放
                audio_player = Audio(filepath)
                display(audio_player)
                print("正在播放音频...")
            
            # 返回音频文件的绝对路径
            return (os.path.abspath(filepath),)
            
        except Exception as e:
            error_message = f"保存音频文件时发生错误: {str(e)}"
            print(error_message)
            raise Exception(error_message)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ToolboxSaveAudio": SaveAudioNode
}

# 节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "ToolboxSaveAudio": "Toolbox Save Audio"
} 