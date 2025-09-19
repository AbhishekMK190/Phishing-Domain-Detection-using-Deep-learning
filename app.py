# app.py
from flask import Flask , render_template ,request, jsonify, session, redirect, url_for
from flask_cors import CORS
import requests
# import last_logic_backup
import web_scarping.Feature_extraction_ff1 as fex
import pickle
import tensorflow as tf
from tensorflow import keras
import os
import time
import sqlite3
from datetime import datetime
from threading import Lock

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')

# Fix for TensorFlow compatibility issue with 'auto' reduction
model = tf.keras.models.load_model("my_model.h5", compile=False)
model.compile(optimizer='adam',
              loss=tf.keras.losses.BinaryCrossentropy(reduction='sum_over_batch_size'),
              metrics=['binary_accuracy'])
# model = pickle.load(open("model.h5","rb"))

# --- SQLite logging setup ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'predictions.db')
_db_lock = Lock()

def init_db():
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  domain TEXT,
                  url TEXT,
                  label TEXT,
                  score REAL,
                  created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedbacks (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  prediction_id INTEGER,
                  domain TEXT,
                  url TEXT,
                  vote TEXT,
                  note TEXT,
                  created_at TEXT,
                  FOREIGN KEY(prediction_id) REFERENCES predictions(id)
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

def is_valid_domain(domain: str) -> bool:
    """Check if domain is valid and not localhost/development domains"""
    if not domain or not isinstance(domain, str):
        return False
    
    # Exclude localhost and development domains
    invalid_domains = [
        'localhost',
        '127.0.0.1',
        '0.0.0.0',
        '::1'
    ]
    
    # Check if domain contains any invalid patterns
    domain_lower = domain.lower()
    for invalid in invalid_domains:
        if invalid in domain_lower:
            return False
    
    # Check if it's a valid domain format (contains at least one dot and valid characters)
    if '.' not in domain:
        return False
    
    # Basic domain validation - should not contain spaces or special characters at start/end
    if domain.startswith('.') or domain.endswith('.') or ' ' in domain:
        return False
    
    return True

def log_prediction(domain: str, url: str, label: str, score: float | None):
    # Only log valid domains to database
    if not is_valid_domain(domain):
        print(f"Skipping database log for invalid domain: {domain}")
        return None
        
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO predictions (domain, url, label, score, created_at) VALUES (?,?,?,?,?)",
                (domain, url, label, None if score is None else float(score), datetime.utcnow().isoformat())
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

init_db()

# Lightweight in-memory prediction cache to avoid repeated model calls
PREDICTION_CACHE_TTL_SECONDS = int(os.getenv('PRED_CACHE_TTL', '900'))  # default 15 minutes
_prediction_cache = {}

# Cache for computed feature vectors to avoid recomputing heavy extraction
FEATURES_CACHE_TTL_SECONDS = int(os.getenv('FEATURES_CACHE_TTL', '1800'))  # default 30 minutes
_features_cache = {}

# Default headers to reduce blocks and speed up responses
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
}

# Trusted domain allowlist (suffix-based). Comma-separated via env TRUSTED_SUFFIXES
_trusted_suffixes_env = os.getenv('TRUSTED_SUFFIXES', 'google.com,gmail.com,googleusercontent.com,googleapis.com,microsoft.com,outlook.com,live.com,yahoo.com,apple.com,icloud.com')
TRUSTED_SUFFIXES = [s.strip().lower() for s in _trusted_suffixes_env.split(',') if s.strip()]

def is_trusted_domain(domain: str) -> bool:
    d = (domain or '').lower().strip().rstrip('.')
    for suf in TRUSTED_SUFFIXES:
        if d == suf or d.endswith('.' + suf):
            return True
    return False

def _get_threshold(default: float = 0.5) -> float:
    try:
        return float(os.getenv('PRED_THRESHOLD', default))
    except Exception:
        return default

def _cache_get(domain: str):
    now = time.time()
    entry = _prediction_cache.get(domain)
    if not entry:
        return None
    if now - entry['ts'] > PREDICTION_CACHE_TTL_SECONDS:
        _prediction_cache.pop(domain, None)
        return None
    return entry

