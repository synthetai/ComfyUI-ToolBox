import { app } from "../../../scripts/app.js";
import { applyTextReplacements } from "../../../scripts/utils.js";

app.registerExtension({
    name: "ToolBox.jsnodes",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // 调试输出，检查节点数据
        console.log("节点数据:", nodeData);
        
        if(!nodeData?.category?.startsWith("ToolBox")) {
            return;
        }

        // 针对 OpenAIImageEdit 节点 (无论它的名称是什么)
        if (nodeData.name === "OpenAIImageEdit" || 
            nodeData.type === "OpenAIImageEdit" ||
            nodeData.comfyClass === "OpenAIImageEdit" || 
            (nodeData.name && nodeData.name.includes("ImageEdit"))) {
            
            console.log(`找到 Image Edit 节点: ${nodeData.name}`);
            
            nodeType.prototype.onNodeCreated = function () {
                // 添加这个属性以便在后续调试中识别
                this.nodeName = nodeData.name;
                console.log(`创建节点 ${this.nodeName}，添加 Update inputs 按钮`);
                
                this._type = "IMAGE";
                
                // 添加按钮
                this.addWidget("button", "Update inputs", null, () => {
                    console.log(`点击了 ${this.nodeName} 的 Update inputs 按钮`);
                    
                    if (!this.inputs) {
                        this.inputs = [];
                    }
                    const target_number_of_inputs = this.widgets.find(w => w.name === "inputcount")["value"];
                    console.log(`目标输入数量: ${target_number_of_inputs}`);
                    
                    const num_inputs = this.inputs.filter(input => input.type === this._type).length;
                    console.log(`当前输入数量: ${num_inputs}`);
                    
                    if(target_number_of_inputs === num_inputs) {
                        console.log("输入数量相同，不需要更新");
                        return; // already set, do nothing
                    }
                    
                    if(target_number_of_inputs < num_inputs) {
                        const inputs_to_remove = num_inputs - target_number_of_inputs;
                        console.log(`需要移除 ${inputs_to_remove} 个输入`);
                        
                        for(let i = 0; i < inputs_to_remove; i++) {
                            this.removeInput(this.inputs.length - 1);
                        }
                    }
                    else {
                        console.log(`需要添加输入从 ${num_inputs+1} 到 ${target_number_of_inputs}`);
                        
                        for(let i = num_inputs+1; i <= target_number_of_inputs; ++i) {
                            this.addInput(`image_${i}`, this._type);
                            console.log(`添加了输入: image_${i}`);
                        }
                    }
                    
                    // 设置画布为脏状态，触发重绘
                    this.setDirtyCanvas(true, true);
                    // 触发图表变更事件
                    this.graph.change();
                    
                    console.log("更新完成");
                });
            };
        }
        
        // 针对 OpenAI_SaveToFile 节点
        if (nodeData.name === "OpenAI_SaveToFile" || 
            nodeData.type === "OpenAI_SaveToFile" ||
            nodeData.comfyClass === "OpenAI_SaveToFile") {
            
            console.log(`找到 SaveToFile 节点: ${nodeData.name}`);
            
            nodeType.prototype.onNodeCreated = function () {
                this._type = "IMAGE";
                this.addWidget("button", "Update inputs", null, () => {
                    if (!this.inputs) {
                        this.inputs = [];
                    }
                    const target_number_of_inputs = this.widgets.find(w => w.name === "inputcount")["value"];
                    const num_inputs = this.inputs.filter(input => input.type === this._type).length;
                    
                    if(target_number_of_inputs === num_inputs) return; // already set, do nothing
                    
                    if(target_number_of_inputs < num_inputs) {
                        const inputs_to_remove = num_inputs - target_number_of_inputs;
                        for(let i = 0; i < inputs_to_remove; i++) {
                            this.removeInput(this.inputs.length - 1);
                        }
                    }
                    else {
                        for(let i = num_inputs+1; i <= target_number_of_inputs; ++i)
                            this.addInput(`image_${i}`, this._type);
                    }
                    
                    // 设置画布为脏状态，触发重绘
                    this.setDirtyCanvas(true, true);
                    // 触发图表变更事件
                    this.graph.change();
                });
            };
        }
    },
    async setup() {
        // Any additional setup code可以在这里添加
        console.log("ToolBox.jsnodes 设置完成");
    }
}); 