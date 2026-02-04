import time
import hashlib
import random
import string
import io
from functools import wraps
from flask import Flask, request, jsonify, session, render_template_string, send_file, redirect, url_for
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)
app.secret_key = 'park_management_secret_key_2024'  # Session 加密密钥



# --- 1. 数据与配置 ---
# 用户数据库
def hash_password(password):
    salt = "park_project_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()


users_db = {
    "admin": {"password": hash_password("password123"), "role": "admin", "name": "超级管理员"}
}

# 登录限制记录
login_attempts = {}
LIMIT_ATTEMPTS = 3
LOCKOUT_DURATION = 300

# 模拟业务数据：企业入驻申请列表
# status: 0-待审核, 1-已入驻
mock_companies = [
    {"id": 101, "name": "未来AI科技有限公司", "type": "人工智能", "capital": "500万", "date": "2023-10-24",
     "status": 1},
    {"id": 102, "name": "绿野生态农业集团", "type": "现代农业", "capital": "1200万", "date": "2023-10-25", "status": 0},
    {"id": 103, "name": "极速云端物流", "type": "物流仓储", "capital": "200万", "date": "2023-10-26", "status": 0},
    {"id": 104, "name": "量子动力新能源", "type": "新能源", "capital": "800万", "date": "2023-10-27", "status": 1},
]


# --- 2. 辅助工具与装饰器 ---

# 登录验证装饰器（保护后台路由）
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/')  # 未登录跳转回首页
        return f(*args, **kwargs)

    return decorated_function


def generate_captcha_image():
    width, height = 120, 40
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font_color = (24, 144, 255)

    chars = string.ascii_uppercase + string.digits
    text = ''.join(random.choices(chars, k=4))
    
    try:
        # 路径指向我们在 Dockerfile 中安装的 Liberation 字体
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    
#    try:
#        font = ImageFont.truetype("arial.ttf", 24)
#    except:
#        font = ImageFont.load_default()

    # 绘制干扰
    for _ in range(5):
        draw.line(
            [random.randint(0, width), random.randint(0, height), random.randint(0, width), random.randint(0, height)],
            fill=(220, 220, 220), width=2)
    for _ in range(40):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=(200, 200, 200))

    # 绘制文字
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except:
        text_w, text_h = draw.textsize(text, font=font)

    draw.text(((width - text_w) / 2, (height - text_h) / 2 - 2), text, font=font, fill=font_color)

    buf = io.BytesIO()
    image.save(buf, 'png')
    buf.seek(0)
    return buf, text


# --- 3. 路由逻辑 ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect('/dashboard')
    return render_template_string(LOGIN_HTML)


@app.route('/api/captcha')
def get_captcha():
    img_io, code = generate_captcha_image()
    session['captcha'] = code.lower()
    return send_file(img_io, mimetype='image/png')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    captcha_input = data.get('captcha')

    # 1. 验证码校验
    if 'captcha' not in session or session['captcha'] != captcha_input.lower():
        return jsonify({"success": False, "message": "验证码错误"}), 400
    session.pop('captcha', None)

    # 2. 锁定校验
    current_time = time.time()
    record = login_attempts.get(username, {"attempts": 0, "lock_until": 0})
    if record["attempts"] >= LIMIT_ATTEMPTS and current_time < record["lock_until"]:
        return jsonify({"success": False, "message": "账户锁定中"}), 403

    # 3. 密码校验
    user = users_db.get(username)
    if user and user['password'] == hash_password(password):
        login_attempts[username] = {"attempts": 0, "lock_until": 0}
        # 设置 Session (关键步骤)
        session['user'] = {"id": username, "name": user['name'], "role": user['role']}
        return jsonify({"success": True, "message": "登录成功"}), 200
    else:
        record["attempts"] += 1
        if record["attempts"] >= LIMIT_ATTEMPTS:
            record["lock_until"] = current_time + LOCKOUT_DURATION
        login_attempts[username] = record
        return jsonify({"success": False, "message": "用户名或密码错误"}), 401


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# --- 后台核心页面 ---
@app.route('/dashboard')
@login_required
def dashboard():
    user = session.get('user')
    # 统计数据
    stats = {
        "total": len(mock_companies),
        "active": sum(1 for c in mock_companies if c['status'] == 1),
        "pending": sum(1 for c in mock_companies if c['status'] == 0)
    }
    return render_template_string(DASHBOARD_HTML, user=user, companies=mock_companies, stats=stats)


# --- 业务功能：审核通过 ---
@app.route('/api/approve', methods=['POST'])
@login_required
def approve_company():
    data = request.json
    company_id = data.get('id')
    # 查找并更新状态
    for comp in mock_companies:
        if comp['id'] == company_id:
            comp['status'] = 1  # 设为已入驻
            return jsonify({"success": True, "message": f"{comp['name']} 已审核通过"})
    return jsonify({"success": False, "message": "未找到企业"}), 404


