# 掐丝珐琅纪念品设计

把人物、宠物、旅行、合照或建筑照片转译为真实掐丝珐琅（景泰蓝 / cloisonné）纪念品的产品摄影概念图。它适合钥匙扣、冰箱贴、包挂、手机挂件、吊坠、徽章、装饰挂件和小型纪念牌；重点是完整的金属结构、烧制珐琅质感与产品展示，而不是给照片套一个普通滤镜。

这是一个可安装的 Agent Skill，也是持续维护的模板库。它只交付视觉概念，不提供可直接投产的 CAD、开模图、工程尺寸、报价或生产证明。

## 能做什么

- 保留参考照片中的主体数量、姿态、服饰、场景和核心构图；
- 将画面拆分为细致金属掐丝与烧制珐琅色区，呈现玻璃光泽、轻微起伏与精致反光；
- 选择匹配构图的产品载体、轮廓、金属颜色、五金结构与展示方式；
- 生成单款、风格对比、产品系列、工艺验证双视图，或先进行提示词审核；
- 在复杂构图下明确哪些信息必须保留、哪些细节会被有意简化。

## 安装

默认使用交互式安装：

```bash
npx -y skills add jjd0324/cloisonne-keepsake-design
```

如果你已经了解自己的 Agent 环境，并希望把它全局安装到所有可用客户端，可使用高级选项：

```bash
npx -y skills add jjd0324/cloisonne-keepsake-design -g --all
```

## 使用与宿主差异

在支持 ChatGPT Skills 选择界面的客户端中，可用 `@` 选择本 Skill；在 Codex CLI / IDE 中可用 `$cloisonne-keepsake-design` 或 `/skills` 显式调用。自动调用由各宿主根据描述匹配，不能保证每个客户端行为一致。

示例：

> 使用 $cloisonne-keepsake-design 将我提供的照片设计成真实掐丝珐琅纪念品成品图。

如果当前环境不能读取图片或没有图片生成工具，Skill 应只交付已标注状态的提示词、设计规格与验收规则，不假装已经生成图片。

## 模板画廊

以下是可公开复用的通用 AI 概念预览。它们不包含、也不复刻任何用户原始照片；每个模板均含适配参考图、产品结构、可复制提示词和验收点。

| 海岛旅行钥匙扣 | 瀑布建筑冰箱贴 | 城市夜景包挂 | 人与宠物吊坠 |
| --- | --- | --- | --- |
| [<img src="skills/cloisonne-keepsake-design/assets/template-previews/01-tropical-beach-keychain.png" width="180" alt="海岛旅行钥匙扣预览">](skills/cloisonne-keepsake-design/references/templates/01-tropical-beach-keychain.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/02-rain-vortex-magnet.png" width="180" alt="瀑布建筑冰箱贴预览">](skills/cloisonne-keepsake-design/references/templates/02-rain-vortex-magnet.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/03-city-night-bag-charm.png" width="180" alt="城市夜景包挂预览">](skills/cloisonne-keepsake-design/references/templates/03-city-night-bag-charm.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/04-cat-companion-pendant.png" width="180" alt="人与宠物吊坠预览">](skills/cloisonne-keepsake-design/references/templates/04-cat-companion-pendant.md) |

| 山野徒步徽章 | 宠物肖像手机挂件 | 合影里程碑纪念牌 | 花园窗景装饰挂件 |
| --- | --- | --- | --- |
| [<img src="skills/cloisonne-keepsake-design/assets/template-previews/05-mountain-hike-badge.png" width="180" alt="山野徒步徽章预览">](skills/cloisonne-keepsake-design/references/templates/05-mountain-hike-badge.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/06-pet-portrait-phone-charm.png" width="180" alt="宠物肖像手机挂件预览">](skills/cloisonne-keepsake-design/references/templates/06-pet-portrait-phone-charm.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/07-group-milestone-plaque.png" width="180" alt="合影里程碑纪念牌预览">](skills/cloisonne-keepsake-design/references/templates/07-group-milestone-plaque.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/08-garden-window-ornament.png" width="180" alt="花园窗景装饰挂件预览">](skills/cloisonne-keepsake-design/references/templates/08-garden-window-ornament.md) |

查看完整的 [模板索引](skills/cloisonne-keepsake-design/references/templates/README.md)。

## 公开评测基线

[`evals/public/`](evals/public/README.md) 提供的是可公开复核的合成契约：触发边界、行为约束与人工视觉抽检量表。它用于防止规则和文件结构回退，不是对任意宿主自动路由、人物一致性或模型视觉稳定性的自动证明。

不提交用户原图、私人评测、真实运行记录、预期生成图或任何可识别个人信息。

## 仓库结构

```text
skills/cloisonne-keepsake-design/
├── SKILL.md                         # 可安装的主 Skill
├── agents/openai.yaml               # UI 与调用信息
├── assets/template-previews/        # 通用 AI 概念预览图
└── references/
    ├── product-presets.md           # 产品载体规则
    ├── style-presets.md             # 珐琅风格规则
    ├── composition-complexity.md    # 复杂构图简化与载体选择
    ├── delivery-format.md           # 结构化交付与打样沟通 Brief
    ├── quality-checklist.md         # 视觉验收规则
    └── templates/                   # 可复制场景模板
evals/public/                        # 公开、合成的评测契约
scripts/validate_skill.py            # 结构、隐私、链接与 PNG 校验
tests/                               # 校验器回归测试
```

## 持续维护

- 新增模板前，请先参照 [贡献规则](CONTRIBUTING.md)；
- 维护节奏与质量门槛见 [维护说明](skills/cloisonne-keepsake-design/references/maintenance.md)；
- 每次提交都会校验 YAML、模板清单、本地链接、路径越界、PNG 完整性和公开隐私标记；
- 完整更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## 授权

- 代码、文档与模板按 [MIT License](LICENSE) 发布；
- `assets/template-previews/` 下的 8 张通用 AI 概念预览图按 [CC BY 4.0](ASSETS-LICENSE.md) 发布：允许商用、改编与再发布，但必须署名、链接许可证并标明改动；
- 这些预览是概念效果图，不是已制造实物或量产可行性证明。用户输入照片和外部图像服务生成的输出仍受各自权利与服务条款约束。

## 边界与隐私

- 本 Skill 生成产品概念摄影图，不提供可直接投产的 CAD、开模图、报价或生产证明；
- 不要把未经授权的人像或私人照片上传、公开或写进 Skill；
- 公开仓库只包含通用规则、非可识别模板预览和合成评测契约，不包含基于用户原图的生成结果、本机路径、密钥或运行记录。
