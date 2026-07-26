import json, os, threading, time, collections, random, urllib.parse, re
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from instagrapi import Client
from apscheduler.schedulers.background import BackgroundScheduler
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-change-me")

# ─── DATA FILE ──────────────────────────────────────────────
DATA_FILE = "data_v2.json"
data_lock = threading.Lock()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: return json.load(f)
    return {"accounts": {}}

def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f, indent=2)

# ─── GLOBALS ────────────────────────────────────────────────
bot_threads = {}
bot_stop    = {}
bot_status  = {}
ig_clients  = {}
bot_logs    = {}
scheduler   = BackgroundScheduler()
scheduler.start()

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ─── HELPER FUNCTIONS ──────────────────────────────────────
def log(acc_id, msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    if acc_id not in bot_logs:
        bot_logs[acc_id] = collections.deque(maxlen=300)
    bot_logs[acc_id].append(line)

def send_telegram(text):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
                timeout=5
            )
        except: pass

def decode_session(session_id):
    if not session_id: return session_id
    try: return urllib.parse.unquote(session_id)
    except: return session_id

def get_client(acc_id, session_id, proxy=None, csrf_token=None):
    if acc_id in ig_clients: return ig_clients[acc_id]
    if 'fetch_temp' in ig_clients:
        cl = ig_clients.pop('fetch_temp')
        ig_clients[acc_id] = cl
        return cl
    cl = Client()
    if proxy: cl.set_proxy(proxy)
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
    except: pass
    try:
        cl.private_request(
            f"direct_v2/threads/{thread_id}/update_title/",
            data={"title": title, "_uuid": cl.uuid, "_uid": str(cl.user_id), "_csrftoken": cl.token}
        )
        return True, None
    except: pass
    try:
        thread = cl.direct_thread(thread_id)
        r = thread.update_title(title)
        if r is not False:
            return True, None
    except: pass
    try:
        cl.private_request(
            f"direct_v2/threads/{thread_id}/update_title/",
            data={"title": title, "_uuid": cl.uuid, "_uid": str(cl.user_id), "use_unified_inbox": "true"}
        )
        return True, None
    except Exception as e4:
        return False, str(e4)

def get_thread_title(cl, thread_id):
    try:
        thread = cl.direct_thread(int(thread_id))
        return (thread.thread_title or "").strip()
    except:
        return None

