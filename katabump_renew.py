import os
import time
from datetime import datetime
from pathlib import Path
import requests
from seleniumbase import SB
from loguru import logger

# ==========================================
# 1. 严格按照仓库 API 逻辑进行函数导入
# ==========================================
try:
    # API 1: 简单模式 (bypass.py)
    # 工作逻辑: 接收 URL, 返回字典
    from bypass import bypass_cloudflare as api_core_1

    # API 2 & 3: 完整模式 (simple_bypass.py)
    # 工作逻辑: 分别对应单次(url, proxy)和并行(url, proxy_file)
    from simple_bypass import bypass_cloudflare as api_core_2
    from simple_bypass import bypass_parallel as api_core_3

    # API 4: 指纹增强模式 (bypass_seleniumbase.py)
    # 工作逻辑: 直接注入现有的浏览器实例 sb
    from bypass_seleniumbase import bypass_logic as api_core_4
    
    logger.info("📡 核心 API 插件已成功挂载至主程序")
except Exception as e:
    logger.error(f"🚨 API 加载失败，请检查文件层级: {e}")

# ==========================================
# 2. TG 通知功能 (保持原样)
# ==========================================
def send_tg_notification(message, photo_path=None):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id): return
    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                              data={'chat_id': chat_id, 'caption': message}, files={'photo': f})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': message})
    except Exception as e: logger.error(f"TG通知失败: {e}")

# ==========================================
# 3. 自动化续期主流程 (API 调用对齐)
# ==========================================
def run_auto_renew():
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    ui_mode = os.environ.get("BYPASS_MODE", "1. 基础单次模式")
    
    login_url = "https://dashboard.katabump.com/auth/login"
    target_url = "https://dashboard.katabump.com/servers/edit?id=177688"
    OUTPUT_DIR = Path("/app/output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with SB(uc=True, xvfb=True) as sb:
        try:
            # ---- [步骤 A] 主流程登录 ----
            sb.uc_open_with_reconnect(login_url, 10)
            sb.type("#email", email)
            sb.type("#password", password)
            sb.click("#submit") # 匹配 id="submit"
            sb.sleep(6)

            # ---- [步骤 B] 跳转至 Renew 页面 ----
            sb.uc_open_with_reconnect(target_url, 10)
            sb.sleep(3)
            sb.js_click('button[data-bs-target="#renew-modal"]') # 触发验证弹窗
            sb.sleep(6)

            # ---- [步骤 C] 核心：正确调用那三个脚本的 API ----
            current_url = sb.get_current_url()
            logger.info(f">>> 正在按原作者逻辑调用 API: {ui_mode}")

            if "1." in ui_mode:
                # 模式 1 调用逻辑: bypass.py (简单模式)
                # 传入 URL，获取 cf_clearance 和 UA
                result = api_core_1(current_url)
                logger.info(f"API 1 结果: {result['success']}")

            elif "2." in ui_mode:
                # 模式 2 调用逻辑: simple_bypass.py (单次绕过)
                # 传入 URL 和代理
                result = api_core_2(current_url, proxy=os.environ.get("PROXY"))

            elif "3." in ui_mode:
                # 模式 3 调用逻辑: simple_bypass.py (并行绕过)
                # 传入 URL, proxy_file 和批处理大小
                result = api_core_3(url=current_url, proxy_file="proxy.txt", batch_size=3)

            elif "4." in ui_mode:
                # 模式 4 调用逻辑: bypass_seleniumbase.py (增强模式)
                # 关键：直接将当前的浏览器实例 sb 交给它注入指纹
                api_core_4(sb)
                result = {"success": True}

            # ---- [步骤 D] 整合 API 成果并最终点击 ----
            # 使用 UC 模式的物理点击确保验证码框消失
            sb.uc_gui_click_captcha()
            sb.sleep(6)
            
            # 解决日志中提到的找不到按钮的问题
            logger.info("正在执行最终提交...")
            sb.wait_for_element('button:contains("更新")', timeout=10)
            sb.click('button:contains("更新")')
            
            sb.sleep(10)
            success_img = str(OUTPUT_DIR / "success_final.png")
            sb.save_screenshot(success_img)
            send_tg_notification(f"✅ 续期完成！模式: {ui_mode}", success_img)

        except Exception as e:
            error_img = str(OUTPUT_DIR / "error.png")
            sb.save_screenshot(error_img)
            send_tg_notification(f"❌ 续期失败: {str(e)}", error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
