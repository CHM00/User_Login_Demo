import hashlib
import random
import string
import io
import time
from functools import wraps
from flask import session, redirect, send_file
from PIL import Image, ImageDraw, ImageFont


# 1. 密码加盐哈希
def hash_password(password):
    salt = "park_project_salt"
    return hashlib.sha256((password + salt).encode()).hexdigest()


# 2. 登录限制全局变量
login_attempts = {}
LIMIT_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # 5分钟


# 3. 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect('/')
        return f(*args, **kwargs)

    return decorated_function


# 4. 验证码生成工具
def generate_captcha_image():
    width, height = 120, 40
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    chars = string.ascii_uppercase + string.digits
    text = ''.join(random.choices(chars, k=4))

    # 绘制干扰线
    for _ in range(5):
        draw.line([random.randint(0, width), random.randint(0, height),
                   random.randint(0, width), random.randint(0, height)], fill=(220, 220, 220))

    # 绘制文本 (使用默认字体以防环境缺失字体文件)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    draw.text((20, 5), text, font=font, fill=(24, 144, 255))

    buf = io.BytesIO()
    image.save(buf, 'png')
    buf.seek(0)
    return buf, text