# ─── BOT WORKER ─────────────────────────────────────────────
def bot_worker(acc_id):
    data = load_data()
    acc = data["accounts"].get(acc_id)
    if not acc: return
    stop_event = bot_stop.get(acc_id)
    if not stop_event: return

    session_id = acc["session_id"]
    proxy = acc.get("proxy", "").strip() or None
    csrf_token = acc.get("csrf_token", "").strip() or None
    raw_groups = [extract_thread_id(g) for g in acc.get("groups", "").split("\n") if g.strip()]
    groups = raw_groups[:5]
    titles = [t.strip() for t in acc.get("nc_titles", "").split(",") if t.strip()]
    messages = [m.strip() for m in acc.get("messages", "").split("---MSG---") if m.strip()]
    if not messages:
        single = acc.get("message", "").strip()
        if single: messages = [single]

    msg_delay_min = float(acc.get("msg_delay_min", 2))
    msg_delay_max = float(acc.get("msg_delay_max", 5))
    cooldown_after_msgs = int(acc.get("cooldown_after", 0))
    cooldown_dur = float(acc.get("cooldown_dur", 5))
    nc_every_msgs = int(acc.get("nc_every_msgs", 0))

    bot_logs[acc_id] = collections.deque(maxlen=300)
    bot_status[acc_id] = {
        "running": True, "sent": 0, "failed": 0,
        "nc_done": 0, "nc_failed": 0, "nc_skipped": 0,
        "gcs_done": 0, "total_gcs": len(groups),
        "last_action": "Logging in...", "started_at": time.time(),
        "cooldown": False, "cooldown_end": 0
    }

    log(acc_id, f"⚡ Starting bot for {acc.get('name', acc_id)}...")
    send_telegram(f"🤖 *{acc.get('name', acc_id)}* is starting...")

    try:
        cl = get_client(acc_id, session_id, proxy, csrf_token)
        log(acc_id, "✅ Logged in")
        bot_status[acc_id]["last_action"] = "Logged in ✓"
    except Exception as e:
        log(acc_id, f"❌ Login failed: {e}")
        bot_status[acc_id]["running"] = False
        send_telegram(f"❌ *{acc.get('name', acc_id)}* Login Failed: {e}")
        return

    title_idx = 0
    msg_idx = 0
    msgs_since_cd = 0
    msgs_since_nc = 0

    def do_nc_for_all():
        nonlocal title_idx
        if not titles: return
        t = titles[title_idx % len(titles)]
        for thread_id in groups:
            if stop_event.is_set(): break
            bot_status[acc_id]["last_action"] = f"Checking NC → {thread_id}"
            current = get_thread_title(cl, thread_id)
            if current is not None and current.strip() == t.strip():
                log(acc_id, f"⏭ NC skip (already '{t}') → {thread_id}")
                bot_status[acc_id]["nc_skipped"] += 1
            else:
                bot_status[acc_id]["last_action"] = f"NC → {t}"
                ok, err = nc_rename(cl, int(thread_id), t)
                if ok:
                    bot_status[acc_id]["nc_done"] += 1
                    log(acc_id, f"✅ NC done [{t}] → {thread_id}")
                else:
                    bot_status[acc_id]["nc_failed"] += 1
                    log(acc_id, f"❌ NC failed → {thread_id}: {err}")
        title_idx += 1

    log(acc_id, "✏️ Initial NC...")
    do_nc_for_all()

    while not stop_event.is_set():
        bot_status[acc_id]["gcs_done"] = 0

        if titles and nc_every_msgs > 0 and msgs_since_nc >= nc_every_msgs:
            log(acc_id, f"✏️ NC after {nc_every_msgs} messages...")
            do_nc_for_all()
            msgs_since_nc = 0

        for thread_id in groups:
            if stop_event.is_set(): break
            message = messages[msg_idx % len(messages)] if messages else ""
            bot_status[acc_id]["last_action"] = f"Sending → {thread_id}"
            try:
                cl.direct_send(message, thread_ids=[int(thread_id)])
                bot_status[acc_id]["sent"] += 1
                msgs_since_cd += 1
                msgs_since_nc += 1
                log(acc_id, f"✅ Sent → {thread_id}")
            except Exception as e:
                bot_status[acc_id]["failed"] += 1
                err_str = str(e)
                status_code = None
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        resp_json = e.response.json()
                        ig_msg = resp_json.get('message') or resp_json.get('error_title') or resp_json.get('feedback_message') or err_str
                        status_code = e.response.status_code
                        err_str = f"{ig_msg} (status {status_code})"
                    except:
                        status_code = e.response.status_code
                        err_str = f"{status_code}: {e.response.text[:120]}"
                log(acc_id, f"❌ Send failed → {thread_id}: {err_str}")

                if status_code == 403 or "user_has_logged_out" in err_str or "login_required" in err_str:
                    log(acc_id, "🔄 Session expired — re-logging in...")
                    bot_status[acc_id]["last_action"] = "Re-logging in..."
                    try:
                        ig_clients.pop(acc_id, None)
                        cl = get_client(acc_id, session_id, proxy, csrf_token)
                        log(acc_id, "✅ Re-login successful")
                        bot_status[acc_id]["last_action"] = "Re-login done ✓"
                    except Exception as re_err:
                        log(acc_id, f"❌ Re-login failed: {re_err}")
                        bot_status[acc_id]["running"] = False
                        send_telegram(f"❌ *{acc.get('name', acc_id)}* Re-login failed! Stopping.")
                        return
                else:
                    log(acc_id, "⏳ Error cooldown — 5 min pause...")
                    bot_status[acc_id]["last_action"] = "Error cooldown 5 min..."
                    bot_status[acc_id]["cooldown"] = True
                    for _ in range(300):
                        if stop_event.is_set(): break
                        time.sleep(1)
                    bot_status[acc_id]["cooldown"] = False

            msg_idx += 1
            bot_status[acc_id]["gcs_done"] += 1
            if stop_event.is_set(): break

            delay = random.uniform(msg_delay_min, msg_delay_max)
            log(acc_id, f"💤 {delay:.1f}s")
            time.sleep(delay)

        if cooldown_after_msgs > 0 and msgs_since_cd >= cooldown_after_msgs:
            dur_secs = cooldown_dur * 60
            log(acc_id, f"😴 Cooldown {cooldown_dur} min...")
            bot_status[acc_id]["cooldown"] = True
            bot_status[acc_id]["cooldown_end"] = time.time() + dur_secs
            time.sleep(dur_secs)
            bot_status[acc_id]["cooldown"] = False
            bot_status[acc_id]["cooldown_end"] = 0
            msgs_since_cd = 0

    log(acc_id, "🛑 Stopped")
    bot_status[acc_id]["running"] = False
    bot_status[acc_id]["last_action"] = "Stopped"
    send_telegram(f"🛑 *{acc.get('name', acc_id)}* stopped.")

