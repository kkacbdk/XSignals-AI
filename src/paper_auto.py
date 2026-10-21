# -*- coding: utf-8 -*-
"""
paper_auto.py — 自动模拟交易引擎（多因子确认 + 风险控制版）

决策流程：
  开仓(做多)需同时满足：1h 信号看多 + 置信度≥阈值 + 高周期不逆势 +
    MACD 多头 + RSI 未超买 + ADX 趋势够强 + 量能足够 + 距压力位有空间
  平仓(任一)：ATR 止损 / ATR 止盈 / 1h 转空 / 4h 强空
  仓位：按「权益×风险比例÷ATR止损距离」计算，受单笔最大占比限制
"""
import os
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
_log_path = os.path.join(LOG_DIR, "paper_{}.log".format(_run_ts))
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

from main import AdvancedTradingBot
from dotenv import load_dotenv
load_dotenv()
import requests

# ------------------------- 配置 -------------------------
SYMBOL = os.getenv("MONITOR_SYMBOL", "SOLUSDT").upper()
SENDKEY = os.getenv("SERVERCHAN_SENDKEY", "").strip()
START_BALANCE = float(os.getenv("PAPER_START_BALANCE", "1000"))
START_HOUR = int(os.getenv("MONITOR_START_HOUR", "8"))
END_HOUR = int(os.getenv("MONITOR_END_HOUR", "20"))

RISK_PCT = float(os.getenv("PAPER_RISK_PCT", "0.02"))       # 每笔风险占权益比例
MAX_PCT = float(os.getenv("PAPER_MAX_PCT", "0.30"))          # 单笔最大仓位占权益
ATR_STOP_MULT = float(os.getenv("PAPER_ATR_STOP_MULT", "1.5"))
ATR_TP_MULT = float(os.getenv("PAPER_ATR_TP_MULT", "3.0"))
MIN_CONF = float(os.getenv("PAPER_MIN_CONF", "60"))          # 开仓最低置信度
EXIT_CONF = float(os.getenv("PAPER_EXIT_CONF", "55"))        # 信号平仓置信度
MIN_ADX = float(os.getenv("PAPER_MIN_ADX", "18"))            # 最低趋势强度
MIN_VOL = float(os.getenv("PAPER_MIN_VOL", "0.7"))           # 最低量能倍数
MIN_SPACE_PCT = float(os.getenv("PAPER_MIN_SPACE", "0.5"))   # 距压力位最小百分比

DATA_API = "https://data-api.binance.vision/api"
STATE_FILE = os.path.join(LOG_DIR, "paper_account.json")


# ------------------------- 工具 -------------------------
def _load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            s = json.load(f)
            s.setdefault("balance", START_BALANCE)
            s.setdefault("position", None)
            s.setdefault("trades", [])
            s.setdefault("equity_history", [])
            return s
    except Exception:
        return {"symbol": SYMBOL, "balance": START_BALANCE, "position": None,
                "trades": [], "equity_history": [], "created": datetime.now().isoformat()}


def _save_state(s):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


def _price(symbol):
    r = requests.get(DATA_API + "/v3/ticker/price", params={"symbol": symbol}, timeout=10)
    return float(r.json()["price"])


def _push(title, desp):
    if not SENDKEY:
        print("[WARN] 未配置 SERVERCHAN_SENDKEY")
        return False
    if len(title) > 32:
        title = title[:32]
    try:
        r = requests.post("https://sctapi.ftqq.com/{}.send".format(SENDKEY),
                          data={"title": title, "desp": desp}, timeout=30)
        d = r.json()
        print("推送结果: {}".format(d))
        return d.get("code") == 0
    except Exception as e:
        print("[ERROR] 推送异常: {}".format(e))
        return False


def _val(latest, key, default=0.0):
    try:
        return float(latest[key])
    except Exception:
        return default


def _tf(result, name):
    d = result.get("multi_tf_analysis", {}).get(name, {})
    a = d.get("analysis", {}) or {}
    sig = (a.get("overall_signal") or {}).get("signal")
    conf = (a.get("overall_signal") or {}).get("confidence", 0)
    return sig, conf, a, d.get("latest")


_SCORE = {"STRONG BUY": 2.0, "BUY": 1.0, "WAIT": 0.0, "SELL": -1.0, "STRONG SELL": -2.0}


