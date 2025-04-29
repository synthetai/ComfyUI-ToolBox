// ComfyUI 前端扩展 —— 给 CreateImageEditNode 加 "inputcount + Update inputs" 逻辑
// 保存后重启 ComfyUI（或刷新浏览器）生效
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "toolbox.openai.image_edit_dynamic_inputs",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "CreateImageEditNode") return;

    // ============ 实例级工具函数 ============
    nodeType.prototype.updateImageInputs = function () {
      // 读取想要的输入数量
      const desired = this.widgets.find(w => w.name === "inputcount")?.value ?? 1;
      const current = this.inputs.filter(i => /^image_\d+$/.test(i.name)).length;

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
    };
  },
});
