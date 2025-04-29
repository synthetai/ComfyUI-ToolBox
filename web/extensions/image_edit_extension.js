// ComfyUI 前端扩展 —— 为 CreateImageEditNode 添加动态输入功能
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "toolbox.openai.image_edit_dynamic_inputs",
    
    async beforeRegisterNodeDef(nodeType, nodeData) {
        // 只处理 CreateImageEditNode 节点
        if (nodeData.name !== "CreateImageEditNode") {
            return;
        }
        
        console.log("为 CreateImageEditNode 添加动态输入功能");
        
        // 定义更新输入的方法
        nodeType.prototype.updateImageInputs = function() {
            // 获取想要的输入数量
            const desiredCount = this.widgets.find(w => w.name === "inputcount")?.value ?? 1;
            
            // 获取当前图像输入数量（只计算 image_X 类型的输入）
            const currentCount = this.inputs.filter(input => 
                input.name && input.name.startsWith("image_") && input.type === "IMAGE"
            ).length;
            
            console.log(`UpdateImageInputs: 当前有 ${currentCount} 个输入，目标是 ${desiredCount} 个输入`);
            
            // 不需要更改
            if (desiredCount === currentCount) {
                return;
            }
            
            // 需要删除输入
            if (desiredCount < currentCount) {
                // 从后往前删除多余的输入
                for (let i = this.inputs.length - 1; i >= 0; i--) {
                    const input = this.inputs[i];
                    if (input.name && input.name.startsWith("image_")) {
                        const index = parseInt(input.name.split("_")[1]);
                        if (index > desiredCount) {
                            // 断开连接并删除输入
                            if (this.disconnectInput) {
                                this.disconnectInput(i);
                            }
                            this.removeInput(i);
                        }
                    }
                }
            } 
            // 需要添加输入
            else if (desiredCount > currentCount) {
                // 添加缺少的输入
                for (let i = currentCount + 1; i <= desiredCount; i++) {
                    this.addInput(`image_${i}`, "IMAGE");
                }
            }
            
            // 更新节点大小
            if (this.computeSize) {
                this.setSize(this.computeSize());
            }
            
            // 刷新画布
            this.setDirtyCanvas(true, true);
            
            // 触发图表变更
            if (this.graph) {
                this.graph.change();
            }
        };
        
        // 节点创建时添加控件
        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            // 调用原来的 onNodeCreated (如果存在)
            if (originalOnNodeCreated) {
                originalOnNodeCreated.apply(this, arguments);
            }
            
            console.log("CreateImageEditNode 节点创建，添加 Update inputs 按钮");
            
            // 添加更新按钮
            this.addWidget("button", "Update inputs", "Update", () => {
                console.log("点击了 Update inputs 按钮");
                this.updateImageInputs();
            });
        };
    }
}); 