def _decide(result, state, price):
    """返回 (action, tag, reason, extra)"""
    s1h, c1h, a1h, l1h = _tf(result, "1h")
    s4h, c4h, a4h, l4h = _tf(result, "4h")
    s1d, c1d, a1d, l1d = _tf(result, "1d")
    atr = _val(l1h, "atr_14")

    pos = state.get("position")
    if pos:
        entry = pos["entry_price"]
        stop = pos.get("stop") or (entry - ATR_STOP_MULT * atr if atr > 0 else entry * 0.98)
        tp = pos.get("tp") or (entry + ATR_TP_MULT * atr if atr > 0 else entry * 1.05)
        if price <= stop:
            return "CLOSE", "止损", "价格 {:.4f} ≤ 止损 {:.4f}".format(price, stop), {"price": price}
        if price >= tp:
            return "CLOSE", "止盈", "价格 {:.4f} ≥ 止盈 {:.4f}".format(price, tp), {"price": price}
        if s1h in ("SELL", "STRONG SELL") and c1h >= EXIT_CONF:
            return "CLOSE", "信号转空", "1h {} {:.0f}%".format(s1h, c1h), {"price": price}
        if s4h == "STRONG SELL" and c4h >= 65:
            return "CLOSE", "高周期转空", "4h 强烈卖出 {:.0f}%".format(c4h), {"price": price}
        return "HOLD", "持仓", "未触发平仓条件", {"price": price}

    # ---- 空仓：逐条检查开仓条件 ----
    if s1h not in ("BUY", "STRONG BUY"):
        return "HOLD", "信号不足", "1h 信号 {}".format(s1h), {"price": price}
    if c1h < MIN_CONF:
        return "HOLD", "置信度不足", "1h {:.0f}% < {:.0f}%".format(c1h, MIN_CONF), {"price": price}

    ht = _SCORE.get(s4h, 0) + 0.75 * _SCORE.get(s1d, 0)
    if ht <= -1.0:
        return "HOLD", "逆势", "高周期偏空（4h {} / 1d {}）".format(s4h, s1d), {"price": price}

    rsi = _val(l1h, "rsi_14", 50)
    if rsi > 72:
        return "HOLD", "超买", "RSI {:.1f}".format(rsi), {"price": price}

    macd = _val(l1h, "macd")
    macd_sig = _val(l1h, "macd_signal")
    if macd <= macd_sig:
        return "HOLD", "动量未确认", "MACD {:.4f} ≤ 信号 {:.4f}".format(macd, macd_sig), {"price": price}

    adx = _val(l1h, "adx")
    if adx < MIN_ADX:
        return "HOLD", "趋势太弱", "ADX {:.1f} < {:.0f}".format(adx, MIN_ADX), {"price": price}

    vol = _val(l1h, "volume_momentum", 1)
    if vol < MIN_VOL:
        return "HOLD", "量能不足", "成交量 {:.1f}x < {:.1f}x".format(vol, MIN_VOL), {"price": price}

    sr = a1h.get("support_resistance", {}) or {}
    dtr = sr.get("distance_to_resistance")
    if dtr is not None and dtr < MIN_SPACE_PCT:
        return "HOLD", "上方空间不足", "距压力位 {:.2f}%".format(dtr), {"price": price}

    return "OPEN", "多条件确认", "1h {} {:.0f}% / RSI {:.0f} / ADX {:.0f} / 量 {:.1f}x".format(
        s1h, c1h, rsi, adx, vol), {"price": price, "atr": atr}


def _size_position(balance, price, atr):
    risk_amount = balance * RISK_PCT
    stop_dist = ATR_STOP_MULT * atr
    if stop_dist > 0:
        qty = risk_amount / stop_dist
        spend = qty * price
    else:
        spend = balance * 0.2
    spend = min(spend, balance * MAX_PCT)
    spend = max(spend, 10.0)
    spend = min(spend, balance)
    return round(spend, 2)