def _cache_set(domain: str, score: float, label: str):
    _prediction_cache[domain] = {"score": float(score), "label": label, "ts": time.time()}

def _features_get(domain: str):
    now = time.time()
    entry = _features_cache.get(domain)
    if not entry:
        return None
    if now - entry['ts'] > FEATURES_CACHE_TTL_SECONDS:
        _features_cache.pop(domain, None)
        return None
    return entry['features']

def _features_set(domain: str, features):
    _features_cache[domain] = {"features": features, "ts": time.time()}

@app.route("/")
def home():
    return render_template('real_index1.html')


@app.route('/check_phishing', methods=['GET', 'POST'])
def check_phishing():
    if request.method == 'POST':
        domain = request.form['url']
        if "." not in domain:
            return render_template('real_result.html', result="invalid")
        
        # Clean the domain - remove http://, https://, www. prefixes
        domain = domain.lower().strip()
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Validate domain before processing
        if not is_valid_domain(domain):
            return render_template('real_result.html', result="invalid")
        # Short-circuit for trusted domains
        if is_trusted_domain(domain):
            try:
                _cache_set(domain, 0.0, "legitimate")
                log_prediction(domain, f"https://{domain}", "legitimate", 0.0)
            except Exception:
                pass
            return render_template('real_result.html', result="The URL  is predicted as a legitimate URL.")
            
        print(domain)
        url = f"https://{domain}"
        try:
            response = requests.get(url, timeout=6, headers=DEFAULT_HEADERS)
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to {url}: {e}")
            return render_template('real_result.html', result="not active")
        if response.status_code == 200:

            # Serve from cache if available
            cached = _cache_get(domain)
            if cached:
                label = cached['label']
                result = f"The URL  is predicted as a {label} URL."
                try:
                    log_prediction(domain, url, label, cached.get('score'))
                except Exception:
                    pass
                return render_template('real_result.html', result=result)

            cached_features = _features_get(domain)
            if cached_features is None:
                new_url_features = fex.data_set_list_creation(domain)
                _features_set(domain, new_url_features)
            else:
                new_url_features = cached_features

            new_url_features = [new_url_features]
            
            # Convert to numpy array for TensorFlow compatibility
            import numpy as np
            new_url_features = np.array(new_url_features, dtype=np.float32)

            prediction = model.predict(new_url_features)
            print(prediction)
            threshold = _get_threshold(0.5)
            if prediction >= threshold:
                print("The URL  is predicted as a phishing URL.")
                result = "The URL  is predicted as a phishing URL."
                _cache_set(domain, float(prediction[0][0]), "phishing")
                try:
                    log_prediction(domain, url, "phishing", float(prediction[0][0]))
                except Exception:
                    pass

            else:
                print("The URL  is predicted as a legitimate URL.")
                result = "The URL  is predicted as a legitimate URL."
                _cache_set(domain, float(prediction[0][0]), "legitimate")
                try:
                    log_prediction(domain, url, "legitimate", float(prediction[0][0]))
                except Exception:
                    pass
            return render_template('real_result.html', result=result)
        else:
            try:
                log_prediction(domain, url, "not_active", None)
            except Exception:
                pass
            return render_template('real_result.html', result="not active")