def start_bot_thread(acc_id):
    if acc_id in bot_stop:
        bot_stop[acc_id].set()
        time.sleep(1)
    stop = threading.Event()
    bot_stop[acc_id] = stop
    t = threading.Thread(target=bot_worker, args=(acc_id,), daemon=True)
    bot_threads[acc_id] = t
    t.start()

# ─── SCHEDULER ──────────────────────────────────────────────
def scheduler_check():
    data = load_data()
    now = time.strftime("%H:%M")
    for acc_id, acc in data["accounts"].items():
        schedule_enabled = acc.get("schedule_enabled", False)
        if not schedule_enabled: continue
        start_time = acc.get("schedule_start")
        stop_time = acc.get("schedule_stop")
        if start_time == now:
            if acc_id not in bot_threads or not bot_threads[acc_id].is_alive():
                start_bot_thread(acc_id)
        if stop_time == now:
            if acc_id in bot_stop:
                bot_stop[acc_id].set()

# ─── SNAPSHOT ──────────────────────────────────────────────
def snapshot_backup():
    data = load_data()
    backup = {"timestamp": time.time(), "accounts": data["accounts"]}
    backup_file = f"snapshot_{int(time.time())}.json"
    with open(backup_file, "w") as f:
        json.dump(backup, f, indent=2)
    # Keep only last 5 backups (optional cleanup)
    files = sorted([f for f in os.listdir(".") if f.startswith("snapshot_") and f.endswith(".json")])
    for old in files[:-5]:
        try: os.remove(old)
        except: pass
    send_telegram(f"💾 *Snapshot Backup* completed! {len(data['accounts'])} accounts backed up.")

# Schedule tasks
scheduler.add_job(scheduler_check, 'interval', minutes=1, id='scheduler_check')
scheduler.add_job(snapshot_backup, 'interval', hours=24, id='snapshot_backup')

