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
    if not token or not chat_id:
        print("[!] 未配置 TG 变量，跳过通知")
        return

    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                              data={'chat_id': chat_id, 'caption': message}, 
                              files={'photo': photo})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': message})
    except Exception as e:
        print(f"[!] TG 通知发送失败: {e}")

def run_auto_renew():
    # 从 Zeabur 环境变量读取
    url = "https://dashboard.katabump.com/login"
    target_id_url = "https://dashboard.katabump.com/servers/edit?id=177688"
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    
    # 增加 Cookie 保存目录定义 (适配 Zeabur 持久化路径)
    COOKIE_DIR = Path("/app/output/cookies")
    os.makedirs(COOKIE_DIR, exist_ok=True)

    # 启动带有虚拟显示器的反检测浏览器
    with SB(uc=True, xvfb=True) as sb:
        # ---- 第一步：访问登录页并过“大门”验证 ----
        sb.uc_open_with_reconnect(url, 5)
        # 优化：增加随机延迟并尝试绕过 CF 验证
        time.sleep(random.uniform(2, 4))
        sb.uc_gui_click_captcha() 
        
        # 增加逻辑：无论是否报错，先尝试捕获并保存初始 Cookie
        def save_cookies_safe(label=""):
            try:
                cookies = sb.get_cookies()
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = COOKIE_DIR / f"cookies_{label}_{ts}.json"
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)
                print(f"[*] Cookie 已保存至: {save_path}")
            except: pass

        # ---- 第二步：执行登录 ----
        # 优化：在输入前等待元素可见，防止加载过慢
        sb.wait_for_element("#email", timeout=10)
        sb.type("#email", email)
        sb.type("#password", password)
        sb.click('button:contains("登录")') # 匹配你提到的“登录”字体按钮
        sb.sleep(3)
        
        # 登录后保存一次有效 Cookie
        save_cookies_safe("post_login")

        # ---- 第三步：跳转到特定的 See 页面 ----
        sb.uc_open_with_reconnect(target_id_url, 5)
        
        # ---- 第四步：触发续期弹窗 ----
        # 页面下滑并寻找 Renew 按钮
        sb.scroll_to('button[data-bs-target="#renew-modal"]')
        sb.click('button[data-bs-target="#renew-modal"]')
        sb.sleep(2)

        # ---- 第五步：处理续期弹窗中的人机验证 ----
        sb.uc_gui_click_captcha() 
        sb.sleep(2)

        # ---- 第六步：点击最后的“更新”按钮 ----
        sb.click('button:contains("更新")')
        
        # 保存成功截图
        success_screenshot = "/app/output/success_renew.png"
        os.makedirs("/app/output", exist_ok=True)
        sb.save_screenshot(success_screenshot)
        
        # 成功后再保存一次最终 Cookie
        save_cookies_safe("final_success")
        
        success_msg = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ 续期指令已发送！"
        print(success_msg)
        
        # 发送 TG 通知
        send_tg_notification(success_msg, success_screenshot)
        
        sb.sleep(5) # 留出时间确认请求发送完毕

if __name__ == "__main__":
    run_auto_renew()