@app.route('/api/check', methods=['POST'])
def api_check():
    from urllib.parse import urlparse
    data = request.get_json(silent=True) or {}
    raw_input = (data.get('domain') or data.get('url') or '').strip()
    threshold_override = data.get('threshold')
    if not raw_input:
        return jsonify({"error": "url or domain is required"}), 400

    # Normalize input: accept full URLs or bare domains
    candidate = raw_input
    # If looks like a URL without scheme, add http:// for parsing
    parsed = urlparse(candidate if '://' in candidate else f"http://{candidate}")
    host = parsed.netloc or parsed.path  # path can contain host when no scheme
    # Strip credentials and port
    if '@' in host:
        host = host.split('@', 1)[1]
    if ':' in host:
        host = host.split(':', 1)[0]
    domain = host.lower().strip()
    if domain.startswith('www.'):
        domain = domain[4:]

    if '.' not in domain or not is_valid_domain(domain):
        try:
            log_prediction(domain or raw_input, raw_input, "invalid", None)
        except Exception:
            pass
        return jsonify({"status": "invalid", "detail": "invalid or local domain"}), 200

    url = f"https://{domain}"

    # Short-circuit for trusted domains
    if is_trusted_domain(domain):
        _cache_set(domain, 0.0, "legitimate")
        try:
            pred_id = log_prediction(domain, url, "legitimate", 0.0)
        except Exception:
            pred_id = None
        return jsonify({
            "status": "ok",
            "domain": domain,
            "url": url,
            "score": 0.0,
            "threshold": _get_threshold(0.5),
            "label": "legitimate",
            "prediction_id": pred_id,
            "cached": False,
            "trusted": True
        }), 200

    # Serve from cache if available
    cached = _cache_get(domain)
    if cached:
        try:
            pred_id = log_prediction(domain, url, cached['label'], cached.get('score'))
        except Exception:
            pred_id = None
        return jsonify({
            "status": "ok",
            "domain": domain,
            "url": url,
            "score": cached['score'],
            "label": cached['label'],
            "cached": True,
            "threshold": _get_threshold(0.5),
            "prediction_id": pred_id
        }), 200
    try:
        response = requests.get(url, timeout=6, headers=DEFAULT_HEADERS)
    except requests.exceptions.RequestException as e:
        try:
            log_prediction(domain, url, "not_active", None)
        except Exception:
            pass
        return jsonify({"status": "not_active", "detail": str(e)}), 200

    if response.status_code != 200:
        try:
            log_prediction(domain, url, "not_active", None)
        except Exception:
            pass
        return jsonify({"status": "not_active", "http_status": response.status_code}), 200

    cached_features = _features_get(domain)
    if cached_features is None:
        new_url_features = fex.data_set_list_creation(domain)
        _features_set(domain, new_url_features)
    else:
        new_url_features = cached_features
    if not isinstance(new_url_features, list):
        return jsonify({"status": "feature_error"}), 200

    import numpy as np
    features_array = np.array([new_url_features], dtype=np.float32)
    pred = model.predict(features_array)
    score = float(pred[0][0])
    th = None
    try:
        th = float(threshold_override)
    except Exception:
        th = _get_threshold(0.5)
    is_phishing = score >= th
    _cache_set(domain, score, "phishing" if is_phishing else "legitimate")
    try:
        pred_id = log_prediction(domain, url, "phishing" if is_phishing else "legitimate", score)
    except Exception:
        pred_id = None
    return jsonify({
        "status": "ok",
        "domain": domain,
        "url": url,
        "score": score,
        "threshold": th,
        "label": "phishing" if is_phishing else "legitimate",
        "prediction_id": pred_id
    }), 200

# --- Feedback APIs and Metrics/Alerts ---
@app.route('/api/feedback', methods=['POST'])
def api_feedback():
    data = request.get_json(silent=True) or {}
    prediction_id = data.get('prediction_id')
    domain = (data.get('domain') or '').strip()
    url = (data.get('url') or '').strip()
    vote = (data.get('vote') or '').strip().lower()  # 'agree' | 'disagree'
    note = (data.get('note') or '').strip()
    if not vote or vote not in ('agree', 'disagree'):
        return jsonify({"error": "vote must be 'agree' or 'disagree'"}), 400
    ts = datetime.utcnow().isoformat()
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO feedbacks (prediction_id, domain, url, vote, note, created_at) VALUES (?,?,?,?,?,?)",
                (prediction_id, domain, url, vote, note, ts)
            )
            conn.commit()
        finally:
            conn.close()
    return jsonify({"status": "ok"}), 200

