# ComfyUI-ToolBox

ComfyUI-ToolBox 是一个功能丰富的 ComfyUI 自定义节点集合，提供多种实用工具和API集成功能。

## 功能特性

### OpenAI API 集成

#### Create Image (OpenAI)
基于OpenAI API的图像生成节点，支持最新的图像生成模型。

**功能特色：**
- 支持多种模型：DALL-E-2、DALL-E-3、GPT-Image-1
- 灵活的图像配置：尺寸、质量、风格等参数可调
- 多种输出格式支持：PNG、JPEG、WebP
- 自动压缩和优化功能
- 随机种子支持，便于结果复现

**节点参数：**
- `api_key`: OpenAI API密钥（必需）
- `prompt`: 图像生成提示词（必需）
- `model`: 选择模型，支持"dall-e-2"、"dall-e-3"、"gpt-image-1"，默认"gpt-image-1"
- `size`: 图像尺寸，根据所选模型提供不同选项
- `quality`: 图像质量，选项有"auto"、"standard"、"hd"等
- `style`: 图像风格，选项有"vivid"、"natural"
- `background`: 背景设置，选项有"auto"、"transparent"、"opaque"
- `n`: 生成图像数量，范围1-10
- `user`: 用户标识符，用于跟踪和监控

**输出：**
- `image`: 生成的图像，作为ComfyUI中的图像对象返回
- `b64_json`: base64编码的图像数据，可传递给Save Image节点

#### Edit Image (OpenAI)
使用OpenAI API编辑现有图像的节点，支持动态输入多张图像。

**功能特色：**
- 支持DALL-E-2和GPT-Image-1模型进行图像编辑
- 动态输入支持：通过设置inputcount参数并点击"Update inputs"按钮可添加多个图像输入
- 模型兼容性自动处理：DALL-E-2仅使用第一张图像，GPT-Image-1支持多张图像（最多4张）

**可选参数：**
- `mask`: 可选的蒙版，用于指定编辑区域（蒙版中的透明区域表示要修改的区域）
- `model`: 使用的模型，"gpt-image-1"或"dall-e-2"（默认："gpt-image-1"）
- `n`: 生成图像数量，范围1-10
- `size`: 图像尺寸，根据模型提供不同选项：
  - GPT-Image-1: "auto"、"1024x1024"、"1536x1024"（横向）、"1024x1536"（纵向）
  - DALL-E-2: "256x256"、"512x512"、"1024x1024"
- `quality`: 图像质量，选项因模型而异（默认："auto"）
- `response_format`: 返回格式，"url"或"b64_json"（默认："b64_json"）
- `user`: 用户标识符，用于跟踪和监控

**使用方法：**
1. 使用`inputcount`参数设置所需的图像输入数量
2. 点击"Update inputs"更新节点界面
3. 将您的图像连接到显示的图像输入端口
4. 使用DALL-E-2模型时，无论inputcount值如何，仅会使用第一张图像
5. 使用GPT-Image-1模型时，最多可使用4张图像；如果inputcount设置更高，仅使用前4张

**输出：**
- `image`: 编辑后的图像，作为ComfyUI中的图像对象返回
- `b64_json`: base64编码的图像数据，可传递给Save Image节点

### 视频处理

#### Video Combine
Video Combine节点将音频文件与视频文件合并，非常适合作为工作流的最终节点使用。

**功能特色：**
- 接受视频文件和音频文件作为输入
- 将音频与视频合并
- 提供多种长音频处理方法（截断音频、弹跳视频、循环视频）
- 可自定义输出文件名前缀
- 合并后的视频保存在ComfyUI的输出目录中

**节点参数：**
- `video_file`: 输入视频文件路径
- `audio_file`: 输入音频文件路径
- `filename_prefix`: 输出文件名前缀，默认为"output"
- `audio_handling`: 处理比视频长的音频的方法：
  - `cut off audio`: 截断音频以匹配视频时长
  - `bounce video`: 交替正向/反向视频播放以匹配音频长度（默认）
  - `loop video`: 重复视频播放以匹配音频长度

**输出：**
- `video_path`: 合并后视频文件的绝对路径

#### Smart Video Combiner
智能视频合成节点，将多个视频文件智能切片并合成为单个视频，根据音频时长自动调整视频长度。

**功能特色：**
- 支持多个视频文件智能切片合并
- 根据音频时长自动调整最终视频长度
- 支持多种视频比例（16:9、9:16、1:1等）
- 提供顺序和随机两种拼接模式
- 支持多种过渡效果（淡入、淡出、随机等）
- 智能尺寸调整，自动添加黑边保持比例

