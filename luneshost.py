import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests
from seleniumbase import SB
from loguru import logger

# ==========================================
# 1. 严格按照仓库 API 逻辑进行函数导入 (完全不改)
# ==========================================
try:
    from bypass import bypass_cloudflare as api_core_1
    from simple_bypass import bypass_cloudflare as api_core_2
    from simple_bypass import bypass_parallel as api_core_3
    from bypass_seleniumbase import bypass_logic as api_core_4
    logger.info("📡 核心 API 插件已成功挂载至主程序")
except Exception as e:
    logger.error(f"🚨 API 加载失败: {e}")

# ==========================================
# 2. 高科技 TGUI 功能 (北京时间锁死)
# ==========================================
def send_tg_notification(status, message, photo_path=None):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id): return
    
    # 强制锁死北京时间 (UTC+8)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    emoji = "✅" if "成功" in status else "⚠️" if "执行中" in status else "❌"
    
    formatted_msg = (
        f"{emoji} **矩阵自动化续期报告**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 **账户**: `{os.environ.get('EMAIL', 'Unknown')}`\n"
        f"📡 **状态**: {status}\n"
        f"📝 **详情**: {message}\n"
        f"🕒 **北京时间**: `{bj_time}`\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                requests.post(f"https://api.telegram.org/bot{token}/sendPhoto", 
                              data={'chat_id': chat_id, 'caption': formatted_msg, 'parse_mode': 'Markdown'}, files={'photo': f})
        else:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          data={'chat_id': chat_id, 'text': formatted_msg, 'parse_mode': 'Markdown'})
    except Exception as e: logger.error(f"TG通知失败: {e}")

# ==========================================
# 3. 自动化续期主流程 (Lunes.host 专项版)
# ==========================================
def run_auto_renew():
    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    ui_mode = os.environ.get("BYPASS_MODE", "1. 基础单次模式")
    
    # 动态参数获取
    stay_time = int(os.environ.get("STAY_TIME", 10))
    refresh_count = int(os.environ.get("REFRESH_COUNT", 3))
    refresh_interval = int(os.environ.get("REFRESH_INTERVAL", 5))
    
    # 修正：直接访问 Beta 登录页面，避免跳转干扰
    login_url = "https://betadash.lunes.host/login?next=/"
    OUTPUT_DIR = Path("/app/output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

with SB(uc=True, xvfb=True) as sb:
        try:
            # ---- [步骤 A] 直接打开登录页 ----
            logger.info(f"正在直接访问登录页面: {login_url}")
            sb.uc_open_with_reconnect(login_url, 10)

            # ---- [步骤 B] 填写登录表单 ----
            logger.info("正在定位表单元素...")
            sb.wait_for_element_visible("#email", timeout=25)
            sb.type("#email", email)
            sb.type("#password", password)
            
            # ---- [步骤 C] 调用核心 API 处理人机验证 ----
            current_url = sb.get_current_url()
            if "1." in ui_mode: api_core_1(current_url)
            elif "2." in ui_mode: api_core_2(current_url, proxy=os.environ.get("PROXY"))
            elif "3." in ui_mode: api_core_3(url=current_url, proxy_file="proxy.txt", batch_size=3)
            elif "4." in ui_mode: api_core_4(sb)
            
            try:
                sb.uc_gui_click_captcha()
            except:
                pass
                
            sb.sleep(5)
            
            # ---- [步骤 D] 增强登录点击逻辑 ----
            logger.info("开始尝试点击登录按钮...")
            # 兼容多种可能的按钮选择器
            submit_selectors = ['button.submit-btn', 'button:contains("Continue")', 'input[type="submit"]']
            clicked = False
            for selector in submit_selectors:
                if sb.is_element_visible(selector):
                    sb.wait_for_element_clickable(selector, timeout=5)
                    sb.click(selector)
                    clicked = True
                    break
            
            if not clicked:
                logger.warning("未找到按钮，尝试回车登录")
                sb.press_keys("#password", "\n")
            
            # 核心修复：替换掉报错的语法，改为 SeleniumBase 原生等待
            logger.info("等待登录跳转中...")
            sb.wait_for_url_not_contains("login", timeout=30) 
            sb.sleep(5)

            # ---- [步骤 E] 直接强攻详情页 (解决“点不到”的核心点) ----
            target_server_url = "https://betadash.lunes.host/servers/52794"
            logger.info(f"不再在主页寻找，直接强行跳转详情页: {target_server_url}")
            # 使用带重连的打开方式，确保在低内存环境下也能加载出详情页
            sb.uc_open_with_reconnect(target_server_url, 15)
            
            # 检查是否成功进入详情页（以 URL 包含 ID 为准）
            if "52794" not in sb.get_current_url():
                logger.error("强制跳转失败，尝试第二次跳转...")
                sb.open(target_server_url)
                sb.sleep(5)

            # ---- [步骤 F] 执行停留与保活刷新 ----
            logger.info(f"成功进入服务器控制台 (URL: {sb.get_current_url()})，执行停留 {stay_time} 秒...")
            sb.sleep(stay_time)
            
            for i in range(refresh_count):
                logger.info(f"正在执行保活刷新 ({i+1}/{refresh_count})...")
                sb.refresh()
                sb.sleep(refresh_interval)

            # ---- [步骤 G] 成果记录与TG推送 ----
            final_img = str(OUTPUT_DIR / "final_result.png")
            sb.save_screenshot(final_img)
            send_tg_notification(
                "保活成功 ✅", 
                f"Lunes.host 控制台保活任务已完成！\n🔄 **刷新次数**: `{refresh_count}`\n⏱️ **停留时间**: `{stay_time}s`", 
                final_img
            )

        except Exception as e:
            error_img = str(OUTPUT_DIR / "error.png")
            sb.save_screenshot(error_img)
            # 记录错误并发送通知
            logger.error(f"Lunes 流程异常: {str(e)}")
            send_tg_notification("执行异常 ❌", f"Lunes 流程中断: `{str(e)}`", error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