@app.route('/admin/metrics')
def admin_metrics():
    gate = _require_admin()
    if gate is not None:
        return gate
    now = datetime.utcnow()
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            # Totals
            cur.execute("SELECT COUNT(*) FROM predictions")
            total = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM predictions WHERE label='phishing'")
            total_phishing = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM predictions WHERE label='legitimate'")
            total_legit = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM predictions WHERE label='not_active'")
            total_not_active = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM predictions WHERE label='invalid'")
            total_invalid = cur.fetchone()[0] or 0

            # Feedback summary
            cur.execute("SELECT COUNT(*) FROM feedbacks")
            fb_total = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM feedbacks WHERE vote='disagree'")
            fb_disagree = cur.fetchone()[0] or 0

            # Recent window (last 24h)
            since = (now.timestamp() - 24*3600)
            # created_at is ISO text; simple filter via LIKE for date prefix fallback
            date_prefix = now.strftime('%Y-%m-%d')
            cur.execute("SELECT COUNT(*) FROM predictions WHERE created_at LIKE ?", (f"{date_prefix}%",))
            day_total = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM predictions WHERE label='phishing' AND created_at LIKE ?", (f"{date_prefix}%",))
            day_phishing = cur.fetchone()[0] or 0

            # Alerts (simple rules)
            alerts = []
            phishing_rate = (total_phishing / total) if total else 0.0
            disagree_rate = (fb_disagree / fb_total) if fb_total else 0.0
            if phishing_rate > 0.5 and total > 50:
                alerts.append({"type": "phishing_rate_high", "severity": "warning", "message": f"High phishing rate overall: {(phishing_rate*100):.1f}%"})
            if disagree_rate > 0.2 and fb_total >= 10:
                alerts.append({"type": "model_disagreement_high", "severity": "warning", "message": f"High user disagreement: {(disagree_rate*100):.1f}%"})
            if day_phishing > 30:
                alerts.append({"type": "daily_phishing_spike", "severity": "critical", "message": f"{day_phishing} phishing detections today"})

        finally:
            conn.close()
    return jsonify({
        "totals": {
            "total": total,
            "phishing": total_phishing,
            "legitimate": total_legit,
            "not_active": total_not_active,
            "invalid": total_invalid
        },
        "feedback": {
            "total": fb_total,
            "disagree": fb_disagree
        },
        "daily": {
            "total": day_total,
            "phishing": day_phishing
        },
        "alerts": alerts
    })

@app.route('/admin/feedback')
def admin_feedback_list():
    gate = _require_admin()
    if gate is not None:
        return gate
    vote = request.args.get('vote')  # agree/disagree
    limit = int(request.args.get('limit', '200'))
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            if vote in ('agree', 'disagree'):
                cur.execute("SELECT id, prediction_id, domain, url, vote, note, created_at FROM feedbacks WHERE vote = ? ORDER BY id DESC LIMIT ?", (vote, limit))
            else:
                cur.execute("SELECT id, prediction_id, domain, url, vote, note, created_at FROM feedbacks ORDER BY id DESC LIMIT ?", (limit,))
            rows = [
                {"id": i, "prediction_id": p, "domain": d or '', "url": u or '', "vote": v or '', "note": n or '', "created_at": c}
                for (i, p, d, u, v, n, c) in cur.fetchall()
            ]
        finally:
            conn.close()
    return jsonify({"items": rows})

@app.route('/admin/feedback/export')
def admin_feedback_export():
    gate = _require_admin()
    if gate is not None:
        return gate
    import csv
    from io import StringIO
    vote = request.args.get('vote')
    filename_vote = (vote or 'all').replace('/', '_')
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            if vote in ('agree', 'disagree'):
                cur.execute("SELECT id, prediction_id, domain, url, vote, note, created_at FROM feedbacks WHERE vote = ? ORDER BY id DESC", (vote,))
            else:
                cur.execute("SELECT id, prediction_id, domain, url, vote, note, created_at FROM feedbacks ORDER BY id DESC")
            rows = cur.fetchall()
        finally:
            conn.close()
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "prediction_id", "domain", "url", "vote", "note", "created_at"])
    for r in rows:
        writer.writerow(r)
    csv_data = buf.getvalue()
    headers = {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': f'attachment; filename="feedback_{filename_vote}.csv"'
    }
    return csv_data, 200, headers