def main(reset=False):
    now = datetime.now()

    if reset:
        _save_state({"symbol": SYMBOL, "balance": START_BALANCE, "position": None,
                     "trades": [], "equity_history": [], "created": now.isoformat()})
        print("模拟账户已重置为 {} USDT".format(START_BALANCE))
        return

    if not (START_HOUR <= now.hour < END_HOUR):
        print("不在交易时段 ({:02d}:00-{:02d}:00)".format(START_HOUR, END_HOUR))
        return

    state = _load_state()
    print("===== 模拟盘 {} @ {} =====".format(SYMBOL, now.strftime("%Y-%m-%d %H:%M:%S")))
    print("账户: 余额 {:.2f} USDT, 持仓 {}".format(state["balance"], state["position"]))

    bot = AdvancedTradingBot()
    result = bot.run_comprehensive_analysis(SYMBOL)
    if not result:
        print("分析无结果，跳过")
        return

    price = _price(SYMBOL)
    action, tag, reason, extra = _decide(result, state, price)
    print("决策: {} [{}] {}".format(action, tag, reason))

    atr = extra.get("atr", 0.0)

    if action == "OPEN":
        spend = _size_position(state["balance"], price, atr)
        if spend >= 10 and state["balance"] >= spend:
            qty = spend / price
            stop = price - ATR_STOP_MULT * atr if atr > 0 else price * 0.98
            tp = price + ATR_TP_MULT * atr if atr > 0 else price * 1.05
            state["balance"] = round(state["balance"] - spend, 2)
            state["position"] = {"qty": qty, "entry_price": price, "spend": spend,
                                 "stop": stop, "tp": tp, "entry_time": now.isoformat()}
            state["trades"].append({"ts": now.strftime("%Y-%m-%d %H:%M:%S"), "action": "BUY",
                                    "qty": qty, "price": price, "pnl": None, "reason": reason})
            print("开多: {:.4f} {} @ {:.4f}, 止损 {:.4f}, 止盈 {:.4f}, 动用 {:.2f} USDT".format(
                qty, SYMBOL, price, stop, tp, spend))
        else:
            action, tag, reason = "HOLD", "资金不足", "可用余额不足以开仓"

    elif action == "CLOSE":
        pos = state["position"]
        qty = pos["qty"]
        proceeds = qty * price
        pnl = proceeds - pos["spend"]
        state["balance"] = round(state["balance"] + proceeds, 2)
        state["position"] = None
        state["trades"].append({"ts": now.strftime("%Y-%m-%d %H:%M:%S"), "action": "SELL",
                                "qty": qty, "price": price, "pnl": pnl, "reason": reason})
        print("平仓: {:.4f} {} @ {:.4f}, 本笔盈亏 {:.2f} USDT".format(qty, SYMBOL, price, pnl))

    pos = state.get("position")
    equity = state["balance"] + (pos["qty"] * price if pos else 0.0)
    state["equity_history"].append({"ts": now.isoformat(), "equity": round(equity, 2)})
    state["equity_history"] = state["equity_history"][-1000:]
    _save_state(state)

    closed = [t for t in state["trades"] if t.get("pnl") is not None]
    wins = [t for t in closed if t["pnl"] > 0]
    total_pnl = sum(t["pnl"] for t in closed)
    win_rate = (len(wins) / len(closed) * 100) if closed else 0

    # ---------------- 推送 ----------------
    s1h, c1h, a1h, l1h = _tf(result, "1h")
    s4h, c4h, a4h, l4h = _tf(result, "4h")
    s1d, c1d, a1d, l1d = _tf(result, "1d")
    sigs = {}
    for name in ("15m", "1h", "4h", "1d"):
        sg, cf, _, _ = _tf(result, name)
        if sg:
            sigs[name] = "{} {:.0f}%".format(sg, cf)
    sr = (a1h.get("support_resistance", {}) or {})

    title = "XSignals 模拟盘 {}".format(SYMBOL)
    parts = []
    parts.append("## {} 各周期信号".format(SYMBOL))
    parts.append("  \n".join("{}: {}".format(k, v) for k, v in sigs.items()))
    if sr:
        parts.append("现价 ${:.4f} ｜ 支撑 ${:.4f} ｜ 压力 ${:.4f}".format(
            sr.get("current_price", price), sr.get("support", 0), sr.get("resistance", 0)))

    parts.append("## 本次决策")
    parts.append("**{}**（{}）".format(action, tag))
    parts.append(reason)
    if action == "OPEN" and pos:
        parts.append("开多 {:.4f} {} @ ${:.4f}  \n止损 ${:.4f} ｜ 止盈 ${:.4f}".format(
            pos["qty"], SYMBOL, pos["entry_price"], pos["stop"], pos["tp"]))
    elif action == "CLOSE":
        last = state["trades"][-1]
        parts.append("平仓 {:.4f} {} @ ${:.4f}，本笔盈亏 **{:.2f} USDT**".format(
            last["qty"], SYMBOL, last["price"], last["pnl"]))

    parts.append("## 模拟账户")
    parts.append("总权益: **{:.2f} USDT**  \n可用余额: {:.2f} USDT".format(equity, state["balance"]))
    if pos:
        upnl = (price - pos["entry_price"]) * pos["qty"]
        parts.append("持仓: {:.4f} {}  \n成本 ${:.4f}  \n浮动盈亏: {:.2f} USDT".format(
            pos["qty"], SYMBOL, pos["entry_price"], upnl))
    parts.append("累计已实现: {:.2f} USDT  \n交易 {} 笔（胜率 {:.0f}%）".format(total_pnl, len(closed), win_rate))

    ai = (result.get("ai_analysis") or "")[:3000]
    parts.append("## AI 行情分析")
    parts.append(ai)
    parts.append("> 模拟交易，仅供研究，不构成投资建议。")

    _push(title, "\n\n".join(parts))


if __name__ == "__main__":
    main("--reset" in sys.argv)