# ─── LOGIN / ROUTES ──────────────────────────────────────────
def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return "Wrong Password", 403
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>AURA Z · Login</title>
    <style>
        body { background: #0a0a12; color: #e8edf5; font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .login-box { background: rgba(18,18,34,0.6); padding: 40px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.04); backdrop-filter: blur(10px); width: 320px; text-align: center; }
        .login-box h1 { font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 28px; color: #4f8cff; margin-bottom: 8px; }
        .login-box h1 span { color: #fff; }
        .login-box p { color: rgba(255,255,255,0.2); font-size: 12px; margin-bottom: 24px; }
        input { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.04); background: rgba(0,0,0,0.3); color: #fff; font-size: 14px; }
        button { width: 100%; padding: 12px; border-radius: 10px; border: none; background: #4f8cff; color: #0a0a12; font-weight: 700; font-size: 14px; cursor: pointer; margin-top: 12px; }
        button:hover { background: #3a7ae6; }
        .made { margin-top: 20px; font-size: 11px; color: rgba(255,255,255,0.1); }
    </style>
    </head>
    <body>
    <div class="login-box">
        <h1><span>AURA</span> Z</h1>
        <p>Command Center</p>
        <form method="post">
            <input type="password" name="password" placeholder="Enter Password" required/>
            <button type="submit">Unlock</button>
        </form>
        <div class="made">MADE BY xSUJAL</div>
    </div>
    </body>
    </html>
    '''

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}

# ─── API ROUTES ────────────────────────────────────────────

@app.route("/api/accounts")
@login_required
def get_accounts():
    data = load_data()
    result = {}
    for acc_id, acc in data["accounts"].items():
        st = bot_status.get(acc_id, {"running": False})
        if st.get("started_at") and st.get("running"):
            runtime = int(time.time() - st["started_at"])
        else:
            runtime = 0
        if st.get("cooldown") and st.get("cooldown_end", 0) > 0:
            cooldown_remaining = max(0, int(st["cooldown_end"] - time.time()))
        else:
            cooldown_remaining = 0
        result[acc_id] = {
            "name": acc.get("name", ""),
            "session_id": acc.get("session_id", "")[:10] + "...",
            "csrf_token": acc.get("csrf_token", ""),
            "proxy": acc.get("proxy", ""),
            "groups": acc.get("groups", ""),
            "group_names": acc.get("group_names", ""),
            "nc_titles": acc.get("nc_titles", ""),
            "messages": acc.get("messages", ""),
            "msg_delay_min": acc.get("msg_delay_min", 2),
            "msg_delay_max": acc.get("msg_delay_max", 5),
            "nc_every_msgs": acc.get("nc_every_msgs", 0),
            "cooldown_after": acc.get("cooldown_after", 0),
            "cooldown_dur": acc.get("cooldown_dur", 5),
            "schedule_start": acc.get("schedule_start", ""),
            "schedule_stop": acc.get("schedule_stop", ""),
            "schedule_enabled": acc.get("schedule_enabled", False),
            "snapshot_enabled": acc.get("snapshot_enabled", False),
            "telegram_enabled": acc.get("telegram_enabled", False),
            "status": st,
            "runtime_secs": runtime,
            "cooldown_remaining": cooldown_remaining
        }
    return jsonify(result)

@app.route("/api/verify", methods=["POST"])
@login_required
def verify_session():
    data = request.json
    sid = data.get("session_id")
    proxy = data.get("proxy")
    try:
        cl = Client()
        if proxy: cl.set_proxy(proxy)
        cl.login_by_sessionid(decode_session(sid))
        return jsonify({"success": True, "user": cl.user_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/accounts", methods=["POST"])
@login_required
def add_account():
    body = request.json
    sid = body.get("session_id")
    if not sid: return jsonify({"success": False, "error": "Session ID required"}), 400
    data = load_data()
    # Duplicate check
    for acc_id, acc in data["accounts"].items():
        if acc.get("session_id") == sid:
            return jsonify({"success": False, "error": "Account with this Session ID already exists!"}), 400
    acc_id = str(int(time.time() * 1000))
    entry = {
        "name": body.get("name", f"Bot_{acc_id}"),
        "session_id": sid,
        "csrf_token": body.get("csrf_token", ""),
        "proxy": body.get("proxy", ""),
        "groups": body.get("groups", ""),
        "group_names": body.get("group_names", ""),
        "nc_titles": body.get("nc_titles", ""),
        "messages": body.get("messages", "Hello"),
        "msg_delay_min": float(body.get("msg_delay_min", 2)),
        "msg_delay_max": float(body.get("msg_delay_max", 5)),
        "nc_every_msgs": int(body.get("nc_every_msgs", 0)),
        "cooldown_after": int(body.get("cooldown_after", 0)),
        "cooldown_dur": float(body.get("cooldown_dur", 5)),
        "schedule_start": body.get("schedule_start", ""),
        "schedule_stop": body.get("schedule_stop", ""),
        "schedule_enabled": body.get("schedule_enabled", False),
        "snapshot_enabled": body.get("snapshot_enabled", False),
        "telegram_enabled": body.get("telegram_enabled", False)
    }
    data["accounts"][acc_id] = entry
    save_data(data)
    return jsonify({"success": True, "id": acc_id})

@app.route("/api/accounts/<acc_id>", methods=["PUT"])
@login_required
def update_account(acc_id):
    body = request.json
    data = load_data()
    if acc_id not in data["accounts"]:
        return jsonify({"success": False, "error": "Not found"}), 404
    acc = data["accounts"][acc_id]
    fields = ["name", "proxy", "csrf_token", "groups", "group_names", "nc_titles",
              "messages", "msg_delay_min", "msg_delay_max", "nc_every_msgs",
              "cooldown_after", "cooldown_dur", "schedule_start", "schedule_stop",
              "schedule_enabled", "snapshot_enabled", "telegram_enabled"]
    for f in fields:
        if f in body:
            if f in ["msg_delay_min", "msg_delay_max", "cooldown_dur"]:
                acc[f] = float(body[f])
            elif f in ["nc_every_msgs", "cooldown_after"]:
                acc[f] = int(body[f])
            elif f in ["schedule_enabled", "snapshot_enabled", "telegram_enabled"]:
                acc[f] = bool(body[f])
            else:
                acc[f] = body[f]
    if body.get("session_id"):
        acc["session_id"] = body["session_id"]
        ig_clients.pop(acc_id, None)
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>", methods=["DELETE"])
@login_required
def delete_account(acc_id):
    if acc_id in bot_stop:
        bot_stop[acc_id].set()
    ig_clients.pop(acc_id, None)
    data = load_data()
    data["accounts"].pop(acc_id, None)
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>/start", methods=["POST"])
@login_required
def start_bot(acc_id):
    data = load_data()
    if acc_id not in data["accounts"]:
        return jsonify({"success": False, "error": "Not found"}), 404
    if acc_id in bot_threads and bot_threads[acc_id].is_alive():
        return jsonify({"success": False, "error": "Already running"}), 400
    start_bot_thread(acc_id)
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>/stop", methods=["POST"])
@login_required
def stop_bot(acc_id):
    if acc_id in bot_stop:
        bot_stop[acc_id].set()
    if acc_id in bot_status:
        bot_status[acc_id]["running"] = False
        bot_status[acc_id]["last_action"] = "Stopped"
    return jsonify({"success": True})

@app.route("/api/accounts/<acc_id>/logs")
@login_required
def get_logs(acc_id):
    return jsonify({"logs": list(bot_logs.get(acc_id, []))})

@app.route("/api/accounts/start-all", methods=["POST"])
@login_required
def start_all():
    data = load_data()
    for acc_id in data["accounts"]:
        start_bot_thread(acc_id)
    return jsonify({"success": True})

@app.route("/api/accounts/stop-all", methods=["POST"])
@login_required
def stop_all():
    for acc_id in bot_stop:
        bot_stop[acc_id].set()
    return jsonify({"success": True})

@app.route("/api/accounts/bulk-gc", methods=["POST"])
@login_required
def bulk_gc():
    body = request.json
    acc_ids = body.get("account_ids", [])
    action = body.get("action")
    group_id = body.get("group_id")
    group_name = body.get("group_name", group_id)
    if not acc_ids or not group_id or action not in ["add", "remove"]:
        return jsonify({"success": False, "error": "Invalid params"}), 400
    data = load_data()
    for acc_id in acc_ids:
        if acc_id not in data["accounts"]: continue
        acc = data["accounts"][acc_id]
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
                if idx < len(names): names.pop(idx)
        acc["groups"] = "\n".join(groups)
        acc["group_names"] = "\n".join(names)
    save_data(data)
    return jsonify({"success": True})

@app.route("/api/backup/export")
@login_required
def export_backup():
    data = load_data()
    return jsonify({"data": data["accounts"]})

@app.route("/api/backup/import", methods=["POST"])
@login_required
def import_backup():
    body = request.json
    accounts = body.get("data", {})
    if not accounts:
        return jsonify({"success": False, "error": "No data"}), 400
    data = load_data()
    for acc_id, acc in accounts.items():
        if acc_id in data["accounts"]:
            continue  # skip existing to avoid duplicate session conflict
        data["accounts"][acc_id] = acc
    save_data(data)
    return jsonify({"success": True, "imported": len(accounts)})

@app.route("/api/fetch-groups", methods=["POST"])
@login_required
def fetch_groups():
    body = request.json
    sid = body.get("session_id")
    proxy = body.get("proxy")
    acc_id = body.get("acc_id", "fetch_temp")
    if not sid:
        return jsonify({"success": False, "error": "Session ID required"}), 400
    try:
        if acc_id not in ig_clients:
            cl = Client()
            if proxy: cl.set_proxy(proxy)
            cl.login_by_sessionid(decode_session(sid))
            ig_clients[acc_id] = cl
        else:
            cl = ig_clients[acc_id]
        threads = cl.direct_threads(amount=50)
        groups = []
        for t in threads:
            if t.is_group:
                groups.append({"id": str(t.id), "name": t.thread_title or str(t.id)})
        return jsonify({"success": True, "groups": groups})
    except Exception as e:
        ig_clients.pop(acc_id, None)
        return jsonify({"success": False, "error": str(e)}), 400

# ─── MAIN ──────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
