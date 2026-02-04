from flask import Flask, request, jsonify, session, render_template_string, send_file, redirect
from utils import hash_password, login_required, generate_captcha_image, login_attempts, LIMIT_ATTEMPTS, LOCKOUT_DURATION
import time

app = Flask(__name__)
app.secret_key = 'park_management_secret_key_2026'

# 模拟数据库
users_db = {
    "admin": {"password": hash_password("password123"), "role": "admin", "name": "超级管理员"}
}

mock_companies = [
    {"id": 101, "name": "未来AI科技", "type": "人工智能", "capital": "500万", "date": "2023-10-24", "status": 1},
    {"id": 102, "name": "绿野生态农业", "type": "现代农业", "capital": "1200万", "date": "2023-10-25", "status": 0},
    {"id": 103, "name": "极速云端物流", "type": "物流仓储", "capital": "200万", "date": "2023-10-26", "status": 0}
]

@app.route('/')
def index():
    if 'user' in session: return redirect('/dashboard')
    with open('login.html', encoding='utf-8') as f: return render_template_string(f.read())

@app.route('/api/captcha')
def get_captcha():
    img_io, code = generate_captcha_image()
    session['captcha'] = code.lower()
    return send_file(img_io, mimetype='image/png')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username, password, captcha_input = data.get('username'), data.get('password'), data.get('captcha')

    # 验证码校验
    if 'captcha' not in session or session['captcha'] != captcha_input.lower():
        return jsonify({"success": False, "message": "验证码错误"}), 400

    # 锁定校验
    current_time = time.time()
    record = login_attempts.get(username, {"attempts": 0, "lock_until": 0})
    if record["attempts"] >= LIMIT_ATTEMPTS and current_time < record["lock_until"]:
        return jsonify({"success": False, "message": "错误次数过多，账号锁定5分钟"}), 403

    # 密码校验
    user = users_db.get(username)
    if user and user['password'] == hash_password(password):
        login_attempts[username] = {"attempts": 0, "lock_until": 0}
        session['user'] = {"id": username, "name": user['name']}
        return jsonify({"success": True})
    else:
        record["attempts"] += 1
        if record["attempts"] >= LIMIT_ATTEMPTS: record["lock_until"] = current_time + LOCKOUT_DURATION
        login_attempts[username] = record
        return jsonify({"success": False, "message": "用户名或密码错误"}), 401

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {"total": len(mock_companies),
             "pending": sum(1 for c in mock_companies if c['status'] == 0),
             "active": sum(1 for c in mock_companies if c['status'] == 1)}
    with open('dashboard.html', encoding='utf-8') as f:
        return render_template_string(f.read(), user=session['user'], companies=mock_companies, stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    from waitress import serve
    print("Server starting on port 3389...")
    serve(app, host='0.0.0.0', port=3389)