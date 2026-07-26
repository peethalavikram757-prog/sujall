Zimport json, os, threading, time, collections, random, urllib.parse, hashlib
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from instagrapi import Client
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-change-me")

# ─── CONFIG ───
DATA_FILE = "data_v2.json"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

data_lock = threading.Lock()
bot_threads = {}
bot_stop = {}
bot_status = {}
ig_clients = {}
bot_logs = {}
scheduler = BackgroundScheduler()
scheduler.start()

# ─── JSON HELPERS ───
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"accounts": {}, "backups": []}

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

def get_account(acc_id):
    d = load_data()
    return d["accounts"].get(acc_id)

def get_all_accounts():
    d = load_data()
    return d["accounts"]

# ─── LOGGER ───
def log(acc_id, msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    if acc_id not in bot_logs:
        bot_logs[acc_id] = collections.deque(maxlen=300)
    bot_logs[acc_id].append(line)

# ─── TELEGRAM ───
def send_telegram(text):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=5)
        except: pass

# ─── LOGIN DECORATOR ───
def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# ─── AURA X CORE FUNCTIONS ───
def decode_session(sid):
    try:
        return urllib.parse.unquote(sid)
    except:
        return sid

def get_client(acc_id, session_id, proxy=None):
    if acc_id in ig_clients:
        return ig_clients[acc_id]
    cl = Client()
    if proxy:
        cl.set_proxy(proxy)
    cl.login_by_sessionid(decode_session(session_id))
    ig_clients[acc_id] = cl
    return cl

def extract_thread_id(s):
    s = s.strip()
    if "instagram.com/direct/t/" in s:
        return s.rstrip("/").split("/")[-1]
    return s

def nc_rename(cl, thread_id, title):
    try:
        result = cl.direct_thread_update_title(thread_id, title)
        if result is not False:
            return True, None
    except:
        pass
    try:
        cl.private_request(
            f"direct_v2/threads/{thread_id}/update_title/",
            data={"title": title, "_uuid": cl.uuid, "_uid": str(cl.user_id), "_csrftoken": cl.token}
        )
        return True, None
    except Exception as e:
        return False, str(e)

def get_thread_title(cl, thread_id):
    try:
        thread = cl.direct_thread(int(thread_id))
        return thread.thread_title or ""
    except:
        return None

