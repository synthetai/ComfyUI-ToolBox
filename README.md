# ComfyUI-ToolBox

ComfyUI-ToolBox是一个为ComfyUI提供实用工具节点的扩展包。当前包含音视频处理等功能节点。

## 功能节点

### Video Combine

Video Combine节点用于将音频文件合并到视频文件中，适合作为工作流的最后一个节点使用。

**功能特点：**
- 输入一个视频文件和一个音频文件
- 合并音频到视频中
- 提供多种处理长音频的方式（截断音频、交替播放视频、循环播放视频）
- 可自定义输出文件名前缀
- 合并后的视频将保存到ComfyUI的output目录下

**节点参数：**
- `video_file`: 输入视频文件的路径
- `audio_file`: 输入音频文件的路径
- `filename_prefix`: 输出文件名前缀，默认为"output"
- `audio_handling`: 当音频比视频长时的处理方式：
  - `cut off audio`: 截断音频使其与视频时长保持一致
  - `bounce video`: 使用正向/反向交替播放视频来匹配音频长度（默认）
  - `loop video`: 循环重复播放视频来匹配音频长度

**输出：**
- `video_path`: 合并后视频文件的绝对路径

## 安装方法

1. 确保您已安装ComfyUI
2. 确保系统已安装FFmpeg（用于音视频处理）
3. 将此仓库克隆到ComfyUI的`custom_nodes`目录下:
```
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-ToolBox.git
```
4. 重启ComfyUI
5. 在ComfyUI界面中，应该能在"ToolBox/Video Combine"分类下找到"Video Combine"节点

## 依赖项

- FFmpeg - 用于音视频处理
- Python 3.8+

## 使用示例

1. 在ComfyUI工作流中，添加"Video Combine"节点（在ToolBox/Video Combine分类下）
2. 设置输入的视频文件和音频文件路径
3. 设置输出文件名前缀
4. 选择当音频比视频长时的处理方式（cut off audio、bounce video或loop video）
5. 运行工作流，获取合并后的视频文件路径
6. 合并后的视频将保存在ComfyUI的output目录下