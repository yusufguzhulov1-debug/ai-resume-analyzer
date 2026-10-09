# 连接与提交

## 验证入口，而不是猜环境

本方法要求 Runtime >=0.5.9，并实际提供所需 workbench commands 与服务 capabilities。2026-09-20 核验的公开 Plugin 配套 Runtime 0.4.11 缺少这些命令；安装 Skill 文件不等于功能可用。缺命令时停止工程操作，报告不兼容；不自动下载、升级或改动私有工程来绕过门槛。

1. 先看用户指定的工作台与工程连接信息、当前提供者工具及受信安装记录。确认本次是 chengfeng-videocut；其他工作台需使用其自身合同，本 Skill 不构成第三方适配器。
2. 从已有安装记录或用户指定位置核实 Runtime 可执行入口，以参数数组调用（可能是可执行文件，也可能是运行时加入口文件）。只读检查 `--help` 和下面的 commands；不把 Plugin/MCP 启动器当 Runtime，不通过 npx 临时下载替代品。不扫描全盘和端口。
3. 使用明确的 HTTP loopback origin，主机仅 `127.0.0.1` 或 `[::1]`。不接受路径、query、凭据、外部地址或重定向；不猜端口。若用户给的是编辑器完整地址，提取 origin 后再核实。projectId 用服务器已确认的 ID，不能仅凭同名目录或标题认定。
4. connect 与 workflow 回读核对产品、版本、PID/build、source、projectId 和所需能力。路径不存在、未启动、认证失败、缺命令分别说明，不笼统说“没安装”。只有实际连上还不够，具体 capability 也须支持。

下列是追加到已验证 Runtime 参数数组的参数，不是可直接复制的 shell 命令：

```json
["workbench","commands","--json"]
["workbench","connect","--api-base","<origin>","--json"]
["workbench","workflow-get","--api-base","<origin>","--project","<projectId>","--json"]
```

同一任务缓存已核实连接；进程、build、source 或项目身份变化，或发生连接失败时重新核验。不能凭本 Skill 较新就断言用户已安装对应能力。

## 统一调用

```json
["workbench","<operation>","--api-base","<origin>","--project","<projectId>","--file","<absolute-request.json>","--json"]
```

- 无请求体就省略 `--file`；connect 不传 project。
- 请求存为新建的普通 JSON 文件，不写回正式工程；路径有空格时仍按独立参数传递，不拼 shell 字符串。
- 写操作追加 `--confirmed`，只在用户已授权此动作与范围时使用。
- `commands` 返回的 `mode/fields/required/capability` 才是实际顶层合同。mode 为 `plan` 时 JSON `confirmed:false` 且不加确认标志；commit 的 JSON `confirmed:true` 加 `--confirmed`。不是所有名字带 plan 的命令都属于 plan 模式。
- 顶层 schema 中的 `operation/document` 仍有嵌套合同；本包方法只覆盖已核实形状。版本不匹配时读当前发行随包说明，不凭字段名猜测。
- 响应是 `ok/data` 或 `error`。失败先检查退出码、error 和业务状态，不仅看有没有 stdout。
- 一种文档的 revision 不能用于另一文档。plan/commit 同一操作保留原 operationId、expected revision、返回的 planRevision 和批准输入。

## 回读与结果未知

| 写入类型 | 核查方式 |
|---|---|
| EDL、visuals、config | 对应 get 回读目标资源；新值相同不单独证明是哪次操作写的 |
| word/segment/prepend 事务 | `operation-get` 用原 operationId，加受影响文档回读 |
| media-import | `media-get` 用原源文件 SHA256，即资产 ID |

不支持 operationId 的操作不要塞入未知字段；不支持通用 dry-run 的操作不要伪造 dry-run。收到冲突、超时或结果未知后先停止后续写入，不能更换 ID/版本来掩盖不确定性。

当前 CLI 也可能把服务返回的 revision_conflict 包在 `workbench_result_unknown` 内；检查 `error.details.serviceError/causeCode/recoveryOperation`，仍按结果未知先停写回读，不只匹配顶层错误字符串。

`connect` 不返回工程 URL，也不启动服务。`playback` 不播放或跳转 Studio。需要界面验收时用已核实的项目地址，必要时手动/受支持 UI 操作定位；没有界面能力就标未验证，不谎称已经播放。
