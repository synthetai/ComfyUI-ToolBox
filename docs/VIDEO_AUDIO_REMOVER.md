# Video Audio Remover Node

## 功能描述

Video Audio Remover 是一个用于从视频中移除音频轨道的 ComfyUI 自定义节点。该节点支持从 URL 下载视频或处理本地视频文件，使用 FFmpeg 高效地移除音频轨道。

## 输入参数

### 必需参数

- **filename_prefix** (STRING): 输出视频文件名前缀
  - 默认值: "no_audio_video"
  - 生成的文件名格式: `{filename_prefix}_0001.mp4`

### 可选参数

- **video_url** (STRING): 视频文件的 HTTP 下载链接
  - 默认值: ""
  - 支持各种视频格式的 URL

- **video_path** (STRING): 本地视频文件路径
  - 默认值: ""
  - 支持绝对路径和相对路径

## 输出参数

- **video_path** (STRING): 处理后的视频文件路径

## 处理逻辑

1. **输入验证**: 确保用户提供了 video_url 或 video_path 中的一个，但不能同时提供两个
2. **视频获取**:
   - 如果提供了 video_url，将视频下载到 ComfyUI 的 output 目录
   - 如果提供了 video_path，直接使用本地文件
3. **音频检测**: 使用 FFprobe 检查视频是否包含音频轨道
4. **音频处理**:
   - 如果视频没有音频轨道，直接复制文件到输出目录
   - 如果视频有音频轨道，使用 FFmpeg 移除音频
5. **文件命名**: 自动生成递增编号的输出文件名，避免覆盖现有文件

## 技术特性

- **高效处理**: 使用 FFmpeg 的 stream copy 模式，不重新编码视频，速度快且质量无损
- **智能检测**: 自动检测视频是否包含音频轨道，避免不必要的处理
- **格式支持**: 保持原视频格式，支持 MP4、AVI、MOV 等多种格式
- **错误处理**: 完善的错误处理和日志输出
- **临时文件清理**: 自动清理下载的临时文件

## 使用示例

### 示例 1: 处理 URL 视频
```
- filename_prefix: "silent_video"
- video_url: "https://example.com/video.mp4"
- video_path: "" (留空)
```

### 示例 2: 处理本地视频
```
- filename_prefix: "no_sound"
- video_url: "" (留空)
- video_path: "/path/to/your/video.mp4"
```

## 依赖要求

- **FFmpeg**: 系统需要安装 FFmpeg 和 FFprobe
- **requests**: Python requests 库用于下载视频
- **folder_paths**: ComfyUI 的内置模块

## 注意事项

1. 确保系统已安装 FFmpeg
2. URL 视频下载需要网络连接
3. 大文件处理可能需要较长时间
4. 输出文件会保存在 ComfyUI 的 output 目录中
5. 如果原视频本身没有音频轨道，节点会直接复制文件，不进行额外处理

## 错误处理

节点会处理以下常见错误：
- 无效的 URL 格式
- 网络下载失败
- 文件不存在
- FFmpeg 处理错误
- 磁盘空间不足

所有错误都会有详细的日志输出，帮助用户诊断问题。 