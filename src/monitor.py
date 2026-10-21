# -*- coding: utf-8 -*-
"""
monitor.py — 在 08:00-20:00 时段内每 15 分钟监测指定币种，并通过 Server酱 推送到微信。
由 Windows 任务计划程序调用。
"""
import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# pythonw 无控制台：先把 stdout/stderr 重定向到本次运行的日志文件
_run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
_log_path = os.path.join(LOG_DIR, "monitor_{}.log".format(_run_ts))
_log_file = open(_log_path, "w", encoding="utf-8", buffering=1)

_orig_out = sys.stdout
if _orig_out is not None and not _orig_out.isatty():
    try:
        _orig_out.reconfigure(encoding="utf-8")
    except Exception:
        pass


class _Tee:
    def __init__(self, file_obj, *streams):
        self.file_obj = file_obj
        self.streams = [s for s in streams if s is not None]

    def write(self, s):
        for st in self.streams:
            try:
                st.write(s)
            except Exception:
                pass
        try:
            self.file_obj.write(s)
        except Exception:
            pass

    def flush(self):
        for st in self.streams:
            try:
                st.flush()
            except Exception:
                pass
        try:
            self.file_obj.flush()
        except Exception:
            pass


sys.stdout = _Tee(_log_file, _orig_out)
sys.stderr = sys.stdout

# 导入主程序：会加载 .env、应用网络与编码补丁
from main import AdvancedTradingBot
from dotenv import load_dotenv
load_dotenv()
import requests

SYMBOL = os.getenv("MONITOR_SYMBOL", "SOLUSDT")
SENDKEY = os.getenv("SERVERCHAN_SENDKEY", "").strip()
PUSH_MODE = os.getenv("PUSH_MODE", "always").strip().lower()
START_HOUR = int(os.getenv("MONITOR_START_HOUR", "8"))
END_HOUR = int(os.getenv("MONITOR_END_HOUR", "20"))
SIMPLIFY_ON_FAIL = os.getenv("SIMPLIFY_ON_FAIL", "true").strip().lower() in ("1", "true", "yes")
STATE_FILE = os.path.join(LOG_DIR, ".monitor_state.json")


def _signal_map(result):
    m = {}
    for tf, data in result.get("multi_tf_analysis", {}).items():
        if "analysis" in data:
            m[tf] = data["analysis"]["overall_signal"]["signal"]
    return m


def _avg_conf(result):
    vals = []
    for tf, data in result.get("multi_tf_analysis", {}).items():
        if "analysis" in data:
            vals.append(data["analysis"]["overall_signal"]["confidence"])
    return sum(vals) / len(vals) if vals else 0.0


def _key_levels(result):
    for tf in ("1h", "4h", "15m", "1d"):
        data = result.get("multi_tf_analysis", {}).get(tf)
        if data and "analysis" in data:
            return data["analysis"]["support_resistance"]
    return None


def _load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception:
        pass


def _send_serverchan(title, desp):
    if not SENDKEY:
        print("[WARN] 未配置 SERVERCHAN_SENDKEY，跳过推送")
        return False
    if len(title) > 32:
        title = title[:32]
    url = "https://sctapi.ftqq.com/{}.send".format(SENDKEY)
    try:
        r = requests.post(url, data={"title": title, "desp": desp}, timeout=30)
        data = r.json()
        ok = (data.get("code") == 0)
        print("Server酱推送结果: {}".format(data))
        return ok
    except Exception as e:
        print("[ERROR] Server酱推送异常: {}".format(e))
        return False


def _build_full(symbol, signals, avg, sr, ai):
    parts = ["## {} 多周期信号".format(symbol), ""]
    parts.append("\n".join("{}: {}".format(k, v) for k, v in signals.items()))
    parts.append("")
    parts.append("**平均置信度: {:.1f}%**".format(avg))
    parts.append("")
    if sr:
        parts.append("## 关键价位")
        parts.append("现价 ${:.4f}".format(sr["current_price"]))
        parts.append("支撑 ${:.4f}".format(sr["support"]))
        parts.append("压力 ${:.4f}".format(sr["resistance"]))
        parts.append("")
    parts.append("## AI 完整解读")
    parts.append("")
    parts.append(ai)
    parts.append("")
    parts.append("> 仅供学习研究，不构成投资建议。")
    return "\n".join(parts)


def _build_simple(symbol, signals, avg, sr, ai):
    sig = " | ".join("{}:{}".format(k, v) for k, v in signals.items())
    level = ""
    if sr:
        level = " 现价${:.4f} 支撑${:.4f} 压力${:.4f}".format(
            sr["current_price"], sr["support"], sr["resistance"])
    short_ai = " ".join(ai.split())
    if len(short_ai) > 600:
        short_ai = short_ai[:600] + "…"
    return "{}: {}\n平均置信度 {:.1f}%{}".format(symbol, sig, avg, level) + "\n\n" + short_ai


def main(force=False):
    now = datetime.now()
    if not force and not (START_HOUR <= now.hour < END_HOUR):
        print("当前不在监测时段 ({:02d}:00-{:02d}:00)，退出".format(START_HOUR, END_HOUR))
        return

    print("===== 监测 {} @ {} =====".format(SYMBOL, now.strftime("%Y-%m-%d %H:%M:%S")))
    bot = AdvancedTradingBot()
    result = bot.run_comprehensive_analysis(SYMBOL)

    if not result:
        print("分析无结果，跳过推送")
        return

    signals = _signal_map(result)
    avg = _avg_conf(result)
    sr = _key_levels(result)
    ai = result.get("ai_analysis", "") or ""

    state = _load_state()
    prev = state.get(SYMBOL, {})

    should_push = True
    reason = "always"
    if PUSH_MODE == "on_change":
        should_push = signals != prev.get("signals")
        reason = "信号变化" if should_push else "信号未变化"
    elif PUSH_MODE == "on_signal":
        should_push = any(s in ("STRONG BUY", "STRONG SELL") for s in signals.values())
        reason = "出现强信号" if should_push else "无强信号"

    state[SYMBOL] = {"signals": signals, "ts": datetime.now().isoformat()}
    _save_state(state)

    if not should_push:
        print("本次不推送（{}）".format(reason))
        return

    title = "XSignals {} 信号".format(SYMBOL)
    full = _build_full(SYMBOL, signals, avg, sr, ai)
    simple = _build_simple(SYMBOL, signals, avg, sr, ai)

    print("推送（{}），完整内容 {} 字符".format(reason, len(full)))
    ok = _send_serverchan(title, full)
    if not ok and SIMPLIFY_ON_FAIL:
        print("完整内容发送失败，改为简化版本重试...")
        _send_serverchan(title, simple)


if __name__ == "__main__":
    main("--force" in sys.argv)
