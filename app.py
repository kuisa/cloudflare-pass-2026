import streamlit as st
from katabump_renew import execute_renew
import time

st.set_page_config(page_title="Katabump 自动续期控制台", page_icon="⚡")

st.title("⚡ Katabump 自动续期控制台")
st.info("此面板将通过 Zeabur 云端容器运行 SeleniumBase 执行续期任务。")

if st.button("🚀 立即开始续期任务"):
    with st.status("正在运行自动化流程...", expanded=True) as status:
        log_area = st.empty()
        result = execute_renew()
        log_area.code(result)
        status.update(label="任务处理结束", state="complete")
    
    if "✅" in result:
        st.success("续期任务已成功触发！")
    else:
        st.error("任务未完全成功，请检查日志或截图。")

st.divider()
st.caption(f"当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
