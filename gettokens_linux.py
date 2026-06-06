import subprocess
import sys
import time
import webbrowser
import shutil
import os

required_packages = ["browser-cookie3"]
for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        print(f"[!] Installing missing package: {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import browser_cookie3
import tkinter as tk
from tkinter import ttk

token_file = "token.txt"
script_path = "NScript.py"
firefox_cmd = r'gnome-terminal -- sh -c "firefox %s"'

MI_DOMAINS = ["c.mi.com", "new.c.mi.com"]
TOKEN_DOMAINS = ["c.mi.com", "new.c.mi.com", "mi.com", "account.xiaomi.com"]

def show_taskbar_prompt(title, message, ok_text="OK"):
    # Fallback to terminal prompt if no GUI/display is available.
    if not os.environ.get("DISPLAY"):
        print(f"\n{title}\n{message}")
        input(f"Press Enter to continue ({ok_text})...")
        return True

    try:
        root = tk.Tk()
        root.title(title)
        root.resizable(False, False)
        width, height = 420, 140
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.attributes("-topmost", True)
        root.after(200, lambda: root.attributes("-topmost", False))
        frm = ttk.Frame(root, padding=12)
        frm.pack(expand=True, fill=tk.BOTH)
        lbl = ttk.Label(frm, text=message, wraplength=width - 30, justify=tk.LEFT)
        lbl.pack(pady=(6, 12), anchor=tk.W)
        result = {"ok": False}

        def on_ok():
            result["ok"] = True
            root.destroy()

        btn = ttk.Button(frm, text=ok_text, command=on_ok)
        btn.pack(side=tk.BOTTOM)
        root.update_idletasks()
        root.deiconify()
        root.lift()
        root.mainloop()
        return result["ok"]
    except tk.TclError:
        print(f"\n{title}\n{message}")
        input(f"Press Enter to continue ({ok_text})...")
        return True

def _extract_cookie_value(cookie_jar, cookie_names):
    for cookie in cookie_jar:
        if cookie.name in cookie_names and cookie.value:
            return cookie.value
    return None

def _read_browser_cookies(browser_getter, cookie_names):
    for domain in TOKEN_DOMAINS:
        try:
            jar = browser_getter(domain_name=domain)
            value = _extract_cookie_value(jar, cookie_names)
            if value:
                return value, domain
        except Exception:
            continue
    return None, None

def _read_browser_cookies_debug(browser_getter, cookie_names):
    errors = []
    for domain in TOKEN_DOMAINS:
        try:
            jar = browser_getter(domain_name=domain)
            value = _extract_cookie_value(jar, cookie_names)
            if value:
                return value, domain, errors
        except Exception as e:
            errors.append(f"{type(e).__name__}: {e}")
            continue
    return None, None, errors

def _collect_chromium_cookie_getters():
    getters = []
    for getter_name in ["chrome", "chromium", "brave", "edge", "opera"]:
        getter = getattr(browser_cookie3, getter_name, None)
        if callable(getter):
            getters.append((getter_name, getter))
    return getters

def _detect_terminal_launcher():
    launchers = [
        ("gnome-terminal", lambda cmd: ["gnome-terminal", "--", "sh", "-lc", cmd]),
        ("konsole", lambda cmd: ["konsole", "-e", "sh", "-lc", cmd]),
        ("xfce4-terminal", lambda cmd: ["xfce4-terminal", "--command", f"sh -lc '{cmd}'"]),
        ("mate-terminal", lambda cmd: ["mate-terminal", "--", "sh", "-lc", cmd]),
        ("xterm", lambda cmd: ["xterm", "-e", f"sh -lc '{cmd}'"]),
        ("alacritty", lambda cmd: ["alacritty", "-e", "sh", "-lc", cmd]),
    ]
    for name, builder in launchers:
        if shutil.which(name):
            return name, builder
    return None, None

def launch_script_terminals(script, python_bin="python3"):
    term_name, build_cmd = _detect_terminal_launcher()
    if not term_name:
        print("[!] No supported terminal emulator found. Install gnome-terminal/konsole/xterm/alacritty.")
        print("[i] Manual fallback: run `python3 NScript.py` in 4 terminals and input rows 1..4.")
        return

    print(f"[i] Launching NScript windows via: {term_name}")
    for i in range(1, 5):
        cmd = f'echo {i} | {python_bin} "{script}"; exec sh'
        try:
            subprocess.Popen(build_cmd(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[!] Failed to launch terminal #{i} with {term_name}: {e}")
        time.sleep(0.1)

def _wait_for_firefox_exit(timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        result = subprocess.run(["pgrep", "-x", "firefox"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            return True
        time.sleep(0.5)
    return False

def extract_firefox_token():
    token, domain = _read_browser_cookies(browser_cookie3.firefox, {"new_bbs_serviceToken", "serviceToken"})
    if token:
        print(f"[✔] Firefox token found from {domain}")
        return token
    print("[✖] Firefox token not found in cookie store.")
    return None

def extract_chrome_token(reference_token=None):
    # Prefer direct cookie extraction to avoid webdriver startup issues.
    keyring_blocked = False
    for browser_name, getter in _collect_chromium_cookie_getters():
        token, domain, errors = _read_browser_cookies_debug(getter, {"new_bbs_serviceToken", "serviceToken"})
        if token:
            if reference_token and token == reference_token:
                print(f"[i] {browser_name} token matches Firefox token; searching for an alternative...")
                continue
            print(f"[✔] Chromium-family service token found via {browser_name} from {domain}")
            return token
        if any("Unable to get key for cookie decryption" in err for err in errors):
            keyring_blocked = True

    # Some setups keep the same service token in Firefox only.
    token, domain = _read_browser_cookies(browser_cookie3.firefox, {"new_bbs_serviceToken", "serviceToken"})
    if token:
        if reference_token and token == reference_token:
            print("[i] Firefox secondary service token matches primary token; trying manual fallback for a distinct pair.")
        else:
            print(f"[✔] Secondary service token found via firefox from {domain}")
            return token

    print("[✖] Secondary service token not found in cookie store.")
    if keyring_blocked:
        print("[i] Detected Linux keyring blockade for Chromium-family cookie decryption.")
        print("[i] Applying workaround: relaunch with --password-store=basic.")
        if not open_chromium_with_basic_password_store("https://c.mi.com/global"):
            print("[i] Could not auto-launch workaround, opening browser normally.")
            open_url("https://c.mi.com/global")
    else:
        print("[i] Fallback: open Chromium-family browser manually, login, then press Enter and re-check cookies.")
        open_url("https://c.mi.com/global")

    show_taskbar_prompt(
        "Login required - Browser",
        "Please log in on c.mi.com/global in your Chromium-family browser.\nPress OK after login so the script can re-check cookies."
    )

    for browser_name, getter in _collect_chromium_cookie_getters():
        token, domain, _ = _read_browser_cookies_debug(getter, {"new_bbs_serviceToken", "serviceToken"})
        if token:
            if reference_token and token == reference_token:
                print(f"[i] {browser_name} token still matches Firefox token after retry.")
                continue
            print(f"[✔] Chromium-family service token found via {browser_name} from {domain} after retry")
            return token

    manual = input("[?] Paste new_bbs_serviceToken manually (leave blank to keep same token pair): ").strip()
    if manual:
        if reference_token and manual == reference_token:
            print("[i] Manual token is identical to Firefox token.")
        return manual

    if reference_token:
        print("[!] Could not obtain a distinct second token; using the same token for all rows.")
        return reference_token

    return None

def update_token_file(firefox_token, chrome_token):
    lines = [
        firefox_token or "N/A",
        chrome_token or "N/A",
        firefox_token or "N/A",
        chrome_token or "N/A"
    ]
    with open(token_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("[✔] token.txt updated with all tokens!")
    unique_count = len({x for x in [firefox_token, chrome_token] if x and x != "N/A"})
    if unique_count < 2:
        print("[i] token.txt currently contains one unique token value across rows.")

def prompt_login_firefox():
    try:
        if shutil.which("firefox"):
            subprocess.Popen(["firefox", "https://c.mi.com/global"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            webbrowser.open("https://c.mi.com/global")
    except Exception:
        webbrowser.open("https://c.mi.com/global")
    show_taskbar_prompt(
        "Login required - Firefox",
        "Please log in on c.mi.com/global in the opened Firefox window.\nAfter you've finished logging in, press OK to continue."
    )
    print("[i] Attempting to close Firefox gently to ensure cookies are saved...")
    try:
        subprocess.run(["killall", "-15", "firefox"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not _wait_for_firefox_exit(timeout=6):
            print("[i] Firefox is still running; continuing anyway.")
    except Exception as e:
        print(f"[!] Could not close Firefox automatically: {e}")
    time.sleep(2)

def open_url(url):
    opened = False
    for candidate in [
        "thorium-browser",
        "thorium",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "brave-browser",
        "vivaldi",
        "opera",
        "microsoft-edge",
        "microsoft-edge-stable",
        "firefox",
    ]:
        if shutil.which(candidate):
            try:
                subprocess.Popen([candidate, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[i] Opened URL using: {candidate}")
                opened = True
                break
            except Exception:
                continue
    if not opened:
        webbrowser.open(url)

def open_chromium_with_basic_password_store(url):
    candidates = [
        "thorium-browser",
        "thorium",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "brave-browser",
        "vivaldi",
        "opera",
        "microsoft-edge",
        "microsoft-edge-stable",
    ]
    for candidate in candidates:
        if shutil.which(candidate):
            try:
                subprocess.Popen([candidate, "--password-store=basic", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[i] Opened URL using workaround on: {candidate}")
                return True
            except Exception:
                continue
    return False

if __name__ == "__main__":
    print("GetTokens V2 - by byBestix on xdaforums")
    if not os.path.exists(script_path):
        print(f"[!] Script not found: {script_path}")
        custom_script = input("Enter script path to run in 4 terminals (or leave blank to skip): ").strip()
        script_path = custom_script if custom_script else ""

    prompt_login_firefox()
    firefox_token = extract_firefox_token()
    if not firefox_token:
        print("[✖] Firefox token not found!")
        print("[i] Tip: open https://c.mi.com/global in Firefox and confirm account is logged in there.")
    else:
        print("[✔] Firefox token extracted.")
    chrome_token = extract_chrome_token(reference_token=firefox_token)
    if not chrome_token:
        print("[✖] Chrome token not found!")
        print("[i] Tip: if using Thorium on KDE, encrypted cookie decryption may fail; manual service-token paste remains available.")
    else:
        print("[✔] Chrome token extracted.")
    update_token_file(firefox_token, chrome_token)
    if script_path:
        python_bin = "python3"
        launch_script_terminals(script_path, python_bin=python_bin)
    else:
        print("[i] Skipping terminal launch because no script path was provided.")
    time.sleep(0.5)
