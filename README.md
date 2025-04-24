# ComfyUI-ToolBox

A utility node extension for ComfyUI providing various tools for video processing and file management.

[中文文档 (Chinese Documentation)](README_CN.md)

## Overview

ComfyUI-ToolBox extends ComfyUI with specialized nodes for:
- Combining audio and video files with various synchronization methods
- Uploading files to AWS S3 storage with flexible directory structures

## Nodes

### Video Combine

The Video Combine node merges audio and video files, ideal as the final node in your workflow.

**Features:**
- Combines an input video with an audio file
- Offers multiple methods for handling longer audio (cutting, bounce playback, looping)
- Customizable output filename prefix
- Saves combined videos to ComfyUI's output directory

**Input Parameters:**
- `video_file`: Path to the input video file
- `audio_file`: Path to the input audio file
- `filename_prefix`: Output filename prefix, defaults to "output"
- `audio_handling`: Strategy for audio longer than video:
  - `cut off audio`: Truncate audio to match video duration
  - `bounce video`: Alternate forward/reverse video playback to match audio length (default)
  - `loop video`: Repeat video from start to match audio length

**Output:**
- `video_path`: Absolute path to the merged video file

### AWS S3 Upload

The AWS S3 Upload node uploads local files to Amazon S3 storage service.

**Features:**
- Supports uploading any local file type to AWS S3 buckets
- Flexible path configuration with parent and sub-directory structure
- Automatic directory hierarchy management
- AWS region specification support
- Returns the S3 path after successful upload

**Input Parameters:**
- `bucket`: AWS S3 bucket name
- `access_key`: AWS access key ID
- `secret_key`: AWS secret access key
- `region`: AWS region name (defaults to "us-east-1")
- `parent_directory`: Parent directory path within the bucket (optional)
- `file_path`: Absolute path to the local file for upload
- `sub_dir_name` (optional): Sub-directory name within the parent directory

**Directory Structure Rules:**
- If both `parent_directory` and `sub_dir_name` have values, files are stored under `bucket/parent_directory/sub_dir_name/`
- If only `parent_directory` has a value, files are stored under `bucket/parent_directory/`
- If only `sub_dir_name` has a value, files are stored under `bucket/sub_dir_name/`
- If neither has a value, files are stored directly in the bucket root

**Output:**
- `s3_file_path`: The path to the uploaded file in S3 (format: s3://bucket/path/to/file)

## Installation

1. Ensure you have ComfyUI installed
2. Make sure FFmpeg is installed on your system (required for video processing)
3. Clone this repository to your ComfyUI's `custom_nodes` directory:
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
6. The nodes should be available under the "ToolBox" category in the ComfyUI interface

## Dependencies

The main dependencies are listed in `requirements.txt`, including:
- boto3 - For AWS S3 file uploads
- FFmpeg - For video processing (requires system-level installation)
- Additional Python libraries - See requirements.txt for details

## Usage Examples

### Video Combine Node
1. Add the "Video Combine" node to your ComfyUI workflow (under ToolBox/Video Combine category)
2. Set the input video and audio file paths
3. Set the output filename prefix
4. Choose the audio handling method (cut off audio, bounce video, or loop video)
5. Run the workflow to get the merged video file path
6. The combined video will be saved in ComfyUI's output directory

### AWS S3 Upload Node
1. Add the "AWS S3 Upload" node to your ComfyUI workflow (under ToolBox/AWS S3 category)
2. Enter your AWS S3 bucket name, access key, and secret key
3. Select the correct AWS region (e.g., "us-east-1", "eu-west-1", etc.)
4. Set parent directory path (optional) and sub-directory name (optional) to define storage structure
5. Enter the local file path to upload
6. Run the workflow to get the S3 file path after upload

## License

This project is released under the MIT License.