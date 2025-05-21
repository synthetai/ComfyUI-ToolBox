// 使用延迟加载的方式，等待app对象可用
(function() {
    // 创建一个函数，稍后执行
    function initializeExtension() {
        if (!window.app) {
            console.warn("等待app对象加载...");
            // 如果app对象还不可用，500毫秒后再尝试
            setTimeout(initializeExtension, 500);
            return;
        }
        
        console.log("找到app对象，开始初始化Save Audio扩展");
        const app = window.app;
        
        // 注册SaveAudio节点的自定义UI
        app.registerExtension({
            name: "Toolbox.SaveAudio",
            async beforeRegisterNodeDef(nodeType, nodeData, app) {
                // 检查是否是我们的SaveAudio节点
                if (nodeData.name === "ToolboxSaveAudio") {
                    console.log("注册 ToolboxSaveAudio 节点的UI");
                    
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
                        
                        // 尝试加载
                        audio.load();
                        console.log("音频播放器已创建");
                    };
                    
                    // 修改onExecuted方法
                    const onExecuted = nodeType.prototype.onExecuted;
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
                }
            }
        });
        
        console.log("Save Audio扩展初始化完成");
    }
    
    // 当页面加载完成后开始尝试初始化
    if (document.readyState === "complete") {
        // 如果页面已经加载完成，立即尝试初始化
        initializeExtension();
    } else {
        // 否则等待页面加载完成
        window.addEventListener("load", function() {
            console.log("页面加载完成，准备初始化Save Audio扩展");
            initializeExtension();
        });
    }
})(); 