**节点参数：**
- `video_paths`: 视频文件路径，每行一个（多行文本）
- `audio_file`: 参考音频文件路径
- `filename_prefix`: 输出文件名前缀
- `max_clip_duration`: 最大片段时长（秒）
- `aspect_ratio`: 目标视频比例（16:9、9:16、1:1、4:3、3:4）
- `concat_mode`: 拼接模式（sequential顺序、random随机）
- `transition_mode`: 过渡效果（none、fade_in、fade_out、shuffle）
- `video_width`/`video_height`: 自定义视频尺寸

**输出：**
- `video_path`: 合成后视频文件的绝对路径

#### Video Subtitle Generator
视频字幕生成节点，为视频添加字幕、背景音乐等效果，支持SRT字幕文件和自定义字体样式。

**功能特色：**
- 支持SRT字幕文件和直接文本输入
- 丰富的字幕样式：字体大小、颜色、描边、背景色
- 多种字幕位置：顶部、底部、居中、自定义位置
- 背景音乐混合功能
- 音量控制（主音频和背景音乐独立调节）
- 智能文本换行处理

**节点参数：**
- `video_file`: 输入视频文件路径
- `audio_file`: 主音频文件路径
- `subtitle_enabled`: 是否启用字幕
- `subtitle_file`: SRT字幕文件路径（可选）
- `subtitle_text`: 直接输入字幕文本（格式：时间-时间 文本内容）
- `font_size`: 字体大小
- `font_color`: 字体颜色
- `bg_color`: 背景颜色
- `stroke_color`/`stroke_width`: 描边颜色和宽度
- `subtitle_position`: 字幕位置
- `bgm_file`: 背景音乐文件（可选）
- `bgm_volume`/`voice_volume`: 背景音乐和主音频音量

**输出：**
- `video_path`: 添加字幕后的视频文件路径

#### Image to Video Converter
图片转视频节点，将静态图片转换为动态视频，支持缩放效果和自定义时长。

**功能特色：**
- 将静态图片转换为动态视频
- 支持缩放效果（Ken Burns效果）
- 自动分辨率检查和尺寸调整
- 支持批量处理（合并或单独输出）
- 智能比例保持，自动添加黑边
- 可自定义帧率和时长

**节点参数：**
- `image_paths`: 图片文件路径，每行一个
- `clip_duration`: 每张图片的视频时长
- `output_width`/`output_height`: 输出视频尺寸
- `zoom_effect`: 是否启用缩放效果
- `zoom_factor`: 缩放倍数
- `min_resolution`: 最低分辨率要求
- `combine_videos`: 是否合并为单个视频
- `fps`: 视频帧率

**输出：**
- `video_path`: 转换后的视频文件路径

### AWS S3 上传

AWS S3 Upload节点将本地文件上传到Amazon S3存储服务。

**功能特色：**
- 支持上传任何本地文件类型到AWS S3存储桶
- 灵活的存储路径配置，支持父目录和子目录
- 自动目录层次结构处理
- AWS区域设置
- 上传后返回S3文件路径

**节点参数：**
- `bucket`: AWS S3存储桶名称
- `access_key`: AWS访问密钥ID
- `secret_key`: AWS秘密访问密钥
- `region`: AWS区域名称（默认为"us-east-1"）
- `parent_directory`: 存储桶内的父目录路径（可选）
- `file_path`: 要上传的本地文件绝对路径
- `sub_dir_name`（可选）: 父目录下的子目录名称，如果设置，文件将存储在子目录中

**目录结构规则：**
- 如果`parent_directory`和`sub_dir_name`都有值，文件将存储在`bucket/parent_directory/sub_dir_name/`下
- 如果只有`parent_directory`有值，文件将存储在`bucket/parent_directory/`下
- 如果只有`sub_dir_name`有值，文件将存储在`bucket/sub_dir_name/`下
- 如果两者都没有值，文件将直接存储在存储桶根目录

**输出：**
- `s3_file_path`: 上传文件的S3路径（格式：s3://bucket/path/to/file）

### 音频处理

#### Trim Audio To Length
Trim Audio To Length节点将音频文件裁剪到指定时长。

**功能特色：**
- 接受音频文件路径作为输入
- 将音频裁剪到用户指定的时长
- 如果目标时长超过原始音频长度，返回原始音频
- 可自定义输出文件名前缀
- 裁剪后的音频保存在ComfyUI的输出目录中

**节点参数：**
- `audio_path`: 输入音频文件路径
- `target_duration`: 裁剪音频的目标时长（秒）（范围：0.1到3600.0秒）
- `filename_prefix`: 输出文件名前缀，默认为"trimmed_audio"

**输出：**
- `file_path`: 裁剪后音频文件的绝对路径

#### Save Audio (MP3)
音频保存节点，将ComfyUI的音频数据保存为MP3文件。

