"""
To run in a virtual environment:
    python3 -m venv pp_env
    source pp_env/bin/activate
    pip install -r requirements.txt
    python pp.py


Cleaned Python script extracted from the notebook.
Features:
- Creates default `config.json` if missing
- Loads URLs from `PiratePunisher_WebsiteList.xlsx`
- Uses Selenium (Firefox/geckodriver) to attempt newsletter signups
- Provides a simple Tkinter GUI to run the process

Use responsibly. Ensure `automation_allowed` is set to true in `config.json`
and you have permission to interact with the target websites.
"""


import os
import sys
import json
import time
import csv
import re
import traceback
import platform
import shutil
import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
try:
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
except ImportError:
    FirefoxOptions = None
try:
    from selenium.webdriver.chrome.options import Options as ChromeOptions
except ImportError:
    ChromeOptions = None

print("pp.py started")  # DEBUG
# ----------------------------
# CONFIG
# ----------------------------
CFG_PATH = "config.json"
DEFAULT_CONFIG = {
    "automation_allowed": False,
    "retries": 1,
    "retry_delay": 6,
    "find_timeout": 20,
    "submit_wait": 5,
    "confirmation_keywords": [
        "thank", "success", "subscribed", "confirmed", "welcome", "thank you", "check your email"
    ],
    "popup_email_selectors": [
        "input[type='email']", "input[name*='email']", "input[placeholder*='email']"
    ],
    "popup_submit_selectors": [
        "button[type='submit']", "input[type='submit']", "button[name*='sub']", "input[name*='sub']"
    ],
    "cookie_accept_xpaths": [
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'accept')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'agree')]",
        "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'ok')]",
    ],
    "headless": False
}


def ensure_config():
    if not os.path.exists(CFG_PATH):
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        print(f"Created default {CFG_PATH}. Edit and set 'automation_allowed': true to enable.")


def load_config():
    ensure_config()
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ----------------------------
# URL loading
# ----------------------------
def load_urls_from_excel(path="PiratePunisher_WebsiteList.xlsx"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing Excel file: {path}")
    df = pd.read_excel(path)
    # try common column names
    col = None
    for c in df.columns:
        if str(c).strip().lower() in ("urls", "url", "links", "website"):
            col = c
            break
    if col is None:
        col = df.columns[0]
    urls = df[col].dropna().astype(str).str.strip().tolist()
    return [u for u in urls if u]


# ----------------------------
# Utilities & detection
# ----------------------------
def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@]+@[^@]+\.[^@]+$", email))



def setup_driver(headless=False, prefer_browser=None):
    """
    Try to set up a Selenium driver. Prefer Firefox, fallback to Chrome if needed.
    """
    browser = prefer_browser or os.environ.get("PIRATEPUNISHER_BROWSER", "firefox").lower()
    errors = []
    if browser in ("firefox", "any") and FirefoxOptions:
        geckodriver_path = shutil.which("geckodriver")
        if geckodriver_path:
            opts = FirefoxOptions()
            if headless:
                opts.headless = True
            try:
                opts.set_preference("dom.webdriver.enabled", False)
                opts.set_preference("useAutomationExtension", False)
            except Exception:
                pass
            opts.add_argument("--width=1200")
            opts.add_argument("--height=900")
            try:
                return webdriver.Firefox(options=opts)
            except Exception as e:
                errors.append(f"Firefox error: {e}")
        else:
            errors.append("geckodriver not found in PATH.")
    if browser in ("chrome", "any") and ChromeOptions:
        chromedriver_path = shutil.which("chromedriver")
        if chromedriver_path:
            opts = ChromeOptions()
            if headless:
                opts.add_argument("--headless=new")
            opts.add_argument("--window-size=1200,900")
            try:
                return webdriver.Chrome(options=opts)
            except Exception as e:
                errors.append(f"Chrome error: {e}")
        else:
            errors.append("chromedriver not found in PATH.")
    raise RuntimeError("No working browser/driver found.\n" + "\n".join(errors) +
        "\nInstall geckodriver (for Firefox) or chromedriver (for Chrome) and ensure it is in your PATH.")


