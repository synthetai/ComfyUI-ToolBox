import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// 注册SaveAudio节点的自定义UI
app.registerExtension({
    name: "ToolBox.SaveAudio",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 检查是否是我们的SaveAudio节点
        if (nodeData.name === "ToolboxSaveAudio") {
            console.log("注册 ToolboxSaveAudio 节点的UI");
            
            // 保存原始的onExecuted函数
            const onExecuted = nodeType.prototype.onExecuted;
            
            // 覆盖onExecuted函数
            nodeType.prototype.onExecuted = function (message) {
                // 调用原始函数
                if (onExecuted) {
                    onExecuted.apply(this, arguments);
                }
                
                console.log("ToolboxSaveAudio 节点执行完成", message);
                
                // 获取音频文件路径
                const audioPath = message.output?.audio_file;
                if (!audioPath) {
                    console.warn("未找到音频文件路径");
                    return;
                }
                
                // 获取音频文件名
                const fileName = audioPath.split('/').pop();
                console.log("音频文件名:", fileName);
                
                // 创建或更新音频播放器
                this.createAudioPlayer(audioPath, fileName);
            };
            
            // 添加创建音频播放器的方法
            nodeType.prototype.createAudioPlayer = function (audioPath, fileName) {
                // 移除已有的播放器小部件
                for (let i = this.widgets.length - 1; i >= 0; i--) {
                    if (this.widgets[i].name === "audiopreview") {
                        this.widgets.splice(i, 1);
                    }
                }
                
                // 创建音频预览元素
                const element = document.createElement("div");
                element.id = "ToolBox_AudioPreview";
                
                // 添加DOM小部件
                const previewWidget = this.addDOMWidget("audiopreview", "preview", element, {
                    serialize: false,
                    hideOnZoom: false,
                    getValue() {
                        return element.value;
                    },
                    setValue(v) {
                        element.value = v;
                    },
                });
                
                // 设置小部件大小计算方法
                previewWidget.computeSize = function (width) {
                    return [width, 70]; // 固定高度的音频播放器
                };
                
                // 设置小部件属性
                previewWidget.value = { hidden: false, paused: false };
                previewWidget.parentEl = document.createElement("div");
                previewWidget.parentEl.className = "audio_preview";
                previewWidget.parentEl.style.width = "100%";
                previewWidget.parentEl.style.padding = "5px";
                
                element.appendChild(previewWidget.parentEl);
                
                // 添加文件名显示
                const fileNameDiv = document.createElement("div");
                fileNameDiv.textContent = fileName;
                fileNameDiv.style.fontSize = "12px";
                fileNameDiv.style.overflow = "hidden";
                fileNameDiv.style.textOverflow = "ellipsis";
                fileNameDiv.style.whiteSpace = "nowrap";
                fileNameDiv.style.marginBottom = "5px";
                fileNameDiv.style.color = "#ddd";
                previewWidget.parentEl.appendChild(fileNameDiv);
                
                // 创建音频元素
                previewWidget.audioEl = document.createElement("audio");
                previewWidget.audioEl.controls = true;
                previewWidget.audioEl.loop = false;
                previewWidget.audioEl.style.width = "100%";
                
                // 监听元数据加载
                previewWidget.audioEl.addEventListener("loadedmetadata", () => {
                    console.log("音频元数据已加载");
                });
                
                // 监听错误
                previewWidget.audioEl.addEventListener("error", (e) => {
                    console.error("音频加载错误:", e);
                });
                
                // 设置音频源
                let params = {
                    filename: audioPath,
                    type: "output",
                };
                
                const audioURL = api.apiURL("/view?" + new URLSearchParams(params));
                console.log("音频URL:", audioURL);
                
                previewWidget.audioEl.src = audioURL;
                previewWidget.parentEl.appendChild(previewWidget.audioEl);
                
                // 添加加载和错误处理
                previewWidget.audioEl.onerror = function(e) {
                    console.error("音频加载失败:", e);
                    fileNameDiv.textContent = "加载失败: " + fileName;
                    fileNameDiv.style.color = "red";
                };
                
                previewWidget.audioEl.onloadeddata = function() {
                    console.log("音频加载成功:", fileName);
                };
                
                // 尝试加载
                previewWidget.audioEl.load();
                console.log("音频播放器已创建");
            };
        }
    }
}); 