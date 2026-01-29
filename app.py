import streamlit as st
import os
import subprocess
import time
from katabump_renew import run_auto_renew  # 导入你的续期函数

st.set_page_config(page_title="综合控制台", page_icon="⚡")

st.title("⚡ 多模式绕过与自动续期控制面板")

# --- 配置区 ---
st.sidebar.header("配置选项")
target_url = st.sidebar.text_input("目标网址", os.environ.get("TARGET_URL", "https://nowsecure.nl"))
run_mode = st.sidebar.selectbox("选择运行脚本 (模式)", [
    "1. Katabump 自动续期 (katabump_renew.py)",
    "2. 单浏览器绕过 (bypass.py)",
    "3. SeleniumBase 增强绕过 (bypass_seleniumbase.py)",
    "4. 核心绕过工具 (simple_bypass.py)"
])

# --- 运行区 ---
if st.button("🚀 立即开始任务"):
    with st.status(f"正在启动 {run_mode}...", expanded=True) as status:
        log_area = st.empty()
        
        # 模式 1: 运行你提供的专属续期逻辑
        if "1. Katabump" in run_mode:
            try:
                # 调用你发给我的 run_auto_renew 函数
                run_auto_renew() 
                result = "✅ 续期流程已在后台执行完毕！"
            except Exception as e:
                result = f"❌ 续期运行失败: {str(e)}"
            log_area.code(result)

        # 模式 2, 3, 4: 严格通过命令行调用你原本的独立文件，不改动其内部代码
        else:
            file_map = {
                "2. 单浏览器": "bypass.py",
                "3. SeleniumBase": "bypass_seleniumbase.py",
                "4. 核心绕过": "simple_bypass.py"
            }
            script_name = next(v for k, v in file_map.items() if k in run_mode)
            
            # 构造命令：使用 xvfb-run 确保在容器内有显示环境
            cmd = ["xvfb-run", "--server-args=-screen 0 1920x1080x24", "python", script_name, target_url]
            
            # 实时捕获并显示你原本代码里的 print 输出
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            full_log = ""
            for line in process.stdout:
                full_log += line
                log_area.code(full_log)
            process.wait()
            result = "✅ 脚本执行结束" if process.returncode == 0 else "❌ 脚本运行出错"

        status.update(label="处理结束", state="complete")
        st.success(result)

st.divider()
st.caption(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
