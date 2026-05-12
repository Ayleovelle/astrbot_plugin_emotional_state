# AstrBot 多维情绪状态插件

> 一个给 AstrBot 使用的多维情绪状态插件。它通过 AstrBot Star 机制安装和加载，为每个会话维护可查询、可注入、可复盘的情绪、关系、群聊氛围和状态轨迹。

![版本 0.1.0-exp.1](https://img.shields.io/badge/version-0.1.0-exp.1-blue)
![AstrBot >=4.9.2,<5.0.0](https://img.shields.io/badge/AstrBot-%3E%3D4.9.2%2C%3C5.0.0-green)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-yellow)
![schema astrbot.emotion_state.v2](https://img.shields.io/badge/schema-astrbot.emotion__state.v2-purple)
![license GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-red)

`astrbot_plugin_qq_voice_call` 是一个 **AstrBot Star 插件**：安装时遵循 AstrBot Star/插件加载规范，运行时提供情绪状态总线、LLM Tools、群聊氛围识别、用户关系轨迹、LivingMemory 写入注解和公开 API。

这次发布页不展开理论依据和长公式。需要跳到仓库或查看实现，请用这个链接：[astrbot_plugin_qq_voice_call](https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call)。

## 为什么走插件安装方式

AstrBot 从 `3.4.0` 后把插件命名为 `Star`，扩展能力仍通过 Star 目录、`metadata.yaml`、`main.py` 和 `@register(...)` 加载。本项目对外就是 AstrBot 插件；区别在于它不是普通提示词插件，而是一层长期情绪状态服务。

一句话：**作为 AstrBot 插件安装，作为情绪状态层运行。**

参考：

- [AstrBot Star 使用文档](https://docs.astrbot.app/use/plugin.html)
- [AstrBot 插件开发文档](https://docs.astrbot.app/dev/star/plugin.html)
- [AstrBot WebUI 管理面板文档](https://docs-v4.astrbot.app/en/use/webui.html)

## 快速导航

| 主题 | 内容 |
| --- | --- |
| [快速安装](#快速安装) | WebUI URL、Release zip、手动 clone 三种安装方式 |
| [安装后检查](#安装后检查) | 确认 Star 被 AstrBot 载入，确认状态服务可查询 |
| [核心能力](#核心能力) | 情绪状态、群聊氛围、用户关系、状态注入、工具查询 |
| [配置](#配置) | 最小配置、常用调优、完整配置表 |
| [命令](#命令) | 会话内可直接调用的状态命令 |
| [LLM Tools](#llm-tools) | 主 LLM 可按需查询详细状态 |
| [公共 API](#公共-api) | 其他 Star/插件如何调用这个状态服务 |
| [LivingMemory 集成](#livingmemory-集成) | 写入记忆时冻结当前状态注解 |
| [测试与发布](#测试与发布) | 本地验证、打包、zip 预检、远程烟测 |
| [故障排查](#故障排查) | 安装失败、状态不变化、群聊识别、延迟问题 |

## 当前版本

| 项目 | 值 |
| --- | --- |
| Star 目录 | `astrbot_plugin_qq_voice_call` |
| 显示名 | `多维情绪状态` |
| 版本 | `0.1.0-exp.1` |
| AstrBot | `>=4.9.2,<5.0.0` |
| Python | `3.10+` |
| license | `GPL-3.0-or-later` |
| repo | `https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call` |

`metadata.yaml` 中的兼容声明：

```yaml
name: astrbot_plugin_qq_voice_call
display_name: 多维情绪状态
version: 0.1.0-exp.1
license: GPL-3.0-or-later
repo: "https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call"
astrbot_version: ">=4.9.2,<5.0.0"
```

## 快速安装：通过 Star 插件载体部署

### 方式一：WebUI URL 安装

1. 打开 AstrBot 管理面板。
2. 进入 `插件` / `Star` 页面。
3. 点击右下角 `+`。
4. 选择通过 URL 安装。
5. 填入：

```
https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call
```

安装完成后，在插件列表里确认 `多维情绪状态` 已启用。

### 方式二：上传 Release zip

从 GitHub Release 下载 `astrbot_plugin_qq_voice_call.zip`，在 AstrBot WebUI 的 `插件` / `Star` 页面点击 `+`，选择文件上传。

如果需要本地重新打包：

```powershell
py -3.13 scripts\package_plugin.py --output dist\astrbot_plugin_qq_voice_call.zip
```

上传前 zip 应该长这样，顶层必须是 `astrbot_plugin_qq_voice_call/`，不能把文件平铺在 zip 根目录：

```text
astrbot_plugin_qq_voice_call/
  __init__.py
  agent_identity.py
  main.py
  emotion_engine.py
  group_atmosphere_engine.py
  humanlike_engine.py
  lifelike_learning_engine.py
  personality_drift_engine.py
  integrated_self.py
  moral_repair_engine.py
  fallibility_engine.py
  psychological_screening.py
  prompts.py
  public_api.py
  metadata.yaml
  _conf_schema.json
  requirements.txt
  LICENSE
  README.md
  docs/
```

发布 zip 不会包含这些目录：`tests/`、`scripts/`、`dist/`、`output/`、`raw/`、`.git/`、`__pycache__/`、`literature_kb/`、`personality_literature_kb/`、`psychological_literature_kb/`、`humanlike_agent_literature_kb/`。

### 方式三：手动 clone 到 AstrBot

在 AstrBot 本体目录下执行：

```powershell
cd AstrBot\data\plugins
git clone https://github.com/Ayleovelle/astrbot_plugin_qq_voice_call.git astrbot_plugin_qq_voice_call
```

然后在 WebUI 的插件管理里重载这个 Star，或者重启 AstrBot。

## 安装后检查

在任意会话里发送：

```text
/emotion
```

如果返回当前状态，说明插件已经被载入。群聊里可以再试：

```text
/integrated_self
```

如果启用了 LLM Tool 调用，主 LLM 也可以按需调用 `query_agent_state` 查询详细状态。默认注入是 `compact`，不会把完整轨迹塞进每轮主 LLM 输入；需要详细状态时再通过 Tool 查询。插件还会估算主请求已有的 system/history/persona/tools/extra parts 长度，超出预算时只跳过“注入给主 LLM 的临时状态片段”，不停止状态更新和轨迹记录。

## 核心能力

| 能力 | 说明 |
| --- | --- |
| 会话情绪状态 | 为每个会话维护情绪值、后果、争吵/冷处理分流、关系修复倾向和简短轨迹 |
| 用户关系轨迹 | 群聊中可识别当前发言用户，并维护 speaker track |
| 群聊氛围 | 记录群聊热度、紧张度、参与节奏和 bot 是否适合插话 |
| 状态注入瘦身 | 默认只注入 compact 摘要，详细状态按需由 LLM Tool 查询 |
| 后台 post 评估 | 可选把回复后评估放到后台，同会话最多 5 个 worker，按顺序提交状态 |
| LivingMemory 注解 | 记忆写入时冻结情绪、拟人、生命化、人格漂移、道德修复、瑕疵和综合自我状态 |
| 公共 API | 其他 Star 可通过 helper 获取只读服务，不需要直接读写 KV |

生气后的走向不是固定冷战。实验分支会按人格模型、责任归因、确定性、对话可行性、修复信号和误读可能性，在 `direct_confrontation`、`cold_war`、`unfair_argument`、`careful_checking` 和 `repair_bid` 之间分流：直率/边界感强的人格更容易短促对质，回避/低表达人格更容易拉开距离；若判断可能是 bot 误读或一时任性，则进入无理争吵风险和自我修正路径。人格模型会公开导出 `direct_confrontation_bias`、`cold_war_bias`、`unfair_argument_bias`、`checking_bias` 和 `repair_orientation`，并用于调制冲突 readiness 与综合自我审计 trace。

## 配置

### 最小可用配置

默认配置已经能运行。建议先只确认这几项：

| 键 | 建议 |
| --- | --- |
| `enabled` | 保持 `true` |
| `use_llm_assessor` | 保持 `true`，需要省钱或断网时可关 |
| `emotion_provider_id` | 留空使用当前会话模型；也可选一个便宜稳定的小模型 |
| `assessment_timing` | 默认 `post`，降低回复前延迟 |
| `inject_state` | 保持 `true` |
| `state_injection_detail` | 建议 `compact` |
| `auxiliary_state_injection_detail` | 建议 `compact` |
| `background_post_assessment` | 需要更低回复延迟时开启 |
| `background_post_max_workers` | 默认 `5`，同一会话后台评估上限 |

`assessment_timing` 可选：`pre`、`post`、`both`。如果最在意实时语气，选 `pre` 或 `both`；如果最在意低延迟，选 `post`。

### 完整配置表

| 键 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `enabled` | bool | `true` | 启用多维情绪状态插件 |
| `use_llm_assessor` | bool | `true` | 使用 LLM 判断情绪观测值；关闭后使用轻量启发式回退 |
| `emotion_provider_id` | string | `""` | 情绪估计使用的 LLM Provider；留空则使用当前会话模型 |
| `low_reasoning_friendly_mode` | bool | `false` | 低推理模型友好模式 |
| `low_reasoning_max_context_chars` | int | `1200` | 低推理模型友好模式下最多读取的上下文字数 |
| `assessment_timing` | string | `post` | 情绪估计时机，可选 `pre`、`post`、`both` |
| `background_post_assessment` | bool | `false` | 把回复后的情绪评估放到后台执行 |
| `background_post_queue_limit` | int | `0` | 每个会话后台回复后评估队列上限；`0` 表示不丢轨迹 |
| `background_post_max_workers` | int | `5` | 每个会话后台回复后评估最大并发 worker 数 |
| `background_post_queue_checkpoint_enabled` | bool | `true` | 持久化后台评估队列 checkpoint，重启后可恢复未提交状态 |
| `background_post_job_lease_seconds` | float | `120` | 后台 job 租约秒数；worker 异常消失后可恢复未提交 job |
| `background_post_job_timeout_seconds` | float | `0` | 单个后台 job 超时秒数；`0` 表示不额外限制 |
| `background_post_retry_max_attempts` | int | `3` | 后台 job 失败后进入 dead-letter 前的最大尝试次数 |
| `background_post_retry_base_delay_seconds` | float | `2` | 后台重试指数退避的基础延迟秒数 |
| `background_post_retry_max_delay_seconds` | float | `60` | 后台重试指数退避的最大延迟秒数 |
| `background_post_dead_letter_limit` | int | `100` | 每会话保留的 dead-letter 摘要上限，不保存原始消息正文 |
| `background_post_diagnostics_warn_lag_count` | int | `20` | runtime diagnostics 标记后台积压数量告警的阈值 |
| `background_post_diagnostics_warn_lag_seconds` | float | `60` | runtime diagnostics 标记后台滞后秒数告警的阈值 |
| `enable_low_signal_light_assessment` | bool | `true` | 短附和、空白、表情/标点等低信号消息走本地轻评估 |
| `low_signal_max_chars` | int | `12` | 低信号轻评估的最大文本长度 |
| `agent_speaker_relationship_tracking` | bool | `true` | 群聊中同时维护会话轨道和发言人关系/情绪轨道 |
| `agent_include_speaker_in_assessment` | bool | `true` | 评估文本中标记当前发言人，便于精准判别对某人的情感变化 |
| `agent_identity_profile_limit` | int | `256` | 身份/发言人 profile 缓存上限 |
| `agent_identity_ttl_seconds` | float | `2592000.0` | 长期沉默发言人 profile 的 TTL 秒数 |
| `enable_group_atmosphere_state` | bool | `true` | 启用群聊氛围状态建模 |
| `group_atmosphere_injection_strength` | float | `0.25` | 群聊氛围状态 prompt 注入强度 |
| `group_atmosphere_alpha_base` | float | `0.34` | 群聊氛围状态基础更新步长 |
| `group_atmosphere_alpha_min` | float | `0.04` | 群聊氛围状态最小更新步长 |
| `group_atmosphere_alpha_max` | float | `0.52` | 群聊氛围状态最大更新步长 |
| `group_atmosphere_half_life_seconds` | float | `1800` | 群聊氛围状态真实时间半衰期（秒） |
| `group_atmosphere_trajectory_limit` | int | `60` | 群聊氛围状态轨迹最多保留点数 |
| `group_atmosphere_join_cooldown_turns` | int | `2` | bot 在群聊发言后，按房间轮次抑制连续插话 |
| `group_atmosphere_join_cooldown_seconds` | float | `45` | bot 在群聊发言后，按真实秒数抑制连续插话 |
| `group_atmosphere_join_cooldown_bypass_attention` | float | `0.8` | 群聊明显点名 bot 时绕过插话冷却的关注度阈值 |
| `enable_agent_causal_trail` | bool | `true` | 启用状态因果轨迹记录 |
| `agent_trail_limit` | int | `80` | 每个会话保留的状态因果轨迹条数 |
| `agent_trail_compaction_enabled` | bool | `true` | 查询因果轨迹时额外返回低信号压缩视图 |
| `agent_trail_low_signal_delta_threshold` | float | `0.03` | 轨迹压缩中判定低信号状态变化的最大 delta |
| `agent_trail_low_signal_window` | int | `5` | 连续低信号轨迹达到该窗口后压缩成摘要项 |
| `inject_state` | bool | `true` | 把当前情绪状态作为临时上下文注入 LLM 请求 |
| `state_injection_detail` | string | `compact` | 主情绪状态注入详情级别 |
| `state_injection_compact_mode` | string | `snapshot` | compact 注入模式；`snapshot` 为完整轻量快照，`diff` 为差分注入 |
| `state_injection_diff_threshold` | float | `0.08` | 主情绪 diff 注入中需要显式列出的最小状态变化 |
| `group_atmosphere_injection_diff_threshold` | float | `0.08` | 群聊氛围 diff 注入中需要显式列出的最小状态变化 |
| `state_injection_diff_force_every_turns` | int | `6` | diff 模式下每隔多少轮强制注入一次完整轻量快照 |
| `auxiliary_state_injection_detail` | string | `compact` | 辅助状态注入详情级别 |
| `state_injection_request_budget_chars` | int | `32000` | 插件侧估算的主 LLM 可见请求预算，超出时跳过状态注入 |
| `state_injection_reserved_chars` | int | `3000` | 给 Provider 包装、工具 schema、Persona 展开等下游内容保留的字符余量 |
| `state_injection_max_added_chars` | int | `2400` | 每轮主请求中本插件最多追加的临时状态注入字符数 |
| `state_injection_max_parts` | int | `8` | 每轮主请求中本插件最多追加的临时状态注入片段数 |
| `llm_tool_response_max_chars` | int | `16000` | 单次状态 LLM Tool 返回 JSON 的字符上限，超出时返回带 `truncated/degraded` 的有效 JSON |
| `enable_safety_boundary` | bool | `true` | 启用情绪后果安全边界 |
| `block_deception_manipulation_evasion_actions` | bool | `false` | 控制插件状态层是否输出欺骗/操控/逃责类硬阻断动作；默认只观察和记录风险信号 |
| `persona_modeling` | bool | `true` | 根据当前会话人格建立不同的情绪基线和反应参数 |
| `persona_influence` | float | `1` | 人格对情绪模型的影响强度 |
| `reset_on_persona_change` | bool | `true` | 检测到当前会话切换人格时重置情绪状态 |
| `max_context_chars` | int | `1600` | 情绪估计时最多读取的上下文字数 |
| `request_context_max_chars` | int | `1600` | 内部情绪评估拼接上下文时的总字数上限；不是主 LLM 最终请求预算 |
| `assessor_timeout_seconds` | float | `4` | 情绪估计 LLM 调用超时秒数 |
| `provider_id_cache_ttl_seconds` | float | `30` | 当前会话 Provider ID 短缓存秒数 |
| `passive_load_fresh_seconds` | float | `1` | 状态缓存命中后的被动衰减短路秒数 |
| `benchmark_enable_simulated_time` | bool | `false` | 基准测试专用：启用模拟时间偏移 |
| `benchmark_time_offset_seconds` | float | `0` | 基准测试专用：当前时间偏移秒数 |
| `assessor_temperature` | float | `0.1` | 情绪估计 LLM 的 temperature |
| `alpha_base` | float | `0.42` | 基础更新步长 |
| `alpha_min` | float | `0.06` | 最小更新步长 |
| `alpha_max` | float | `0.72` | 最大更新步长 |
| `baseline_decay` | float | `0.035` | 兼容项：旧版基线回归系数 |
| `baseline_half_life_seconds` | float | `21600` | 情绪向人格基线自然恢复的半衰期（秒） |
| `reactivity` | float | `0.55` | 当前事件反应系数 |
| `confidence_midpoint` | float | `0.5` | 置信门控中点 |
| `confidence_slope` | float | `7` | 置信门控斜率 |
| `min_update_interval_seconds` | float | `8` | 反刷屏最小有效更新时间间隔（秒） |
| `rapid_update_half_life_seconds` | float | `20` | 快速连续更新的门控半衰期（秒） |
| `arousal_from_surprise` | float | `0.18` | 惊讶度对唤醒度的耦合强度 |
| `dominance_control_coupling` | float | `0.12` | 支配感与可控性的耦合强度 |
| `consequence_decay` | float | `0.68` | 兼容项：旧版情绪后果每轮衰减系数 |
| `consequence_half_life_seconds` | float | `10800` | 情绪后果强度自然衰减半衰期（秒） |
| `consequence_threshold` | float | `0.48` | 触发情绪后果的阈值 |
| `consequence_strength` | float | `1` | 情绪后果强度倍率 |
| `cold_war_turns` | int | `3` | 兼容项：旧版冷处理持续轮数 |
| `cold_war_duration_seconds` | float | `1800` | 冷处理触发后的真实持续时间（秒） |
| `short_effect_duration_seconds` | float | `900` | 普通短期情绪后果持续时间（秒） |
| `allow_emotion_reset_backdoor` | bool | `true` | 允许手动/API 重置情绪状态后门 |
| `enable_psychological_screening` | bool | `false` | 启用非诊断心理状态筛查备用模块 |
| `enable_humanlike_state` | bool | `false` | 启用拟人化状态模拟模块 |
| `humanlike_injection_strength` | float | `0.35` | 拟人化状态注入强度 |
| `humanlike_alpha_base` | float | `0.3` | 拟人化状态基础更新步长 |
| `humanlike_alpha_min` | float | `0.03` | 拟人化状态最小更新步长 |
| `humanlike_alpha_max` | float | `0.46` | 拟人化状态最大更新步长 |
| `humanlike_confidence_midpoint` | float | `0.5` | 拟人化状态置信门控中点 |
| `humanlike_confidence_slope` | float | `6` | 拟人化状态置信门控斜率 |
| `humanlike_state_half_life_seconds` | float | `21600` | 拟人化状态按真实时间回落的半衰期（秒） |
| `humanlike_min_update_interval_seconds` | float | `8` | 拟人化状态反刷屏最小有效更新时间间隔（秒） |
| `humanlike_rapid_update_half_life_seconds` | float | `20` | 拟人化状态快速连续更新门控半衰期（秒） |
| `humanlike_max_impulse_per_update` | float | `0.18` | 拟人化状态单次更新最大冲量 |
| `humanlike_trajectory_limit` | int | `40` | 拟人化状态轨迹最多保留点数 |
| `humanlike_memory_write_enabled` | bool | `true` | 为记忆写入附带拟人化状态标注 |
| `humanlike_clinical_like_enabled` | bool | `false` | 启用类临床长期状态备用模块 |
| `allow_humanlike_reset_backdoor` | bool | `true` | 允许手动/API 重置拟人化状态后门 |
| `enable_lifelike_learning` | bool | `false` | 启用生命化学习状态模块 |
| `lifelike_learning_injection_strength` | float | `0.3` | 生命化学习 prompt 注入强度 |
| `lifelike_learning_half_life_seconds` | float | `2592000` | 生命化学习状态真实时间半衰期（秒） |
| `lifelike_learning_min_update_interval_seconds` | float | `10` | 生命化学习反刷屏最小有效更新时间间隔（秒） |
| `lifelike_learning_max_terms` | int | `120` | 生命化学习最多保留的新词/黑话条目数 |
| `lifelike_learning_trajectory_limit` | int | `60` | 生命化学习轨迹最多保留点数 |
| `lifelike_learning_confidence_growth` | float | `0.25` | 新词/黑话置信度每次证据增长系数 |
| `lifelike_learning_memory_write_enabled` | bool | `true` | 为记忆写入附带生命化学习状态标注 |
| `allow_lifelike_learning_reset_backdoor` | bool | `true` | 允许手动/API 重置生命化学习状态后门 |
| `enable_personality_drift` | bool | `false` | 启用真实时间人格漂移/长期适应状态 |
| `personality_drift_injection_strength` | float | `0.22` | 人格漂移 prompt 注入强度 |
| `personality_drift_apply_strength` | float | `0.65` | 人格漂移偏移应用到运行时 persona 画像的强度 |
| `personality_drift_half_life_seconds` | float | `7776000` | 人格漂移真实时间半衰期（秒） |
| `personality_drift_rapid_update_half_life_seconds` | float | `86400` | 人格漂移快速连续更新门控半衰期（秒） |
| `personality_drift_min_update_interval_seconds` | float | `21600` | 人格漂移完全有效更新的最小间隔（秒） |
| `personality_drift_learning_rate` | float | `0.055` | 人格漂移事件到特质偏移的学习率 |
| `personality_drift_event_threshold` | float | `0.12` | 人格漂移事件固化的最小信号阈值 |
| `personality_drift_max_impulse_per_update` | float | `0.015` | 单次更新最大有符号人格冲量 |
| `personality_drift_max_trait_offset` | float | `0.22` | 相对静态 persona 特质先验的最大绝对偏移 |
| `personality_drift_confidence_growth` | float | `0.1` | 每次固化漂移事件带来的置信增长 |
| `personality_drift_trajectory_limit` | int | `80` | 人格漂移轨迹最多保留点数 |
| `personality_drift_memory_write_enabled` | bool | `true` | 为记忆写入附带人格漂移状态标注 |
| `allow_personality_drift_reset_backdoor` | bool | `true` | 允许手动/API 重置人格漂移状态后门 |
| `enable_moral_repair_state` | bool | `false` | 启用道德修复/信任修复状态模拟 |
| `moral_repair_injection_strength` | float | `0.35` | 道德修复 prompt 注入强度 |
| `moral_repair_alpha_base` | float | `0.28` | 道德修复基础更新步长 |
| `moral_repair_alpha_min` | float | `0.03` | 道德修复最小更新步长 |
| `moral_repair_alpha_max` | float | `0.42` | 道德修复最大更新步长 |
| `moral_repair_confidence_midpoint` | float | `0.5` | 道德修复置信门控中点 |
| `moral_repair_confidence_slope` | float | `6` | 道德修复置信门控斜率 |
| `moral_repair_state_half_life_seconds` | float | `604800` | 道德修复真实时间半衰期（秒） |
| `moral_repair_min_update_interval_seconds` | float | `8` | 道德修复反刷屏最小有效更新时间间隔（秒） |
| `moral_repair_rapid_update_half_life_seconds` | float | `30` | 道德修复快速连续更新门控半衰期（秒） |
| `moral_repair_max_impulse_per_update` | float | `0.16` | 道德修复单次更新最大冲量 |
| `moral_repair_trajectory_limit` | int | `40` | 道德修复轨迹最多保留点数 |
| `moral_repair_memory_write_enabled` | bool | `true` | 为记忆写入附带道德修复状态标注 |
| `allow_moral_repair_reset_backdoor` | bool | `true` | 允许手动/API 重置道德修复状态后门 |
| `enable_fallibility_state` | bool | `false` | 启用低风险瑕疵/犯错模拟状态 |
| `fallibility_injection_strength` | float | `0` | 瑕疵模拟 prompt 注入强度 |
| `fallibility_alpha_base` | float | `0.22` | 瑕疵模拟基础更新步长 |
| `fallibility_alpha_min` | float | `0.02` | 瑕疵模拟最小更新步长 |
| `fallibility_alpha_max` | float | `0.34` | 瑕疵模拟最大更新步长 |
| `fallibility_confidence_midpoint` | float | `0.5` | 瑕疵模拟置信门控中点 |
| `fallibility_confidence_slope` | float | `6` | 瑕疵模拟置信门控斜率 |
| `fallibility_state_half_life_seconds` | float | `86400` | 瑕疵模拟真实时间半衰期（秒） |
| `fallibility_min_update_interval_seconds` | float | `10` | 瑕疵模拟反刷屏最小有效更新时间间隔（秒） |
| `fallibility_rapid_update_half_life_seconds` | float | `45` | 瑕疵模拟快速连续更新门控半衰期（秒） |
| `fallibility_max_impulse_per_update` | float | `0.12` | 瑕疵模拟单次更新最大冲量 |
| `fallibility_max_error_pressure` | float | `0.55` | 瑕疵模拟允许暴露的最大低风险错误压力 |
| `fallibility_trajectory_limit` | int | `40` | 瑕疵模拟轨迹最多保留点数 |
| `fallibility_memory_write_enabled` | bool | `true` | 为记忆写入附带瑕疵模拟状态标注 |
| `allow_fallibility_reset_backdoor` | bool | `true` | 允许手动/API 重置瑕疵模拟状态后门 |
| `enable_shadow_diagnostics` | bool | `false` | 启用只读阴影冲动诊断视图 |
| `enable_integrated_self_state` | bool | `true` | 启用综合自我状态总线 |
| `integrated_self_memory_write_enabled` | bool | `true` | 为记忆写入附带综合自我状态标注 |
| `integrated_self_degradation_profile` | string | `balanced` | 综合自我状态成本档位 |
| `psychological_alpha_base` | float | `0.32` | 心理筛查状态基础更新步长 |
| `psychological_alpha_min` | float | `0.04` | 心理筛查状态最小更新步长 |
| `psychological_alpha_max` | float | `0.55` | 心理筛查状态最大更新步长 |
| `psychological_state_half_life_seconds` | float | `604800` | 心理筛查长期状态自然回落半衰期（秒） |
| `psychological_crisis_half_life_seconds` | float | `2592000` | 心理红旗风险信号保留半衰期（秒） |
| `psychological_trajectory_limit` | int | `40` | 心理筛查轨迹最多保留点数 |

## 命令

| 命令 | 别名 | 用途 |
| --- | --- | --- |
| `/emotion` | `/emotion_state`、`/情绪状态` | 查看当前会话情绪摘要 |
| `/emotion_reset` | `/情绪重置` | 重置当前会话情绪状态 |
| `/emotion_model` | `/情绪模型` | 查看情绪模型当前值 |
| `/emotion_effects` | `/情绪后果` | 查看后果、边界和修复倾向 |
| `/psych_state` | `/心理筛查`、`/心理状态` | 查看非诊断心理状态筛查 |
| `/humanlike_state` | `/拟人状态`、`/有机体状态` | 查看拟人化状态 |
| `/humanlike_reset` | `/拟人状态重置` | 重置拟人化状态 |
| `/lifelike_state` | `/生命化状态`、`/共同语境` | 查看共同语境/生命化学习状态 |
| `/lifelike_reset` | `/生命化状态重置`、`/共同语境重置` | 重置生命化学习状态 |
| `/personality_drift_state` | `/人格漂移状态`、`/人格适应状态` | 查看长期人格适应状态 |
| `/personality_drift_reset` | `/人格漂移重置`、`/人格适应重置` | 重置人格适应状态 |
| `/moral_repair_state` | `/道德修复状态`、`/信任修复状态` | 查看道德修复/信任修复状态 |
| `/moral_repair_reset` | `/道德修复重置`、`/信任修复重置` | 重置道德修复状态 |
| `/integrated_self` | `/综合自我状态`、`/自我状态` | 查看综合自我仲裁摘要 |
| `/shadow_diagnostics` | `/阴影诊断`、`/阴影状态` | 查看只读维护诊断，不生成策略 |
| `/fallibility_state` | `/瑕疵状态`、`/犯错模拟状态` | 查看低风险瑕疵模拟状态 |
| `/fallibility_reset` | `/瑕疵状态重置`、`/犯错模拟重置` | 重置瑕疵模拟状态 |

## LLM Tools

| 工具 | 用途 |
| --- | --- |
| `get_bot_emotion_state` | 查询情绪状态；支持 summary/full 和 conversation/speaker track |
| `get_bot_group_atmosphere_state` | 查询群聊氛围，用于判断是否适合插话 |
| `query_agent_state` | 统一查询 emotion、group_atmosphere、integrated_self、trail、runtime 等状态 |
| `simulate_bot_emotion_update` | 只读模拟候选文本会如何影响情绪 |
| `get_bot_humanlike_state` | 查询拟人化状态 |
| `get_bot_lifelike_learning_state` | 查询共同语境/生命化学习状态 |
| `get_bot_personality_drift_state` | 查询长期人格适应状态 |
| `get_bot_moral_repair_state` | 查询道德修复/信任修复状态 |
| `get_bot_fallibility_state` | 查询低风险瑕疵模拟状态 |
| `get_bot_integrated_self_state` | 查询综合自我仲裁状态 |

## LivingMemory 集成

推荐其他记忆类 Star 在写入记忆前调用。如果 LivingMemory 的接口只能写普通 dict，也可以只写 `payload["state_annotations_at_write"]`：

```python
from astrbot_plugin_qq_voice_call.public_api import get_emotion_service

emotion = get_emotion_service(self.context)
if emotion:
    payload = await emotion.build_emotion_memory_payload(
        event,
        memory_text=memory_text,
        source="livingmemory",
        include_raw_snapshot=False,
    )
```

如果服务为 `None`，表示该状态服务未安装、未激活或版本不匹配，调用方应该跳过注解而不是自己读 KV。

如果没有 `AstrMessageEvent`，可以传 `session_key="..."`，但要确保和 AstrBot 会话 key 一致。

## 公共 API

如果不能 import helper，可以通过 AstrBot context 枚举 Star，但这种做法不保证公共 API 完整，也不会校验版本/schema。推荐始终使用 helper。

### 情绪 API

| helper | schema/version | 说明 |
| --- | --- | --- |
| `get_emotion_service` | `EMOTION_SCHEMA_VERSION`、`EMOTION_MEMORY_SCHEMA_VERSION` | 情绪、心理筛查、综合自我、生命化、人性化瑕疵相关主服务 |
| `get_humanlike_service` | `HUMANLIKE_STATE_SCHEMA_VERSION` | 拟人化状态服务 |
| `get_moral_repair_service` | `MORAL_REPAIR_STATE_SCHEMA_VERSION` | 道德修复服务 |
| `get_lifelike_learning_service` | `LIFELIKE_LEARNING_SCHEMA_VERSION` | 共同语境/生命化学习服务 |
| `get_personality_drift_service` | `PERSONALITY_DRIFT_SCHEMA_VERSION` | 长期人格适应服务 |
| `get_fallibility_service` | `FALLIBILITY_STATE_SCHEMA_VERSION` | 低风险瑕疵模拟服务 |
| `get_group_atmosphere_service` | `GROUP_ATMOSPHERE_SCHEMA_VERSION` | 群聊氛围服务 |

helper 会校验核心方法是否完整，也会校验公开版本/schema 是否匹配。

Emotion 主服务公开方法：

`get_emotion_snapshot`、`get_emotion_state`、`get_emotion_values`、`get_emotion_consequences`、`get_emotion_relationship`、`get_emotion_prompt_fragment`、`build_emotion_memory_payload`、`inject_emotion_context`、`observe_emotion_text`、`simulate_emotion_update`、`reset_emotion_state`、`get_psychological_screening_snapshot`、`get_psychological_screening_values`、`observe_psychological_text`、`simulate_psychological_update`、`reset_psychological_screening_state`、`get_integrated_self_snapshot`、`get_integrated_self_prompt_fragment`、`get_integrated_self_policy_plan`、`build_integrated_self_replay_bundle`、`replay_integrated_self_bundle`、`probe_integrated_self_compatibility`、`export_integrated_self_diagnostics`、`get_lifelike_learning_snapshot`、`get_lifelike_initiative_policy`、`get_lifelike_prompt_fragment`、`observe_lifelike_text`、`simulate_lifelike_update`、`reset_lifelike_learning_state`、`get_personality_drift_snapshot`、`get_personality_drift_values`、`get_personality_drift_prompt_fragment`、`observe_personality_drift_event`、`simulate_personality_drift_update`、`reset_personality_drift_state`、`get_fallibility_snapshot`、`get_fallibility_values`、`get_fallibility_prompt_fragment`、`observe_fallibility_text`、`simulate_fallibility_update`、`reset_fallibility_state`。

### 拟人状态 API

```python
humanlike = get_humanlike_service(self.context)
if humanlike:
    snapshot = await humanlike.get_humanlike_snapshot(event)
    if snapshot.get("enabled"):
        values = await humanlike.get_humanlike_values(event)
        energy = values.get("energy")
```

当 `enable_humanlike_state=false` 时，接口仍返回 `enabled=false` 的安全载荷，调用方不应把它当作真实生理或临床状态。

Humanlike 服务公开方法：

`get_humanlike_snapshot`、`get_humanlike_values`、`get_humanlike_prompt_fragment`、`observe_humanlike_text`、`simulate_humanlike_update`、`reset_humanlike_state`。

### 道德修复 API

`get_moral_repair_snapshot`、`get_moral_repair_values`、`get_moral_repair_prompt_fragment`、`observe_moral_repair_text`、`simulate_moral_repair_update`、`reset_moral_repair_state`。

### 生命化学习 API

`get_lifelike_learning_snapshot`、`get_lifelike_initiative_policy`、`get_lifelike_prompt_fragment`、`observe_lifelike_text`、`simulate_lifelike_update`、`reset_lifelike_learning_state`。

### 人格漂移 API

`get_personality_drift_snapshot`、`get_personality_drift_values`、`get_personality_drift_prompt_fragment`、`observe_personality_drift_event`、`simulate_personality_drift_update`、`reset_personality_drift_state`。

### 瑕疵模拟 API

`get_fallibility_snapshot`、`get_fallibility_values`、`get_fallibility_prompt_fragment`、`observe_fallibility_text`、`simulate_fallibility_update`、`reset_fallibility_state`。

### 群聊氛围 API

`get_group_atmosphere_snapshot`、`get_group_atmosphere_values`、`get_group_atmosphere_prompt_fragment`、`observe_group_atmosphere_text`、`simulate_group_atmosphere_update`、`reset_group_atmosphere_state`。

### 表达边界

这个状态服务只模拟可计算状态，不声明真实意识、真实主观体验、真实身体状态或医学诊断。心理筛查和瑕疵模拟都只用于安全分流、澄清和修复。欺骗、操控、逃责类风险默认只观察和记录，不在插件状态层输出 `blocked_actions` / `not_allowed` / 拒绝类硬阻断；如需恢复旧阻断行为，可开启 `block_deception_manipulation_evasion_actions`。上游模型、平台或其他插件的安全策略不受此开关影响。

## 群聊与用户识别

群聊里每条消息都会先进入会话轨道，再根据 AstrBot 暴露的 sender id / nickname 建立 speaker track。这样“任何人都能影响整体情绪”和“对某个人的关系变化要精准判别”可以同时成立。

默认行为：

- `agent_speaker_relationship_tracking=true`：维护群聊会话轨道和当前发言人轨道。
- `agent_include_speaker_in_assessment=true`：把当前发言人标记放入内部评估文本。
- `enable_group_atmosphere_state=true`：维护群聊氛围，用于判断 bot 是否适合加入对话。
- 如果平台适配器没有暴露 `group_id`，但能提供稳定 `sender_id`，插件会把该会话按可区分发言人的 room-mood 轨道兜底处理；纯单人私聊不会额外建立 speaker track。
- `query_agent_state(state="group_atmosphere")`：主 LLM 可按需查询房间气氛。
- `query_agent_state(state="emotion", track="speaker")`：主 LLM 可查询当前发言人的 speaker track。

## 延迟策略

默认 `assessment_timing=post`，主回复先走，回复后的状态评估再修正下一轮。需要进一步降低主链路延迟时，可以开启：

```json
{
  "background_post_assessment": true,
  "background_post_max_workers": 5,
  "background_post_queue_limit": 0,
  "state_injection_detail": "compact",
  "state_injection_compact_mode": "snapshot",
  "auxiliary_state_injection_detail": "compact"
}
```

`background_post_queue_limit=0` 表示不丢弃未处理评估，保留精细轨迹。后台 worker 空闲后会自动退出；同一会话最多使用 `background_post_max_workers` 个 worker，状态提交仍按消息顺序执行。

后台队列带 lease、retry 和 dead-letter。worker 异常或单个 job 超时时，未提交 job 会按顺序重试；连续失败超过 `background_post_retry_max_attempts` 后进入 dead-letter，并通过 `query_agent_state(state="runtime", include_runtime=true)` 或公共 API runtime diagnostics 暴露 `warning_level`、`warnings`、`retrying_count`、`dead_letter_count`、`expired_lease_count` 等字段。dead-letter 只保留序号、尝试次数和错误类型，不保存原始消息正文。

如果主 LLM 输入 token 仍偏高，先区分三件事：模型/Provider 标称上下文窗口、实际请求 token、插件追加到 `extra_user_content_parts` 的状态文本。默认 compact 状态注入通常只是短摘要和 Tool 查询提示，不会单独形成几十万上下文；更常见的来源是 AstrBot 主请求里可见的 Persona、tools/schema、历史上下文，或 Provider 把超长上下文窗口当成可用上限后未截断。插件侧的 `state_injection_request_budget_chars`、`state_injection_reserved_chars`、`state_injection_max_added_chars` 会在追加前做估算，接近或超过预算时跳过可选状态片段。

如果确认是状态注入仍偏高，可以把 `state_injection_compact_mode` 改成 `diff`。diff 模式会周期性注入完整轻量快照，中间轮次只注入显著变化；详细状态仍走 `get_bot_emotion_state(detail="full")` 或 `query_agent_state(...)` 按需查询。这个开关默认保持 `snapshot`，方便和旧行为做 A/B 对照。`request_context_max_chars` 只影响内部情绪评估读取多少上下文，不等于主 LLM 最终请求预算。

群聊里，`group_atmosphere_join_cooldown_turns` 和 `group_atmosphere_join_cooldown_seconds` 会在 bot 刚发言后降低连续插话倾向；如果群聊明显点名 bot，`group_atmosphere_join_cooldown_bypass_attention` 会允许绕过冷却。

因果轨迹不会被真正删细节；`get_agent_trail()` 和 `query_agent_state(state="trail")` 会保留原始 `items`，并额外提供 `compacted_items` 给低信号连续片段做摘要视图。`compacted_items` 只是查询响应视图，不代表每轮都会把轨迹注入主 LLM。

## 测试与发布

### 本地验证

```powershell
py -3.13 -m unittest discover -s tests -v
py -3.13 -m py_compile __init__.py agent_identity.py main.py emotion_engine.py group_atmosphere_engine.py humanlike_engine.py lifelike_learning_engine.py personality_drift_engine.py integrated_self.py moral_repair_engine.py fallibility_engine.py psychological_screening.py public_api.py prompts.py scripts\package_plugin.py
py -3.13 -m json.tool _conf_schema.json > $null
py -3.13 scripts\benchmark_plugin_hot_path.py
py -3.13 scripts\package_plugin.py --output dist\astrbot_plugin_qq_voice_call.zip
```

### zip 预检

内置 Node 文档契约如下。先设置 Node，再执行 smoke 或 preflight，不要直接写裸 `node scripts\...` 命令。

```powershell
$node = "$HOME\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
$nodeModules = "$HOME\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules"
if (Test-Path $node) { $env:NODE_PATH = $nodeModules } else { $node = "node" }

& $node scripts\plugin_zip_preflight.js dist\astrbot_plugin_qq_voice_call.zip astrbot_plugin_qq_voice_call
```

预检必要文件包括：`__init__.py`、`agent_identity.py`、`metadata.yaml`、`main.py`、`emotion_engine.py`、`group_atmosphere_engine.py`、`humanlike_engine.py`、`lifelike_learning_engine.py`、`personality_drift_engine.py`、`integrated_self.py`、`moral_repair_engine.py`、`fallibility_engine.py`、`psychological_screening.py`、`prompts.py`、`public_api.py`、`README.md`、`LICENSE`、`requirements.txt`、`_conf_schema.json`。

`scripts\plugin_zip_preflight.js` 会读取 central directory、校验 `metadata.yaml` 的 `name:`、确认 zip 位于 `astrbot_plugin_qq_voice_call/` 根目录下，并拒绝 `tests`、`scripts`、`output`、`dist`、`raw`、`.git`、`__pycache__` 等目录。

### 远程烟测

远程烟测只读，不安装、不删除、不重启：

```powershell
$env:ASTRBOT_EXPECT_PLUGIN = "astrbot_plugin_qq_voice_call"
$env:ASTRBOT_EXPECT_PLUGIN_VERSION = "0.1.0-exp.1"
$env:ASTRBOT_EXPECT_PLUGIN_DISPLAY_NAME = "多维情绪状态"
& $node scripts\remote_smoke_playwright.js
```

远程脚本使用这些环境变量：`ASTRBOT_REMOTE_URL`、`ASTRBOT_REMOTE_USERNAME`、`ASTRBOT_REMOTE_PASSWORD`、`ASTRBOT_EXPECT_PLUGIN`、`ASTRBOT_EXPECT_PLUGIN_VERSION`、`ASTRBOT_EXPECT_PLUGIN_DISPLAY_NAME`。

重点看：

- `expectedPluginChecks.ok`
- `expectedPluginChecks.ok=true`
- `expectedPluginRuntime`
- `expectedFailedPlugin`
- `failedPluginSummary`
- `hasExpectedPluginFailure`
- `unrelatedCount`
- `apiHealth`
- `uiProbeStatus`
- `selectorCounts`
- `containsExpectedPlugin=true`
- `expectedPluginRuntime.activated !== false`

`/api/plugin/source/get-failed-plugins` 可能包含其他插件的失败记录；只有目标插件出现在失败记录里才算本项目失败。`expectedFailedPlugin` 和 `failedPluginSummary.hasExpectedPluginFailure` 用于区分这件事。`API 健康摘要` 看 `/api/stat/version`、`/api/plugin/get`、`/api/plugin/source/get-failed-plugins`；`UI 尽力诊断字段` 看 `uiProbeStatus`、`selectorCounts` 和页面预览。

退出码 `5` 表示目标插件出现在 failed plugin 记录；退出码 `9` 表示 failed-plugins API 本身不健康。远程安装插件后如果旧版本已经存在，上传脚本可能返回 `already_installed_no_overwrite`，同时 `overwriteAttempted=false`，需要再看 strict smoke 是否报告版本漂移。

### 远程安装和清理

上传脚本只允许调用 `/api/plugin/install-upload`，失败上传目录只允许通过 `uninstall-failed` 清理，且必须 `delete_config=false`、`delete_data=false`。如果出现 `plugin_upload_astrbot_plugin_qq_voice_call`，可用清理脚本处理；清理脚本必须带：

```powershell
$env:ASTRBOT_EXPECT_PLUGIN = "astrbot_plugin_qq_voice_call"
$env:ASTRBOT_REMOTE_CLEAN_CONFIRM = "astrbot_plugin_qq_voice_call"
$env:ASTRBOT_REMOTE_CLEAN_FORMAL = "1"
$env:ASTRBOT_REMOTE_CLEAN_FAILED_UPLOAD = "1"
& $node scripts\remote_cleanup_plugin_playwright.js
```

清理脚本只允许处理 `astrbot_plugin_qq_voice_call` 和 `plugin_upload_astrbot_plugin_qq_voice_call`，不会触碰 LivingMemory 或其他插件。

### 当前测试覆盖方向

当前本地契约覆盖：命令/alias、LLM 工具注册名、`assessment_timing`、类型化配置表、Protocol 方法面、required tuple、schema-version、metadata 驱动的插件身份、zip/env 示例、slug/badge/version/display_name、发布包运行文件、公开 API helper、LivingMemory 注解、群聊氛围、speaker track、后台 worker 上限和完整轨迹。

### 持久迭代计划

长期研发记录保留在 `task_plan.md`、`findings.md`、`progress.md`，发布包不包含这些文件。README 只保留用户安装、使用和维护所需的信息。

## 故障排查

| 现象 | 处理 |
| --- | --- |
| WebUI URL 安装失败 | 下载 Release zip 后上传；国内网络访问 GitHub 不稳定时更推荐 zip |
| 上传 zip 后不显示 | 检查 zip 顶层是否是 `astrbot_plugin_qq_voice_call/`，不要上传 GitHub 的 source code zip |
| 提示缺运行文件 | 先跑 `scripts\plugin_zip_preflight.js`，确认 `agent_identity.py` 和 `group_atmosphere_engine.py` 在 zip 中 |
| `/emotion` 无响应 | 确认 Star 已启用，AstrBot 版本满足 `>=4.9.2,<5.0.0` |
| 群聊里识别不出用户 | 确认平台适配器能提供 sender id；没有 id 时会退回 nickname 或会话轨道 |
| bot 插话不合时宜 | 保持 `enable_group_atmosphere_state=true`，并用 `query_agent_state(state="group_atmosphere")` 查询氛围 |
| 主 LLM 输入 token 过高 | 先查 Persona/tools/schema/history/provider 截断，再看 runtime diagnostics 的 `state_injection`；compact 注入只是短摘要，`request_context_max_chars` 不是主请求预算 |
| 回复延迟高 | 使用 `assessment_timing=post`，必要时开启 `background_post_assessment=true` |
| LivingMemory 没有注解 | 确认调用 `build_emotion_memory_payload(...)`，并检查对应 `*_memory_write_enabled` 配置 |

## 更多文档

- `docs/theory.md`：设计说明和历史理论材料，发布首页不展开。
- `docs/remote_testing.md`：远程烟测和基准测试说明。
- `docs/release_branch_sync_checklist.md`：发布前分支同步和远程上传清单。
- `docs/humanlike_agent_model_roadmap.md`：拟人化状态路线图。
- `docs/humanlike_agent_iteration_log.md`：拟人化状态迭代记录。
- `docs/psychological_screening.md`：非诊断心理筛查说明。
- `docs/branching_strategy.md`：维护分支策略。

## License

GPL-3.0-or-later
