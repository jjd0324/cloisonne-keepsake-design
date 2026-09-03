# 公开评测契约

这些文件是 Skill 的公开、合成回归基线，覆盖参考图、纯文字、参考图加文字三种输入路线，以及风格选择、展示形式选择、开放载体适配、隐私与生产边界；不包含用户原图、私人文字内容、私人运行记录、真实生成图或标准视觉答案。

- `routing-cases.jsonl`：应触发与不应触发的路由边界样本；
- `behavior-cases.jsonl`：使用 Skill 后必须遵守的行为契约；
- `visual-rubric.md`：对实际生成结果进行人工或人工辅助抽检的量表。

CI 只验证 JSONL 格式、最小样本数、文件关系与静态约束；它不会调用图像模型，也不应被解读为自动证明人物一致性、隐式路由或视觉质量。

## JSONL 约定

每行都是独立 JSON 对象。`routing-cases.jsonl` 使用 `id`、`intent`、`prompt` 和 `reason`；`intent` 只能是 `should_trigger` 或 `should_not_trigger`。`behavior-cases.jsonl` 使用 `id`、`request`、`must` 和 `must_not`，后两项均为字符串数组。
