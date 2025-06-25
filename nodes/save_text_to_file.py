import os
import folder_paths

class SaveTextToFileNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True}),
                "file_name": ("STRING", {"default": "output"}),
                "file_extension": ("STRING", {"default": "txt"}),
                "output_dir": ("STRING", {"default": ""}),
                "overwrite": ("BOOLEAN", {"default": True}),
                "auto_increment": ("BOOLEAN", {"default": False})  # 自动编号开关
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("file_path", "text_output")
    FUNCTION = "save_text"
    CATEGORY = "ToolBox/File"

    def save_text(self, text, file_name, file_extension, output_dir, overwrite, auto_increment):
        # 处理输出路径
        if output_dir.strip() == "":
            # 如果用户未定义，则使用 ComfyUI 的 output 目录
            full_output_path = folder_paths.get_output_directory()
        elif os.path.isabs(output_dir):
            full_output_path = output_dir
        else:
            # 相对路径基于 ComfyUI 的 output 目录
            full_output_path = os.path.join(folder_paths.get_output_directory(), output_dir)

        # 确保输出目录存在
        os.makedirs(full_output_path, exist_ok=True)

        # 处理文件名
        if auto_increment:
            counter = 1
            while True:
                full_file_name = f"{file_name}_{counter:04d}.{file_extension}"
                file_path = os.path.join(full_output_path, full_file_name)
                if not os.path.exists(file_path):
                    break
                counter += 1
        else:
            full_file_name = f"{file_name}.{file_extension}"
            file_path = os.path.join(full_output_path, full_file_name)

        # 检查文件是否已存在（仅在非自动编号模式下）
        if not auto_increment and os.path.exists(file_path) and not overwrite:
            raise ValueError(f"文件 '{file_path}' 已存在，且 overwrite 设置为 False。操作已终止。")

        # 保存文本到文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text)

        # 返回绝对路径和输入的文本内容
        return (os.path.abspath(file_path), text)

# 节点类映射
NODE_CLASS_MAPPINGS = {
    "SaveTextToFileNode": SaveTextToFileNode
}

# 显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveTextToFileNode": "Save Text To File"
} 