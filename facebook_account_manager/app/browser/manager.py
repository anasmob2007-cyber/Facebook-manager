"""
Isolated browser profiles per account via Playwright persistent context.

- User completes login manually when required.
- Does NOT bypass CAPTCHA, 2FA, or security checks.
- Does NOT auto-extract cookies/tokens from the browser.
- Session cookies are only accepted when the user explicitly imports them.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from app.core.config import BROWSER_PROFILES_DIR

logger = logging.getLogger("fam.browser")


class BrowserManager:
    def __init__(self) -> None:
        self._playwright = None
        self._contexts: dict[int, object] = {}

    def profile_dir(self, account_id: int) -> Path:
        d = BROWSER_PROFILES_DIR / f"account_{account_id}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def open_for_account(
        self,
        account_id: int,
        start_url: str = "https://www.facebook.com/",
        session_json: Optional[str] = None,
    ) -> str:
        """
        Launch Chromium persistent context for this account.
        Returns status message. Blocks until browser window is closed if called sync.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return "Playwright not installed. Run: pip install playwright && playwright install chromium"

        profile = self.profile_dir(account_id)
        logger.info("Opening browser profile for account_id=%s path=%s", account_id, profile)

        try:
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(profile),
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                    args=["--disable-blink-features=AutomationControlled"],
                )
                # Optional: apply user-supplied cookies once (not scraped)
                if session_json:
                    try:
                        cookies = json.loads(session_json)
                        if isinstance(cookies, list):
                            # Ensure domain for FB
                            fixed = []
                            for c in cookies:
                                if not isinstance(c, dict) or "name" not in c:
                                    continue
                                item = dict(c)
                                item.setdefault("domain", ".facebook.com")
                                item.setdefault("path", "/")
                                fixed.append(item)
                            if fixed:
                                context.add_cookies(fixed)
                                logger.info("Applied %s user-provided cookies (names only logged)", len(fixed))
                    except Exception as e:
                        logger.warning("Could not apply session cookies: %s", e)

                page = context.pages[0] if context.pages else context.new_page()
                page.goto(start_url, wait_until="domcontentloaded", timeout=60000)
                # Wait until user closes the browser — no auto login, no token steal
                page.wait_for_event("close", timeout=0) if False else None
                # Simpler: keep open until context closes
                try:
                    page.pause()  # opens inspector; user closes when done
                except Exception:
                    pass
                context.close()
            return "Browser session closed"
        except Exception as e:
            logger.error("Browser error: %s", e)
            return f"Browser error: {e}"

    def open_manual_login(self, account_id: int) -> str:
        """Open clean profile so user can log in manually (no password stored by app)."""
        return self.open_for_account(account_id, session_json=None)
