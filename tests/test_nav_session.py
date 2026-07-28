"""Real-browser navigation test: the session must SURVIVE clicking around the
gated app. The rail is st.page_link (SPA nav) — raw anchors used to cause a
full reload and logged the user out on every click.

Boots a throwaway gated server on :8659, logs in as a coach (legacy password)
and as a client, clicks every rail destination, and asserts the lock screen
never reappears. Needs playwright (installed locally); run directly:

    python3 tests/test_nav_session.py
"""
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import coachlib as cl

PORT = 8659
BASE = f"http://localhost:{PORT}"
LOCK_MARKER = "This console is private"
GATE_PW = "navtest-pw"
CLIENT = "Nav Test Client"


def _wait_up(timeout=45):
    for _ in range(timeout):
        try:
            urllib.request.urlopen(BASE, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def _login(pg, username, password):
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(1800)
    pg.get_by_text("Login  →").click()
    pg.wait_for_timeout(900)
    pg.locator('input[aria-label="Username"]').fill(username)
    pg.locator('input[aria-label="Password"]').fill(password)
    pg.get_by_role("button", name="Log in").click()
    pg.wait_for_timeout(2400)


def _click_through(pg, labels, failures, who):
    for label in labels:
        pg.locator('.st-key-te_rail').first.hover()   # expand the rail
        pg.wait_for_timeout(400)
        pg.get_by_role("link", name=label, exact=True).click()
        pg.wait_for_timeout(2000)
        body = pg.content()
        if LOCK_MARKER in body:
            failures.append(f"{who}: logged out navigating to {label!r}")
        if who == "client" and "Your coach handles this page" in body:
            failures.append(f"{who}: role-blocked on own page {label!r}")


def main():
    from playwright.sync_api import sync_playwright

    cl.upsert_client(CLIENT, {"goals": "Lose fat", "bodyweight": "180 lbs"})
    cl.set_client_login(CLIENT, "nav.client@test.co", "nav-pw-1")
    env = dict(os.environ, APP_PASSWORD=GATE_PW)
    srv = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.port", str(PORT), "--server.headless", "true"],
        cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    failures = []
    try:
        assert _wait_up(), "gated test server did not come up"
        with sync_playwright() as p:
            browser = p.chromium.launch()
            # coach: any username + the legacy access password
            pg = browser.new_page(viewport={"width": 1440, "height": 950})
            _login(pg, "coach", GATE_PW)
            if LOCK_MARKER in pg.content():
                failures.append("coach: login itself failed")
            else:
                _click_through(pg, ["Clients", "Meal Planner", "Weigh-ins",
                                    "Check-in", "Applications", "Home"],
                               failures, "coach")
            # client: their own credentials, their own trimmed nav
            pg2 = browser.new_page(viewport={"width": 1440, "height": 950})
            _login(pg2, "nav.client@test.co", "nav-pw-1")
            if LOCK_MARKER in pg2.content():
                failures.append("client: login itself failed")
            else:
                _click_through(pg2, ["My Training", "Weigh-ins", "Check-in",
                                     "My Plan", "Supplements", "Home"],
                               failures, "client")
            browser.close()
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=10)
        except Exception:
            srv.kill()
        cl.delete_client(CLIENT)

    if failures:
        for f in failures:
            print("FAIL ", f)
        print(f"\n{len(failures)} failure(s)")
        sys.exit(1)
    print("PASS  coach + client navigated every rail page, session survived")
    sys.exit(0)


if __name__ == "__main__":
    main()