# ─── BOT WORKER ───
def bot_worker(acc_id):
    acc = get_account(acc_id)
    if not acc:
        return
    stop_event = bot_stop.get(acc_id)
    if not stop_event:
        return

    session_id = acc["session_id"]
    proxy = acc.get("proxy", "").strip() or None
    raw_groups = [extract_thread_id(g) for g in acc.get("groups", "").split("\n") if g.strip()]
    groups = raw_groups[:5]
    titles = [t.strip() for t in acc.get("nc_titles", "").split(",") if t.strip()]
    messages = [m.strip() for m in acc.get("messages", "").split("---MSG---") if m.strip()]
    if not messages:
        messages = ["Hello from AURA Z!"]

    msg_delay_min = float(acc.get("msg_delay_min", 2))
    msg_delay_max = float(acc.get("msg_delay_max", 5))
    cooldown_after = int(acc.get("cooldown_after", 0))
    cooldown_dur = float(acc.get("cooldown_dur", 5))
    nc_every_msgs = int(acc.get("nc_every_msgs", 0))

    bot_status[acc_id] = {
        "running": True,
        "sent": 0,
        "failed": 0,
        "nc_done": 0,
        "nc_failed": 0,
        "nc_skipped": 0,
        "gcs_done": 0,
        "total_gcs": len(groups),
        "last_action": "Logging in...",
        "started_at": time.time(),
        "cooldown": False,
        "cooldown_end": 0
    }

    log(acc_id, f"⚡ AURA Z starting for {acc.get('name', acc_id)}")
    send_telegram(f"🤖 *{acc.get('name', acc_id)}* is starting...")

    try:
        cl = get_client(acc_id, session_id, proxy)
        log(acc_id, "✅ Logged in")
        bot_status[acc_id]["last_action"] = "Logged in ✓"
    except Exception as e:
        log(acc_id, f"❌ Login failed: {e}")
        bot_status[acc_id]["running"] = False
        send_telegram(f"❌ *{acc.get('name', acc_id)}* Login Failed")
        return

    # ─── NC LOGIC ───
    def do_nc():
        nonlocal titles
        if not titles:
            return
        title = titles[0]
        for tid in groups:
            if stop_event.is_set():
                break
            try:
                current = get_thread_title(cl, tid)
                if current and current.strip() == title.strip():
                    log(acc_id, f"⏭ NC skip (already '{title}') → {tid}")
                    bot_status[acc_id]["nc_skipped"] += 1
                else:
                    ok, err = nc_rename(cl, int(tid), title)
                    if ok:
                        log(acc_id, f"✅ NC done [{title}] → {tid}")
                        bot_status[acc_id]["nc_done"] += 1
                    else:
                        log(acc_id, f"❌ NC failed → {tid}: {err}")
                        bot_status[acc_id]["nc_failed"] += 1
            except Exception as e:
                log(acc_id, f"❌ NC error → {tid}: {e}")
                bot_status[acc_id]["nc_failed"] += 1

    # Initial NC
    log(acc_id, "✏️ Initial NC...")
    do_nc()

    msg_idx = 0
    msgs_since_cd = 0
    msgs_since_nc = 0

    while not stop_event.is_set():
        if nc_every_msgs > 0 and msgs_since_nc >= nc_every_msgs:
            log(acc_id, f"✏️ NC after {nc_every_msgs} msgs")
            do_nc()
            msgs_since_nc = 0

        for tid in groups:
            if stop_event.is_set():
                break
            msg = messages[msg_idx % len(messages)]
            try:
                cl.direct_send(msg, thread_ids=[int(tid)])
                bot_status[acc_id]["sent"] += 1
                msgs_since_cd += 1
                msgs_since_nc += 1
                log(acc_id, f"✅ Sent → {tid}")
            except Exception as e:
                bot_status[acc_id]["failed"] += 1
                log(acc_id, f"❌ Send failed → {tid}: {e}")
                if "login_required" in str(e):
                    send_telegram(f"⚠️ *{acc.get('name', acc_id)}* Session expired")
                    stop_event.set()
                    break
                # Error cooldown
                bot_status[acc_id]["cooldown"] = True
                log(acc_id, "⏳ Error cooldown 5 min")
                for _ in range(300):
                    if stop_event.is_set():
                        break
                    time.sleep(1)
                bot_status[acc_id]["cooldown"] = False

            msg_idx = (msg_idx + 1) % len(messages)
            bot_status[acc_id]["gcs_done"] += 1
            if stop_event.is_set():
                break

            delay = random.uniform(msg_delay_min, msg_delay_max)
            log(acc_id, f"💤 {delay:.1f}s")
            time.sleep(delay)

        if cooldown_after > 0 and msgs_since_cd >= cooldown_after:
            dur = cooldown_dur * 60
            log(acc_id, f"😴 Cooldown {cooldown_dur} min")
            bot_status[acc_id]["cooldown"] = True
            bot_status[acc_id]["cooldown_end"] = time.time() + dur
            for _ in range(int(dur)):
                if stop_event.is_set():
                    break
                time.sleep(1)
            bot_status[acc_id]["cooldown"] = False
            bot_status[acc_id]["cooldown_end"] = 0
            msgs_since_cd = 0

    log(acc_id, "🛑 Stopped")
    bot_status[acc_id]["running"] = False
    send_telegram(f"🛑 *{acc.get('name', acc_id)}* stopped.")

# ─── SCHEDULER ───
def scheduler_job():
    with app.app_context():
        accounts = get_all_accounts()
        now = datetime.now().strftime("%H:%M")
        for acc_id, acc in accounts.items():
            if acc.get("schedule_enabled") and acc.get("is_active", True):
                if acc.get("schedule_start") == now:
                    if acc_id not in bot_threads or not bot_threads.get(acc_id, threading.Thread()).is_alive():
                        start_bot_thread(acc_id)
                if acc.get("schedule_stop") == now:
                    if acc_id in bot_stop:
                        bot_stop[acc_id].set()

def start_bot_thread(acc_id):
    if acc_id in bot_stop:
        bot_stop[acc_id].set()
        time.sleep(1)
    stop = threading.Event()
    bot_stop[acc_id] = stop
    t = threading.Thread(target=bot_worker, args=(acc_id,), daemon=True)
    bot_threads[acc_id] = t
    t.start()

scheduler.add_job(scheduler_job, "interval", minutes=1, id="scheduler_job")

