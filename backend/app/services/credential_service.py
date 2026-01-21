"""登录凭证服务"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import base64
import hashlib
import secrets
import threading
import time
import re
import logging
from typing import Dict, Optional

from app.services.http_client import get_sync_client

from app.config import settings

logger = logging.getLogger(__name__)

PIXIV_CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
PIXIV_CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
PIXIV_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
PIXIV_REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
PIXIV_USER_AGENT = "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)"


@dataclass
class CredentialState:
    state: str = "idle"
    message: str = ""
    updated_at: str = ""
    running: bool = False


class CredentialManager:
    def __init__(self) -> None:
        """初始化状态与控制"""
        self._states: Dict[str, CredentialState] = {
            "lofter": CredentialState(),
            "pixiv": CredentialState(),
        }
        self._locks: Dict[str, threading.Lock] = {
            "lofter": threading.Lock(),
            "pixiv": threading.Lock(),
        }

    def status(self, source: str) -> CredentialState:
        """获取当前状态"""
        return self._states[source]

    def start_lofter(self) -> CredentialState:
        """启动 Lofter 登录"""
        return self._start("lofter", self._lofter_worker)

    def start_pixiv(self) -> CredentialState:
        """启动 Pixiv 登录"""
        return self._start("pixiv", self._pixiv_worker)

    def _start(self, source: str, target) -> CredentialState:
        """启动登录任务"""
        state = self._states[source]
        lock = self._locks[source]
        with lock:
            if state.running:
                return state
            state.state = "running"
            state.message = "正在打开登录窗口，请完成登录..."
            state.updated_at = datetime.utcnow().isoformat()
            state.running = True
            thread = threading.Thread(target=target, daemon=True)
            thread.start()
            return state

    def clear(self, source: str) -> None:
        """清除登录信息"""
        if source == "lofter":
            settings.LOFTER_COOKIE = ""
            settings.LOFTER_CAPTTOKEN = ""
            self._write_env("LOFTER_COOKIE", "")
            self._write_env("LOFTER_CAPTTOKEN", "")
        if source == "pixiv":
            settings.PIXIV_REFRESH_TOKEN = ""
            self._write_env("PIXIV_REFRESH_TOKEN", "")
            try:
                from app.adapters import get_adapter
                from app.schemas.novel import NovelSource

                adapter = get_adapter(NovelSource.PIXIV)
                reset = getattr(adapter, "reset", None)
                if callable(reset):
                    reset()
            except Exception as exc:
                logger.warning("Pixiv adapter reset failed: %s", exc)
        self._set_state(source, "idle", "凭证已清除")

    def _set_state(self, source: str, state: str, message: str) -> None:
        """更新状态信息"""
        record = self._states[source]
        record.state = state
        record.message = message
        record.updated_at = datetime.utcnow().isoformat()
        record.running = state == "running"

    def _lofter_worker(self) -> None:
        """处理 Lofter 登录流程"""
        try:
            cookie, capttoken = self._capture_lofter_credentials()
            if cookie and self._is_lofter_cookie_valid(cookie):
                settings.LOFTER_COOKIE = cookie
                self._write_env("LOFTER_COOKIE", cookie)
            if capttoken:
                settings.LOFTER_CAPTTOKEN = capttoken
                self._write_env("LOFTER_CAPTTOKEN", capttoken)
            if cookie and self._is_lofter_cookie_valid(cookie):
                self._set_state("lofter", "success", "Lofter 登录成功")
            else:
                self._set_state("lofter", "error", "未获取到 Lofter Cookie")
        except Exception as exc:
            self._set_state("lofter", "error", f"Lofter 登录失败: {exc}")

    def _pixiv_worker(self) -> None:
        """处理 Pixiv 登录流程"""
        try:
            refresh_token = self._capture_pixiv_refresh_token()
            if refresh_token:
                settings.PIXIV_REFRESH_TOKEN = refresh_token
                self._write_env("PIXIV_REFRESH_TOKEN", refresh_token)
                try:
                    from app.adapters import get_adapter
                    from app.schemas.novel import NovelSource

                    adapter = get_adapter(NovelSource.PIXIV)
                    reset = getattr(adapter, "reset", None)
                    if callable(reset):
                        reset()
                except Exception as exc:
                    logger.warning("Pixiv adapter reset after login failed: %s", exc)
                self._set_state("pixiv", "success", "Pixiv 登录成功")
            else:
                self._set_state("pixiv", "error", "未获取到 Pixiv Refresh Token")
        except Exception as exc:
            self._set_state("pixiv", "error", f"Pixiv 登录失败: {exc}")

    def _capture_lofter_credentials(self):
        """获取 Lofter 登录信息"""
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
        except ImportError as exc:
            raise RuntimeError("Playwright 未安装") from exc

        capttoken_holder = {"value": ""}
        cookie_string = ""

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            def on_request(request):
                """记录请求里的参数"""
                if "TagBean.search.dwr" in request.url:
                    token = request.headers.get("capttoken")
                    if token:
                        capttoken_holder["value"] = token

            page.on("request", on_request)
            page.goto("https://www.lofter.com/login", wait_until="domcontentloaded")

            deadline = time.time() + 300
            while time.time() < deadline:
                cookies = context.cookies()
                cookie_string = self._extract_lofter_cookie(cookies)
                if cookie_string and self._is_lofter_cookie_valid(cookie_string):
                    break
                time.sleep(1)

            if cookie_string and self._is_lofter_cookie_valid(cookie_string):
                page.goto(
                    "https://www.lofter.com/tag/素祥", wait_until="domcontentloaded"
                )
                try:
                    page.wait_for_timeout(3000)
                except PWTimeout:
                    pass

            context.close()
            browser.close()

        return cookie_string, capttoken_holder["value"]

    def _extract_lofter_cookie(self, cookies) -> str:
        """整理 Lofter 登录信息"""
        cookie_parts = []
        for c in cookies:
            if "lofter" in c.get("domain", "").lower():
                cookie_parts.append(f"{c['name']}={c['value']}")
        return "; ".join(cookie_parts)

    def _is_lofter_cookie_valid(self, cookie: str) -> bool:
        """判断 Lofter 登录信息是否可用"""
        if not cookie:
            return False
        has_token = "token=" in cookie
        login_markers = [
            "LOFTER-PHONE-LOGIN-AUTH=",
            "LOFTER-PHONE-LOGIN-FLAG=1",
            "LOFTER-PHONE-LOGINNUM=",
            "NEWTOKEN=",
            "reglogin_isLoginFlag=1",
        ]
        return has_token and any(marker in cookie for marker in login_markers)

    def _capture_pixiv_refresh_token(self) -> Optional[str]:
        """获取 Pixiv 登录码"""
        try:
            from playwright.sync_api import sync_playwright, TimeoutError
        except ImportError as exc:
            raise RuntimeError("Playwright 未安装") from exc

        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode("ascii")
        )

        auth_url = (
            "https://app-api.pixiv.net/web/v1/login?"
            f"code_challenge={code_challenge}&"
            "code_challenge_method=S256&client=pixiv-android&"
            f"redirect_uri={PIXIV_REDIRECT_URI}"
        )

        captured_code = {"value": None}

        def try_capture(url: str) -> None:
            """从地址中取出登录码"""
            if not url or captured_code["value"]:
                return
            match = re.search(r"[?&]code=([^&]+)", url)
            if match:
                captured_code["value"] = match.group(1)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            cdp_session = context.new_cdp_session(page)
            cdp_session.send("Network.enable")

            def on_request(event):
                """检查请求里有没有登录码"""
                url = event.get("request", {}).get("url", "")
                check_url = url or event.get("documentURL", "")
                if (
                    check_url.startswith("pixiv://account/login")
                    or "pixiv/callback" in check_url
                ):
                    try_capture(check_url)
                    if captured_code["value"]:
                        page.close()

            cdp_session.on("Network.requestWillBeSent", on_request)
            page.on("request", lambda request: try_capture(request.url))
            page.on("framenavigated", lambda frame: try_capture(frame.url))
            page.goto(auth_url, wait_until="domcontentloaded")

            try:
                page.wait_for_event("close", timeout=180000)
            except TimeoutError:
                pass
            try_capture(page.url)

            context.close()
            browser.close()

        code = captured_code["value"]
        if not code:
            return None

        data = {
            "client_id": PIXIV_CLIENT_ID,
            "client_secret": PIXIV_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": PIXIV_REDIRECT_URI,
            "include_policy": "true",
        }
        headers = {"User-Agent": PIXIV_USER_AGENT}

        client = get_sync_client()
        response = client.post(PIXIV_TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        payload = response.json()
        return payload.get("refresh_token")

    def _write_env(self, key: str, value: str) -> None:
        """写入配置文件"""
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if not env_path.exists():
            env_path.write_text(f"{key}={value}\n", encoding="utf-8")
            return
        lines = env_path.read_text(encoding="utf-8").splitlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"{key}={value}")
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


credential_manager = CredentialManager()
