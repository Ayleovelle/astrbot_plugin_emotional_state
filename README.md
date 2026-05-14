# AstrBot QQ 语音电话助手

`astrbot_plugin_qq_voice_call` 是一个面向 **QQ 语音电话** 的 AstrBot 插件：用户拨打 QQ 语音电话时，插件通过 NapCat 电话桥接层接听通话，把实时 PCM 音频送入火山引擎豆包端到端实时语音大模型，再把模型返回的音频写回电话。通话结束后，插件会生成摘要，并接入 Sylanne 的记忆模块与情绪模块。

## 重要边界

公开的 OneBot v11 / NapCat 常规事件并没有稳定标准化“QQ 电话接听 + 双向实时音频流”接口。所以本插件采用“方案 1”的工程落地方式：

- AstrBot 插件负责会话管理、豆包实时语音、摘要、Sylanne 集成。
- 外部 NapCat 电话桥接层负责真实 QQ 电话接听、采集来电 PCM、播放模型返回音频。
- 如果桥接层没有实现真实电话媒体能力，本插件不能凭空接入 QQ 语音电话。

## 功能

- 识别 `qq_call_invite` 来电事件，可按配置自动接听。
- 接收 `qq_call_audio` PCM 帧并流式发送到豆包实时语音 WebSocket。
- 读取豆包返回的文本与音频，记录转写并把音频送回电话桥接层。
- 处理 `qq_call_hangup`，结束通话并生成摘要。
- 调用 Sylanne `build_emotion_memory_payload(...)` 生成带情绪状态注解的记忆 payload。
- 调用 Sylanne `observe_emotion_text(...)` 把通话摘要提交给情绪观察。
- 若安装 LivingMemory，插件会尝试通过 `add_memory` / `write_memory` / `record_memory` / `remember` 写入摘要记忆。

## 安装

```powershell
cd AstrBot\data\plugins
git clone https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call.git astrbot_plugin_qq_voice_call
```

安装依赖：

```powershell
pip install -r astrbot_plugin_qq_voice_call\requirements.txt
```

## 配置

在 AstrBot 插件配置中填写：

| 配置项 | 说明 |
| --- | --- |
| `auto_answer` | 是否自动接听 QQ 语音电话，默认 `false` |
| `start_bridge_listener` | 插件启动后是否自动监听桥接层事件 |
| `napcat_call_bridge_url` | 电话桥接层 WebSocket 地址 |
| `doubao_realtime_url` | 豆包实时语音 WebSocket 地址 |
| `doubao_app_id` | 火山引擎 App ID |
| `doubao_access_token` | 火山引擎访问密钥 / Access Token |
| `doubao_resource_id` | 实时语音资源 ID，默认 `volc.speech.dialog` |
| `doubao_model` | 端到端实时语音模型名 |
| `system_prompt` | 电话通话时给模型的系统提示词 |
| `write_sylanne_memory` | 通话结束后构建并写入 Sylanne 记忆 |
| `observe_sylanne_emotion` | 通话结束后触发 Sylanne 情绪观察 |

## 电话桥接协议

桥接层向插件发送来电：

```json
{
  "type": "qq_call_invite",
  "call_id": "call-123",
  "user_id": "10001",
  "group_id": "20002",
  "nickname": "Alice"
}
```

桥接层向插件发送 PCM：

```json
{
  "type": "qq_call_audio",
  "call_id": "call-123",
  "pcm_base64": "...",
  "sample_rate": 16000,
  "timestamp_ms": 123456,
  "sequence": 1
}
```

桥接层向插件发送挂断：

```json
{
  "type": "qq_call_hangup",
  "call_id": "call-123",
  "reason": "remote_hangup"
}
```

插件会向桥接层发送命令：

- `accept_call`
- `reject_call`
- `hangup_call`
- `send_audio`

`send_audio` 会携带 `pcm_base64`、`audio_base64`、`sample_rate`、`timestamp_ms` 和 `sequence`。

## Sylanne 接入

插件优先导入：

- `astrbot_plugin_sylanne.public_api.get_emotion_service`
- `astrbot_plugin_emotional_state.public_api.get_emotion_service`

通话结束后使用稳定公开 API：

```python
await service.build_emotion_memory_payload(
    session_key="qq-user:10001",
    memory_text="QQ 语音电话摘要...",
    source="qq_voice_call",
    include_prompt_fragment=False,
    include_raw_snapshot=False,
)

await service.observe_emotion_text(
    session_key="qq-user:10001",
    text="QQ 语音电话摘要...",
    phase="call_summary",
    role="user",
    source="qq_voice_call_summary",
    commit=True,
)
```

群聊电话会话键为 `qq-group:{group_id}:user:{user_id}`，私聊电话会话键为 `qq-user:{user_id}`。

## 命令

- `/qq_call_status`：查看当前通话数。
- `/qq_call_help`：查看桥接层与配置提醒。

## 本地验证

```powershell
py -3.13 -m unittest discover -s tests -p "test*.py" -v
py -3.13 -m py_compile __init__.py call_session.py doubao_realtime_client.py main.py napcat_call_adapter.py summary.py sylanne_bridge.py scripts\package_plugin.py
py -3.13 scripts\package_plugin.py --output dist\astrbot_plugin_qq_voice_call.zip
node scripts\plugin_zip_preflight.js dist\astrbot_plugin_qq_voice_call.zip astrbot_plugin_qq_voice_call
```
