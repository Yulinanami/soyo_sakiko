"""
Lofter Login Script - Get login cookie for API access
Run with: python get_lofter_cookie.py

This script will help you get the Lofter cookie needed for API access.
"""

import sys
import os


def get_lofter_cookie_manual():
    """Guide user to manually get cookie"""
    print("🔐 Lofter Cookie 获取指南")
    print("=" * 50)
    print()
    print("由于 Lofter 需要登录才能搜索内容，请按以下步骤获取 Cookie：")
    print()
    print("1. 打开浏览器，访问 https://www.lofter.com")
    print("2. 登录你的 Lofter 账号")
    print("3. 登录成功后，访问 https://www.lofter.com/tag/素祥")
    print("4. 按 F12 打开开发者工具")
    print("5. 切换到 Network（网络）面板")
    print("6. 刷新页面")
    print("7. 找到 'TagBean.search.dwr' 请求")
    print("8. 点击该请求，在 Headers 中找到 Cookie")
    print("9. 复制整个 Cookie 值")
    print()
    print("=" * 50)

    cookie = input("请粘贴 Cookie 值 (或按 Enter 跳过): ").strip()

    if cookie:
        # Save to file
        with open(".lofter_cookie.txt", "w", encoding="utf-8") as f:
            f.write(cookie)
        print("\n✅ Cookie 已保存到 .lofter_cookie.txt")

        # Also update .env if exists
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                content = f.read()

            if "LOFTER_COOKIE=" in content:
                # Replace existing
                lines = content.split("\n")
                new_lines = []
                for line in lines:
                    if line.startswith("LOFTER_COOKIE="):
                        new_lines.append(f"LOFTER_COOKIE={cookie}")
                    else:
                        new_lines.append(line)
                content = "\n".join(new_lines)
            else:
                # Add new
                content += f"\nLOFTER_COOKIE={cookie}\n"

            with open(env_file, "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ Cookie 已添加到 .env 文件")
        else:
            print(f"\n📝 请将以下内容添加到 {env_file} 文件：")
            print(f"LOFTER_COOKIE={cookie}")

        return cookie
    return None


def get_lofter_cookie_browser():
    """Use browser automation to get cookie"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("⚠️ playwright 未安装，使用手动模式")
        return get_lofter_cookie_manual()

    print("🔐 Lofter Cookie 自动获取")
    print("=" * 50)
    print()
    print("1. 浏览器窗口将打开")
    print("2. 登录你的 Lofter 账号")
    print("3. 登录成功后回到这里按 Enter")
    print()
    input("按 Enter 开始...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("\n📱 正在打开 Lofter...")
        page.goto("https://www.lofter.com/login")

        print("⏳ 请登录 Lofter...")
        print("   登录成功后，请按 Enter 键继续")
        input()

        # Get cookies
        cookies = context.cookies()
        browser.close()

        # Find Lofter cookies
        lofter_cookies = []
        for cookie in cookies:
            if "lofter" in cookie.get("domain", "").lower():
                lofter_cookies.append(f"{cookie['name']}={cookie['value']}")

        if lofter_cookies:
            cookie_string = "; ".join(lofter_cookies)
            print("\n" + "=" * 50)
            print("✅ Cookie 获取成功!")

            # Save to file
            with open(".lofter_cookie.txt", "w", encoding="utf-8") as f:
                f.write(cookie_string)
            print("📁 Cookie 已保存到 .lofter_cookie.txt")

            # Update .env
            env_file = ".env"
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    content = f.read()

                if "LOFTER_COOKIE=" in content:
                    lines = content.split("\n")
                    new_lines = []
                    for line in lines:
                        if line.startswith("LOFTER_COOKIE="):
                            new_lines.append(f"LOFTER_COOKIE={cookie_string}")
                        else:
                            new_lines.append(line)
                    content = "\n".join(new_lines)
                else:
                    content += f"\nLOFTER_COOKIE={cookie_string}\n"

                with open(env_file, "w", encoding="utf-8") as f:
                    f.write(content)
                print("✅ Cookie 已添加到 .env 文件")

            return cookie_string
        else:
            print("\n❌ 未找到 Lofter Cookie，请确认已登录成功")
            return get_lofter_cookie_manual()


def test_cookie():
    """Test if the cookie works"""
    from dotenv import load_dotenv

    load_dotenv()

    cookie = os.getenv("LOFTER_COOKIE")
    if not cookie:
        try:
            with open(".lofter_cookie.txt", "r", encoding="utf-8") as f:
                cookie = f.read().strip()
        except:
            pass

    if not cookie:
        print("❌ 未找到 LOFTER_COOKIE")
        return False

    print("\n🔍 测试 Cookie...")

    import httpx

    api_url = "https://www.lofter.com/dwr/call/plaincall/TagBean.search.dwr"

    body = {
        "callCount": "1",
        "scriptSessionId": "${scriptSessionId}187",
        "httpSessionId": "",
        "c0-scriptName": "TagBean",
        "c0-methodName": "search",
        "c0-id": "0",
        "c0-param0": "string:素祥",
        "c0-param1": "number:0",
        "c0-param2": "string:",
        "c0-param3": "string:new",
        "c0-param4": "boolean:false",
        "c0-param5": "number:0",
        "c0-param6": "number:5",
        "c0-param7": "number:0",
        "c0-param8": "number:0",
        "batchId": "493053",
    }

    headers = {
        "Referer": "https://www.lofter.com/tag/素祥",
        "Cookie": cookie,
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    body_str = "&".join(f"{k}={v}" for k, v in body.items())

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(api_url, content=body_str, headers=headers)

            if response.status_code == 200:
                if "blogPageUrl" in response.text:
                    print("✅ Cookie 有效! 成功获取到搜索结果")
                    return True
                elif "请先登录" in response.text:
                    print("❌ Cookie 无效或已过期")
                    return False
                else:
                    print(f"⚠️ 收到响应但无法验证 (长度: {len(response.text)} bytes)")
                    return True
            else:
                print(f"❌ 请求失败: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_cookie()
    elif len(sys.argv) > 1 and sys.argv[1] == "manual":
        cookie = get_lofter_cookie_manual()
        if cookie:
            test_cookie()
    else:
        # Try browser first, fallback to manual
        cookie = get_lofter_cookie_browser()
        if cookie:
            test_cookie()
