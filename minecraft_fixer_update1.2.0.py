#!/usr/bin/env python3
"""
world_fixer_with_admin_debug_updater.py
Includes Admin tab (/clear), Dev Debug + Updater with safe backup system
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import nbtlib
import random
import shutil
import hashlib
import datetime
from pathlib import Path
import subprocess

# ------------------ Configuration / Version ------------------ #
BUILD_VERSION = "1.2.0"  # (main.update.bugfix)

SALT = "r4nd0mS@1t_v2025"
DEV_PASSWORD_HASH = "79014e3841bb695deaf9ce45e26d178ce686b681bb05c61332f99f7072b0c37b"
DEV_CMD_PREFIX = "Pass "

# ------------------ Globals ------------------ #
start_time = time.time()
OUTPUT_DIR = "output"
ERROR_DIR = "errors"
BACKUP_DIR = os.path.join(OUTPUT_DIR, "backups")
BUILD_HISTORY_FILE = "build_history.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

MAIN_SCRIPT = "world_fixer_with_admin_debug_updater.py"  # self filename

# ------------------ Helper: resource path for PyInstaller ------------------ #
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ------------------ UI Setup ------------------ #
root = tk.Tk()
root.title(f"Minecraft World Fixer v{BUILD_VERSION}")
root.geometry("800x560")

# Try to set icon safely
icon_file = resource_path("icon.ico")
if os.path.exists(icon_file):
    try:
        root.iconbitmap(icon_file)
    except Exception:
        print("⚠ Warning: iconbitmap failed.")
else:
    print("⚠ Icon not found, using default window icon.")

# Startup warning
messagebox.showwarning(
    "WARNING",
    "⚠ WARNING:\n\nThis tool is for Minecraft 1.5.2 to convert Eaglercraft worlds into Vanilla Minecraft.\n"
    "It does NOT work the opposite way."
)

# Notebook (tabs)
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=8, pady=8)

# Logging area
log_text = tk.Text(root, height=8, state="disabled", bg="#111213", fg="#e6e6e6")
log_text.pack(fill="x", side="bottom", padx=6, pady=(0,6))

def log_message(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    log_text.config(state="normal")
    log_text.insert("end", line + "\n")
    log_text.see("end")
    log_text.config(state="disabled")

# ------------------ Timer ------------------ #
def update_timer():
    elapsed = int(time.time() - start_time)
    if elapsed < 60:
        timer_label.config(text=f"⏱ Runtime: {elapsed} secs")
    else:
        mins = elapsed // 60
        timer_label.config(text=f"⏱ Runtime: {mins} min{'s' if mins > 1 else ''}")
    root.after(1000, update_timer)

timer_label = ttk.Label(root, text="⏱ Runtime: 0 secs")
timer_label.pack(side="bottom", pady=(0,6))

# ------------------ Tabs ------------------ #
# --- Cords tab ---
frame_cords = ttk.Frame(notebook)
notebook.add(frame_cords, text="Cords")

ttk.Label(frame_cords, text="Player Position (X Y Z)").pack(pady=6)
cords_frame = ttk.Frame(frame_cords)
cords_frame.pack(pady=4, padx=8)

ttk.Label(cords_frame, text="X =").grid(row=0, column=0, padx=(0,4))
x_entry = ttk.Entry(cords_frame, width=12)
x_entry.grid(row=0, column=1, padx=(0,12))

ttk.Label(cords_frame, text="Y =").grid(row=0, column=2, padx=(0,4))
y_entry = ttk.Entry(cords_frame, width=12)
y_entry.grid(row=0, column=3, padx=(0,12))

ttk.Label(cords_frame, text="Z =").grid(row=0, column=4, padx=(0,4))
z_entry = ttk.Entry(cords_frame, width=12)
z_entry.grid(row=0, column=5, padx=(0,12))

world_dir_var = tk.StringVar(value="")

def fix_world():
    path = world_dir_var.get()
    if not os.path.isdir(path):
        messagebox.showerror("Error", "No valid world folder selected!")
        return

    level_path = os.path.join(path, "level.dat")
    if not os.path.exists(level_path):
        messagebox.showerror("Error", "Missing level.dat in world folder!")
        return

    try:
        x, y, z = float(x_entry.get()), float(y_entry.get()), float(z_entry.get())
    except Exception:
        messagebox.showerror("Error", "Invalid coordinates entered.")
        return

    if y < 60:
        y = 60.0
        y_entry.delete(0, tk.END)
        y_entry.insert(0, "60")
        messagebox.showwarning("Adjusted", "Y adjusted to 60 to avoid suffocation.")

    try:
        level = nbtlib.load(level_path)
        # Backup
        bak_dir = os.path.join(BACKUP_DIR, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(bak_dir, exist_ok=True)
        bak_file = os.path.join(bak_dir, "level.dat.bak")
        shutil.copy2(level_path, bak_file)
        log_message(f"💾 Backup saved: {bak_file}")

        # Update player + spawn
        if "Player" not in level["Data"]:
            level["Data"]["Player"] = nbtlib.tag.Compound()
            level["Data"]["Player"]["Pos"] = nbtlib.tag.List([nbtlib.tag.Double(0), nbtlib.tag.Double(0), nbtlib.tag.Double(0)])
        player = level["Data"]["Player"]
        player["Pos"][0] = nbtlib.tag.Double(x)
        player["Pos"][1] = nbtlib.tag.Double(y)
        player["Pos"][2] = nbtlib.tag.Double(z)
        level["Data"]["SpawnX"] = nbtlib.tag.Int(int(x))
        level["Data"]["SpawnY"] = nbtlib.tag.Int(int(y))
        level["Data"]["SpawnZ"] = nbtlib.tag.Int(int(z))

        level.save(level_path)
        messagebox.showinfo("Success", f"World fixed!\nBackup: {bak_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Fix failed: {e}")

ttk.Button(frame_cords, text="Fix World", command=fix_world, width=20).pack(pady=12)

# --- Advanced tab ---
frame_advanced = ttk.Frame(notebook)
notebook.add(frame_advanced, text="Advanced")

ttk.Label(frame_advanced, text="World Folder").pack(pady=(6,2))
ttk.Entry(frame_advanced, textvariable=world_dir_var, width=70).pack(padx=8)

def browse_world():
    folder = filedialog.askdirectory(title="Select world folder")
    if folder:
        world_dir_var.set(folder)
        log_message(f"📂 Selected world folder: {folder}")

ttk.Button(frame_advanced, text="Browse...", command=browse_world).pack(pady=6)

# --- Admin tab ---
frame_admin = ttk.Frame(notebook)
notebook.add(frame_admin, text="Admin")

ttk.Label(frame_admin, text="Admin Command Console").pack(pady=6)
admin_entry = ttk.Entry(frame_admin, width=60)
admin_entry.pack(pady=(0,4), padx=8)

admin_output = tk.Text(frame_admin, height=12, wrap="word", bg="#151515", fg="#e6e6e6")
admin_output.pack(fill="both", expand=True, padx=8, pady=8)

def run_admin_command():
    cmd = admin_entry.get().strip()
    admin_entry.delete(0, tk.END)

    if cmd == "/help":
        msg = "Available admin commands:\n/help\n/reset\n/locate\n/clear"
    elif cmd == "/reset":
        if world_dir_var.get() and os.path.isdir(world_dir_var.get()):
            backups = sorted(Path(BACKUP_DIR).glob("*/level.dat.bak"))
            if backups:
                latest = backups[-1]
                shutil.copy2(latest, os.path.join(world_dir_var.get(), "level.dat"))
                msg = f"♻ Restored level.dat from backup: {latest}"
            else:
                msg = "⚠ No backups found."
        else:
            msg = "⚠ No world selected."
    elif cmd == "/locate":
        msg = f"📂 Current world folder: {world_dir_var.get()}" if world_dir_var.get() else "⚠ No world selected."
    elif cmd == "/clear":
        admin_output.delete("1.0", "end")
        msg = "🧹 Admin log cleared."
    else:
        msg = f"❌ Unknown command: {cmd} (try /help)"

    admin_output.insert("end", msg + "\n")
    admin_output.see("end")

ttk.Button(frame_admin, text="Run", command=run_admin_command).pack(pady=6)

# --- Dev tab (hidden until unlocked) ---
frame_dev = ttk.Frame(notebook)
ttk.Label(frame_dev, text=f"🛠 Dev Tools - Build {BUILD_VERSION}").pack(pady=8)
output_box = tk.Text(frame_dev, height=12, wrap="word", bg="#151515", fg="#e6e6e6")
output_box.pack(fill="both", expand=True, padx=8, pady=8)

def debug_system():
    results = []
    # Check modules
    try:
        import nbtlib
        results.append("✔ nbtlib module OK")
    except Exception as e:
        results.append(f"❌ nbtlib missing: {e}")
    try:
        import tkinter
        results.append("✔ tkinter module OK")
    except Exception as e:
        results.append(f"❌ tkinter missing: {e}")
    # Check folders
    for d in [OUTPUT_DIR, ERROR_DIR, BACKUP_DIR]:
        if os.path.exists(d):
            results.append(f"✔ Folder exists: {d}")
        else:
            results.append(f"❌ Missing folder: {d}")
    # Check world folder + level.dat
    if world_dir_var.get():
        level_path = os.path.join(world_dir_var.get(), "level.dat")
        if os.path.exists(level_path):
            results.append("✔ level.dat found in selected world")
        else:
            results.append("⚠ level.dat missing in selected world")
    else:
        results.append("ℹ No world folder selected")
    output_box.insert("end", "\n".join(results) + "\n")
    output_box.see("end")

def run_updater():
    win = tk.Toplevel(root)
    win.title("Updater Test Window")
    win.geometry("600x400")

    ttk.Label(win, text="Select new .py to test").pack(pady=4)
    test_file_var = tk.StringVar()
    ttk.Entry(win, textvariable=test_file_var, width=50).pack(pady=4)
    def browse_py():
        f = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if f:
            test_file_var.set(f)
    ttk.Button(win, text="Browse", command=browse_py).pack(pady=4)

    log_area = tk.Text(win, height=15, wrap="word", bg="#151515", fg="#e6e6e6")
    log_area.pack(fill="both", expand=True, padx=8, pady=8)

    process = {"p": None}

    def start_test():
        if not test_file_var.get():
            messagebox.showerror("Error", "No .py file selected")
            return
        cmd = [sys.executable, test_file_var.get()]
        process["p"] = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        def reader():
            for line in process["p"].stdout:
                log_area.insert("end", line)
                log_area.see("end")
        threading.Thread(target=reader, daemon=True).start()
    ttk.Button(win, text="Start Test", command=start_test).pack(pady=4)

    def do_update():
        if not test_file_var.get():
            return
        # Kill process if running
        if process["p"] and process["p"].poll() is None:
            process["p"].terminate()
        # Backup current file
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_name = f"{MAIN_SCRIPT}.bak_{ts}"
        shutil.copy2(MAIN_SCRIPT, os.path.join(BACKUP_DIR, bak_name))
        shutil.copy2(test_file_var.get(), MAIN_SCRIPT)
        messagebox.showinfo("Updated", f"Main script updated. Restarting...")
        os.execv(sys.executable, ["python"] + [MAIN_SCRIPT])
    def do_cancel():
        if process["p"] and process["p"].poll() is None:
            process["p"].terminate()
        win.destroy()
    ttk.Button(win, text="✅ Update", command=do_update).pack(side="left", padx=20, pady=6)
    ttk.Button(win, text="❌ Don't Update", command=do_cancel).pack(side="right", padx=20, pady=6)

ttk.Button(frame_dev, text="Debug System", command=debug_system).pack(pady=6)
ttk.Button(frame_dev, text="Updater", command=run_updater).pack(pady=6)

# Dev unlock listener
def check_dev_password(plain):
    h = hashlib.sha256((SALT + plain).encode()).hexdigest()
    return h == DEV_PASSWORD_HASH

def console_listener():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                time.sleep(0.1)
                continue
            if line.startswith(DEV_CMD_PREFIX):
                provided = line.strip().split(" ", 1)[1]
                if check_dev_password(provided):
                    if "Extra" not in [notebook.tab(i,"text") for i in range(notebook.index("end"))]:
                        notebook.add(frame_dev, text="Extra")
                        log_message("✔ Extra tools unlocked")
        except Exception:
            time.sleep(0.5)

threading.Thread(target=console_listener, daemon=True).start()

# ------------------ Startup ------------------ #
log_message(f"🚀 Minecraft World Fixer - Build {BUILD_VERSION} started")
update_timer()
root.mainloop()
