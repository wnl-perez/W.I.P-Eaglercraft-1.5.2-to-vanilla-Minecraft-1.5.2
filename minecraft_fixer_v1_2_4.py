#!/usr/bin/env python3
"""
minecraft_fixer_v1_2_1.py - Consolidated build (practical)
Features: GUI, load zip/folder, stats editor, apply stats, apply fix, backups (keep last 10), settings.
Dependencies (optional): nbtlib, requests
"""

import os, sys, json, time, shutil, zipfile, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import nbtlib
except Exception:
    nbtlib = None

BUILD_VERSION = "1.2.1"
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "mc_saves": os.path.join(os.getenv("APPDATA") or ".", ".minecraft", "saves"),
    "backup_mode": "default", "backup_custom_dir": "", "ask_overwrite": True, "last_world_path":"", "last_coords":[0,64,0]
}
MAX_BACKUPS = 10

def load_config():
    if os.path.exists(CONFIG_FILE):
        try: return json.load(open(CONFIG_FILE,"r",encoding="utf-8"))
        except: pass
    cfg = DEFAULT_CONFIG.copy(); save_config(cfg); return cfg
def save_config(c): json.dump(c, open(CONFIG_FILE,"w",encoding="utf-8"), indent=2)

config = load_config()

def ts(): return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
def ensure(d): os.makedirs(d, exist_ok=True)

