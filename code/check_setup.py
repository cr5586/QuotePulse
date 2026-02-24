import sys
import shutil
import subprocess

def check_python():
    print(f"[*] Checking Python version: {sys.version.split()[0]} - OK")

def check_chrome():
    chrome_names = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser']
    found = False
    for name in chrome_names:
        path = shutil.which(name)
        if path:
            print(f"[*] Found Chrome/Chromium at: {path}")
            found = True
            break
    if not found:
        print("[!] WARNING: Chrome or Chromium not found in PATH.")
        print("    If you are on Fedora, try: sudo dnf install google-chrome-stable")
    return found

def check_dependencies():
    try:
        import selenium
        print(f"[*] Selenium version: {selenium.__version__} - OK")
    except ImportError:
        print("[!] Selenium is NOT installed. Run: pip install -r requirements.txt")

    try:
        import fpdf
        print("[*] fpdf2 - OK")
    except ImportError:
        print("[!] fpdf2 is NOT installed. Run: pip install -r requirements.txt")

    try:
        import click
        print("[*] click - OK")
    except ImportError:
        print("[!] click is NOT installed. Run: pip install -r requirements.txt")

if __name__ == "__main__":
    print("--- QuotePulse Environment Check ---")
    check_python()
    check_chrome()
    check_dependencies()
    print("------------------------------------")
