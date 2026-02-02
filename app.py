import streamlit as st
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

# 配置文件路径
CONFIG_FILE = "/app/output/tasks_config.json"
# 授权码持久化路径
AUTH_FILE = "/app/output/auth_config.json"

def load_auth():
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r') as f:
                return json.load(f).get("access_code", "admin123")
        except: pass
    return os.environ.get("WEB_ACCESS_CODE", "admin123")

def save_auth(new_code):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, 'w') as f:
        json.dump({"access_code": new_code}, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return [{"name": "Lunes 保活任务", "script": "luneshost.py", "mode": "SB增强模式 (对应脚本: bypass_seleniumbase.py)", "email": "", "password": "", "freq": 3, "active": True, "last_run": "从未运行", "stay_time": 10, "refresh_count": 3, "refresh_interval": 5}]

def save_config(tasks):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    temp_file = CONFIG_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, CONFIG_FILE)

# --- 页面全局配置 ---
st.set_page_config(page_title="矩阵自动化控制内核", layout="wide", initial_sidebar_state="expanded")

# --- 响应式 CSS (微缩版) ---
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #a0aec0; font-size: 0.85rem; }
    h1 { font-size: 1.5rem !important; color: #00e5ff !important; text-shadow: 0 0 10px rgba(0,229,255,0.5); }
    .stExpander { border: 1px solid rgba(0, 229, 255, 0.2) !important; background-color: rgba(18, 22, 31, 0.8) !important; border-radius: 8px !important; margin-bottom: 8px !important; }
    .stButton>button { background: linear-gradient(45deg, #0099ff, #0055ff); color: white; border: none; font-size: 0.75rem !important; border-radius: 4px; padding: 0.2rem 0.5rem; height: auto !important; }
    .stButton>button:hover { box-shadow: 0 0 15px #00e5ff; transform: translateY(-1px); }
    .status-tag { padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: bold; }
    .active-tag { background-color: rgba(0, 255, 128, 0.1); color: #00ff80; border: 1px solid #00ff80; }
    @media (max-width: 768px) { [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; } }
    .stTextInput>div>div>input { background-color: #000 !important; color: #00ff80 !important; font-size: 0.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 登录鉴权 ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

current_access_code = load_auth()

if not st.session_state.authenticated:
    st.title("🛡️ 内核访问授权")
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        auth_code = st.text_input("请输入矩阵授权码", type="password")
        if st.button("验证身份"):
            if auth_code == current_access_code:
                st.session_state.authenticated = True
                st.rerun()
            else: st.error("授权码错误。")
    st.stop()

# --- 主界面 ---
st.title("🛡️ 矩阵自动化控制内核")

if 'tasks' not in st.session_state:
    st.session_state.tasks = load_config()

# --- 侧边栏：管理与改密 ---
with st.sidebar:
    st.header("⚙️ 终端管理")
    new_item = st.text_input("项目识别码", placeholder="识别码...")
    script_options = ["katabump_renew.py", "luneshost.py"]
    selected_script = st.selectbox("核心脚本", script_options)
    if st.button("➕ 注入新进程"):
        new_task = {"name": new_item, "script": selected_script, "mode": "SB增强模式 (对应脚本: bypass_seleniumbase.py)", "email": "", "password": "", "freq": 3, "active": True, "last_run": "从未运行"}
        if selected_script == "luneshost.py": new_task.update({"stay_time": 10, "refresh_count": 3, "refresh_interval": 5})
        st.session_state.tasks.append(new_task)
        save_config(st.session_state.tasks)
        st.rerun()
    
    st.divider()
    with st.expander("🔐 安全设置"):
        old_code = st.text_input("当前授权码", type="password", key="old_code")
        new_code = st.text_input("新授权码", type="password", key="new_code")
        if st.button("确认修改密码"):
            if old_code == current_access_code:
                if new_code:
                    save_auth(new_code)
                    st.success("授权码已更新，请牢记。")
                    time.sleep(1)
                    st.rerun()
                else: st.warning("新授权码不能为空")
            else: st.error("当前授权码验证失败")
    
    st.divider()
    if st.button("🚪 退出授权"):
        st.session_state.authenticated = False
        st.rerun()

# --- 任务轨道监控 ---
updated_tasks = st.session_state.tasks
bj_tz = timezone(timedelta(hours=8))

for i, task in enumerate(updated_tasks):
    with st.expander(f"🛰️ {task['name']} | {task.get('script')}", expanded=True):
        head_1, head_2 = st.columns([1, 5])
        status_html = '<span class="status-tag active-tag">在线</span>' if task.get('active') else '<span class="status-tag">离线</span>'
        head_1.markdown(status_html, unsafe_allow_html=True)
        task['active'] = head_2.checkbox("激活该轨道进程", value=task.get('active', True), key=f"active_{i}")

        c1, c2, c3 = st.columns([2, 2, 2])
        task['mode'] = c1.selectbox("破解算法", ["单浏览器模式 (对应脚本: simple_bypass.py)", "SB增强模式 (对应脚本: bypass_seleniumbase.py)", "并行竞争模式 (对应脚本: bypass.py)"], key=f"mode_{i}")
        task['email'] = c2.text_input("Email", value=task.get('email', ''), key=f"email_{i}")
        task['password'] = c3.text_input("Password", type="password", value=task.get('password', ''), key=f"pw_{i}")

        if task.get('script') == "luneshost.py":
            st.markdown("<div style='margin: 5px 0; border-top: 1px solid rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)
            l1, l2, l3, l4 = st.columns([1.2, 1, 1, 1])
            l1.caption("🛠️ Lunes 参数:")
            task['stay_time'] = l2.number_input("停留(s)", 5, 300, task.get('stay_time', 10), key=f"stay_{i}")
            task['refresh_count'] = l3.number_input("刷新(次)", 1, 20, task.get('refresh_count', 3), key=f"count_{i}")
            task['refresh_interval'] = l4.number_input("间隔(s)", 1, 60, task.get('refresh_interval', 5), key=f"interval_{i}")

        st.markdown("<div style='margin: 5px 0; border-top: 1px solid rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)
        t1, t2, t3 = st.columns([1, 2, 2])
        task['freq'] = t1.number_input("周期(天)", 1, 30, task.get('freq', 3), key=f"freq_{i}")
        last = task.get('last_run', "从未运行")
        t2.caption(f"上次: {last}")
        t3.caption(f"下次: { (datetime.strptime(last, '%Y-%m-%d %H:%M:%S').replace(tzinfo=bj_tz) + timedelta(days=task['freq'])).strftime('%m-%d %H:%M') if last != '从未运行' else '等待运行' }")

        st.markdown("<div style='margin: 8px 0;'></div>", unsafe_allow_html=True)
        btn_1, btn_2, btn_3, _ = st.columns([1, 1, 1, 1.5])
        if btn_1.button("💾 保存", key=f"save_{i}"):
            save_config(updated_tasks)
            st.toast(f"{task['name']} 已保存")
        if btn_2.button("🚀 同步", key=f"run_{i}"):
            log_area = st.empty()
            with st.status(f"同步中...", expanded=True) as status:
                env = os.environ.copy()
                env.update({"EMAIL": task['email'], "PASSWORD": task['password'], "BYPASS_MODE": task['mode'], "PYTHONUNBUFFERED": "1"})
                if task.get('script') == "luneshost.py":
                    env.update({"STAY_TIME": str(task.get('stay_time', 10)), "REFRESH_COUNT": str(task.get('refresh_count', 3)), "REFRESH_INTERVAL": str(task.get('refresh_interval', 5))})
                process = subprocess.Popen(["xvfb-run", "--server-args=-screen 0 1920x1080x24", "python", task.get('script')], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                full_log = ""
                for line in process.stdout:
                    full_log += line
                    log_area.code("\n".join(full_log.splitlines()[-6:]))
                process.wait()
                if process.returncode == 0:
                    task['last_run'] = datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M:%S")
                    save_config(updated_tasks)
                    status.update(label="成功", state="complete")
                    st.rerun()
        if btn_3.button("🗑️ 移除", key=f"del_{i}"):
            st.session_state.tasks.pop(i)
            save_config(st.session_state.tasks)
            st.rerun()

st.divider()
st.caption("矩阵内核独立自治驱动 · 信息已加密")
