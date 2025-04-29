# ComfyUI-ToolBox

ComfyUI-ToolBox是一个为ComfyUI提供实用工具节点的扩展包。当前包含音视频处理、文件上传和AI图像生成等功能节点。

## 功能节点

### Create Image (OpenAI)

Create Image 节点用于调用 OpenAI 的 API 生成图像，支持 DALL-E 和 GPT-Image 模型。

**功能特点：**
- 支持 OpenAI 的 DALL-E 和 GPT-Image 图像生成 API
- 可定制生成图像的尺寸、质量、风格和背景
- 支持 URL 或 base64 JSON 格式的返回值
- 自动处理 API 限流和错误重试
- 支持多种输出格式和压缩设置
- 支持透明背景生成（GPT-Image-1模型）

**节点参数：**
- 必填参数：
  - `api_key`: OpenAI API 密钥
  - `prompt`: 文本描述，用于生成图像（最大长度因模型而异：GPT-Image-1为32000字符，DALL-E-3为4000字符，DALL-E-2为1000字符）

- 可选参数：
  - `model`: 使用的模型，可选 "dall-e-2"、"dall-e-3" 或 "gpt-image-1"（默认为 "gpt-image-1"）
  - `size`: 图像尺寸，支持多种尺寸选项，与模型兼容的选项会自动验证（默认为 "1024x1024"）
  - `quality`: 图像质量，可选项根据模型而不同（默认为 "auto"）
    - GPT-Image-1: "auto", "high", "medium", "low"
    - DALL-E-3: "auto", "standard", "hd"
    - DALL-E-2: "auto", "standard"
  - `style`: 图像风格，仅适用于 DALL-E-3 模型，可选 "vivid" 或 "natural"（默认为 "vivid"）
  - `background`: 背景设置，仅适用于 GPT-Image-1 模型，可选 "auto", "transparent" 或 "opaque"（默认为 "auto"）
  - `moderation`: 内容审核级别，仅适用于 GPT-Image-1 模型，可选 "auto" 或 "low"（默认为 "auto"）
  - `response_format`: DALL-E 模型的返回格式，可选 "url" 或 "b64_json"（默认为 "b64_json"）
  - `output_format`: GPT-Image-1 模型的输出格式，可选 "png", "jpeg" 或 "webp"（默认为 "png"）
  - `output_compression`: 图像压缩级别，仅适用于 GPT-Image-1 模型的 webp 或 jpeg 格式，范围 0-100（默认为 100）
  - `n`: 生成图像数量，范围 1-10（DALL-E-3 仅支持 n=1）
  - `user`: 用户标识符，用于跟踪和监控

**输出：**
- `image`: 生成的图像，作为 ComfyUI 中的图像对象返回
- `b64_json`: Base64 编码的图像数据，可传递给保存图像节点

### Save Image (OpenAI)

专门用于处理和保存 OpenAI 图像数据的节点。

**功能特点：**
- 解码 base64 图像数据并保存为文件
- 自动从文件加载图像并输出到工作流以供进一步处理
- 正确处理图像格式和 EXIF 方向数据
- 提取 alpha 通道作为 mask（如果有）
- 提供详细的调试日志
- 完全兼容 ComfyUI 的 Preview Image 节点

**节点参数：**
- `b64_json`: 来自 OpenAI 的 Base64 编码图像数据
- `filename_prefix`: 保存文件名的前缀（默认为 "openai"）
- `output_dir`: 自定义输出目录（可选，如果为空则使用 ComfyUI 默认输出目录）

**输出：**
- `filename`: 保存的图像文件路径
- `image`: 作为 ComfyUI 图像对象的图像（可直接用于预览或进一步处理）
- `mask`: Alpha 通道 mask（如果图像中存在 alpha 通道，否则返回空 mask）

### Edit Image (OpenAI)

Edit Image 节点用于使用 OpenAI 的 API 编辑或扩展现有图像，支持 DALL-E-2 和 GPT-Image-1 模型。

**功能特点：**
- 接收现有图像并根据文本提示词进行修改
- 动态输入接口，可调整图像输入数量（1-4个）
- 使用 GPT-Image-1 模型时支持最多 4 个独立的图像输入
- 支持可选掩码来指定需要编辑的区域
- 支持 DALL-E-2 和 GPT-Image-1 模型
- 自动处理图像格式转换和尺寸要求
- 自动重试 API 限流和错误
- 支持生成多张图像（通过 n 参数）

**节点参数：**
- 必填参数：
  - `api_key`: OpenAI API 密钥
  - `inputcount`: 显示的图像输入数量（1-4）
  - `image_1`: 主要输入图像（作为 ComfyUI IMAGE 类型）
  - `prompt`: 期望修改的文本描述（最大长度：GPT-Image-1 为 32000 字符，DALL-E-2 为 1000 字符）

- 可选参数：
  - `image_2`, `image_3`, `image_4`: 额外的输入图像（根据 inputcount 值显示）
  - `mask`: 可选掩码，用于指定要编辑的区域（掩码中的透明区域表示要修改的区域）
  - `model`: 使用的模型，可选 "gpt-image-1" 或 "dall-e-2"（默认为 "gpt-image-1"）
  - `n`: 生成图像数量，范围 1-10
  - `size`: 图像尺寸，不同模型支持不同选项：
    - GPT-Image-1: "auto", "1024x1024", "1536x1024"（横向）, "1024x1536"（纵向）
    - DALL-E-2: "256x256", "512x512", "1024x1024"
  - `quality`: 图像质量，选项根据模型而不同（默认为 "auto"）
  - `response_format`: 返回格式，可选 "url" 或 "b64_json"（默认为 "b64_json"）
  - `user`: 用户标识符，用于跟踪和监控

**使用方法：**
1. 使用 `inputcount` 参数设置所需的图像输入数量
2. 点击 "Update inputs" 更新节点界面
3. 将图像连接到显示的图像输入接口
4. 当使用 DALL-E-2 模型时，无论 inputcount 值如何，只会使用第一张图像

**输出：**
- `image`: 编辑后的图像，作为 ComfyUI 中的图像对象返回
- `b64_json`: Base64 编码的图像数据，可传递给保存图像节点

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
3. 将此仓库克隆到ComfyUI的`custom_nodes`目录下:
```
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-ToolBox.git
```
4. 安装所需的Python依赖项:
```
cd ComfyUI-ToolBox
pip install -r requirements.txt
```
5. 重启ComfyUI
6. 在ComfyUI界面中，应该能在"ToolBox"分类下找到相应的节点

## 依赖项

项目所需的主要依赖项已在`requirements.txt`中列出，包括：
- boto3 - 用于AWS S3文件上传
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