# --- Admin views ---
def _require_admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login', next=request.path))
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        admin_user = os.getenv('ADMIN_USER', 'admin')
        admin_pass = os.getenv('ADMIN_PASS', 'admin123')
        if username == admin_user and password == admin_pass:
            session['admin_logged_in'] = True
            return redirect(request.args.get('next') or url_for('admin_page'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin_page():
    gate = _require_admin()
    if gate is not None:
        return gate
    return render_template('admin.html')

@app.route('/admin/data')
def admin_data():
    gate = _require_admin()
    if gate is not None:
        return gate
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute("SELECT label, COUNT(*) FROM predictions GROUP BY label")
            counts = {row[0] if row[0] is not None else 'unknown': row[1] for row in cur.fetchall()}
            cur.execute("SELECT domain, url, label, score, created_at FROM predictions ORDER BY id DESC LIMIT 50")
            recent = [
                {"domain": d or '', "url": u or '', "label": l or '', "score": s, "created_at": c}
                for (d,u,l,s,c) in cur.fetchall()
            ]
        finally:
            conn.close()
    return jsonify({"counts": counts, "recent": recent})

# --- Admin enhanced data APIs ---
@app.route('/admin/list')
def admin_list():
    gate = _require_admin()
    if gate is not None:
        return gate
    label = request.args.get('label')
    limit = int(request.args.get('limit', '200'))
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            if label and label != 'all':
                cur.execute(
                    "SELECT id, domain, url, label, score, created_at FROM predictions WHERE label = ? ORDER BY id DESC LIMIT ?",
                    (label, limit)
                )
            else:
                cur.execute(
                    "SELECT id, domain, url, label, score, created_at FROM predictions ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
            rows = [
                {"id": i, "domain": d or '', "url": u or '', "label": l or '', "score": s, "created_at": c}
                for (i, d, u, l, s, c) in cur.fetchall()
            ]
        finally:
            conn.close()
    return jsonify({"items": rows})

@app.route('/admin/delete', methods=['POST'])
def admin_delete():
    gate = _require_admin()
    if gate is not None:
        return gate
    payload = request.get_json(silent=True) or {}
    ids = payload.get('ids') or []
    label = payload.get('label')
    delete_all = bool(payload.get('all'))
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            if ids:
                qmarks = ','.join(['?'] * len(ids))
                cur.execute(f"DELETE FROM predictions WHERE id IN ({qmarks})", ids)
            elif delete_all and label and label != 'all':
                cur.execute("DELETE FROM predictions WHERE label = ?", (label,))
            elif delete_all and (label == 'all' or label is None):
                cur.execute("DELETE FROM predictions")
            else:
                return jsonify({"error": "nothing to delete"}), 400
            conn.commit()
        finally:
            conn.close()
    return jsonify({"status": "deleted"})

@app.route('/admin/export')
def admin_export():
    gate = _require_admin()
    if gate is not None:
        return gate
    import csv
    from io import StringIO
    label = request.args.get('label')
    filename_label = (label or 'all').replace('/', '_')
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            if label and label != 'all':
                cur.execute(
                    "SELECT id, domain, url, label, score, created_at FROM predictions WHERE label = ? ORDER BY id DESC",
                    (label,)
                )
            else:
                cur.execute(
                    "SELECT id, domain, url, label, score, created_at FROM predictions ORDER BY id DESC"
                )
            rows = cur.fetchall()
        finally:
            conn.close()
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "domain", "url", "label", "score", "created_at"])
    for r in rows:
        writer.writerow(r)
    csv_data = buf.getvalue()
    headers = {
        'Content-Type': 'text/csv; charset=utf-8',
        'Content-Disposition': f'attachment; filename="predictions_{filename_label}.csv"'
    }
    return csv_data, 200, headers
    
if __name__=='__main__':
    app.run(debug=True)