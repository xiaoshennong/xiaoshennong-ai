# 小神农中医AI · 设计与动效规约（DESIGN.md）

> 全站统一的设计语言与动效规范。新页面、小程序端、第三方贡献都必须遵守。
> 动效逻辑蒸馏自 [emilkowalski/skills 的 apple-design](https://github.com/emilkowalski/skills)（WWDC《Designing Fluid Interfaces》的 Web 转译），并按中文古风审美做了本土化适配。

## 一、设计 token（见 `assets/xsn-theme.css`）

| 角色 | 值 | 用途 |
|---|---|---|
| 宣纸 `--paper` `#f7f3e9` | 页面底色 | 全局背景 |
| 卡片 `--card` `#fffdf8` | 内容卡片 | 卡片/弹窗 |
| 墨色 `--ink` `#2b2b2b` | 正文 | 文字 |
| 淡墨 `--ink-light` `#5a5a5a` | 次要文字 | 说明/副文 |
| 枯墨 `--ink-faint` `#8b7355` | 辅助文字 | 时间/注释 |
| 朱砂 `--cinnabar` `#a53232` | 主强调 | 印章/主按钮/标题 |
| 玉绿 `--jade` `#4a7c59` | 次强调 | 成功/健康/次按钮 |
| 鎏金 `--gold` `#b8860b` | 点缀 | 数字/警示/描边 |
| 深红 `--cinnabar-dark` `#8a2525` | 深色块 | 页头/用户头像 |

- 字体：`--font-serif`（Noto Serif SC / SimSun 等衬线），全站不用无衬线正文字。
- **字距**：中文大标题加宽 `0.15–0.3em`（书法端庄感；这是与 Apple 负字距规则的刻意分歧，古风审美优先）；正文 `0`；按钮/徽章 `0.08–0.12em`。
- 行高：大标题 1.05–1.15，正文 1.6–1.8。
- **emoji 禁令**：任何图标/装饰不得使用彩色 emoji，一律用汉字印章（`.xsn-seal`）或纯文字。✓/⚠/● 等纯文本符号允许在已样式化的状态元素内使用。

## 二、动效十条（全站铁律）

1. **即时响应**：可点元素必须有 `:active { transform: scale(0.97); transition: 100ms }` 按压反馈，pointer-down 瞬间响应，不等 click。
2. **临界阻尼**：所有入场/位移用 `--ease-spring: cubic-bezier(0.22,1,0.36,1)`，**禁止回弹/overshoot**。回弹只允许出现在用户手势自带惯性的场景（本项目基本没有，默认全禁）。
3. **时长档位**：按压 100ms / 微交互 150ms / 常规 300ms / 入场 600ms。不得出现 1s 以上的 UI 过渡（SVG 描边 1.6s 是唯一特许）。
4. **只动 transform 和 opacity**（外加弹窗的 filter blur）；禁止动画 width/height/top/left。
5. **空间一致性**：弹窗/浮层从触发元素位置长出（transform-origin 锚定触发点），**进出走同一条路**；用 `XSNModal.open/close`，禁止手写 display 切换。
6. **材质分层**：吸顶栏/浮层用半透明宣纸材质（`--material-paper` + `backdrop-filter: blur(20px) saturate(160%)`），内容从下面滚过；边缘渐变淡出，不用生硬 1px 分割线；玻璃表面入场要 materialize（blur+scale+opacity 同动）。
7. **滚动叙事**：IntersectionObserver 驱动 `[data-reveal]`（浮起 12px+淡入，600ms），stagger 用 `data-reveal-delay`（相邻元素 80–150ms）。粘性滚动段同样只做 transform/opacity。
8. **数字与线条**：数据用 `[data-counter]` 滚动计数（1.5s easeOutExpo）；流程/装饰线用 `[data-draw]` SVG 描边。
9. **reduced-motion 必须降级**：`prefers-reduced-motion` 时全部动效降为 200ms 透明度过渡，视差/弹簧/描边全关（主题包已内置，页面不得绕过）。
10. **克制**：视差最多三层，不做粒子飘落/闪烁/循环摆动等装饰性噪声。Delight 是 Craft 的结果，不是撒花。

## 三、组件速查

- 按钮：`.xsn-btn` + `.xsn-btn-cinnabar/-jade/-gold`（实心）或 `.xsn-btn-outline-cinnabar/-gold/-jade`（描边）
- 印章：`.xsn-seal`（22px 内联）、`.xsn-seal-lg`（40px 独立）、变体 `-jade/-gold`
- 状态徽章：`.xsn-status` + `-pending`（鎏金）/`-ok`（玉绿）/`-bad`（朱砂）
- 卡片：`.xsn-card`，悬停上浮 `.xsn-card-hover`
- 材质栏：`.xsn-material-bar`
- 弹窗：`.xsn-m-overlay > .xsn-m-dialog`，用 `XSNModal.open(overlay, triggerEl)` 打开

## 四、文案规范

- 古朴典雅中医文风，禁止网络流行语；slogan：「古有神农尝百草，今有小神农辩百症」。
- 按钮/导航用具体直接的词（「开始问诊」「医馆入驻」），不用含糊的「点击这里」。
- 涉及诊疗结论处必须带免责声明：AI 建议仅供参考，不能替代执业医师诊断。

## 五、接入方式

```html
<link rel="stylesheet" href="assets/xsn-theme.css">
<script src="assets/xsn-motion.js" defer></script>
```

主题包只新增 `xsn-*` 前缀类与 `[data-*]` 行为，**不覆盖页面既有类名**。页面特有样式继续写在页面内联 `<style>` 里。
