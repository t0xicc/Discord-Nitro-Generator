import random
import string
import requests
import threading
import time
import os
from tkinter import *
from tkinter import ttk, messagebox
from plyer import notification  # pip install plyer
from tkinter.scrolledtext import ScrolledText



# ---------- DILLER ----------
LANGS = {
    "en": {
        "start": "Start",
        "stop": "Stop",
        "cancel": "Cancel",
        "proxy": "Use Proxy (Optional) (http://ip:port)",
        "delay": "Delay between tries (sec)",
        "status": "Status",
        "valid_codes": "Valid Codes",
        "tested_codes": "Tested Codes",
        "found_valid": "Valid code found!",
        "language": "Language",
        "webhook": "Discord Webhook URL",
        "dark_mode": "Dark Mode",
        "enter_webhook": "Please enter your Discord webhook URL!",
        "invalid_proxy": "Invalid proxy format! Example: http://127.0.0.1:8080",
        "no_code_found": "No valid code found yet.",
        "already_running": "Checker is already running.",
        "stopped": "Checker stopped.",
        "error": "Error",
        "success": "Success",
    },
    "tr": {
        "start": "Başlat",
        "stop": "Durdur",
        "cancel": "İptal",
        "proxy": "Proxy Kullan (İsteğe Bağlı) (http://ip:port)",
        "delay": "Denemeler Arası Gecikme (sn)",
        "status": "Durum",
        "valid_codes": "Geçerli Kodlar",
        "tested_codes": "Denenen Kodlar",
        "found_valid": "Geçerli kod bulundu!",
        "language": "Dil",
        "webhook": "Discord Webhook URL'si",
        "dark_mode": "Karanlık Mod",
        "enter_webhook": "Lütfen Discord webhook URL'si girin!",
        "invalid_proxy": "Geçersiz proxy formatı! Örnek: http://127.0.0.1:8080",
        "no_code_found": "Henüz geçerli kod bulunamadı.",
        "already_running": "Checker zaten çalışıyor.",
        "stopped": "Checker durduruldu.",
        "error": "Hata",
        "success": "Başarılı",
    }
}

# ---------- GLOBALLAR ----------
CURRENT_LANG = "en"
running = False
lock = threading.Lock()
tested_codes = 0
valid_codes = 0
proxy = None

# ---------- FONKSIYONLAR ----------

def _(key):
    """Dil desteği için çeviri fonksiyonu"""
    return LANGS[CURRENT_LANG].get(key, key)

def generate_code(length=18):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def send_webhook(webhook_url, code):
    data = {
        "content": f"Valid Nitro Code found: https://discord.gift/{code}"
    }
    try:
        response = requests.post(webhook_url, json=data)
        return response.status_code == 204 or response.status_code == 200
    except Exception as e:
        return False

def check_code(code, webhook_url):
    global valid_codes
    url = f"https://discordapp.com/api/v9/entitlements/gift-codes/{code}?with_application=false&with_subscription_plan=true"
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = requests.get(url, proxies=proxies)
        if response.status_code == 200:
            valid_codes += 1
            save_valid_code(code)
            send_webhook(webhook_url, code)
            show_notification(_("found_valid"), f"https://discord.gift/{code}")
            return True
    except Exception as e:
        pass
    return False

def save_valid_code(code):
    with open("valid_codes.txt", "a", encoding="utf-8") as f:
        f.write(f"{code}\n")

def show_notification(title, message):
    try:
        notification.notify(title=title, message=message, timeout=5)
    except:
        pass

def append_code_to_text(code, is_valid):
    text_codes.config(state=NORMAL)
    status = "✅ Valid" if is_valid else "❌ Invalid"
    text_codes.insert(END, f"https://discord.gift/{code} {status}\n")
    text_codes.see(END)  # Scroll to bottom
    text_codes.config(state=DISABLED)


def worker(webhook_url, delay_sec):
    global running, tested_codes
    while running:
        code = generate_code()
        is_valid = check_code(code, webhook_url)
        append_code_to_text(code, is_valid)
        with lock:
            tested_codes += 1
        update_stats()
        if is_valid:
            running = False
            update_stats()
            update_status(_("found_valid"))
            toggle_buttons(start_enabled=True, stop_enabled=False)
            break
        time.sleep(delay_sec)

def update_stats():
    tested_var.set(str(tested_codes))
    valid_var.set(str(valid_codes))

def update_status(text):
    status_var.set(text)

def toggle_buttons(start_enabled, stop_enabled):
    btn_start.config(state=NORMAL if start_enabled else DISABLED)
    btn_stop.config(state=NORMAL if stop_enabled else DISABLED)

def start_check():
    global running, proxy, tested_codes, valid_codes
    if running:
        messagebox.showwarning(_("error"), _("already_running"))
        return

    webhook_url = entry_webhook.get().strip()
    if not webhook_url:
        messagebox.showerror(_("error"), _("enter_webhook"))
        return

    proxy_text = entry_proxy.get().strip()
    if proxy_text:
        if not (proxy_text.startswith("http://") or proxy_text.startswith("https://")):
            messagebox.showerror(_("error"), _("invalid_proxy"))
            return
        proxy = proxy_text
    else:
        proxy = None

    try:
        delay_sec = float(entry_delay.get().strip())
        if delay_sec < 0:
            raise ValueError
    except:
        delay_sec = 1.0  # Default

    running = True
    tested_codes = 0
    valid_codes = 0
    update_stats()
    update_status(_("status") + ": Running...")
    toggle_buttons(start_enabled=False, stop_enabled=True)

    thread = threading.Thread(target=worker, args=(webhook_url, delay_sec), daemon=True)
    thread.start()

