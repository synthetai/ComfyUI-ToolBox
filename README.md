# ComfyUI-ToolBox

A collection of utility nodes for ComfyUI, including audio/video processing, file uploads, and AI image generation.

[中文文档 (Chinese Documentation)](README_CN.md)

## Utility Nodes

### Create Image (OpenAI)

The Create Image node allows you to generate images using OpenAI's API, supporting DALL-E and GPT-Image models.

**Features:**
- Integration with OpenAI's DALL-E and GPT-Image image generation APIs
- Customizable image size, quality, style, and background
- Support for URL or base64 JSON response formats
- Automatic handling of API rate limits and error retries
- Support for various output formats and compression settings
- Transparent background support (with GPT-Image-1 model)

**Node Parameters:**
- Required Parameters:
  - `api_key`: OpenAI API key
  - `prompt`: Text description for image generation (max length varies by model: 32000 chars for GPT-Image-1, 4000 chars for DALL-E-3, 1000 chars for DALL-E-2)

- Optional Parameters:
  - `model`: Model to use, one of "dall-e-2", "dall-e-3", or "gpt-image-1" (default: "gpt-image-1")
  - `size`: Image dimensions, with various size options that are validated against the selected model (default: "1024x1024")
  - `quality`: Image quality, options vary by model (default: "auto")
    - GPT-Image-1: "auto", "high", "medium", "low"
    - DALL-E-3: "auto", "standard", "hd"
    - DALL-E-2: "auto", "standard"
  - `style`: Image style, only for DALL-E-3 model, one of "vivid" or "natural" (default: "vivid")
  - `background`: Background setting, only for GPT-Image-1 model, one of "auto", "transparent", or "opaque" (default: "auto")
  - `moderation`: Content moderation level, only for GPT-Image-1 model, one of "auto" or "low" (default: "auto")
  - `response_format`: Return format for DALL-E models, one of "url" or "b64_json" (default: "b64_json")
  - `output_format`: Output format for GPT-Image-1 model, one of "png", "jpeg", or "webp" (default: "png")
  - `output_compression`: Image compression level, only for GPT-Image-1 model with webp or jpeg formats, range 0-100 (default: 100)
  - `n`: Number of images to generate, range 1-10 (DALL-E-3 only supports n=1)
  - `user`: User identifier for tracking and monitoring

**Output:**
- `image`: The generated image, returned as an image object in ComfyUI

### Video Combine

The Video Combine node merges an audio file with a video file, ideal for use as the final node in a workflow.

**Features:**
- Takes a video file and an audio file as input
- Combines the audio with the video
- Provides various methods for handling long audio (cut off audio, bounce video, loop video)
- Customizable output filename prefix
- Merged video is saved to ComfyUI's output directory

**Node Parameters:**
- `video_file`: Path to the input video file
- `audio_file`: Path to the input audio file
- `filename_prefix`: Prefix for the output filename, defaults to "output"
- `audio_handling`: Method for handling audio longer than the video:
  - `cut off audio`: Truncate audio to match video duration
  - `bounce video`: Alternate forward/reverse video playback to match audio length (default)
  - `loop video`: Repeat video playback to match audio length

**Output:**
- `video_path`: Absolute path to the merged video file

### AWS S3 Upload

The AWS S3 Upload node uploads local files to Amazon S3 storage service.

**Features:**
- Support for uploading any local file type to AWS S3 buckets
- Flexible storage path configuration with parent and subdirectory support
- Automatic directory hierarchy handling
- AWS region specification
- Returns the S3 file path after upload

**Node Parameters:**
- `bucket`: AWS S3 bucket name
- `access_key`: AWS access key ID
- `secret_key`: AWS secret access key
- `region`: AWS region name (defaults to "us-east-1")
- `parent_directory`: Parent directory path within the bucket (optional)
- `file_path`: Absolute path to the local file to upload
- `sub_dir_name` (optional): Subdirectory name under the parent directory, if set files will be stored in the subdirectory

**Directory Structure Rules:**
- If both `parent_directory` and `sub_dir_name` have values, files will be stored under `bucket/parent_directory/sub_dir_name/`
- If only `parent_directory` has a value, files will be stored under `bucket/parent_directory/`
- If only `sub_dir_name` has a value, files will be stored under `bucket/sub_dir_name/`
- If neither has a value, files will be stored directly in the bucket root

**Output:**
- `s3_file_path`: S3 path of the uploaded file (format: s3://bucket/path/to/file)

## Installation

1. Make sure you have ComfyUI installed
2. Ensure FFmpeg is installed on your system (for audio/video processing)
3. Clone this repository into the `custom_nodes` directory of ComfyUI:
```
cd ComfyUI/custom_nodes
git clone https://github.com/yourusername/ComfyUI-ToolBox.git
```
4. Install the required Python dependencies:
```
cd ComfyUI-ToolBox
pip install -r requirements.txt
```
5. Restart ComfyUI
6. The nodes should now be available in the ComfyUI interface under the "ToolBox" category

## Dependencies

The main dependencies for this project are listed in `requirements.txt`, including:
- boto3 - for AWS S3 file uploads
- FFmpeg - for audio/video processing (system-level installation required)
- requests - for API requests and file downloads
- Other Python libraries - see requirements.txt for details

## Usage Examples

### Create Image (OpenAI) Node Usage
1. Add the "Create Image (OpenAI)" node to your ComfyUI workflow (under the ToolBox/OpenAI category)
2. Enter your OpenAI API key
3. Input your desired image description (prompt)
4. Select a model (such as dall-e-3 or gpt-image-1)
5. Configure the appropriate parameters based on your selected model (size, quality, style, background, etc.)
6. Run the workflow to generate the image
7. The generated image can be used directly in ComfyUI for further processing, such as editing or applying effects with other nodes

### Video Combine Node Usage
1. Add the "Video Combine" node to your ComfyUI workflow (under the ToolBox/Video Combine category)
2. Set the paths for input video file and audio file
3. Set the output filename prefix
4. Choose the method for handling audio longer than the video (cut off audio, bounce video, or loop video)
5. Run the workflow to get the merged video file path
6. The merged video will be saved in the ComfyUI output directory

### AWS S3 Upload Node Usage
1. Add the "AWS S3 Upload" node to your ComfyUI workflow (under the ToolBox/AWS S3 category)
2. Enter your AWS S3 bucket name, access key, and secret key
3. Select the correct AWS region (e.g., "us-east-1", "eu-west-1", etc.)
4. Set the parent directory path (optional) and subdirectory name (optional) to define the storage structure
5. Enter the path of the local file to upload
6. Run the workflow to get the S3 file path of the uploaded file

## License

This project is released under the MIT License.