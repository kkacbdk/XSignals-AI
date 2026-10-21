# XSignals AI · 实时监测 + 手机推送 + 信号交易（模拟/实盘）

> 基于 XSignals AI 加密货币多周期技术分析引擎的扩展项目：**定时监测行情 → Server酱 推送到手机 → 按信号自动交易（模拟/实盘）**，形成一个可观测、可回测（用模拟盘验证）的完整闭环。

⚠️ **本项目仅用于学习与研究，不构成任何投资建议。加密货币交易风险极高，请勿投入无法承受损失的资金。**

---

## ✨ 功能特性

| 功能 | 说明 |
|---|---|
| **多周期技术分析** | 15m / 1h / 4h / 1d 四个周期，60+ 专业指标（RSI、MACD、ADX、布林带、ATR、量能等） |
| **AI 中文解读** | 通过 OpenRouter 调用大模型（如 Claude），对多周期数据生成中文分析报告 |
| **实时监测 + 手机推送** | 定时抓取行情并分析，通过 [Server酱](https://sct.ftqq.com/) 推送到微信 |
| **自动交易（模拟/实盘）** | 按信号自动开/平仓，支持**模拟盘与实盘**，记录成交价、盈亏、胜率（默认模拟盘，不花真钱） |
| **多因子 + 风险控制** | 开仓需多条件同时确认；ATR 止损止盈；按风险比例计算仓位 |
| **可选网页面板** | Flask 写的手机端小面板，可查看分析、模拟下单、一键急停（PIN 保护） |
| **Windows 计划任务** | 每天 08:00–20:00 每 15 分钟自动运行，无需人工干预 |

---

## 🧠 交易决策逻辑（模拟/实盘通用）

> 核心理念：**宁可错过，不逆势、不追高、不无量交易。**

### 开仓（做多）需同时满足 8 个条件

| # | 条件 | 说明 |
|---|---|---|
| 1 | 1h 信号 = `BUY` / `STRONG BUY` | 主触发信号 |
| 2 | 1h 置信度 ≥ 60% | 过滤弱信号 |
| 3 | 高周期不逆势 | 4h + 1d 加权趋势分 > -1 |
| 4 | MACD 线 > 信号线 | 动量确认 |
| 5 | RSI < 72 | 不追超买 |
| 6 | ADX ≥ 18 | 不在死水震荡里做 |
| 7 | 成交量 ≥ 0.7x 均量 | 避免无量假突破 |
| 8 | 距压力位 ≥ 0.5% | 上方要有空间 |

### 平仓（任一触发）

- **ATR 止损**：价格 ≤ 入场价 − 1.5 × ATR
- **ATR 止盈**：价格 ≥ 入场价 + 3.0 × ATR（盈亏比 1:2）
- **信号转空**：1h 转 `SELL` 且置信度 ≥ 55%
- **高周期转空**：4h `STRONG SELL` 且置信度 ≥ 65%

### 仓位管理

- 每笔风险 = 权益 × 2%
- 按 ATR 止损距离反推仓位：`仓位 = 风险金额 ÷ 止损距离`
- 单笔最大占权益 30%，最小 10 USDT

> 所有参数均可在 `.env` 中调整，见下方配置说明。

---

## 📁 项目结构

```
XSignals-AI/
├── README.md
├── LICENSE.txt
├── DISCLAIMER.txt
├── .gitignore
├── run.bat                  # Windows：交互式分析菜单
├── web.bat                  # Windows：启动网页面板
├── install.bat              # Windows：一键安装环境
├── install.sh               # macOS/Linux：一键安装环境
├── src/
│   ├── main.py              # 分析引擎主程序（多周期 + AI）
│   ├── indicators.py        # 60+ 指标计算
│   ├── monitor.py           # 定时监测 + Server酱 推送
│   ├── paper_auto.py        # 自动交易（模拟/实盘，多因子 + 风控）
│   ├── app.py               # 可选网页面板（Flask + PIN）
│   ├── requirements.txt
│   └── .env.example         # 配置模板
└── examples/
    └── example_output.txt
```

---

## 🚀 快速开始（Windows）

1. **安装 Python 3.8+**（推荐 3.10–3.13），安装时勾选 *Add Python to PATH*
2. 双击 **`install.bat`** 自动创建虚拟环境并安装依赖
3. 复制 `src/.env.example` 为 `src/.env`，填入自己的 Key（见下）
4. 双击 **`run.bat`** 使用交互菜单；或运行 `python src/paper_auto.py` 做自动交易（默认模拟盘）

> 中国大陆网络提示：分析/模拟盘走币安**公共行情接口** `data-api.binance.vision`，无需翻墙；
> 但**实盘下单**需要访问 `api.binance.com`，需自行配置代理。

---

## ⚙️ 配置说明（`src/.env`）

| 配置项 | 必填 | 说明 |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | OpenRouter Key，用于 AI 解读 |
| `MODEL_NAME` | ✅ | 模型 ID（OpenRouter 任意模型，如 Claude、DeepSeek 等） |
| `SERVERCHAN_SENDKEY` | ✅ | Server酱 SendKey，用于微信推送 |
| `MONITOR_SYMBOL` | | 监测币种，默认 `SOLUSDT` |
| `PUSH_MODE` | | `always` / `on_change` / `on_signal` |
| `PAPER_START_BALANCE` | | 模拟账户初始资金，默认 1000 USDT |
| `PAPER_RISK_PCT` | | 每笔风险比例，默认 2% |
| `PAPER_MAX_PCT` | | 单笔最大仓位比例，默认 30% |
| `PAPER_ATR_STOP_MULT` / `PAPER_ATR_TP_MULT` | | 止损/止盈 ATR 倍数 |
| `PAPER_MIN_CONF` / `PAPER_MIN_ADX` / `PAPER_MIN_VOL` | | 开仓过滤阈值 |
| `MONITOR_START_HOUR` / `MONITOR_END_HOUR` | | 监测时段，默认 8–20 点 |
| `WEB_PIN` / `WEB_PORT` | | 网页面板 PIN 与端口 |
| `LIVE_TRADING` / `MAX_ORDER_USDT` / `BINANCE_PROXY` | | 实盘相关（默认关闭，慎用） |

---

## 📱 手机推送（Server酱）

1. 打开 https://sct.ftqq.com/ ，微信扫码登录
2. 获取 **SendKey**（`SCT` 开头）
3. 填入 `src/.env` 的 `SERVERCHAN_SENDKEY`
4. 运行 `python src/paper_auto.py` 即可收到首条推送

---

## ⏰ 定时任务（Windows 计划任务）

```bat
schtasks /Create /TN "XSignals Monitor" ^
  /TR "D:\XSignals-AI\venv\Scripts\pythonw.exe D:\XSignals-AI\src\paper_auto.py" ^
  /SC DAILY /ST 08:00 /RI 15 /DU 12:00 /F
```

> 每天 08:00 开始，每 15 分钟运行一次，持续 12 小时（到 20:00）。
> 如需 24 小时监控，改用 `/SC MINUTE /MO 15`，或把时段写入脚本判断。

---

## 🖥️ 网页面板（可选）

```bash
python src/app.py
```

浏览器打开 `http://127.0.0.1:5000`，输入 `.env` 中的 `WEB_PIN`。
可查看分析、模拟买卖（默认）、急停开关。**如需暴露到公网请自行加认证与 HTTPS，务必谨慎。**

---

## 🔐 安全建议

- **`.env` 绝对不要提交**（本项目已用 `.gitignore` 排除）
- 币安 API Key 建议**只开"读取"权限**；模拟盘/分析完全不需要交易权限
- 若要实盘：使用**独立子账户 + 小额资金 + 只开现货交易权限（绝不要提现权限）**
- Server酱 SendKey、OpenRouter Key 都属于敏感凭证，泄露后请立即重置

---

## ⚠️ 免责声明

- 本项目仅为技术学习与研究演示，**不构成投资建议**。
- 加密货币价格波动剧烈，自动化交易可能导致**全部本金损失**。
- 技术指标信号**不保证盈利**，历史表现不代表未来收益。
- 请自行了解并遵守所在国家/地区的法律法规（中国大陆对加密货币交易有明确限制）。
- 使用本项目产生的任何后果由使用者自行承担。

详见 [DISCLAIMER.txt](DISCLAIMER.txt)。

---

## 📄 开源协议

本项目基于原 XSignals AI 项目扩展，沿用其许可证（见 [LICENSE.txt](LICENSE.txt)）。

如果这个项目对你有帮助，欢迎 Star ⭐
