// ComfyUI-ToolBox 前端入口文件
console.log("ComfyUI-ToolBox 扩展加载中...");

// 导入所有扩展
import "./js/toolbox_save_audio.js";

// 导入其他扩展（如果存在）
try {
  import("./js/index.js").catch(e => console.log("无法加载index.js扩展", e));
  import("./extensions/image_edit_extension.js").catch(e => console.log("无法加载image_edit扩展", e));
} catch (e) {
  console.log("加载其他扩展时出错", e);
} 