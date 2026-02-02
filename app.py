import streamlit as st
import json
import os
import subprocess
import time
from datetime import datetime, timedelta, timezone

# 配置文件路径
CONFIG_FILE = "/app/output/tasks_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return [{"name": "Katabump 自动续期任务", "script": "katabump_renew.py", "mode": "SB增强模式 (对应脚本: bypass_seleniumbase.py)", "email": "", "password": "", "freq": 3, "active": True, "last_run": "从未运行"}]

def save_config(tasks):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    temp_file = CONFIG_FILE + ".tmp"
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    os.replace(temp_file, CONFIG_FILE)

# --- 页面全局配置 ---
st.set_page_config(page_title="矩阵自动化控制内核", layout="wide")

# 自定义全中文高科技感 CSS (完全保留，仅微调间距以缩小卡片)
st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #00e5ff; font-family: 'Microsoft YaHei', sans-serif; }
    .stButton>button { background: linear-gradient(45deg, #00e5ff, #0055ff); color: white; border: none; font-weight: bold; width: 100%; height: 2.5em; border-radius: 8px; box-shadow: 0 0 10px rgba(0,229,255,0.3); font-size: 0.9em; }
    .stButton>button:hover { box-shadow: 0 0 20px #00e5ff; transform: translateY(-2px); }
    .stExpander { border: 1px solid #00e5ff !important; background-color: #12161f !important; border-radius: 10px; margin-bottom: -10px !important; }
    .status-tag { padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: bold; }
    .active-tag { background-color: rgba(0, 255, 128, 0.2); color: #00ff80; border: 1px solid #00ff80; }
    .status-tag.standby-tag { background-color: rgba(255, 255, 255, 0.1); color: #888; border: 1px solid #555; }
    code { background-color: #000 !important; color: #00ff80 !important; border: 1px solid #333; font-size: 0.85em !important; }
    /* 缩小输入框间距 */
    div[data-testid="stVerticalBlock"] > div { padding-top: 0.1rem !important; padding-bottom: 0.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ 矩阵自动化控制内核")
st.caption("版本: 2026.02.03 | 核心架构: 任务级自治驱动 | 语言: 简体中文")

if 'tasks' not in st.session_state:
    st.session_state.tasks = load_config()

# --- 侧边栏：终端管理 ---
with st.sidebar:
    st.header("⚙️ 系统环境自检")
    chrome_ok = os.path.exists("/usr/bin/google-chrome")
    xvfb_ok = os.path.exists("/usr/bin/Xvfb")
    c1, c2 = st.columns(2)
    c1.metric("Chrome 内核", "就绪" if chrome_ok else "缺失")
    c2.metric("虚拟显示器", "在线" if xvfb_ok else "离线")
    
    st.divider()
    st.header("🧬 终端管理")
    new_item = st.text_input("新增项目名", placeholder="输入项目识别码...")
    script_options = ["katabump_renew.py", "luneshost.py"]
    selected_script = st.selectbox("业务逻辑脚本选择", script_options)
    
    if st.button("➕ 注入新进程"):
        new_task = {
            "name": new_item, 
            "script": selected_script, 
            "mode": "SB增强模式 (对应脚本: bypass_seleniumbase.py)", 
            "email": "", "password": "", "freq": 3, "active": True, "last_run": "从未运行"
        }
        if selected_script == "luneshost.py":
            new_task.update({"stay_time": 10, "refresh_count": 3, "refresh_interval": 5})
        st.session_state.tasks.append(new_task)
        save_config(st.session_state.tasks)
        st.rerun()

# --- 任务轨道监控 ---
st.subheader("🛰️ 任务轨道监控")
bj_tz = timezone(timedelta(hours=8))
updated_tasks = st.session_state.tasks

for i, task in enumerate(updated_tasks):
    # 缩小卡片标题栏占用
    with st.expander(f"项目: {task['name']} ({task.get('script', '未知')})", expanded=True):
        # 紧凑状态栏
        c_status, c_void = st.columns([1, 5])
        status_html = '<span class="status-tag active-tag">正在运行</span>' if task.get('active') else '<span class="status-tag standby-tag">待命状态</span>'
        c_status.markdown(status_html, unsafe_allow_html=True)
        
        # 基础输入区 - 紧凑排布
        c1, c2, c3, c4 = st.columns([0.8, 2.2, 2, 2])
        task['active'] = c1.checkbox("激活", value=task.get('active', True), key=f"active_{i}")
        mode_options = ["单浏览器模式 (对应脚本: simple_bypass.py)", "SB增强模式 (对应脚本: bypass_seleniumbase.py)", "并行竞争模式 (对应脚本: bypass.py)"]
        curr_mode = task.get('mode', mode_options[1])
        task['mode'] = c2.selectbox("破解算法", mode_options, index=mode_options.index(curr_mode) if curr_mode in mode_options else 1, key=f"mode_{i}")
        task['email'] = c3.text_input("Email", value=task.get('email', ''), key=f"email_{i}", label_visibility="collapsed", placeholder="Email")
        task['password'] = c4.text_input("Password", type="password", value=task.get('password', ''), key=f"pw_{i}", label_visibility="collapsed", placeholder="Password")

        # Lunes 专项参数区 - 紧凑排布
        if task.get('script') == "luneshost.py":
            l1, l2, l3, l4 = st.columns([1.5, 1, 1, 1])
            l1.markdown("🛠️ **Lunes 专项参数:**")
            task['stay_time'] = l2.number_input("停留(秒)", 5, 300, task.get('stay_time', 10), key=f"stay_{i}")
            task['refresh_count'] = l3.number_input("刷新(次)", 1, 20, task.get('refresh_count', 3), key=f"count_{i}")
            task['refresh_interval'] = l4.number_input("间隔(秒)", 1, 60, task.get('refresh_interval', 5), key=f"interval_{i}")

        # 运行状态与周期 - 紧凑排布
        t1, t2, t3 = st.columns([1.5, 2.5, 2.5])
        task['freq'] = t1.number_input("周期(天)", 1, 30, task.get('freq', 3), key=f"freq_{i}")
        
        last = task.get('last_run', "从未运行")
        next_date = "等待首次运行"
        if last and last != "从未运行":
            try:
                last_dt = datetime.strptime(str(last), "%Y-%m-%d %H:%M:%S").replace(tzinfo=bj_tz)
                next_date = (last_dt + timedelta(days=task['freq'])).strftime("%Y-%m-%d %H:%M:%S")
            except: next_date = "格式异常"
        
        t2.markdown(f"**上次:** `{last}`")
        t3.markdown(f"**下次:** `{next_date}`")

        # 核心按钮区：保存配置、启动同步、移除任务
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 2])
        
        if btn_col1.button("💾 保存", key=f"save_{i}"):
            save_config(updated_tasks)
            st.success(f"已保存")

        if btn_col2.button("🚀 同步", key=f"run_{i}"):
            log_area = st.empty()
            with st.status(f"建立神经链接...", expanded=True) as status:
                env = os.environ.copy()
                env.update({"EMAIL": task['email'], "PASSWORD": task['password'], "BYPASS_MODE": task['mode'], "PYTHONUNBUFFERED": "1"})
                if task.get('script') == "luneshost.py":
                    env.update({"STAY_TIME": str(task.get('stay_time', 10)), "REFRESH_COUNT": str(task.get('refresh_count', 3)), "REFRESH_INTERVAL": str(task.get('refresh_interval', 5))})
                
                target_script = task.get('script', 'katabump_renew.py')
                cmd = ["xvfb-run", "--server-args=-screen 0 1920x1080x24", "python", target_script]
                process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                
                full_log = ""
                for line in process.stdout:
                    full_log += line
                    log_area.code(f"Terminal@Matrix:~$ \n" + "\n".join(full_log.splitlines()[-10:]))
                
                process.wait()
                if process.returncode == 0:
                    task['last_run'] = datetime.now(bj_tz).strftime("%Y-%m-%d %H:%M:%S")
                    save_config(updated_tasks)
                    status.update(label=f"同步成功", state="complete")
                    st.toast(f"任务完成", icon="✅")
                else:
                    status.update(label=f"运行异常", state="error")

        if btn_col3.button("🗑️ 移除", key=f"del_{i}"):
            st.session_state.tasks.pop(i)
            save_config(st.session_state.tasks)
            st.rerun()

        # 已移除截图显示代码

st.divider()
st.info("💡 每个项目独立自治。")