def click_cookie_banners(driver, config):
    for xp in config.get("cookie_accept_xpaths", []):
        try:
            els = driver.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    if el.is_displayed():
                        el.click()
                        time.sleep(0.5)
                        return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def simulate_user_actions(driver):
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(0.8)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(0.8)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.0)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(0.5)
        return True
    except Exception:
        return False


def search_email_input_in_element(el):
    try:
        itype = (el.get_attribute("type") or "").lower()
        name = (el.get_attribute("name") or "").lower()
        pid = (el.get_attribute("id") or "").lower()
        placeholder = (el.get_attribute("placeholder") or "").lower()
        aria = (el.get_attribute("aria-label") or "").lower()
        combined = " ".join([itype, name, pid, placeholder, aria])
        if itype == "email":
            return True
        for kw in ("email", "newsletter", "subscribe", "signup", "join"):
            if kw in combined:
                return True
    except Exception:
        pass
    return False


def find_candidate_email_inputs(driver, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            candidates = [inp for inp in inputs if inp.is_displayed() and search_email_input_in_element(inp)]
            if candidates:
                return candidates
        except Exception:
            pass
        time.sleep(1)
    return []


def find_submit_button_near_input(driver, input_el):
    try:
        try:
            form = input_el.find_element(By.XPATH, "./ancestor::form[1]")
            if form:
                btns = form.find_elements(By.XPATH, ".//button|.//input[@type='submit']")
                for b in btns:
                    try:
                        if b.is_displayed():
                            return b
                    except Exception:
                        continue
        except Exception:
            pass

        btns = driver.find_elements(By.XPATH, "//button|//input[@type='submit']")
        for b in btns:
            try:
                if not b.is_displayed():
                    continue
                btext = ((b.get_attribute("value") or "") + " " + (b.text or "")).lower()
                if any(k in btext for k in ("subscribe", "sign", "join", "submit", "get")):
                    return b
            except Exception:
                continue
    except Exception:
        pass
    return None


def check_confirmation_present(driver, config, timeout=12):
    deadline = time.time() + timeout
    keys = [k.lower() for k in config.get("confirmation_keywords", [])]
    while time.time() < deadline:
        try:
            page_text = driver.page_source.lower()
            if any(k in page_text for k in keys):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


# ----------------------------
# Core attempt flow
# ----------------------------
def attempt_signup_on_site(driver, url, email, config):
    try:
        driver.get(url)
    except Exception as e:
        return False, f"nav_error: {e}"

    try:
        time.sleep(2)
        click_cookie_banners(driver, config)
        simulate_user_actions(driver)
    except Exception:
        pass

    # Strategy A: selectors from config
    for sel in config.get("popup_email_selectors", []):
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in els:
                if not e.is_displayed():
                    continue
                try:
                    e.clear()
                    e.send_keys(email)
                except Exception:
                    continue
                # try submit selectors
                for ssub in config.get("popup_submit_selectors", []):
                    try:
                        btns = driver.find_elements(By.CSS_SELECTOR, ssub)
                        for b in btns:
                            if b.is_displayed():
                                try:
                                    b.click()
                                    time.sleep(config.get("submit_wait", 5))
                                    if check_confirmation_present(driver, config, timeout=7):
                                        return True, "submitted_via_config_selectors"
                                except Exception:
                                    continue
                    except Exception:
                        continue
                try:
                    e.submit()
                    time.sleep(config.get("submit_wait", 5))
                    if check_confirmation_present(driver, config, timeout=7):
                        return True, "submitted_via_input_submit"
                except Exception:
                    pass
        except Exception:
            continue

    # Strategy B: find candidate inputs
    candidates = find_candidate_email_inputs(driver, timeout=config.get("find_timeout", 15))
    if not candidates:
        return False, "no_email_input_found"

    for inp in candidates:
        try:
            if not inp.is_displayed():
                continue
            try:
                inp.clear()
                inp.send_keys(email)
            except Exception:
                pass
            btn = find_submit_button_near_input(driver, inp)
            if btn:
                try:
                    btn.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                    except Exception:
                        pass
            else:
                try:
                    inp.submit()
                except Exception:
                    pass
            time.sleep(config.get("submit_wait", 5))
            if check_confirmation_present(driver, config, timeout=config.get("find_timeout", 12)):
                return True, "submitted_and_confirmed"
        except Exception as e:
            traceback.print_exc()
            continue

    return False, "submitted_but_no_confirmation"


# ----------------------------
# GUI / Main
# ----------------------------
class NewsletterSignupApp:
    def __init__(self, root):
        self.root = root
        root.title("Pirate Punisher")
        self.config = load_config()
        if not self.config.get("automation_allowed", False):
            messagebox.showwarning("Automation Disabled", "Edit config.json and set 'automation_allowed': true to enable.")
            root.destroy()
            return

        self.entries = {}
        for label in ("First Name", "Last Name", "Email", "Address", "Contact Number"):
            tk.Label(root, text=label).pack(anchor="w", padx=8)
            ent = tk.Entry(root, width=60)
            ent.pack(padx=8, pady=2)
            self.entries[label] = ent

        self.start_btn = tk.Button(root, text="Start", command=self.on_start)
        self.start_btn.pack(pady=8)

        self.progress = ttk.Progressbar(root, length=600, mode="determinate")
        self.progress.pack(pady=6, padx=8)

        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=4)

        self.success_count = 0
        self.failure_count = 0

    def on_start(self):
        first = self.entries["First Name"].get().strip()
        last = self.entries["Last Name"].get().strip()
        email = self.entries["Email"].get().strip()
        address = self.entries["Address"].get().strip()
        contact = self.entries["Contact Number"].get().strip()

        if not all([first, last, email, address, contact]):
            messagebox.showwarning("Input required", "Please fill every field.")
            return
        if not is_valid_email(email):
            messagebox.showwarning("Invalid email", "Please enter a valid email address.")
            return

        self.start_btn.config(state="disabled")
        self.root.update_idletasks()
        try:
            self.run_process({"first": first, "last": last, "email": email, "address": address, "contact": contact})
        finally:
            self.start_btn.config(state="normal")

    def run_process(self, data):
        try:
            urls = load_urls_from_excel()
        except Exception as e:
            messagebox.showerror("File error", str(e))
            return

        total = len(urls)
        self.progress['maximum'] = total
        self.progress['value'] = 0
        self.status_label.config(text=f"0 / {total}")
        self.root.update_idletasks()

        driver = setup_driver(headless=self.config.get("headless", False))

        success_log_path = "signup_successes.csv"
        failed_log_path = "failed_sites.txt"

        if not os.path.exists(success_log_path):
            with open(success_log_path, "w", newline="", encoding="utf-8") as csvf:
                writer = csv.writer(csvf)
                writer.writerow(["url", "email", "result", "note", "timestamp"]) 

        with open(failed_log_path, "w", encoding="utf-8") as failf:
            for idx, url in enumerate(urls):
                self.status_label.config(text=f"Processing {idx+1}/{total}: {url}")
                self.root.update_idletasks()
                attempt = 0
                success = False
                note = ""
                while attempt <= self.config.get("retries", 0) and not success:
                    attempt += 1
                    try:
                        ok, reason = attempt_signup_on_site(driver, url, data["email"], self.config)
                        if ok:
                            success = True
                            note = reason
                            with open(success_log_path, "a", newline="", encoding="utf-8") as csvf:
                                writer = csv.writer(csvf)
                                writer.writerow([url, data["email"], "success", reason, time.strftime("%Y-%m-%d %H:%M:%S")])
                            print(f"[OK] {url} -> {reason}")
                            break
                        else:
                            note = reason
                            print(f"[TRY-{attempt}] {url} not successful: {reason}")
                            if attempt <= self.config.get("retries", 0):
                                time.sleep(self.config.get("retry_delay", 6))
                    except Exception as e:
                        note = f"exception: {e}"
                        print("exception during attempt_signup:", e)
                        if attempt <= self.config.get("retries", 0):
                            time.sleep(self.config.get("retry_delay", 6))
                        else:
                            break

                if not success:
                    failf.write(url + "\n")
                    with open(success_log_path, "a", newline="", encoding="utf-8") as csvf:
                        writer = csv.writer(csvf)
                        writer.writerow([url, data["email"], "failed", note, time.strftime("%Y-%m-%d %H:%M:%S")])

                self.progress['value'] = idx + 1
                self.status_label.config(text=f"{idx+1} / {total}")
                self.root.update_idletasks()

        try:
            driver.quit()
        except Exception:
            pass

        messagebox.showinfo("Done", f"Completed. See {success_log_path} and {failed_log_path} for logs.")