def log(s):
    line = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {s}"
    print(line)
    try:
        log_widget.config(state="normal")
        log_widget.insert("end", line + "\n")
        log_widget.see("end")
        log_widget.config(state="disabled")
    except:
        pass
    with open("build_history.txt", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def backup_level(level_path, world_name):
    if not os.path.exists(level_path): return None
    mode = config.get("backup_mode","default")
    if mode=="default": root = os.path.join(os.getcwd(),"backups")
    elif mode=="world": root = os.path.join(os.path.dirname(level_path),"backups")
    elif mode=="custom" and config.get("backup_custom_dir"): root = config["backup_custom_dir"]
    else: root = os.path.join(os.getcwd(),"backups")
    ensure(root)
    name = f"{world_name}_level_{ts()}.dat"; dest = os.path.join(root,name)
    try: shutil.copy2(level_path,dest)
    except Exception as e: log(f"Backup failed: {e}"); return None
    files = sorted(Path(root).glob(f"{world_name}_level_*.dat"), key=lambda p:p.stat().st_mtime)
    while len(files) > MAX_BACKUPS:
        try: files[0].unlink(); files.pop(0)
        except: break
    return dest

# GUI
root = tk.Tk(); root.title(f"Minecraft Fixer v{BUILD_VERSION}"); root.geometry("920x700")
nb = ttk.Notebook(root); nb.pack(fill="both", expand=True, padx=8, pady=8)

# Log widget
log_widget = tk.Text(root, height=8, state="disabled", bg="#111", fg="#eee"); log_widget.pack(fill="x", side="bottom", padx=6, pady=(0,6))

# State
working_world = None; loaded_from_zip = False

# General tab
tab_gen = ttk.Frame(nb); nb.add(tab_gen, text="General")
top = ttk.Frame(tab_gen); top.pack(fill="x", padx=8, pady=6)
ttk.Label(top, text="Load world (.zip or folder):").pack(side="left")
def on_browse_zip():
    p = filedialog.askopenfilename(filetypes=[("ZIP","*.zip")])
    if p: load_world_from_zip(p)
ttk.Button(top, text="Browse ZIP...", command=on_browse_zip).pack(side="left", padx=6)
def on_browse_folder():
    p = filedialog.askdirectory()
    if p: load_world_from_folder(p)
ttk.Button(top, text="Browse Folder...", command=on_browse_folder).pack(side="left", padx=6)
loaded_label = ttk.Label(top, text="(none)"); loaded_label.pack(side="left", padx=10)

opts = ttk.LabelFrame(tab_gen, text="Options"); opts.pack(fill="x", padx=8, pady=8)
clear_inv_var = tk.BooleanVar(); clear_inv_chk = ttk.Checkbutton(opts, text="Clear Inventory", variable=clear_inv_var); clear_inv_chk.grid(row=0,column=0,padx=6,pady=4,sticky="w")
chest_clear_var = tk.BooleanVar(); chest_clear_chk = ttk.Checkbutton(opts, text="Clear 9x9 chest area (plan)", variable=chest_clear_var); chest_clear_chk.grid(row=1,column=0,padx=6,sticky="w")
ttk.Label(opts, text="Search radius:").grid(row=1,column=1); chest_radius = ttk.Entry(opts,width=6); chest_radius.grid(row=1,column=2); chest_radius.insert(0,"30")
ttk.Label(opts, text="Seed override:").grid(row=2,column=0,sticky="w"); seed_entry = ttk.Entry(opts,width=30); seed_entry.grid(row=2,column=1,columnspan=2,padx=6)
export_var = tk.BooleanVar(value=True); export_chk = ttk.Checkbutton(opts, text="Export to Minecraft saves after fix (if from zip)", variable=export_var); export_chk.grid(row=3,column=0,sticky="w",padx=6)
apply_fix_btn = ttk.Button(tab_gen, text="Apply Fix to Chosen World", command=lambda: apply_fix()); apply_fix_btn.pack(pady=8)

# Player Stats tab
tab_stats = ttk.Frame(nb); nb.add(tab_stats, text="Player Stats")
ttk.Label(tab_stats, text="Adjust player stats and click Apply Stats (creates backup)").pack(padx=8,pady=6)
sf = ttk.Frame(tab_stats); sf.pack(fill="x", padx=8, pady=6)
ttk.Label(sf, text="Health (0-20)").grid(row=0,column=0,sticky="w"); health_scale = tk.Scale(sf, from_=0,to=20, orient="horizontal", length=360); health_scale.grid(row=0,column=1)
ttk.Label(sf, text="Hunger (0-20)").grid(row=1,column=0,sticky="w"); hunger_scale = tk.Scale(sf, from_=0,to=20, orient="horizontal", length=360); hunger_scale.grid(row=1,column=1)
ttk.Label(sf, text="XP Level (0-100)").grid(row=2,column=0,sticky="w"); xp_level_scale = tk.Scale(sf, from_=0,to=100, orient="horizontal", length=360); xp_level_scale.grid(row=2,column=1)
ttk.Label(sf, text="XP Progress % (0-100)").grid(row=3,column=0,sticky="w"); xp_prog_scale = tk.Scale(sf, from_=0,to=100, orient="horizontal", length=360); xp_prog_scale.grid(row=3,column=1)
manual_var = tk.BooleanVar(value=False)
def toggle_manual():
    manual = manual_var.get()
    for s in (health_scale,hunger_scale,xp_level_scale,xp_prog_scale):
        s.config(state="disabled" if manual else "normal")
    for e in (health_entry,hunger_entry,xp_level_entry,xp_prog_entry):
        e.config(state="normal" if manual else "disabled")
manual_chk = ttk.Checkbutton(tab_stats, text="Manual Input Mode", variable=manual_var, command=toggle_manual); manual_chk.pack(anchor="w", padx=8)
ef = ttk.Frame(tab_stats); ef.pack(fill="x", padx=8, pady=6)
ttk.Label(ef,text="Health:").grid(row=0,column=0); health_entry = ttk.Entry(ef,width=8); health_entry.grid(row=0,column=1,padx=6)
ttk.Label(ef,text="Hunger:").grid(row=0,column=2); hunger_entry = ttk.Entry(ef,width=8); hunger_entry.grid(row=0,column=3,padx=6)
ttk.Label(ef,text="XP Level:").grid(row=1,column=0); xp_level_entry = ttk.Entry(ef,width=8); xp_level_entry.grid(row=1,column=1,padx=6)
ttk.Label(ef,text="XP Progress %:").grid(row=1,column=2); xp_prog_entry = ttk.Entry(ef,width=8); xp_prog_entry.grid(row=1,column=3,padx=6)
apply_stats_btn = ttk.Button(tab_stats, text="Apply Stats to World (creates backup)", command=lambda: apply_stats()); apply_stats_btn.pack(pady=8)

# Advanced tab
tab_adv = ttk.Frame(nb); nb.add(tab_adv, text="Advanced")
ttk.Label(tab_adv, text="Custom blocks (comma separated):").pack(anchor="w", padx=8, pady=(8,0))
custom_blocks_entry = ttk.Entry(tab_adv, width=90); custom_blocks_entry.pack(padx=8,pady=6)
advanced_blocks_var = tk.BooleanVar(); advanced_blocks_chk = ttk.Checkbutton(tab_adv, text="Advanced block parsing", variable=advanced_blocks_var); advanced_blocks_chk.pack(anchor="w", padx=8)
clear_plan_btn = ttk.Button(tab_adv, text="Generate Clear Plan", command=lambda: generate_clear_plan()); clear_plan_btn.pack(pady=8)

# Settings tab
tab_set = ttk.Frame(nb); nb.add(tab_set, text="Settings")
ttk.Label(tab_set, text="Minecraft saves folder:").pack(anchor="w", padx=8, pady=(8,0))
mc_var = tk.StringVar(value=config.get("mc_saves","")); mc_entry = ttk.Entry(tab_set, textvariable=mc_var, width=80); mc_entry.pack(padx=8,pady=4)
def choose_mc():
    d = filedialog.askdirectory()
    if d:
        mc_var.set(d)
        config["mc_saves"] = d
        save_config(config)

ttk.Button(tab_set, text="Browse...", command=lambda: (lambda d=filedialog.askdirectory(): mc_var.set(d) or (config.update({'mc_saves':d}) or save_config(config)) if d else None)()).pack(padx=8,pady=4)
ttk.Label(tab_set, text="Backup location:").pack(anchor="w", padx=8)
backup_mode_var = tk.StringVar(value=config.get("backup_mode","default"))
def set_backup_mode(m): backup_mode_var.set(m); config["backup_mode"]=m; save_config(config)
ttk.Radiobutton(tab_set, text="Default (app folder /backups)", variable=backup_mode_var, value="default", command=lambda:set_backup_mode("default")).pack(anchor="w", padx=16)
ttk.Radiobutton(tab_set, text="Inside world folder", variable=backup_mode_var, value="world", command=lambda:set_backup_mode("world")).pack(anchor="w", padx=16)
ttk.Radiobutton(tab_set, text="Custom folder", variable=backup_mode_var, value="custom", command=lambda:set_backup_mode("custom")).pack(anchor="w", padx=16)
custom_backup_var = tk.StringVar(value=config.get("backup_custom_dir","")); custom_backup_entry = ttk.Entry(tab_set, textvariable=custom_backup_var, width=80); custom_backup_entry.pack(padx=8,pady=4)
ttk.Button(tab_set, text="Choose custom backup folder...", command=lambda: (lambda d=filedialog.askdirectory(): custom_backup_var.set(d) or (config.update({'backup_custom_dir':d}) or save_config(config)) if d else None)()).pack(padx=8,pady=4)


import requests
import tempfile

# --- Admin tab ---
tab_admin = ttk.Frame(nb); nb.add(tab_admin, text="Admin")
admin_entry = ttk.Entry(tab_admin, width=80); admin_entry.pack(padx=8,pady=6)
admin_output = tk.Text(tab_admin, height=12, bg="#151515", fg="#e6e6e6"); admin_output.pack(fill="both", expand=True, padx=8, pady=6)
ttk.Button(tab_admin, text="Run", command=lambda: run_admin()).pack(pady=6)

# --- Dev tab (hidden until unlocked) ---
tab_dev = ttk.Frame(nb)
dev_label = ttk.Label(tab_dev, text="Developer Interface - Advanced Tools", font=("Arial", 12, "bold"))
dev_label.pack(padx=8,pady=8)

# Dev actions frame
dev_frame = ttk.Frame(tab_dev)
dev_frame.pack(fill="x", padx=8, pady=6)

# Dev info text box
dev_info = tk.Text(tab_dev, height=20, bg="#1a1a1a", fg="#00ff66")
dev_info.pack(fill="both", expand=True, padx=8, pady=8)

# Dev password + state
DEV_PASSWORD = "mcdevtools2025"
dev_unlocked = False
CURRENT_VERSION = BUILD_VERSION  # use the build version for updater

# --- Dev helper functions ---
def dev_force_backup():
    if working_world is None:
        messagebox.showwarning("No world","Load a world first")
        return
    level = os.path.join(working_world,"level.dat")
    if not os.path.exists(level):
        messagebox.showerror("Missing","level.dat not found")
        return
    b = backup_level(level, Path(working_world).name)
    log(f"[Dev] Forced backup: {b}" if b else "[Dev] Backup failed")

def dev_reload_config():
    global config
    config = load_config()
    log("[Dev] Reloaded config.json")

def dev_save_config():
    save_config(config)
    log("[Dev] Saved config.json")

def dev_prefill_test():
    prefill_stats()
    log("[Dev] Ran prefill test on level.dat")

def dev_quick_fix():
    apply_fix()
    log("[Dev] Quick fix executed")

def dev_clear_logs():
    open("build_history.txt","w").close()
    try:
        log_widget.config(state="normal")
        log_widget.delete("1.0","end")
        log_widget.config(state="disabled")
    except:
        pass
    log("[Dev] Logs cleared")

# --- Update system ---
def dev_check_updates():
    try:
        resp = requests.get("https://raw.githubusercontent.com/wnl-perez/W.I.P-Eaglercraft-1.5.2-to-vanilla-Minecraft-1.5.2/main/latest.json", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        latest = data.get("latest_version")
        changelog = data.get("changelog","")
        if latest == CURRENT_VERSION:
            dev_info.insert("end", f"[Update] You are up to date (v{CURRENT_VERSION}).\n")
        else:
            dev_info.insert("end", f"[Update] New version available: v{latest}\nChangelog: {changelog}\n")
        log(f"[Dev] Checked for updates: current v{CURRENT_VERSION}, latest v{latest}")
    except Exception as e:
        dev_info.insert("end", f"[Update] Failed to check updates: {e}\n")
        log(f"[Dev] Error checking updates: {e}")

def dev_simulate_update():
    try:
        resp = requests.get("https://raw.githubusercontent.com/wnl-perez/W.I.P-Eaglercraft-1.5.2-to-vanilla-Minecraft-1.5.2/main/latest.json", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        latest = data.get("latest_version")
        download = data.get("download_url")
        if latest == CURRENT_VERSION:
            dev_info.insert("end", f"[Update] Already on latest version (v{CURRENT_VERSION}). Nothing to update.\n")
            return
        dev_info.insert("end", f"[Update] Downloading version {latest} script...\n")
        log(f"[Dev] Downloading update from: {download}")
        r2 = requests.get(download, timeout=10)
        r2.raise_for_status()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp.write(r2.content)
        tmp.close()
        dev_info.insert("end", f"[Update] Downloaded update script to {tmp.name} (simulation).\n")
        log(f"[Dev] Simulated update download complete.")
    except Exception as e:
        dev_info.insert("end", f"[Update] Update simulation failed: {e}\n")
        log(f"[Dev] Error simulating update: {e}")

def dev_revert_build():
    dev_info.insert("end", "[Update] Simulated reverting to previous build v1.2.0.\n")
    log("[Dev] Simulated build revert")

# --- Dev tab buttons ---
ttk.Button(dev_frame, text="Force Backup", command=dev_force_backup).grid(row=0,column=0,padx=6,pady=4,sticky="w")
ttk.Button(dev_frame, text="Reload Config", command=dev_reload_config).grid(row=0,column=1,padx=6,pady=4,sticky="w")
ttk.Button(dev_frame, text="Save Config", command=dev_save_config).grid(row=0,column=2,padx=6,pady=4,sticky="w")

ttk.Button(dev_frame, text="Run Prefill Test", command=dev_prefill_test).grid(row=1,column=0,padx=6,pady=4,sticky="w")
ttk.Button(dev_frame, text="Apply Quick Fix", command=dev_quick_fix).grid(row=1,column=1,padx=6,pady=4,sticky="w")
ttk.Button(dev_frame, text="Clear Logs", command=dev_clear_logs).grid(row=1,column=2,padx=6,pady=4,sticky="w")

ttk.Button(dev_frame, text="Check for Updates", command=dev_check_updates).grid(row=2,column=0,padx=6,pady=4,sticky="w")
ttk.Button(dev_frame, text="Simulate Update", command=dev_simulate_update).grid(row=2,column=1,padx=6,pady=4,sticky="w")
ttk.Button(dev_frame, text="Revert Build", command=dev_revert_build).grid(row=2,column=2,padx=6,pady=4,sticky="w")

# --- Admin runner ---
def run_admin():
    global dev_unlocked
    cmd = admin_entry.get().strip()
    admin_entry.delete(0,"end")

    if cmd.startswith("pass "):
        pw = cmd.split(" ",1)[1]
        if pw == DEV_PASSWORD:
            if not dev_unlocked:
                dev_unlocked = True
                nb.add(tab_dev, text="Dev")  # show the Dev tab
                admin_output.insert("end","[Dev] Interface unlocked!\n")
            else:
                admin_output.insert("end","[Dev] Already unlocked.\n")
        else:
            admin_output.insert("end","[Dev] Wrong password.\n")

    elif cmd == "/help":
        if dev_unlocked:
            admin_output.insert("end","Commands: /help /locate /clear /devstats /config\n")
        else:
            admin_output.insert("end","Commands: /help /locate /clear\n")

    elif cmd == "/locate":
        admin_output.insert("end", f"Working world: {working_world}\n")

    elif cmd == "/clear":
        admin_output.delete("1.0","end")

    elif dev_unlocked and cmd == "/devstats":
        admin_output.insert("end", f"[Dev] Config: {json.dumps(config, indent=2)}\n")

    elif dev_unlocked and cmd == "/config":
        dev_info.delete("1.0","end")
        dev_info.insert("end", f"Current Config:\n{json.dumps(config, indent=2)}\n")

    else:
        admin_output.insert("end", f"Unknown: {cmd}\n")


# --- World Selector ---
import tkinter.filedialog as fd

DEFAULT_SAVES = r"C:\Users\12201\AppData\Roaming\.minecraft 1.5.2\saves"

world_frame = ttk.Frame(tab_gen)
world_frame.pack(fill="x", padx=8, pady=6)

ttk.Label(world_frame, text="Select World:").pack(side="left", padx=4)

world_var = tk.StringVar()
world_dropdown = ttk.Combobox(world_frame, textvariable=world_var, state="readonly")

def refresh_worlds():
    import os
    worlds = []
    if os.path.isdir(DEFAULT_SAVES):
        for d in os.listdir(DEFAULT_SAVES):
            if os.path.isdir(os.path.join(DEFAULT_SAVES, d)):
                worlds.append(d)
    world_dropdown["values"] = worlds
    if worlds:
        world_dropdown.current(0)
        set_world(worlds[0])

def set_world(name):
    global working_world
    working_world = os.path.join(DEFAULT_SAVES, name)
    current_world_label.config(text=f"Current World: {name}")

def on_world_select(event):
    sel = world_var.get()
    set_world(sel)

world_dropdown.bind("<<ComboboxSelected>>", on_world_select)
world_dropdown.pack(side="left", padx=4)

def browse_world_dir():
    global working_world
    sel = fd.askdirectory(title="Select Minecraft Saves Folder")
    if sel:
        working_world = sel
        current_world_label.config(text=f"Current World: {Path(sel).name}")

ttk.Button(world_frame, text="Browse...", command=browse_world_dir).pack(side="left", padx=4)

current_world_label = ttk.Label(world_frame, text="Current World: None")
current_world_label.pack(side="left", padx=8)

refresh_worlds()

# -- core functions --
def generate_clear_plan():
    if working_world is None: messagebox.showwarning("No world","Load a world first"); return
    blocks = [b.strip() for b in custom_blocks_entry.get().split(",") if b.strip()]
    plan = os.path.join(working_world, "FIXER_clear_plan.txt")
    with open(plan,"w",encoding="utf-8") as f: f.write("Clear plan generated:\n"); f.write("Blocks: "+", ".join(blocks)+"\n")
    messagebox.showinfo("Plan created", f"Plan created at: {plan}"); log(f"Wrote clear plan: {plan}")

def load_world_from_zip(p):
    global working_world, loaded_from_zip
    dest = os.path.join("working", Path(p).stem+"_"+str(int(time.time()))); ensure(dest)
    try:
        with zipfile.ZipFile(p,"r") as z: z.extractall(dest)
    except Exception as e: messagebox.showerror("Extract failed", str(e)); return
    cand=None
    for r,d,f in os.walk(dest):
        if "level.dat" in f: cand=r; break
    if not cand: messagebox.showerror("No level.dat","Zip doesn't include level.dat"); return
    working_world = cand; loaded_from_zip=True; loaded_label.config(text=f"{Path(working_world).name} (zip)"); on_world_loaded()

def load_world_from_folder(p):
    global working_world, loaded_from_zip
    cand=None
    for r,d,f in os.walk(p):
        if "level.dat" in f: cand=r; break
    if not cand: messagebox.showerror("No level.dat","Folder has no level.dat"); return
    working_world = cand; loaded_from_zip=False; loaded_label.config(text=f"{Path(working_world).name} (folder)"); on_world_loaded()

def on_world_loaded():
    set_ui_enabled(True); prefill_stats(); config["last_world_path"]=working_world; save_config(config)

def prefill_stats():
    if working_world is None: return
    level = os.path.join(working_world,"level.dat")
    if not os.path.exists(level): return
    if nbtlib is None:
        log("nbtlib missing; cannot prefill stats."); return
    try:
        lvl = nbtlib.load(level); data = lvl["Data"]; player = data.get("Player", {})
        health = float(player.get("Health",20.0)); hunger = int(player.get("foodLevel", player.get("FoodLevel",20)))
        xp_lvl = int(player.get("XpLevel", player.get("XpLevel",0))); xp_p = float(player.get("XpP", player.get("XpProgress",0.0)))
        health_scale.set(max(0,min(20,int(health)))); hunger_scale.set(max(0,min(20,int(hunger))))
        xp_level_scale.set(max(0,min(100,int(xp_lvl)))); xp_prog_scale.set(max(0,min(100,int(xp_p*100))))
        health_entry.delete(0,"end"); health_entry.insert(0,str(int(health)))
        hunger_entry.delete(0,"end"); hunger_entry.insert(0,str(int(hunger)))
        xp_level_entry.delete(0,"end"); xp_level_entry.insert(0,str(int(xp_lvl)))
        xp_prog_entry.delete(0,"end"); xp_prog_entry.insert(0,str(int(xp_p*100)))
        log("Prefilled stats from level.dat")
    except Exception as e: log(f"Prefill failed: {e}")

def apply_stats():
    if working_world is None: messagebox.showwarning("No world","Load a world first"); return
    level = os.path.join(working_world,"level.dat"); 
    if not os.path.exists(level): messagebox.showerror("Missing","level.dat not found"); return
    b = backup_level(level, Path(working_world).name); log(f"Backup created: {b}" if b else "Backup failed")
    if manual_var.get():
        try:
            h = float(health_entry.get()); hunger = int(hunger_entry.get()); xl = int(xp_level_entry.get()); xp_p = float(xp_prog_entry.get())/100.0
        except: messagebox.showerror("Invalid","Manual values invalid"); return
    else:
        h = float(health_scale.get()); hunger = int(hunger_scale.get()); xl = int(xp_level_scale.get()); xp_p = float(xp_prog_scale.get())/100.0
    if nbtlib is None: messagebox.showerror("Missing","Install nbtlib to edit level.dat"); return
    try:
        lvl = nbtlib.load(level); data = lvl["Data"]; player = data.get("Player", nbtlib.tag.Compound())
        player["Health"] = nbtlib.tag.Float(h); player["foodLevel"] = nbtlib.tag.Int(hunger); player["XpLevel"] = nbtlib.tag.Int(xl); player["XpP"] = nbtlib.tag.Float(xp_p)
        data["Player"] = player; lvl.save(level); messagebox.showinfo("Done","Player stats applied (backup created)"); log("Applied player stats")
    except Exception as e: log(f"Apply stats failed: {e}"); messagebox.showerror("Error", str(e))

def apply_fix():
    if working_world is None: messagebox.showwarning("No world","Load a world first"); return
    level = os.path.join(working_world,"level.dat"); 
    if not os.path.exists(level): messagebox.showerror("Missing","level.dat not found"); return
    b = backup_level(level, Path(working_world).name); log(f"Backup created: {b}" if b else "Backup failed")
    if nbtlib is None: messagebox.showerror("Missing","Install nbtlib to edit level.dat"); return
    try:
        lvl = nbtlib.load(level); data = lvl["Data"]
        if seed_entry.get().strip():
            try: data["RandomSeed"] = nbtlib.tag.Long(int(seed_entry.get().strip())); log("Seed overridden")
            except: pass
        if clear_inv_var.get():
            pl = data.get("Player", nbtlib.tag.Compound()); pl["Inventory"] = nbtlib.tag.List(); data["Player"]=pl; log("Cleared inventory")
        lvl.save(level); messagebox.showinfo("Done","Fixes applied (backup created)"); log("Applied fixes to level.dat")
    except Exception as e: log(f"Apply fix failed: {e}"); messagebox.showerror("Error", str(e)); return
    if loaded_from_zip and export_var.get():
        mc = config.get("mc_saves") or filedialog.askdirectory(title="Select Minecraft saves folder")
        if not mc: messagebox.showwarning("No saves","Minecraft saves not set"); return
        tgt = os.path.join(mc, Path(working_world).name)
        if os.path.exists(tgt):
            if config.get("ask_overwrite",True):
                res = messagebox.askyesno("Exists","World exists in saves. Overwrite? (No = keep both)")
                if res: shutil.rmtree(tgt)
                else: tgt = os.path.join(mc, f"{Path(working_world).name} (Fixed)")
        try: shutil.copytree(working_world, tgt); messagebox.showinfo("Exported", f"Copied fixed world to: {tgt}"); log(f"Exported to saves: {tgt}")
        except Exception as e: log(f"Export failed: {e}"); messagebox.showerror("Error", str(e))

# Wire UI state
set_ui_enabled = lambda enabled: [w.config(state=("normal" if enabled else "disabled")) for w in (apply_fix_btn, clear_inv_chk, chest_clear_chk, seed_entry, export_chk, custom_blocks_entry, advanced_blocks_chk, clear_plan_btn, apply_stats_btn, manual_chk)]
set_ui_enabled(False)
loaded_label.config(text="(none) - load a zip or folder to enable actions")
log("Ready. Load a world to begin.")

root.mainloop()