# ─── ROUTES ──────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        return "Wrong Password", 403
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>AURA Z · Login</title>
    <style>body{background:#0a0a12;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}
    .box{background:#14141e;padding:40px;border-radius:20px;border:1px solid rgba(255,255,255,0.05);text-align:center;min-width:300px;}
    h1{font-size:28px;margin-bottom:8px;}.x{color:#4f8cff;}.sujal{color:#fff;}
    input{background:#0a0a12;border:1px solid rgba(255,255,255,0.1);color:#fff;padding:12px 16px;border-radius:10px;width:100%;margin:16px 0;}
    button{background:#4f8cff;color:#0a0a12;border:none;padding:12px 24px;border-radius:40px;font-weight:700;cursor:pointer;width:100%;}
    .made{color:rgba(255,255,255,0.1);font-size:11px;margin-top:20px;}
    </style>
    </head>
    <body>
    <div class="box">
        <h1><span class="x">x</span><span class="sujal">SUJAL</span></h1>
        <div style="font-size:14px;color:rgba(255,255,255,0.3);margin-bottom:16px;">AURA Z · Command Center</div>
        <form method="post">
            <input type="password" name="password" placeholder="Enter Password" required />
            <button type="submit">Enter</button>
        </form>
        <div class="made">⚡ MADE BY xSUJAL</div>
    </div>
    </body>
    </html>
    '''

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login_page"))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status": "ok"}

# ─── API ────────────────────────────────────────────────
@app.route("/api/accounts")
@login_required
def api_get_accounts():
    d = load_data()
    result = {}
    for acc_id, acc in d["accounts"].items():
        st = bot_status.get(acc_id, {"running": False})
        result[acc_id] = {
            "name": acc.get("name", ""),
            "session_id": acc.get("session_id", "")[:10] + "...",
            "proxy": acc.get("proxy", ""),
            "groups": acc.get("groups", ""),
            "group_names": acc.get("group_names", ""),
            "nc_titles": acc.get("nc_titles", ""),
            "messages": acc.get("messages", "Hello from AURA Z!"),
            "msg_delay_min": acc.get("msg_delay_min", 2),
            "msg_delay_max": acc.get("msg_delay_max", 5),
            "nc_every_msgs": acc.get("nc_every_msgs", 0),
            "cooldown_after": acc.get("cooldown_after", 0),
            "cooldown_dur": acc.get("cooldown_dur", 5),
            "schedule_start": acc.get("schedule_start", "09:00"),
            "schedule_stop": acc.get("schedule_stop", "18:00"),
            "schedule_enabled": acc.get("schedule_enabled", False),
            "is_active": acc.get("is_active", True),
            "status": st,
            "runtime_secs": int(time.time() - st.get("started_at", time.time())) if st.get("running") else 0
        }
    return jsonify(result)

@app.route("/api/accounts", methods=["POST"])
@login_required
def add_account():
    body = request.json
    sid = body.get("session_id", "").strip()
    if not sid:
        return jsonify({"success": False, "error": "Session ID required"}), 400
    d = load_data()
    for acc_id, acc in d["accounts"].items():
        if acc["session_id"] == sid:
            return jsonify({"success": False, "error": "Session ID already exists!"}), 400
    acc_id = str(int(time.time() * 1000))
    d["accounts"][acc_id] = {
        "name": body.get("name", f"Bot_{acc_id}"),
        "session_id": sid,
        "csrf_token": body.get("csrf_token", ""),
        "proxy": body.get("proxy", ""),
        "groups": body.get("groups", ""),
        "group_names": body.get("group_names", ""),
        "nc_titles": body.get("nc_titles", ""),
        "messages": body.get("messages", "Hello from AURA Z!"),
        "msg_delay_min": float(body.get("msg_delay_min", 2)),
        "msg_delay_max": float(body.get("msg_delay_max", 5)),
        "nc_every_msgs": int(body.get("nc_every_msgs", 0)),
        "cooldown_after": int(body.get("cooldown_after", 0)),
        "cooldown_dur": float(body.get("cooldown_dur", 5)),
        "schedule_start": body.get("schedule_start", "09:00"),
        "schedule_stop": body.get("schedule_stop", "18:00"),
        "schedule_enabled": body.get("schedule_enabled", False),
        "is_active": True
    }
    save_data(d)
    return jsonify({"success": True, "id": acc_id})

@app.route("/api/accounts/<acc_id>", methods=["PUT"])
@login_required
def update_account(acc_id):
    body = request.json
    d = load_data()
    if acc_id not in d["accounts"]:
        return jsonify({"success": False, "error": "Not found"}), 404
    acc = d["accounts"][acc_id]
    for key in ["name", "proxy", "csrf_token", "groups", "group_names", "nc_titles", "messages",
                "msg_delay_min", "msg_delay_max", "nc_every_msgs", "cooldown_after", "cooldown_dur",
                "schedule_start", "schedule_stop", "schedule_enabled"]:
        if key in body:
            if key in ["msg_delay_min", "msg_delay_max", "cooldown_dur"]:
                acc[key] = float(body[key])
            elif key in ["nc_every_msgs", "cooldown_after"]:
                acc[key] = int(body[key])
            elif key in ["schedule_enabled"]:
                acc[key] = bool(body[key])
            else:
                acc[key] = body[key]
    if body.get("session_id"):
        acc["session_id"] = body["session_id"]
        ig_clients.pop(acc_id, None)
    save_data(d)
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>", methods=["DELETE"])
@login_required
def delete_account(acc_id):
    if acc_id in bot_stop:
        bot_stop[acc_id].set()
    d = load_data()
    if acc_id in d["accounts"]:
        del d["accounts"][acc_id]
        save_data(d)
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>/start", methods=["POST"])
@login_required
def start_bot(acc_id):
    if acc_id in bot_threads and bot_threads[acc_id].is_alive():
        return jsonify({"success": False, "error": "Already running"}), 400
    start_bot_thread(acc_id)
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>/stop", methods=["POST"])
@login_required
def stop_bot(acc_id):
    if acc_id in bot_stop:
        bot_stop[acc_id].set()
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>/logs")
@login_required
def get_logs(acc_id):
    return jsonify({"logs": list(bot_logs.get(acc_id, []))})

@app.route("/api/accounts/start-all", methods=["POST"])
@login_required
def start_all():
    d = load_data()
    for acc_id in d["accounts"]:
        if acc_id not in bot_threads or not bot_threads[acc_id].is_alive():
            start_bot_thread(acc_id)
            time.sleep(0.5)
    return jsonify({"success": True})

@app.route("/api/accounts/stop-all", methods=["POST"])
@login_required
def stop_all():
    for acc_id in list(bot_stop.keys()):
        bot_stop[acc_id].set()
    return jsonify({"success": True})

@app.route("/api/accounts/bulk-gc", methods=["POST"])
@login_required
def bulk_gc():
    data = request.json
    acc_ids = data.get("account_ids", [])
    action = data.get("action")
    group_id = data.get("group_id")
    group_name = data.get("group_name", group_id)
    if not acc_ids or not group_id or action not in ["add", "remove"]:
        return jsonify({"error": "Invalid params"}), 400
    d = load_data()
    for acc_id in acc_ids:
        if acc_id not in d["accounts"]:
            continue
        acc = d["accounts"][acc_id]
        groups = [g.strip() for g in acc.get("groups", "").split("\n") if g.strip()]
        names = [n.strip() for n in acc.get("group_names", "").split("\n") if n.strip()]
        if action == "add":
            if group_id not in groups:
                groups.append(group_id)
                names.append(group_name)
        else:
            if group_id in groups:
                idx = groups.index(group_id)
                groups.pop(idx)
                if idx < len(names):
                    names.pop(idx)
        acc["groups"] = "\n".join(groups)
        acc["group_names"] = "\n".join(names)
    save_data(d)
    return jsonify({"success": True})

@app.route("/api/fetch-groups", methods=["POST"])
@login_required
def fetch_groups():
    body = request.json
    sid = body.get("session_id")
    proxy = body.get("proxy")
    if not sid:
        return jsonify({"success": False, "error": "Session ID required"}), 400
    try:
        cl = Client()
        if proxy:
            cl.set_proxy(proxy)
        cl.login_by_sessionid(decode_session(sid))
        threads = cl.direct_threads(amount=50)
        groups = []
        for t in threads:
            if t.is_group:
                groups.append({"id": str(t.id), "name": t.thread_title or str(t.id)})
        return jsonify({"success": True, "groups": groups})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/backup/export")
@login_required
def export_backup():
    d = load_data()
    return jsonify({"data": d["accounts"]})

@app.route("/api/backup/import", methods=["POST"])
@login_required
def import_backup():
    data = request.json.get("data", {})
    if not data:
        return jsonify({"error": "No data"}), 400
    d = load_data()
    count = 0
    for acc_id, acc in data.items():
        if acc_id not in d["accounts"]:
            d["accounts"][acc_id] = acc
            count += 1
    save_data(d)
    return jsonify({"success": True, "imported": count})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
