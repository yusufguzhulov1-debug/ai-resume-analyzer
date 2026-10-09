# 高频操作方法

先按 [连接与提交](connection.md) 验证实际 CLI；以下请求仅是字段模板，所有占位必须来自当前工程回读或明确用户输入。删除见 [删除方法](deletion.md)。

## 查看与定位

- 工程当前状态：`workflow-get`。
- 片段顺序、源位置、剪后位置、播放速率、片段 ID：`edit-list-get`。
- 词句内容和位置：`playback`，请求 `{ "limit": 64 }`，按 `page.nextCursor` 原样串行翻页到结束；版本变化整轮重读，不混页。只定位已有词，不重新转录。
- 现有覆盖画面：`visuals-get`；字幕状态：`subtitles-get`；素材来源/多源实例与事务版本：`sources-get`（先验证 capability）。
- 文本匹配可在只读返回数据中完成，但要列出重复位置，用真实 wordId/source/instance 确定目标。跨源时间相同不代表同一片段。

区分四类对象：原媒体 asset、主轨片段 segment、转录词 word、覆盖画面 layer。它们的 ID 不互换。时间也分源时间、剪后时间和片段局部时间；不直接拿播放器秒数当源时间。

## 添加或替换画面

这是覆盖画面，保留主轨声音和时长，不是新媒体顺延插入。

1. 读取最新 EDL、目标词及 visuals。确认目标词还保留，来源/实例明确；检查已有层是否重叠，不假定任意层叠合成都支持。
2. 对用户指定 MP4 计算 SHA256，检查格式后调用 `media-import`：

   ```json
   { "sourcePath": "<absolute.mp4>", "expectedSourceSha256": "<actual-sha256>" }
   ```

   当前核实的媒体接口接收 H.264 / yuv420p MP4；不是 WAV/MP3 通用音轨导入。保持原素材不变；需要转码时说明并产出新文件，不覆盖输入。
3. 用返回的 `manifest.assetId` 调用 `media-get` 核对元数据。**导入成功不代表已经放进工程。**
4. 从 `visuals-get` 的完整 document 制作候选，保留其余字段及每一层；新增唯一 layer ID 或替换明确的原 layer，绝不只用新的一层覆盖整个 layers 数组。典型媒体层：

   ```json
   {
     "id": "<unique-layer-id>",
     "wordIds": ["<real-word-id>"],
     "media": {
       "assetId": "<verified-sha256>",
       "sourceIn": 0,
       "sourceOut": 2,
       "fit": "cover",
       "muted": true
     }
   }
   ```

   `sourceIn/sourceOut` 是素材局部秒数，必须落在已核实素材范围内；示例 2 秒不代表默认时长。画面位置由词锚点决定，素材选段短于词跨度会缩短画面展示，不承诺自动循环/拉伸。铺满用 cover（会裁边），完整展示用 contain（可能留边）；不可拉伸比例。替换素材后重核选段范围。
5. 文档尚不存在时，必须从当前工程取得准确 projectId/baseTranscriptRevision、合法 animationStyle，按当前 visual 合同创建 document；禁止拿 EDL revision 当 transcript revision。字段取不到则停止，不编造空壳文档。
6. `visuals-put` 请求 `{ "expectedRevision": "<visuals-revision>", "document": <complete-candidate> }`，确认标志按授权添加；再 get 核对新层和其余层、主轨时长及声音未被该操作更改。

HTML 动画仅绑定已经按当前 Runtime 模块合同发布并回读验证的 `entryPath`，放在 layer 的 `module` 字段；同一层不能同时有 module 与 media。动画制作、模块包发布及 local0/seek 适配交给现有动画 Skill；不把本机绝对 HTML 路径或任意外链直接塞进工程。

调整现有画面起止：修改它绑定的真实 wordIds 后按完整 visual 文档提交；不私加 start/end 秒数字段。已有 animation 的锚点/时长也要重新检查，发现失配交回动画作者，不静默拉伸。

## 拆分裁剪和移动已有片段

`edit-list-patch` 顶层请求：

```json
{ "expectedRevision": "<current-edl-revision>", "operation": { "type": "<supported-type>", "clipId": "<real-segment-id>" } }
```

按动作替换完整 operation：

| 动作 | operation 形状 | 语义 |
|---|---|---|
| 拆分 | `{type:"split",clipId,offset}` | offset 是片段内剪后秒数；源切点 = sourceStart + offset × playbackRate。不能贴边切；最小保留长度按当前合同 |
| 裁剪 | `{type:"trim",clipId,sourceStart,sourceEnd}` | 绝对源时间，不是剪后起止；不得越界、与同实例其他片段重叠 |
| 移动 | `{type:"move",clipId,start}` | start 是用于选择顺序的剪后位置；引擎按其他片段中点判定插入顺序，再重排磁性时间线，不是精确自由摆放 |

提交每一步后读取新的 EDL，使用返回的新片段 ID 和 revision 执行下一步；检查总时长、相邻内容、源实例、字幕和动画锚点。move/split/trim 可使 EDL 进入 manual 模式，不再用重新生成整套 cuts 的方式覆盖人工排列。

语义不清的“缩短一点”“移到中间”先确认具体范围；缺乏期望顺序时不随意计算 start。恢复与任意撤销不是本节的常规能力，不能通过覆盖整个 EDL 实现。

## 画布与适配

- `config-get` 读取当前比例及 `projectRevision`。
- 核实当前版本/工程支持后，`config-set` 请求 `{ "expectedRevision": "<projectRevision>", "config": { "aspectRatio": "<requested-ratio>" } }`。不要用 configRevision；比例须经服务验证。
- 当前该入口只修改比例，不支持任意 width/height/fps。媒体 cover/contain 属于画面层，不等于工程比例。
- 改比例后回读配置并复核已有字幕、画面裁边与动画适配；如果界面未检查，只说配置写入成功。

## 不塞进本入口的事

自动选择删哪句、改字幕文本、创作动画、云转录、导出、软件安装更新由对应 Skill 负责。本入口只做必要状态读取与明确交接，不复制各 Skill 的完整流程。

有需求但当前不能承诺：任意位置新增素材并顺延、通用复制片段、音轨混音与淡入淡出、统一撤销栈、自由关键帧/速度修改、CLI 控制预览播放。`prepend` 仅是特定片头拼接，不能用来伪装通用插入。
