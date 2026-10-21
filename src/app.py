# -*- coding: utf-8 -*-
"""
app.py — XSignals AI 手机远程面板（建议通过 Tailscale 访问）
功能：查看分析、模拟下单、实盘下单（需代理 + 开启开关）、急停。
"""
import os
import sys
import json
from datetime import datetime

from flask import Flask, request, jsonify, render_template_string, make_response

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SRC_DIR, ".env"))

from main import AdvancedTradingBot

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
PAPER_FILE = os.path.join(LOG_DIR, "paper_trades.json")
KILL_FILE = os.path.join(LOG_DIR, ".kill_switch")

WEB_PIN = os.getenv("WEB_PIN", "1234").strip()
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").strip().lower() in ("1", "true", "yes")
MAX_ORDER_USDT = float(os.getenv("MAX_ORDER_USDT", "50"))
BINANCE_PROXY = os.getenv("BINANCE_PROXY", "").strip()
DEFAULT_SYMBOL = os.getenv("MONITOR_SYMBOL", "SOLUSDT")
DATA_API = "https://data-api.binance.vision/api"

app = Flask(__name__)


# ---------------------------------------------------------------- helpers
def _authed():
    return request.cookies.get("xs_pin") == WEB_PIN


def _price(symbol):
    import requests
    r = requests.get(DATA_API + "/v3/ticker/price", params={"symbol": symbol}, timeout=10)
    return float(r.json()["price"])


