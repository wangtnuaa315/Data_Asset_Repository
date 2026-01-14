@ui-ux-pro-max-skill

# Role
你现在是 UI/UX Pro Max 的执行专家。请读取本地 `.agent` 文件夹中的样式定义。

# Task
将当前的“数据检索页面”完全重构为 **"CEX Trading" (中心化交易所)** 风格。
参考预设 ID: `demo/cex-trading`。

# Style Guidelines (风格指南 - CEX 特化版)
尽管交易所通常是深色，但为了适应本系统的业务属性，请使用 **"Professional Light CEX" (专业亮色交易所)** 变体（类似 Coinbase Pro 或 Binance Light）。

1. **整体布局 (Structural Layout)**:
   - 放弃“大留白”。使用 **Compact Layout (紧凑布局)**。
   - 背景色：使用极浅的冷灰 `#F7F9FC`。
   - 容器背景：纯白 `#FFFFFF`，完全去掉阴影 (No Drop Shadows)，改为使用 **1px 的硬边框** (`border: 1px solid #E6E8EA`) 来划分区域。

2. **组件映射 (Component Mapping)**:
   - **搜索栏 (The Filter Bar)**: 
     - 模仿交易所的“币对选择栏”。
     - 输入框不要做成大圆角，改为 **Height: 32px** 的紧凑矩形 (Radius: 2px)。
     - 按钮使用 **Ghost Button** (幽灵按钮) 样式，仅在 Hover 时显示浅灰色背景。
   
   - **结果展示 (The Data Grid)**:
     - 放弃“卡片式”布局，改为 **"Order Book Style" (订单簿列表)**。
     - 每一行数据的高度压缩至 `40px`。
     - 必须添加 **竖向分割线** (Vertical Dividers)。
     - 关键数据（如 ID、日期、状态码）必须强制使用 **Monospace Font (等宽字体)**，如 `Roboto Mono` 或 `JetBrains Mono`。

3. **色彩策略 (Color Strategy)**:
   - **状态色**: 使用金融级配色。
     - 告警/危险: `#F6465D` (Trading Red)
     - 安全/正常: `#0ECB81` (Trading Green)
     - 选中/高亮: `#F0B90B` (Binance Yellow) 或 `#1E2329` (Black)
   
   - **文字**:
     - 标题: `#1E2329` (接近纯黑，高对比)
     - 辅助信息: `#848E9C` (冷灰)

# Output
请根据上面的风格指南，在不影响功能的情况下重构当前的“登录页面”。