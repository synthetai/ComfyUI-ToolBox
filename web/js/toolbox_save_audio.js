// 使用window对象获取app和api，避免import问题
const app = window.app;
const api = window.api;

// 注册SaveAudio节点的自定义UI
if (app) {
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
                    // 获取或创建音频容器
                    let audioContainer = this.audioContainer;
                    if (!audioContainer) {
                        console.log("创建音频播放器容器");
                        // 创建音频容器
                        audioContainer = document.createElement("div");
                        audioContainer.style.padding = "10px";
                        audioContainer.style.backgroundColor = "#1a1a1a";
                        audioContainer.style.borderRadius = "5px";
                        audioContainer.style.marginTop = "10px";
                        audioContainer.style.width = "100%";
                        
                        // 将容器添加到节点的DOM元素
                        this.audioContainer = audioContainer;
                        this.widgets_panel.appendChild(audioContainer);
                    }
                    
                    // 清空容器
                    audioContainer.innerHTML = "";
                    
                    // 创建音频元素
                    const audio = document.createElement("audio");
                    audio.controls = true;
                    audio.style.width = "100%";
                    audio.style.marginBottom = "10px";
                    
                    // 获取音频文件的URL
                    const fileURL = encodeURIComponent(audioPath);
                    const audioURL = `view?filename=${fileURL}&type=output`;
                    console.log("音频URL:", audioURL);
                    
                    // 直接设置音频源
                    audio.src = audioURL;
                    
                    // 添加文件名显示
                    const fileNameDiv = document.createElement("div");
                    fileNameDiv.textContent = fileName;
                    fileNameDiv.style.fontSize = "12px";
                    fileNameDiv.style.overflow = "hidden";
                    fileNameDiv.style.textOverflow = "ellipsis";
                    fileNameDiv.style.whiteSpace = "nowrap";
                    fileNameDiv.style.marginBottom = "5px";
                    fileNameDiv.style.color = "#ddd";
                    
                    // 添加元素到容器
                    audioContainer.appendChild(fileNameDiv);
                    audioContainer.appendChild(audio);
                    
                    // 尝试加载并播放
                    audio.load();
                    console.log("音频播放器已创建");
                };
            }
        }
    });
} else {
    console.error("无法找到app对象，扩展注册失败");
} 