def stop_check():
    global running
    running = False
    update_status(_("stopped"))
    toggle_buttons(start_enabled=True, stop_enabled=False)

def change_language(event=None):
    global CURRENT_LANG
    sel = combo_lang.get()
    if sel == "English":
        CURRENT_LANG = "en"
    else:
        CURRENT_LANG = "tr"
    refresh_texts()

def refresh_texts():
    # Update all text on GUI
    lbl_webhook.config(text=_("webhook"))
    lbl_proxy.config(text=_("proxy"))
    lbl_delay.config(text=_("delay"))
    lbl_status.config(text=_("status") + ":")
    lbl_tested.config(text=_("tested_codes") + ":")
    lbl_valid.config(text=_("valid_codes") + ":")
    chk_dark_mode.config(text=_("dark_mode"))
    btn_start.config(text=_("start"))
    btn_stop.config(text=_("stop"))
    combo_lang_label.config(text=_("language") + ":")

def toggle_dark_mode():
    if dark_mode_var.get():
        style.theme_use("clam")
        style.configure(".", background="#2f3136", foreground="white", fieldbackground="#40444b")
        style.map("TButton", background=[('active', '#7289da')])
        root.configure(bg="#2f3136")
        for widget in root.winfo_children():
            try:
                widget.configure(background="#2f3136", foreground="white")
            except:
                pass
    else:
        style.theme_use("default")
        root.configure(bg=default_bg)
        for widget in root.winfo_children():
            try:
                widget.configure(background=default_bg, foreground="black")
            except:
                pass

# ---------- GUI OLUŞTURMA ----------

root = Tk()
root.title("Discord Nitro Gift Checker")

default_bg = root.cget("bg")

style = ttk.Style(root)
style.theme_use("default")

# Dil seçimi
combo_lang_label = ttk.Label(root, text=_("language") + ":")
combo_lang_label.grid(row=0, column=0, sticky=W, padx=5, pady=5)
combo_lang = ttk.Combobox(root, values=["English", "Türkçe"], state="readonly", width=10)
combo_lang.current(0)
combo_lang.grid(row=0, column=1, sticky=W)
combo_lang.bind("<<ComboboxSelected>>", change_language)

# Discord webhook url
lbl_webhook = ttk.Label(root, text=_("webhook"))
lbl_webhook.grid(row=1, column=0, sticky=W, padx=5, pady=5)
entry_webhook = ttk.Entry(root, width=50)
entry_webhook.grid(row=1, column=1, columnspan=2, sticky=W, padx=5, pady=5)

# Proxy
lbl_proxy = ttk.Label(root, text=_("proxy"))
lbl_proxy.grid(row=2, column=0, sticky=W, padx=5, pady=5)
entry_proxy = ttk.Entry(root, width=50)
entry_proxy.grid(row=2, column=1, columnspan=2, sticky=W, padx=5, pady=5)

# Delay
lbl_delay = ttk.Label(root, text=_("delay"))
lbl_delay.grid(row=3, column=0, sticky=W, padx=5, pady=5)
entry_delay = ttk.Entry(root, width=10)
entry_delay.insert(0, "1.0")
entry_delay.grid(row=3, column=1, sticky=W, padx=5, pady=5)

# Dark mode
dark_mode_var = BooleanVar()
chk_dark_mode = ttk.Checkbutton(root, text=_("dark_mode"), variable=dark_mode_var, command=lambda: toggle_dark_mode())
chk_dark_mode.grid(row=0, column=2, sticky=E, padx=5, pady=5)

# Status
status_var = StringVar(value=_("no_code_found"))
lbl_status = ttk.Label(root, text=_("status") + ":")
lbl_status.grid(row=4, column=0, sticky=W, padx=5, pady=5)
status_label = ttk.Label(root, textvariable=status_var)
status_label.grid(row=4, column=1, sticky=W, padx=5, pady=5)

# Tested & valid counters
tested_var = StringVar(value="0")
valid_var = StringVar(value="0")

lbl_tested = ttk.Label(root, text=_("tested_codes") + ":")
lbl_tested.grid(row=5, column=0, sticky=W, padx=5, pady=5)
lbl_tested_val = ttk.Label(root, textvariable=tested_var)
lbl_tested_val.grid(row=5, column=1, sticky=W, padx=5, pady=5)

lbl_valid = ttk.Label(root, text=_("valid_codes") + ":")
lbl_valid.grid(row=6, column=0, sticky=W, padx=5, pady=5)
lbl_valid_val = ttk.Label(root, textvariable=valid_var)
lbl_valid_val.grid(row=6, column=1, sticky=W, padx=5, pady=5)

# Scrollable text area for showing tried codes
lbl_codes = ttk.Label(root, text="Tested Nitro Codes:")
lbl_codes.grid(row=8, column=0, sticky=W, padx=5)
text_codes = ScrolledText(root, height=8, width=60, state=DISABLED)
text_codes.grid(row=9, column=0, columnspan=3, padx=10, pady=5)

# Buttons
btn_start = ttk.Button(root, text=_("start"), command=start_check)
btn_start.grid(row=7, column=0, padx=5, pady=10)
btn_stop = ttk.Button(root, text=_("stop"), command=stop_check, state=DISABLED)
btn_stop.grid(row=7, column=1, padx=5, pady=10)

# Grid ayarları (geliştirmek için)
for i in range(8):
    root.grid_rowconfigure(i, weight=1)
for j in range(3):
    root.grid_columnconfigure(j, weight=1)

root.geometry("800x600")

root.mainloop()
