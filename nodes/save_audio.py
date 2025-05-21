import os
import numpy as np
import soundfile as sf
from scipy.io import wavfile
import folder_paths
import json
import torch
import tempfile
import shutil
from pydub import AudioSegment

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
        
        # 创建临时文件
        temp_wav_path = None
        
        try:
            # 确定质量设置
            quality_settings = {
                "V0": {"bitrate": 320},
                "V1": {"bitrate": 256},
                "V2": {"bitrate": 224},
                "V3": {"bitrate": 192},
                "V4": {"bitrate": 128}
            }
            
            bitrate = quality_settings.get(quality, {"bitrate": 320})["bitrate"]
            
            # 从AUDIO字典中提取波形数据和采样率
            print(f"音频数据类型: {type(audio)}")
            
            # 如果是字典类型，提取waveform和sample_rate
            if isinstance(audio, dict):
                waveform = audio.get('waveform')
                sample_rate = audio.get('sample_rate', 44100)
                print(f"从音频字典中提取数据：采样率 = {sample_rate}")
            else:
                waveform = audio
                sample_rate = 44100
                print("使用默认采样率: 44100")
            
            # 如果是张量，转换为numpy数组
            if isinstance(waveform, torch.Tensor):
                # 从张量中提取通道数据
                # 张量形状可能是 [batch, channels, samples] 或 [channels, samples]
                if waveform.dim() == 3:
                    # 取第一个批次
                    waveform = waveform[0]
                    
                # 转换为numpy数组
                waveform = waveform.cpu().numpy()
                print(f"转换后的波形形状: {waveform.shape}")
            
            # 确保数据是正确的浮点范围 [-1.0, 1.0]
            if waveform.max() <= 1.0 and waveform.min() >= -1.0:
                # 已经在正确范围内，不需要调整
                print("波形数据在正确的范围内 [-1.0, 1.0]")
            else:
                # 如果数据在其他范围，将其归一化到 [-1.0, 1.0]
                print(f"波形数据需要归一化，当前范围: [{waveform.min()}, {waveform.max()}]")
                waveform = waveform.astype(np.float32)
                waveform = waveform / max(abs(waveform.max()), abs(waveform.min()))
            
            # 确保数据是float32类型
            waveform = waveform.astype(np.float32)
            
            # 确保我们有正确的通道顺序 [samples, channels]
            if waveform.shape[0] == 2 and waveform.shape[1] > 2:
                # 如果是 [channels, samples] 格式，转置为 [samples, channels]
                waveform = waveform.T
                print(f"转置后的波形形状: {waveform.shape}")
            
            # 创建临时wav文件
            fd, temp_wav_path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            
            print(f"创建临时WAV文件: {temp_wav_path}")
            
            # 保存为临时WAV文件
            wavfile.write(temp_wav_path, sample_rate, waveform)
            
            # 使用pydub转换为MP3
            print(f"使用pydub将WAV转换为MP3，比特率: {bitrate}kbps")
            sound = AudioSegment.from_wav(temp_wav_path)
            sound.export(filepath, format="mp3", bitrate=f"{bitrate}k")
            
            print(f"MP3文件已保存: {filepath}")
            
            # 返回音频文件的绝对路径
            return (os.path.abspath(filepath),)
            
        except Exception as e:
            error_message = f"保存音频文件时发生错误: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            raise Exception(error_message)
        finally:
            # 清理临时文件
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                    print(f"删除临时WAV文件: {temp_wav_path}")
                except:
                    pass
    
    @classmethod
    def IS_CHANGED(cls, audio, filename_prefix, quality="V0"):
        # 返回时间戳，确保每次都会保存
        import time
        return time.time()

# 配置节点的UI显示
WEB_DIRECTORY = "./web"

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ToolboxSaveAudio": SaveAudioNode
}

# 节点显示名称
NODE_DISPLAY_NAME_MAPPINGS = {
    "ToolboxSaveAudio": "Save Audio (MP3)"
} 