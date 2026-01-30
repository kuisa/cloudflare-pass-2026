import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
from seleniumbase import SB
from loguru import logger

# ==========================================
# 1. 严格按照仓库 API 逻辑进行函数导入 (保持原样)
# ==========================================
try:
    # API 1: 简单模式 (bypass.py)
    from bypass import bypass_cloudflare as api_core_1
    # API 2 & 3: 完整模式 (simple_bypass.py)
    from simple_bypass import bypass_cloudflare as api_core_2
    from simple_bypass import bypass_parallel as api_core_3
    # API 4: 指纹增强模式 (bypass_seleniumbase.py)
    from bypass_seleniumbase import bypass_logic as api_core_4
    logger.info("📡 核心 API 插件已成功挂载至主程序")
except Exception as e:
    logger.error(f"🚨 API 加载失败: {e}")

# ==========================================
# 2. 高科技 TGUI 功能 (北京时间 + 状态判断)
# ==========================================
def send_tg_notification(status, message, photo_path=None):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id): return
    
    # 强制转换为北京时间 (UTC+8)
    bj_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    emoji = "✅" if "成功" in status else "⚠️" if "未到期" in status else "❌"
    
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

            # ---- [步骤 C] 核心：正确调用 API ----
            current_url = sb.get_current_url()
            logger.info(f">>> 正在按原作者逻辑调用 API: {ui_mode}")

            if "1." in ui_mode:
                result = api_core_1(current_url)
            elif "2." in ui_mode:
                result = api_core_2(current_url, proxy=os.environ.get("PROXY"))
            elif "3." in ui_mode:
                result = api_core_3(url=current_url, proxy_file="proxy.txt", batch_size=3)
            elif "4." in ui_mode:
                api_core_4(sb)
                result = {"success": True}

            # ---- [步骤 D] 整合成果与精准点击 ----
            sb.uc_gui_click_captcha()
            logger.info("验证已完成，进入 20 秒稳定缓冲期...")
            sb.sleep(20) # 按照要求：给 20 秒时间让脚本启动过人机验证并稳定
            
            # 精准打击：根据 HTML 源码定位 Renew 按钮
            logger.info("执行最终 Renew 提交点击...")
            try:
                # 优先点击 id 为 renew-modal 容器下的 primary 按钮
                sb.wait_for_element_visible('#renew-modal button[type="submit"].btn-primary', timeout=20)
                sb.click('#renew-modal button[type="submit"].btn-primary')
            except:
                # 兜底：使用 JS 强制点击
                sb.js_click('#renew-modal button.btn-primary')
            
            sb.sleep(12) # 等待页面刷新处理

            # ---- [步骤 E] 结果抓取与智能通知 ----
            final_img = str(OUTPUT_DIR / "final_result.png")
            sb.save_screenshot(final_img)
            
            # 读取页面源码分析结果
            page_source = sb.get_page_source()
            
            # 逻辑：检查页面是否出现了新的日期格式
            if "2026-" in page_source:
                try:
                    # 使用 Expiry 邻近节点定位抓取具体日期：<div class="col-lg-9 col-md-8">2026-02-02</div>
                    expiry_date = sb.get_text('//div[contains(text(), "Expiry")]/following-sibling::div')
                    send_tg_notification("续期成功 ✅", f"服务器续期已生效！\n📅 **下次到期**: `{expiry_date}`", final_img)
                except:
                    # 备选提取方式
                    expiry_date = sb.get_text('div.col-lg-9.col-md-8')
                    send_tg_notification("续期成功 ✅", f"服务器续期成功！\n📅 **下次到期**: `{expiry_date}`", final_img)
            else:
                send_tg_notification("未到期 ⚠️", "验证已过但页面未更新日期，可能尚未达到可续期时间。", final_img)

        except Exception as e:
            error_img = str(OUTPUT_DIR / "error.png")
            sb.save_screenshot(error_img)
            send_tg_notification("执行异常 ❌", f"错误详情: `{str(e)}`", error_img)
            raise e

if __name__ == "__main__":
    run_auto_renew()
