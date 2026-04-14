# WeChat Group Guard

Desktop WeChat moderation assistant for ordinary WeChat groups.

**核心原则：检测永不自动踢人，必须人工审批。**

## 功能特性

| 功能 | 状态 |
|------|------|
| 规则检测（关键词/URL/电话/域名黑名单） | ✅ |
| 伪装字符检测（微✨信、加➕V） | ✅ |
| 重复发报者追踪（24h内≥3条可疑） | ✅ |
| 忽略用户白名单 | ✅ |
| 5分钟时窗去重 | ✅ |
| Tkinter GUI审核面板（颜色分级行） | ✅ |
| GUI自动刷新（每5秒） | ✅ |
| 完整的操作审计日志 | ✅ |
| `config.yaml`配置化 | ✅ |
| Windows微信桌面读取（UI Automation） | ✅ stub，待实测 |
| 真正踢人执行器 | ✅ stub，待实测 |
| EXE打包 | 🛠 |

## 工作流程

```
微信桌面客户端
    ↓ (UI Automation)
watcher (windows_wechat.py)
    ↓ ChatMessage
detector (规则 + 评分)
    ↓ score ≥ 30?
    ├─ 否 → 仅记录日志
    └─ 是 → 写入 pending_reviews.json
                ↓
         GUI 审核面板 / 控制台
                ↓ 人工审批
         executor → 踢人 (默认 dry_run)
                ↓
         logs/review_actions.jsonl (审计)
```

## 快速开始

### Windows（真实微信功能）

```bat
:: 第一次安装
scripts\install.bat

:: 编辑 config.yaml（至少确认 dry_run: true）
notepad config.yaml

:: 启动 GUI 审核面板
scripts\run_gui.bat

:: 或者控制台轮询模式（可以看到检测日志）
python main.py --mode console
```

### Linux / macOS / Git Bash（仅模拟模式）

```bash
./scripts/install.sh
./scripts/run.sh              # GUI
python main.py --mode mock     # 单次模拟检测
python main.py --mode console  # 连续模拟轮询
```

## 配置说明

```yaml
# config.yaml
dry_run: true           # ⚠️ 默认为 true，不会真正踢人
allowed_groups: []      # 空 = 监控所有群
poll_interval: 5         # 轮询间隔（秒）
keywords:
  - 加V
  - 兼职
  - 推广
blocked_domains:
  - t.cn
  - bit.ly
trusted_senders: []     # 完全跳过检测的用户
```

## 推荐工作流

1. **测试阶段**：`dry_run: true`
   - 触发审核，观察分数和行为是否符合预期
   - 调整关键词、域名黑名单、评分阈值

2. **正式使用**：确认 dry_run 行为正确后
   - 将 `dry_run: false`
   - 所有踢人操作都会经过人工审批，不会自动执行

## 项目结构

```
wechat-group-guard/
├── main.py                     # 入口（gui / console / mock 模式）
├── config.example.yaml          # 配置模板
├── requirements.txt
├── watcher/
│   ├── windows_wechat.py       # 真实 Windows 微信读取（UI Automation）
│   ├── mock_file.py            # 模拟读取（演示用）
│   └── dedup.py                # 时窗去重
├── detector/
│   ├── rules.py                # 检测规则引擎
│   └── scoring.py              # 评分 + 重复发报者追踪
├── review/
│   ├── queue.py                # ReviewItem 数据模型
│   └── console.py              # 控制台审核交互
├── executor/
│   └── desktop_stub.py         # 踢人执行器（dry_run 模式）
├── storage/
│   ├── pending_store.py        # 待审核队列
│   ├── decision_store.py      # 审核决定记录
│   ├── ignore_store.py         # 忽略用户白名单
│   └── group_store.py          # 群列表
├── gui/
│   └── app.py                  # Tkinter GUI（自动刷新）
├── scripts/
│   ├── install.sh / .bat       # 安装脚本
│   ├── run.sh / run_gui.bat    # 运行脚本
│   ├── build_spec.spec         # PyInstaller 打包配置
│   └── probe_wechat_groups.py  # 探测微信群聊列表
├── docs/
│   ├── architecture.md
│   ├── detection-rules.md
│   ├── review-flow.md
│   └── run-mvp.md
└── samples/
    ├── mock_messages.json       # 模拟消息数据
    └── groups.json              # 群列表模板
```

## 数据文件

所有数据文件在首次运行时自动创建在 `data/` 目录下：

- `pending_reviews.json` — 待审核队列（GUI实时读取）
- `reviewer_decisions.json` — 所有审核决定
- `ignored_users.json` — 永久白名单（忽略用户）
- `messages.jsonl` — 所有扫描消息记录

日志文件：

- `logs/review_actions.jsonl` — 追加式审计日志（所有操作）
