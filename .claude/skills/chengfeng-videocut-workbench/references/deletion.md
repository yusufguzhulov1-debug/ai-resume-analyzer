# 删除已明确的对象

删除是从工程移除，不删除磁盘原件、录音、模块文件或缓存。用户已明确对象与删除动作时直接执行相应流程，不机械重复确认；“删掉这一段”无法判断是遮盖画面还是口播内容时，先澄清对象。不要自行扩大到附近句子、其他 take 或关联画面。

先按入口说明核实实际 Runtime、显式 origin、服务器 projectId；读取 `workbench commands --json` 与服务能力。下面字段是已核对的合同形状，执行时以当前入口的 `fields/required/mode` 为准。缺命令或服务能力就报告缺口，不直接修改正式 JSON，不改用另一 registry。

## 选择操作

| 对象 | 操作 | 影响 |
|---|---|---|
| 某个 visual layer | `visuals-get` → `visuals-put` | 只移除该层；不删原口播、主轨片段和素材文件 |
| 用户指定词句 | 支持时 `word-cuts-plan` → `word-cuts-commit` | 删除对应已保留内容，缩短时间线；同步检查字幕与画面层 |
| 已有主轨片段 | 优先 `segment-cuts-plan` → `segment-cuts-commit` | 按真实 clipId 删除，后续内容顺延；不是留黑或静音 |
| 无跨文档依赖的简单片段 | 受限 `edit-list-patch` | 仅在下述条件全部满足时使用 |
| 磁盘视频、录音、模块、缓存 | 不属于本 Skill | 不调用文件删除命令 |

## 只删画面层

1. `visuals-get` 读取最新 `document` 与 `revision`，用真实 layerId 确认目标。
2. 在候选文档中仅从 `layers` 移除该 ID，保留其他层及所有其他字段。
3. `visuals-put` 请求 `{ "expectedRevision": "<visuals revision>", "document": <完整候选文档> }`，命令带 `--confirmed`；不要添加不在合同中的 JSON `confirmed`。
4. 回读 `visuals-get`：该 ID 已不存在，其他层未变。原口播和主轨不应因此被删，素材仍留在资源库；当前媒体画面层合同要求 `muted:true`，不能把移除画面层当作删除原口播声音。

## 按词或主轨片段删除

### 先核实 schema、对象与版本

- `edit-list-get` 读取当前 EDL，`sources-get` 读取工程快照；删除请求的 `expectedTargetRevision` 来自 **`sources-get` 的 `data.revision`**，不是 EDL 单文件 revision、visuals revision 或 project-config revision。
- 已核对实现的 word/segment 事务均要求显式多源 **EDL schemaVersion 2**；有命令名不代表单源 schemaVersion 1 也能用。不要为删除任务偷偷升级或改写 schema。
- wordIds 来自当前 Runtime 转录/播放数据，clipIds 来自当前 EDL `segments[].id`。字幕 cue ID、句子序号、文本内容和秒数都不是 wordId。重复词句还要区分 source/instance；不凭文字匹配删除全部同名内容。
- 读取当前字幕、visuals，确认用户所指范围。单源词句删除只有在已核实服务支持单源 cuts 路径、明确当前完整语义删除集合与 apply-cut 门禁时才走对应剪口播流程；不把多源事务硬套到单源，也不覆盖原有 cuts。无法安全适配则停止并说明能力缺口。

### plan：不写工程

为这次明确的新操作生成并保存一个 operationId（1–96 位字母、数字、下划线或连字符）。请求文件是普通候选文件，不是正式工程文件。

词句请求：

```json
{
  "operationId": "<本次固定ID>",
  "expectedTargetRevision": "<sources-get revision>",
  "wordIds": ["<当前真实wordId>"],
  "confirmed": false
}
```