def can_start_gui():
    # On Linux, check DISPLAY; on macOS/Windows, assume GUI is available
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY"))
    return True

def cli_main():
    print("PiratePunisher CLI mode\n")
    config = load_config()
    if not config.get("automation_allowed", False):
        print("Edit config.json and set 'automation_allowed': true to enable.")
        sys.exit(1)
    try:
        urls = load_urls_from_excel()
    except Exception as e:
        print(f"File error: {e}")
        sys.exit(1)
    email = input("Enter email to use for signups: ").strip()
    if not is_valid_email(email):
        print("Invalid email address.")
        sys.exit(1)
    driver = None
    try:
        driver = setup_driver(headless=True)
    except Exception as e:
        print(f"Could not start browser: {e}")
        sys.exit(1)
    success_log_path = "signup_successes.csv"
    failed_log_path = "failed_sites.txt"
    if not os.path.exists(success_log_path):
        with open(success_log_path, "w", newline="", encoding="utf-8") as csvf:
            writer = csv.writer(csvf)
            writer.writerow(["url", "email", "result", "note", "timestamp"])
    with open(failed_log_path, "w", encoding="utf-8") as failf:
        for idx, url in enumerate(urls):
            print(f"[{idx+1}/{len(urls)}] {url}")
            attempt = 0
            success = False
            note = ""
            while attempt <= config.get("retries", 0) and not success:
                attempt += 1
                try:
                    ok, reason = attempt_signup_on_site(driver, url, email, config)
                    if ok:
                        success = True
                        note = reason
                        with open(success_log_path, "a", newline="", encoding="utf-8") as csvf:
                            writer = csv.writer(csvf)
                            writer.writerow([url, email, "success", reason, time.strftime("%Y-%m-%d %H:%M:%S")])
                        print(f"[OK] {url} -> {reason}")
                        break
                    else:
                        note = reason
                        print(f"[TRY-{attempt}] {url} not successful: {reason}")
                        if attempt <= config.get("retries", 0):
                            time.sleep(config.get("retry_delay", 6))
                except Exception as e:
                    note = f"exception: {e}"
                    print("exception during attempt_signup:", e)
                    if attempt <= config.get("retries", 0):
                        time.sleep(config.get("retry_delay", 6))
                    else:
                        break
            if not success:
                failf.write(url + "\n")
                with open(success_log_path, "a", newline="", encoding="utf-8") as csvf:
                    writer = csv.writer(csvf)
                    writer.writerow([url, email, "failed", note, time.strftime("%Y-%m-%d %H:%M:%S")])
    try:
        driver.quit()
    except Exception:
        pass
    print(f"\nCompleted. See {success_log_path} and {failed_log_path} for logs.")

if __name__ == "__main__":
    # If GUI is available, use it; else fallback to CLI
    if can_start_gui():
        try:
            root = tk.Tk()
            app = NewsletterSignupApp(root)
            root.mainloop()
        except Exception as e:
            print(f"GUI error: {e}\nFalling back to CLI mode.")
            cli_main()
    else:
        cli_main()
