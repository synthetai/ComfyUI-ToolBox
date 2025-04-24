# ComfyUI-ToolBox

ComfyUI-ToolBox是一个为ComfyUI提供实用工具节点的扩展包。当前包含音视频处理和文件上传等功能节点。

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

### AWS S3 Upload

AWS S3 Upload节点用于将本地文件上传到Amazon S3存储服务中。

**功能特点：**
- 支持将任何类型的本地文件上传到AWS S3存储桶
- 灵活配置存储路径，支持父目录和子目录结构
- 自动处理目录层次结构
- 支持指定AWS区域
- 返回上传后的S3文件路径

**节点参数：**
- `bucket`: AWS S3存储桶名称
- `access_key`: AWS访问密钥ID
- `secret_key`: AWS秘密访问密钥
- `region`: AWS区域名称（默认为"us-east-1"）
- `parent_directory`: 存储桶内的父目录路径（可选）
- `file_path`: 要上传的本地文件绝对路径
- `sub_dir_name` (可选): 在父目录下的子目录名称，如设置则文件将存储在子目录下

**目录结构规则：**
- 如果`parent_directory`和`sub_dir_name`都有值，文件将存储在`bucket/parent_directory/sub_dir_name/`下
- 如果只有`parent_directory`有值，文件将存储在`bucket/parent_directory/`下
- 如果只有`sub_dir_name`有值，文件将存储在`bucket/sub_dir_name/`下
- 如果两者都没有值，文件将直接存储在存储桶根目录

**输出：**
- `s3_file_path`: 上传后文件在S3中的路径（格式：s3://bucket/path/to/file）

## 安装方法

1. 确保您已安装ComfyUI
2. 确保系统已安装FFmpeg（用于音视频处理）
3. 安装Python依赖：`pip install boto3`（用于AWS S3上传）
4. 将此仓库克隆到ComfyUI的`custom_nodes`目录下:
```
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-ToolBox.git
```
5. 重启ComfyUI
6. 在ComfyUI界面中，应该能在"ToolBox"分类下找到相应的节点

## 依赖项

- FFmpeg - 用于音视频处理
- boto3 - 用于AWS S3文件上传
- Python 3.8+

## 使用示例

### Video Combine节点使用示例
1. 在ComfyUI工作流中，添加"Video Combine"节点（在ToolBox/Video Combine分类下）
2. 设置输入的视频文件和音频文件路径
3. 设置输出文件名前缀
4. 选择当音频比视频长时的处理方式（cut off audio、bounce video或loop video）
5. 运行工作流，获取合并后的视频文件路径
6. 合并后的视频将保存在ComfyUI的output目录下

### AWS S3 Upload节点使用示例
1. 在ComfyUI工作流中，添加"AWS S3 Upload"节点（在ToolBox/AWS S3分类下）
2. 输入您的AWS S3存储桶名称、访问密钥和秘密密钥
3. 选择正确的AWS区域（如"us-east-1"、"eu-west-1"等）
4. 设置父目录路径（可选）和子目录名称（可选）来定义存储结构
5. 输入要上传的本地文件路径
6. 运行工作流，获取上传后的S3文件路径