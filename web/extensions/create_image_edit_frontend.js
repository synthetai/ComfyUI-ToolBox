// ComfyUI 前端扩展 —— 给 CreateImageEditNode 加 "inputcount + Update inputs" 逻辑
// 保存后重启 ComfyUI（或刷新浏览器）生效
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "toolbox.openai.image_edit_dynamic_inputs",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    // 打印节点信息以便调试
    console.log("检查节点:", nodeData.name, nodeData.type, nodeData.comfyClass);
    
    // 按照注册名称匹配，而不是类名
    if (nodeData.name !== "CreateImageEditNode" && 
        nodeData.type !== "CreateImageEditNode" && 
        nodeData.comfyClass !== "CreateImageEditNode") {
      return;
    }
    
    console.log("找到 CreateImageEditNode 节点，准备添加 Update inputs 按钮");

    // ============ 实例级工具函数 ============
    nodeType.prototype.updateImageInputs = function () {
      // 读取想要的输入数量
      const desired = this.widgets.find(w => w.name === "inputcount")?.value ?? 1;
      const current = this.inputs.filter(i => /^image_\d+$/.test(i.name)).length;
      
      console.log(`updateImageInputs: 当前 ${current} 个输入，目标 ${desired} 个输入`);

      // 1) 删除多余的
      for (let idx = this.inputs.length - 1; idx >= 0; idx--) {
        const inp = this.inputs[idx];
        if (/^image_\d+$/.test(inp.name) && parseInt(inp.name.split("_")[1]) > desired) {
          this.disconnectInput(idx);
          this.removeInput(idx);
        }
      }

      // 2) 添加不足的
      for (let i = current + 1; i <= desired; i++) {
        this.addInput(`image_${i}`, "IMAGE");  // ComfyUI 内部 IMAGE 类型
      }

      // 3) 画布刷新
      this.setSize(this.computeSize());
      this.setDirtyCanvas(true, true);
      this.graph?.change();
    };

    // ============ 创建时插入控件 ============
    const originalCreated = nodeType.prototype.onNodeCreated ?? (() => {});
    nodeType.prototype.onNodeCreated = function () {
      console.log("CreateImageEditNode 实例创建，添加控件");
      originalCreated.apply(this, arguments);

      // inputcount 控件（int slider）
      this.addWidget(
        "int",
        "inputcount",
        1,
        v => {},                   // 实时改不自动调整，等点按钮
        { min: 1, max: 10 }
      );

      // Update inputs 按钮
      const btn = this.addWidget(
        "button",
        "update inputs",
        "Update",
        () => this.updateImageInputs()
      );
      btn.serialize = false;       // 不写进工作流文件
      
      console.log("CreateImageEditNode 控件添加完成");
    };
  },
});