# --- 4. 前端页面模板 ---

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>园区管理 - 登录</title>
    <style>
        body { background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; font-family: sans-serif; margin:0;}
        .card { background: white; padding: 40px; width: 360px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        input { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .row { display: flex; gap: 10px; margin-bottom: 15px; }
        .btn { width: 100%; background: #1890ff; color: white; border: none; padding: 12px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #40a9ff; }
        h2 { text-align: center; color: #333; margin-top: 0; }
        #msg { text-align: center; color: #ff4d4f; height: 20px; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>园区入驻管理系统</h2>
        <input type="text" id="u" placeholder="管理员账号" value="admin">
        <input type="password" id="p" placeholder="密码">
        <div class="row">
            <input type="text" id="c" placeholder="验证码">
            <img src="/api/captcha" id="c-img" onclick="this.src='/api/captcha?'+Date.now()" style="height:38px; cursor:pointer; border:1px solid #ddd; border-radius:4px;">
        </div>
        <button class="btn" onclick="login()">登 录</button>
        <div id="msg"></div>
    </div>
    <script>
        async function login() {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: document.getElementById('u').value,
                    password: document.getElementById('p').value,
                    captcha: document.getElementById('c').value
                })
            });
            const data = await res.json();
            if (data.success) location.href = '/dashboard';
            else {
                document.getElementById('msg').innerText = data.message;
                document.getElementById('c-img').click();
            }
        }
    </script>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>后台管理</title>
    <style>
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #f0f2f5; display: flex; height: 100vh; }
        /* 侧边栏 */
        .sidebar { width: 240px; background: #001529; color: white; display: flex; flex-direction: column; }
        .logo { height: 64px; line-height: 64px; text-align: center; font-size: 20px; font-weight: bold; background: #002140; }
        .menu-item { padding: 15px 24px; cursor: pointer; color: rgba(255,255,255,0.65); transition: 0.3s; }
        .menu-item:hover, .menu-item.active { background: #1890ff; color: white; }

        /* 主内容区 */
        .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        .header { height: 64px; background: white; display: flex; justify-content: space-between; align-items: center; padding: 0 24px; box-shadow: 0 1px 4px rgba(0,21,41,0.08); }
        .content { padding: 24px; overflow-y: auto; }

        /* 卡片统计 */
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 24px; }
        .stat-card { background: white; padding: 24px; border-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
        .stat-title { color: #8c8c8c; font-size: 14px; margin-bottom: 8px; }
        .stat-num { font-size: 30px; font-weight: bold; color: #333; }

        /* 表格样式 */
        .table-card { background: white; padding: 24px; border-radius: 4px; }
        table { width: 100%; border-collapse: collapse; margin-top: 16px; }
        th, td { text-align: left; padding: 16px; border-bottom: 1px solid #f0f0f0; }
        th { background: #fafafa; font-weight: 500; }

        /* 状态标签 */
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .badge-success { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
        .badge-pending { background: #fffbe6; color: #faad14; border: 1px solid #ffe58f; }

        .btn-mini { padding: 4px 12px; background: #1890ff; color: white; border: none; border-radius: 2px; cursor: pointer; }
        .btn-mini:disabled { background: #ccc; cursor: not-allowed; }
        .user-info span { margin-right: 10px; font-weight: 500;}
        .logout-link { color: #ff4d4f; text-decoration: none; font-size: 14px; }
    </style>
</head>
<body>

<div class="sidebar">
    <div class="logo">园区管理中心</div>
    <div class="menu-item active">入驻审核</div>
    <div class="menu-item">企业列表</div>
    <div class="menu-item">财务报表</div>
    <div class="menu-item">系统设置</div>
</div>

<div class="main">
    <div class="header">
        <h3>企业入驻管理控制台</h3>
        <div class="user-info">
            <span>👋 欢迎, {{ user.name }}</span>
            <a href="/logout" class="logout-link">退出登录</a>
        </div>
    </div>

    <div class="content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">总申请企业</div>
                <div class="stat-num">{{ stats.total }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">待审核申请</div>
                <div class="stat-num" style="color: #faad14">{{ stats.pending }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">已入驻企业</div>
                <div class="stat-num" style="color: #52c41a">{{ stats.active }}</div>
            </div>
        </div>

        <div class="table-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3>最新入驻申请</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>企业名称</th>
                        <th>行业类型</th>
                        <th>注册资金</th>
                        <th>申请日期</th>
                        <th>当前状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for comp in companies %}
                    <tr>
                        <td>{{ comp.name }}</td>
                        <td>{{ comp.type }}</td>
                        <td>{{ comp.capital }}</td>
                        <td>{{ comp.date }}</td>
                        <td>
                            {% if comp.status == 1 %}
                            <span class="badge badge-success">已入驻</span>
                            {% else %}
                            <span class="badge badge-pending">待审核</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if comp.status == 0 %}
                            <button class="btn-mini" onclick="approve({{ comp.id }})">通过审核</button>
                            {% else %}
                            <button class="btn-mini" disabled>已处理</button>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
    function approve(id) {
        if(!confirm('确定要通过该企业的入驻申请吗？')) return;

        fetch('/api/approve', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: id})
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message);
            location.reload(); // 刷新页面更新状态
        });
    }
</script>

</body>
</html>
"""

if __name__ == '__main__':
    # 生产环境部署建议：
    from waitress import serve

    # 端口建议：如果你已经在阿里云安全组开了 3389，就用 3389
    # 但通常 Web 服务建议使用 80, 443 或 5000, 8080 等
    print("服务已启动，正在监听端口 3389...")

    # host='0.0.0.0' 是必须的，否则公网无法访问
    serve(app, host='0.0.0.0', port=3389, threads=4)