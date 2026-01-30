import os
import time
import json
import random
from datetime import datetime
from pathlib import Path
import requests
from seleniumbase import SB

def send_tg_notification(message, photo_path=None):
    """发送 Telegram 消息和截图"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id): return
    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                              data={'chat_id': chat_id, 'caption': message}, 
                              files={'photo': f})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': message})
    except Exception as e: print(f"TG通知失败: {e}")

def run_auto_renew():
    # 1. 变量初始化
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    ui_mode = os.environ.get("BYPASS_MODE", "SB增强模式") # 从 UI 获取当前模式
    
    login_url = "https://dashboard.katabump.com/auth/login"
    target_url = "https://dashboard.katabump.com/servers/edit?id=177688"
    OUTPUT_DIR = Path("/app/output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[*] [{datetime.now().strftime('%H:%M:%S')}] 流程启动 - 2026.01.29 核心版本")
    print(f"[*] 预设算法映射: {ui_mode}")

    # 使用集成了反检测的 uc 模式启动浏览器
    with SB(uc=True, xvfb=True) as sb:
        try:
            # ---- 步骤 1: 登录 ----
            print(">>> [1/5] 正在打开登录页...")
            sb.uc_open_with_reconnect(login_url, 10)
            sb.uc_gui_click_captcha() # 处理可能存在的入场验证
            
            sb.wait_for_element("#email", timeout=20)
            sb.type("#email", email)
            sb.type("#password", password)
            
            # 使用 ID 定位登录按钮，穿透 font 标签
            print(">>> 正在点击 <font>登录</font> (ID: submit)...")
            sb.click("#submit") 
            sb.sleep(6)

            # ---- 步骤 2: 访问 See 页面 ----
            print(">>> [2/5] 正在跳转至 See 页面...")
            sb.uc_open_with_reconnect(target_url, 10)
            sb.sleep(3)

            # ---- 步骤 3: 触发续期弹窗 ----
            print(">>> [3/5] 寻找 Renew 按钮并点击...")
            sb.scroll_to('button[data-bs-target="#renew-modal"]')
            # 使用 JS 点击防止元素遮挡
            sb.js_click('button[data-bs-target="#renew-modal"]') 
            print("    [OK] 续期弹窗已弹出")
            sb.sleep(4) 

            # ---- 步骤 4: 核心破解逻辑调用 (真正核心所在) ----
            print(f">>> [4/5] 关键点：弹出验证码！正在调用 [{ui_mode}] 对应的脚本核心逻辑...")
            
            # 存证截图：点击前
            sb.save_screenshot(str(OUTPUT_DIR / "before_bypass.png"))

            if "增强" in ui_mode:
                # 对应 bypass_seleniumbase.py 的核心：底层指纹篡改
                print("    [核心确认为: bypass_seleniumbase] 正在注入 CDP 指纹抹除特征...")
                sb.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
                sb.uc_gui_click_captcha() # 物理模拟点击
                
            elif "竞争" in ui_mode:
                # 对应 bypass.py 的核心：随机震荡模拟
                delay = random.uniform(2.5, 5.0)
                print(f"    [核心确认为: bypass] 注入随机真人延迟: {delay:.2f}s...")
                time.sleep(delay)
                sb.uc_gui_click_captcha()
                
            else:
                # 对应 simple_bypass.py 的核心：直接物理过盾
                print("    [核心确认为: simple_bypass] 执行基础 UC 点击逻辑...")
                sb.uc_gui_click_captcha()

            sb.sleep(5)
            # 存证截图：点击后
            sb.save_screenshot(str(OUTPUT_DIR / "after_bypass.png"))
            print("    [OK] 人机校验核心逻辑执行结束")

            # ---- 步骤 5: 最终确认 ----
            print(">>> [5/5] 正在点击最终的 <font>更新</font> 按钮...")
            # 使用 XPath 定位包含“更新”文本的按钮
            sb.click('//button[contains(., "更新")]')
            sb.sleep(10)

            # ---- 流程结束 ----
            success_img = str(OUTPUT_DIR / "success_final.png")
            sb.save_screenshot(success_img)
            finish_msg = f"✅ [{datetime.now().strftime('%H:%M')}] 续期任务成功跑通！模式: {ui_mode}"
            print(finish_msg)
            send_tg_notification(finish_msg, success_img)

        except Exception as e:
            error_img = str(OUTPUT_DIR / "error_state.png")
            sb.save_screenshot(error_img)
            err_msg = f"❌ [{ui_mode}] 流程中断: {str(e)}"
            print(err_msg)
            send_tg_notification(err_msg, error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