主轨片段请求将 `wordIds` 换成 `clipIds`；只有已明确要一起移除的受影响画面层，才增加 `removeVisualLayerIds`。**该字段仅 segment-cuts 支持，word-cuts 不接受。** 词删除的关联层需要额外处理时，停止并另行规划，不往 word 请求塞这个字段。选择列表须为 1–500 个不重复 ID。不要为了绕过错误自动删除关联层。

通过已核实的 Runtime 可执行入口，以参数数组调用：

```json
["workbench","word-cuts-plan","--api-base","<origin>","--project","<projectId>","--file","<绝对请求文件>","--json"]
```

片段使用 `segment-cuts-plan`。当前两者 `mode:"plan"` 要求 JSON `confirmed:false`，不能加 `--confirmed`。

业务响应位于 envelope 的 `data`。保存 `operationId`、`targetRevision`、`afterRevision`、`planRevision`、`summary`，核对 `committed:false`。关注：

- `summary.previousDuration / removedDuration / duration`；删掉的是否正是授权内容。
- `summary.wordIds / removedSubtitleIds / removedVisualIds / trimmedMediaIds`。
- 片段计划还给出 `removedSegments / removedRanges / removedWords / visualChanges / retainedVisualRemainders / warnings`，检查关联层移除、裁短与短残片。

部分字幕删除可能需要重新审定文字，部分 HTML 删除可能需要重新制作动画，媒体层中间挖空可能无法保留内部时钟；规划器会拒绝这些不安全映射。不要直写文件绕过，或擅自扩大删除范围。需要新的文字/动画判断或额外删除时再向用户说明具体问题。

### commit：原计划精确提交

若计划与已有授权一致，无须再问一次。复制原 plan 请求，只把 `confirmed` 改成 `true`，加入返回的 `planRevision`；保留原 operationId、expectedTargetRevision、选择列表；仅 segment 请求还需保留原 removeVisualLayerIds（若有）。

```json
["workbench","word-cuts-commit","--api-base","<同一origin>","--project","<同一projectId>","--file","<绝对commit请求文件>","--confirmed","--json"]
```

片段改用 `segment-cuts-commit`。JSON `confirmed:true` 与独立 `--confirmed` 都要符合当前合同。检查 `data.committed`、`data.revision`，并核对 `data.readback.operationId`、`state:"committed"`、`currentRevision`。不要仅以退出码或 `changed:false` 推断删除是否完成。

### 回读与异常

- 用原 operationId 查询 `operation-get`（请求 `{ "operationId": "<原ID>" }`），再读 EDL、字幕、visuals，核对时长减少、目标消失、保留内容与关联层符合计划。
- 提交或回读失联：保存原请求、origin/projectId、operationId、planRevision，停止写入；精确查询原 operation。`not_found/unknown` 不授权换 ID 重提，也不证明没有写入。
- revision 冲突：停止原提交，重读并解释变化；不能将最新 revision 偷换进旧批准方案。新计划必须是已判明的新操作，不是未知提交的重试。
- `operation-recover` 仅在查明原事务后，按明确授权使用 finish/rollback；不是通用 undo/redo。回滚整个事务可能要求当前快照仍匹配，不能覆盖后续编辑。
- 结构回读不等于试听通过。必要时检查删除边界与画面/字幕接续；没有做的视觉、听觉验收明确标未验证。

## 受限的单片段 EDL 删除

只有确认目标不需要词、cuts、字幕或关联层的跨文档同步，且当前服务器支持时，才用 `edit-list-patch`；否则优先现有 segment 事务，或报告当前 schema 的缺口。不得以 patch 绕过事务规划失败。

先 `edit-list-get`，以该响应的 revision 提交：

```json
{
  "expectedRevision": "<edit-list revision>",
  "operation": { "type": "delete", "clipId": "<真实clipId>" }
}
```

`workbench edit-list-patch ... --file <请求文件> --confirmed --json` 后回读 EDL；这是单个受保护操作，不是任意批量原子编辑。不能删光最后一段，也不删除源文件。超时后先回读，不盲重发。
