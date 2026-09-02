# 掐丝珐琅纪念品设计

当用户想把人物、宠物、风景、合照或纪念照片转译为真实掐丝珐琅工艺的个性化纪念品成品摄影图时使用。适用于设计钥匙扣、冰箱贴、包挂、手机挂件、吊坠、徽章、纪念章和小型纪念牌，并支持选择产品载体、珐琅风格、金属颜色及展示方式。仅生成视觉概念图，不提供可直接投产的 CAD、开模图或生产证明。

这是一个可安装的 Agent Skill，也是持续扩充的产品模板库：模板、预览图和质量规则会随着真实使用场景迭代。

## 能做什么

- 保留参考照片中的人物、宠物、姿态、服饰、场景和核心构图；
- 把画面转译为真实金属掐丝、烧制珐琅和完整产品结构；
- 支持钥匙扣、冰箱贴、包挂、手机挂件、吊坠、徽章、纪念章和小型纪念牌；
- 支持经典鎏金、现代极简、东方宫廷、清透宝石釉、复古铜胎和柔和雅致等风格；
- 支持单款、风格对比、产品系列和生成前提示词审核。

## 安装

```bash
npx -y skills add jjd0324/cloisonne-keepsake-design -g --all
```

## 使用

安装后，可以这样开始：

> 使用 $cloisonne-keepsake-design 将我提供的照片设计成真实掐丝珐琅纪念品成品图。

## 模板画廊

以下预览图是可公开复用的通用场景示意，不包含或复刻任何用户原始照片。每个模板均含适配参考图、产品结构、可复制提示词和验收点。

| 海岛旅行钥匙扣 | 瀑布建筑冰箱贴 | 城市夜景包挂 | 人与宠物吊坠 |
| --- | --- | --- | --- |
| [<img src="skills/cloisonne-keepsake-design/assets/template-previews/01-tropical-beach-keychain.png" width="180" alt="海岛旅行钥匙扣预览">](skills/cloisonne-keepsake-design/references/templates/01-tropical-beach-keychain.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/02-rain-vortex-magnet.png" width="180" alt="瀑布建筑冰箱贴预览">](skills/cloisonne-keepsake-design/references/templates/02-rain-vortex-magnet.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/03-city-night-bag-charm.png" width="180" alt="城市夜景包挂预览">](skills/cloisonne-keepsake-design/references/templates/03-city-night-bag-charm.md) | [<img src="skills/cloisonne-keepsake-design/assets/template-previews/04-cat-companion-pendant.png" width="180" alt="人与宠物吊坠预览">](skills/cloisonne-keepsake-design/references/templates/04-cat-companion-pendant.md) |

查看完整的 [模板索引](skills/cloisonne-keepsake-design/references/templates/README.md)。

## 仓库结构

```text
skills/cloisonne-keepsake-design/
├── SKILL.md                         # 可安装的主 Skill
├── agents/openai.yaml               # Codex 显示与调用信息
├── assets/template-previews/        # 通用模板预览图
└── references/
    ├── product-presets.md           # 产品载体规则
    ├── style-presets.md             # 珐琅风格规则
    ├── quality-checklist.md         # 视觉验收规则
    └── templates/                   # 可复制场景模板
```

## 持续维护

- 新增模板前，请先参照 [贡献规则](CONTRIBUTING.md)；
- 维护节奏与质量门槛见 [维护说明](skills/cloisonne-keepsake-design/references/maintenance.md)；
- 每次提交都会运行基础结构校验，避免断链、遗漏预览或把私人路径写入公开仓库。

完整更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## 运行依赖

- 支持 Agent Skills 的客户端；
- 能读取用户提供的参考图片；
- 可用的图片生成工具。Codex 内置图片生成能力可直接使用，不需要把 API Key 写入本仓库。

## 边界与隐私

- 本 Skill 生成产品概念摄影图，不提供可直接投产的 CAD、开模图、报价或生产证明；
- 不要把未经授权的人像或私人照片上传、公开或写进 Skill；
- 仓库不包含作者的参考照片、生成结果、评测样本、预期答案、本机路径、密钥或运行记录。

## 内容

本仓库只发布运行这个 Skill 所需的文件、通用模板和非可识别的预览图。本地评测样本、预期答案、用户原图、私人路径、密钥和运行记录不包含在公开包中。