**功能特色：**
- 支持将ComfyUI的AUDIO数据类型保存为MP3格式
- 多种音质选项（V0-V4，对应不同比特率）
- 自动文件名递增，避免覆盖
- 支持目录结构组织
- 高兼容性的音频格式转换

**节点参数：**
- `audio`: AUDIO数据类型输入
- `filename_prefix`: 文件名前缀，支持目录路径
- `quality`: 音质等级（V0=320kbps, V1=256kbps, V2=224kbps, V3=192kbps, V4=128kbps）

**输出：**
- `audio_file`: 保存的MP3文件绝对路径

## 安装

### 方法一：使用 Conda 安装（推荐）

1. 确保已安装ComfyUI
2. 将此仓库克隆到ComfyUI的`custom_nodes`目录：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-ToolBox.git
cd ComfyUI-ToolBox
```
3. 使用conda安装所有依赖：
```bash
# 一条命令安装所有依赖（推荐）
conda install -c conda-forge numpy pillow scipy imageio imageio-ffmpeg ffmpeg soundfile requests boto3 botocore moviepy

# 或者分别安装
conda install -c conda-forge moviepy ffmpeg
pip install pydub ffmpeg-python
```

### 方法二：使用 pip 安装

1. 确保已安装ComfyUI和FFmpeg
2. 将此仓库克隆到ComfyUI的`custom_nodes`目录：
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-ToolBox.git
cd ComfyUI-ToolBox
```
3. 安装Python依赖：
```bash
pip install -r requirements.txt
```

### 快速解决moviepy错误

如果遇到 `ModuleNotFoundError: No module named 'moviepy'` 错误，可以直接运行：
```bash
# 使用conda安装moviepy（推荐）
conda install -c conda-forge moviepy

# 或者同时安装相关依赖
conda install -c conda-forge moviepy imageio imageio-ffmpeg ffmpeg
```

**最新修复（2024年）：** 
如果遇到 `ImportError: cannot import name 'VideoFileClip' from 'moviepy'` 错误，这是因为 MoviePy v2 改变了导入语法。我们已经修复了所有节点文件中的导入问题：
- 现在使用 `from moviepy.editor import ...` 而不是 `from moviepy import ...`
- 所有视频处理节点都已更新到 MoviePy v2 兼容的语法
- 如果您仍然遇到导入问题，请确保安装了最新版本的 moviepy

## 依赖库

项目的主要依赖库列在`requirements.txt`中，包括：
- boto3 - 用于AWS S3文件上传
- moviepy - 用于视频处理和合成
- FFmpeg - 用于音视频处理 (需要系统级安装)
- requests - 用于API请求和文件下载
- 其他Python库 - 详见requirements.txt

## 使用示例

### Create Image (OpenAI) 节点使用示例
1. 在ComfyUI工作流中，添加"Create Image (OpenAI)"节点（在ToolBox/OpenAI分类下）
2. 输入您的OpenAI API密钥
3. 输入您想要生成的图像描述（提示词）
4. 选择模型（如 dall-e-3 或 gpt-image-1）
5. 根据选择的模型，设置相应的参数（尺寸、质量、风格、背景等）
6. 运行工作流，获取生成的图像
7. 生成的图像可以直接在ComfyUI中用于后续处理，例如通过其他节点进一步编辑或应用效果

### Smart Video Combiner节点使用示例
1. 在ComfyUI工作流中，添加"Smart Video Combiner"节点（在ToolBox/Video分类下）
2. 在`video_paths`参数中输入视频文件路径，每行一个
3. 设置参考音频文件路径
4. 选择视频比例和拼接模式
5. 配置过渡效果和片段时长
6. 运行工作流，获取智能合成的视频

### Video Subtitle Generator节点使用示例
1. 添加"Video Subtitle Generator"节点
2. 设置视频文件和音频文件路径
3. 选择字幕输入方式（SRT文件或直接文本）
4. 配置字幕样式（字体、颜色、位置等）
5. 可选择添加背景音乐
6. 运行工作流，获取带字幕的视频

### Image to Video Converter节点使用示例
1. 添加"Image to Video Converter"节点
2. 在`image_paths`中输入图片路径，每行一个
3. 设置视频时长和输出尺寸
4. 选择是否启用缩放效果
5. 配置合并选项和帧率
6. 运行工作流，获取图片转换的视频

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

### Trim Audio To Length节点使用示例
1. 在ComfyUI工作流中，添加"Trim Audio To Length"节点（在ToolBox/Audio分类下）
2. 设置输入的音频文件路径
3. 指定裁剪后音频的目标时长（秒）
4. 设置输出文件名前缀（可选，默认为"trimmed_audio"）
5. 运行工作流，获取裁剪后的音频文件路径
6. 裁剪后的音频将保存在ComfyUI的output目录下，文件名采用递增编号

## 许可证

本项目采用MIT许可证发布。