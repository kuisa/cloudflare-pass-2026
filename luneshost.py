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
            # 增加显式等待，防止页面加载慢
            sb.wait_for_element_visible("#email", timeout=25)
            sb.type("#email", email)
            sb.type("#password", password)
            
            # ---- [步骤 C] 调用核心 API 处理人机验证 ----
            # 注意：在点击登录前，必须确保 CF 验证已通过
            current_url = sb.get_current_url()
            if "1." in ui_mode: api_core_1(current_url)
            elif "2." in ui_mode: api_core_2(current_url, proxy=os.environ.get("PROXY"))
            elif "3." in ui_mode: api_core_3(url=current_url, proxy_file="proxy.txt", batch_size=3)
            elif "4." in ui_mode: api_core_4(sb)
            
            # 尝试点击 CF 复选框（如果存在）
            try:
                sb.uc_gui_click_captcha()
            except:
                pass
                
            sb.sleep(5)
            
            # 点击登录提交
            logger.info("点击 Continue 按钮...")
            sb.click('button.submit-btn')
            
            # 验证登录是否成功：检查是否跳转到了 Dashboard
            sb.wait_for_condition(lambda d: "login" not in d.current_url, timeout=20)
            logger.info("登录成功，正在进入控制台...")
            sb.sleep(5)

            # ---- [步骤 D] 进入服务器详情页 (ID: 52794) ----
            logger.info("正在定位服务器卡片 52794...")
            # 如果在 Dashboard 页面找不到，尝试直接访问详情页 URL
            target_server_url = "https://betadash.lunes.host/servers/52794"
            sb.uc_open_with_reconnect(target_server_url, 10)
            
            # ---- [步骤 E] 执行停留与保活刷新 ----
            logger.info(f"成功进入服务器控制台，执行停留 {stay_time} 秒...")
            sb.sleep(stay_time)
            
            for i in range(refresh_count):
                logger.info(f"正在执行保活刷新 ({i+1}/{refresh_count})...")
                sb.refresh()
                sb.sleep(refresh_interval)

            # ---- [步骤 F] 成果记录与TG推送 ----
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
            send_tg_notification("执行异常 ❌", f"Lunes 流程中断: `{str(e)}`", error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