def _load_paper():
    try:
        with open(PAPER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_paper(rows):
    with open(PAPER_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def _kill_active():
    return os.path.exists(KILL_FILE)


def _analyze(symbol):
    bot = AdvancedTradingBot()
    result = bot.run_comprehensive_analysis(symbol)
    if not result:
        return None
    tf = result.get("multi_tf_analysis", {})
    signals, confs = {}, []
    for name, data in tf.items():
        if "analysis" in data:
            signals[name] = data["analysis"]["overall_signal"]["signal"]
            confs.append(data["analysis"]["overall_signal"]["confidence"])
    sr = None
    for name in ("1h", "4h", "15m", "1d"):
        if name in tf and "analysis" in tf[name]:
            sr = tf[name]["analysis"]["support_resistance"]
            break
    return {
        "symbol": symbol,
        "signals": signals,
        "avg_confidence": (sum(confs) / len(confs)) if confs else 0,
        "support": sr["support"] if sr else None,
        "resistance": sr["resistance"] if sr else None,
        "price": sr["current_price"] if sr else None,
        "ai": result.get("ai_analysis", ""),
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _live_order(symbol, side, quote_usdt):
    from binance.client import Client
    api_key = os.getenv("BINANCE_API_KEY", "")
    api_secret = os.getenv("BINANCE_API_SECRET", "")
    proxies = {"http": BINANCE_PROXY, "https": BINANCE_PROXY} if BINANCE_PROXY else None
    c = Client(api_key, api_secret, requests_params={"proxies": proxies} if proxies else None)
    c.API_URL = "https://api.binance.com/api"  # 覆盖 main.py 的公共行情补丁，走真实交易接口
    return c.create_order(symbol=symbol, side=side, type="MARKET", quoteOrderQty=quote_usdt)


# ---------------------------------------------------------------- pages
LOGIN_PAGE = """<!doctype html><html><meta name=viewport content="width=device-width,initial-scale=1">
<title>XSignals 登录</title>
<body style="font-family:sans-serif;max-width:420px;margin:60px auto;padding:16px">
<h2>🔐 XSignals 远程面板</h2>
<p>请输入 PIN：</p>
<input id=pin type=password style="width:100%;padding:10px;font-size:18px">
<button onclick="go()" style="margin-top:12px;width:100%;padding:12px;font-size:18px">登录</button>
<script>
function go(){fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:document.getElementById('pin').value})}).then(r=>{location.reload()})}
</script></body></html>"""

DASH_PAGE = """<!doctype html><html><meta name=viewport content="width=device-width,initial-scale=1">
<title>XSignals 控制台</title>
<style>
body{font-family:-apple-system,sans-serif;max-width:520px;margin:0 auto;padding:14px;background:#f5f6f8}
.card{background:#fff;border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
button{border:0;border-radius:8px;padding:12px;font-size:16px;margin:4px 4px 0 0;color:#fff}
.b{background:#16a34a}.s{background:#dc2626}.g{background:#2563eb}.k{background:#111}
pre{white-space:pre-wrap;font-size:13px;background:#fafafa;padding:8px;border-radius:8px;max-height:340px;overflow:auto}
.muted{color:#888;font-size:12px}
</style>
<body>
<div class="card">
  <b>📊 XSignals 远程面板</b>
  <div class="muted">币种：<span id=sym>__SYM__</span> · 实盘：<span id=live>__LIVE__</span> · 急停：<span id=kill>__KILL__</span></div>
</div>
<div class="card">
  <button class="g" onclick="refresh()">刷新分析（约30秒）</button>
  <button class="b" onclick="order('BUY')">模拟买入</button>
  <button class="s" onclick="order('SELL')">模拟卖出</button>
  <button class="k" onclick="emg()">急停开关</button>
</div>
<div class="card"><b>最新分析</b><pre id=out>点“刷新分析”获取</pre></div>
<div class="card"><b>模拟持仓</b><pre id=paper>加载中...</pre></div>
<script>
const SYM = "__SYM__";
function j(u,o){return fetch(u,o).then(r=>r.json())}
function refresh(){document.getElementById('out').textContent='分析中，约30秒...';j('/api/analysis?symbol='+SYM).then(d=>{document.getElementById('out').textContent=JSON.stringify(d,null,2)})}
function order(side){if(!confirm('确认 '+side+' '+SYM+' ?'))return;j('/api/order',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol:SYM,side:side,quote_usdt:__MAX__})}).then(d=>{alert(JSON.stringify(d));loadPaper()})}
function emg(){j('/api/emergency',{method:'POST'}).then(d=>{document.getElementById('kill').textContent=d.kill?'开启':'关闭'});alert(JSON.stringify(d))}
function loadPaper(){j('/api/paper').then(d=>{document.getElementById('paper').textContent=JSON.stringify(d,null,2)})}
loadPaper();
</script></body></html>"""


@app.route("/")
def index():
    if not _authed():
        return LOGIN_PAGE
    html = (DASH_PAGE
            .replace("__SYM__", DEFAULT_SYMBOL)
            .replace("__LIVE__", "开启" if LIVE_TRADING else "关闭")
            .replace("__KILL__", "开启" if _kill_active() else "关闭")
            .replace("__MAX__", str(MAX_ORDER_USDT)))
    return html


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    resp = make_response(jsonify({"ok": data.get("pin") == WEB_PIN}))
    if data.get("pin") == WEB_PIN:
        resp.set_cookie("xs_pin", WEB_PIN, max_age=86400 * 7)
    return resp


@app.route("/api/analysis")
def api_analysis():
    if not _authed():
        return jsonify({"error": "unauthorized"}), 401
    symbol = request.args.get("symbol", DEFAULT_SYMBOL).upper()
    data = _analyze(symbol)
    if not data:
        return jsonify({"error": "分析失败"}), 500
    return jsonify(data)


@app.route("/api/order", methods=["POST"])
def api_order():
    if not _authed():
        return jsonify({"error": "unauthorized"}), 401
    if _kill_active():
        return jsonify({"error": "急停开关已开启，禁止交易"}), 403
    data = request.get_json(silent=True) or {}
    symbol = (data.get("symbol") or DEFAULT_SYMBOL).upper()
    side = (data.get("side") or "").upper()
    if side not in ("BUY", "SELL"):
        return jsonify({"error": "side 必须是 BUY 或 SELL"}), 400
    try:
        quote = float(data.get("quote_usdt", MAX_ORDER_USDT))
    except Exception:
        return jsonify({"error": "金额无效"}), 400
    if quote <= 0 or quote > MAX_ORDER_USDT:
        return jsonify({"error": f"单笔金额必须在 0~{MAX_ORDER_USDT} USDT 之间"}), 400

    price = _price(symbol)

    if LIVE_TRADING:
        if not BINANCE_PROXY:
            return jsonify({"error": "实盘已开但未配置代理（api.binance.com 直连不通），请设置 BINANCE_PROXY"}), 400
        try:
            order = _live_order(symbol, side, quote)
            return jsonify({"live": True, "order": order})
        except Exception as e:
            return jsonify({"error": f"实盘下单失败：{e}"}), 500

    # 模拟交易
    rows = _load_paper()
    rows.append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol, "side": side, "quote_usdt": quote, "price": price,
    })
    _save_paper(rows)
    return jsonify({"live": False, "paper": True, "symbol": symbol, "side": side,
                    "quote_usdt": quote, "price": price})


@app.route("/api/paper")
def api_paper():
    if not _authed():
        return jsonify({"error": "unauthorized"}), 401
    return jsonify(_load_paper()[-50:])


@app.route("/api/emergency", methods=["POST"])
def api_emergency():
    if not _authed():
        return jsonify({"error": "unauthorized"}), 401
    if _kill_active():
        os.remove(KILL_FILE)
        return jsonify({"kill": False, "message": "急停已解除"})
    with open(KILL_FILE, "w") as f:
        f.write(datetime.now().isoformat())
    return jsonify({"kill": True, "message": "急停已开启，所有下单被禁止"})


if __name__ == "__main__":
    print(f"XSignals 面板启动: http://127.0.0.1:{WEB_PORT}")
    print(f"实盘: {'开启' if LIVE_TRADING else '关闭'} | 单笔上限: {MAX_ORDER_USDT} USDT")
    print(f"代理: {BINANCE_PROXY or '未配置'}")
    app.run(host="0.0.0.0", port=WEB_PORT, threaded=True)
