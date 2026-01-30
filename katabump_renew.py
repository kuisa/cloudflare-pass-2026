import os
import time
from datetime import datetime
from pathlib import Path
import requests
from seleniumbase import SB
from loguru import logger

# ==========================================
# 步骤 1: 按照仓库工作方式导入 4 种 API
# ==========================================
try:
    # 模式 1: 简单模式 (来自 bypass.py)
    from bypass import bypass_cloudflare as api_bypass_simple
    
    # 模式 2 & 3: 完整模式 (来自 simple_bypass.py)
    from simple_bypass import bypass_cloudflare as api_simple_once
    from simple_bypass import bypass_parallel as api_simple_parallel
    
    # 模式 4: 指纹增强模式 (来自 bypass_seleniumbase.py)
    from bypass_seleniumbase import bypass_logic as api_enhanced
    
    logger.info("📡 四大核心破解 API 插件已全部就位")
except ImportError as e:
    logger.error(f"🚨 API 插件缺失，请检查脚本完整性: {e}")

# ==========================================
# 步骤 2: 你的 TG 通知功能 (原封不动保留)
# ==========================================
def send_tg_notification(message, photo_path=None):
    """发送 Telegram 消息和截图"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id): 
        logger.warning("未配置 TG 机器人，跳过通知")
        return
    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                              data={'chat_id': chat_id, 'caption': message}, files={'photo': f})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': message})
        logger.info("TG 通知发送成功")
    except Exception as e: 
        logger.error(f"TG 通知失败: {e}")

# ==========================================
# 步骤 3: 自动化续期主流程 (2026.01.29 版)
# ==========================================
def run_auto_renew():
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    ui_mode = os.environ.get("BYPASS_MODE", "2. 代理单次模式")
    
    # 你指定的 2026.01.29 确切页面
    login_url = "https://dashboard.katabump.com/auth/login"
    target_url = "https://dashboard.katabump.com/servers/edit?id=177688"
    OUTPUT_DIR = Path("/app/output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info(f"🚀 启动自动续期 | 选定 API 逻辑: {ui_mode}")

    with SB(uc=True, xvfb=True) as sb:
        try:
            # ---- 1. 登录流程 (匹配 id="submit") ----
            sb.uc_open_with_reconnect(login_url, 10)
            sb.wait_for_element("#email", timeout=20)
            sb.type("#email", email)
            sb.type("#password", password)
            sb.click("#submit") 
            sb.sleep(6)

            # ---- 2. 跳转编辑页 ----
            sb.uc_open_with_reconnect(target_url, 10)
            sb.sleep(3)

            # ---- 3. 触发 Renew 弹窗 ----
            sb.scroll_to('button[data-bs-target="#renew-modal"]')
            sb.js_click('button[data-bs-target="#renew-modal"]')
            sb.sleep(5) 

            # ---- 4. 关键：根据 4 种工作逻辑精准调用 API ----
            target_url_api = sb.get_current_url()
            result = {"success": False}

            # 存证截图：绕过前
            before_img = str(OUTPUT_DIR / "before_bypass.png")
            sb.save_screenshot(before_img)

            if "1." in ui_mode:
                # 简单模式
                result = api_bypass_simple(target_url_api)
                
            elif "2." in ui_mode:
                # 代理单次
                result = api_simple_once(target_url_api, proxy=os.environ.get("PROXY"))
                
            elif "3." in ui_mode:
                # 并行模式 (读取 proxy.txt, batch_size=3)
                result = api_simple_parallel(url=target_url_api, proxy_file="proxy.txt", batch_size=3)
                
            elif "4." in ui_mode:
                # 增强模式 (直接操作当前 sb 实例)
                api_enhanced(sb)
                result = {"success": True} 

            # ---- 5. 整合 API 结果并最终提交 ----
            after_img = str(OUTPUT_DIR / "after_bypass.png")
            sb.save_screenshot(after_img)

            if result.get("success"):
                logger.success("✅ API 绕过逻辑执行成功")
                sb.uc_gui_click_captcha() # 物理补点确保关闭
                sb.sleep(4)
            
            # 点击 <font>更新</font> 按钮
            sb.click('//button[contains(., "更新")]') 
            sb.sleep(8)

            # 流程结束，保存最终成果图并发送 TG
            success_img = str(OUTPUT_DIR / "success_final.png")
            sb.save_screenshot(success_img)
            finish_msg = f"✅ [{datetime.now().strftime('%H:%M')}] Katabump 续期成功！\n使用模式: {ui_mode}\n账户: {email}"
            logger.success(finish_msg)
            send_tg_notification(finish_msg, success_img)

        except Exception as e:
            error_img = str(OUTPUT_DIR / "error.png")
            sb.save_screenshot(error_img)
            err_msg = f"❌ [{datetime.now().strftime('%H:%M')}] 续期任务失败！\n模式: {ui_mode}\n原因: {str(e)}"
            logger.error(err_msg)
            send_tg_notification(err_msg, error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
