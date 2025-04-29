// ComfyUI 前端扩展 —— 为 CreateImageEditNode 添加动态输入功能
import { app } from "../../scripts/app.js";

// 调试日志 - 帮助确认扩展是否加载
console.log("正在加载 CreateImageEditNode 动态输入扩展...");

// 让我们全局导出更新输入的函数，以便检查是否正确加载
window.updateImageEditInputs = function(node) {
    console.log("手动执行 updateImageInputs", node);
    if (!node) return;

    // 获取想要的输入数量
    const desiredCount = node.widgets.find(w => w.name === "inputcount")?.value ?? 1;
    
    // 获取当前图像输入数量
    const currentCount = node.inputs.filter(input => 
        input.name && input.name.startsWith("image_") && input.type === "IMAGE"
    ).length;
    
    console.log(`当前有 ${currentCount} 个输入，目标是 ${desiredCount} 个输入`);
    
    // 不需要更改
    if (desiredCount === currentCount) {
        return;
    }
    
    // 需要删除输入
    if (desiredCount < currentCount) {
        for (let i = node.inputs.length - 1; i >= 0; i--) {
            const input = node.inputs[i];
            if (input.name && input.name.startsWith("image_")) {
                const index = parseInt(input.name.split("_")[1]);
                if (index > desiredCount) {
                    if (node.graph) node.graph.removeLink(input.link);
                    node.removeInput(i);
                }
            }
        }
    } 
    // 需要添加输入
    else if (desiredCount > currentCount) {
        for (let i = currentCount + 1; i <= desiredCount; i++) {
            node.addInput(`image_${i}`, "IMAGE");
        }
    }
    
    // 更新节点大小和画布
    if (node.computeSize) {
        node.setSize(node.computeSize());
    }
    node.setDirtyCanvas(true, true);
    if (node.graph) {
        node.graph.change();
    }
};

app.registerExtension({
    name: "ToolBox.CreateImageEditDynamicInputs",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        console.log("检查节点:", nodeData.name, nodeData.comfyClass);
        
        // 匹配我们的节点
        if (nodeData.name === "CreateImageEditNode" || 
            nodeData.comfyClass === "CreateImageEditNode") {
            
            console.log("找到匹配节点:", nodeData.name);
            
            // 在节点原型上添加更新函数
            nodeType.prototype.updateImageInputs = function() {
                window.updateImageEditInputs(this);
            };
            
            // 修改原始的 onNodeCreated 函数
            const original_onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                if (original_onNodeCreated) {
                    original_onNodeCreated.apply(this, arguments);
                }
                
                console.log("节点创建, 添加 Update inputs 按钮");
                
                // 添加更新按钮 - 确保在最后添加
                const updateBtn = this.addWidget("button", "Update inputs", "Update", () => {
                    console.log("点击了 Update inputs 按钮");
                    this.updateImageInputs();
                });
                
                // 确保按钮不会被序列化到工作流中
                updateBtn.serialize = false;
                
                console.log("按钮添加完成");
            };
        }
    },
    
    // 也使用 nodeCreated 确保在节点创建后添加按钮
    nodeCreated(node) {
        // 检查是否为我们的目标节点
        const nodeType = node.type || node.comfyClass;
        if (nodeType === "CreateImageEditNode") {
            console.log("节点已创建:", nodeType);
            
            // 确保 updateImageInputs 方法存在
            if (!node.updateImageInputs) {
                node.updateImageInputs = function() {
                    window.updateImageEditInputs(this);
                };
            }
            
            // 添加按钮（仅当不存在时）
            if (!node.widgets || !node.widgets.find(w => w.name === "Update inputs")) {
                console.log("添加 Update inputs 按钮");
                
                // 添加更新按钮
                const btn = node.addWidget("button", "Update inputs", "Update", () => {
                    console.log("点击了 Update inputs 按钮");
                    node.updateImageInputs();
                });
                
                // 确保按钮不会被序列化
                if (btn) btn.serialize = false;
                
                // 强制刷新画布
                node.graph.setDirtyCanvas(true, true);
            }
        }
    }
}); 