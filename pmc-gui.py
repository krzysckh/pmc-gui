#/usr/bin/env python3
# -*- mode: python; python-indent-offset: 2 -*-

import typing
from threading import Thread
from portablemc.standard import *
from portablemc.forge import *
import re
import os.path
import os
import json
import sys
import subprocess
from functools import cmp_to_key

import tkinter
from tkinter import ttk
import sv_ttk

import pmcgui.cfauth as cfauth
import pmcgui.common as common
from pmcgui.common import log
from pmcgui.common import get_mc_location
import pmcgui.moddl  as moddl
import pmcgui.cfscrape as cfscrape
import pmcgui.modpack as mp
from pmcgui.v import *          #
import pmcgui.auth as auth

default_jvm_opts = "-Xmx2G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"

v_ent: ttk.Entry
n_ent: ttk.Entry
start_btn: ttk.Button
clear_cache_b: ttk.Button
ta: tkinter.Text
sl: ttk.Checkbutton
progressv: tkinter.IntVar
progress: ttk.Progressbar
jvm_opts: str = default_jvm_opts

debug: bool = False

base_dir: str

launcher_profiles_json = '{"profiles": {}, "settings": {}, "version": 3, "selectedProfile": "OptiFine"}'

class PMCRunner(StreamRunner):
  def process_stream_event(self, event: Any) -> None:
    if isinstance(event, XmlStreamEvent):
      # log(f"Minecraft XML-Log: {repr(event)}")
      pass
    else:
      log(f"PortableMC: {event}")

class PMCWatcher(Watcher):
  def handle(self, ev: Any):
    if type(ev) is DownloadProgressEvent:
      if debug:
        set_progress(ev.size, ev.entry.size)

def opend(path) -> None:
  if os.name == 'nt':
    subprocess.Popen(f"explorer {path}", shell=True)
  else:
    subprocess.Popen(f"gtk-launch `xdg-mime query default inode/directory` {path}", shell=True)
    pass

def open_readme() -> None:
  w = tkinter.Toplevel()
  w.configure(width=1000, height=700)
  w.resizable(width=False, height=False)
  t = tkinter.Text(master=w)
  t.pack(fill="both", expand=False, padx=5)
  with open(os.path.join(os.path.dirname(__file__), "README"), 'r') as f:
    for l in f.readlines():
      t.insert("end", l)
  t.configure(state=tkinter.DISABLED)

def setjopts() -> None:
  global jvm_opts
  w = tkinter.Toplevel()
  t = tkinter.Text(master=w)
  t.pack(expand=True, padx=5)
  t.insert('end', jvm_opts)
  w.resizable(width=False, height=False)
  def close():
    jvm_opts = t.get("1.0", "end-1c")
    w.destroy()
  b = ttk.Button(master=w, text="Ok", command=close)
  b.pack(fill="both", expand=False, padx=5, pady=5)

def write_lp_json() -> None:
  mc_location = get_mc_location()
  lp_json_location = os.path.join(mc_location, "launcher_profiles.json")

  if not os.path.exists(mc_location):
    os.mkdir(mc_location)

  if not os.path.exists(lp_json_location):
    log(f"writing to {lp_json_location}")
    with open(lp_json_location, "w") as f:
      f.write(launcher_profiles_json)

  # vs = list(filter(lambda v: v.id == name, list(Context().list_versions())))
  # version = vs[0];

def set_progress(x, maximum):
  global progress, progressv
  progress.config(maximum=maximum)
  progressv.set(x)

def start_minecraft():
  disable_btns()
  v_text: str = v_ent.get()
  nick: str = n_ent.get()
  log(f"loading minecraft: v: {v_text}, nick: {nick}")
  v: Version | None = None
  try:
    v = get_version(v_text, set_progress, PMCWatcher())
  except Exception as e:
    log(f"Couldn't start {v_text}: {str(e)}")
    reset_btns()
    return

  # maybe auth tuah
  session = auth.maybe_get_session()
  if session:
    v.auth_session = session
    log("running in authenticated mode")
  else:
    v.set_auth_offline(nick, None)
    log("running in offline mode")

  log("installing...")
  env: Environment
  try:
    env = v.install(watcher=PMCWatcher())
    env.jvm_args.extend(jvm_opts.split(' '))
  except Exception as e:
    log(f"couldn't install() {v_text}: {str(e)}")
    reset_btns()
    return

  log(f"starting Minecraft {v_text}...")
  try:
    env.run(PMCRunner())
  except Exception as e:
    log(f"Stopped minecraft {v_text}: {str(e)}")
    reset_btns()
    return

  log(f"Minecraft {v_text} exited successfully")
  reset_btns()

def set_btns_state(s) -> None:
  start_btn.config(state=s)
  # ...

def disable_btns() -> None:
  set_btns_state("disabled")

def reset_btns() -> None:
  set_btns_state("normal")

def load_prefs() -> None:
  try:
    pp = common.get_prefs_path()
    if os.path.exists(pp):
      with open(pp, "r") as f:
        p = json.loads(f.read())
        v_ent.delete(0, tkinter.END)
        v_ent.insert(0, p["version"])
        n_ent.delete(0, tkinter.END)
        n_ent.insert(0, p["uname"])
  except Exception as e:
    log(f'failed to load preferences: {e}')

def clear_cache() -> None:
  disable_btns()

  fs = list(filter(lambda s: s.find('.jar') != -1 or s.find('.pmcpack') != -1 or s == "pmc-data.json", os.listdir(base_dir)))
  for f in fs:
    os.unlink(os.path.join(base_dir, f))

  reset_btns()

def save_prefs() -> None:
  pp = common.get_prefs_path()
  with open(pp, "w") as f:
    f.write(json.dumps({'uname': n_ent.get(), 'version': v_ent.get()}))

def main():
  global v_ent, n_ent, info_text, start_btn, ta, base_dir, progressv, progress

  # %APPDATA%/pmc-gui on windows, ~/.local/share/pmc-gui on unix
  base_dir = common.get_base_dir()

  root = tkinter.Tk()
  common._root = root

  root.title("pmc-gui")
  root.resizable(width=False, height=False)

  v_text: ttk.Label = ttk.Label(master=root, text="version: ")
  v_ent = ttk.Entry(master=root)
  v_ent.insert("end", "optifine:newest")
  v_text.pack(fill="both", expand=False, padx=5)
  v_ent.pack(fill="both", expand=False, padx=5, pady=5)

  n_text: ttk.Label = ttk.Label(master=root, text="nick: ")
  n_ent = ttk.Entry(master=root)
  n_ent.insert("end", "epicgamer")
  n_text.pack(fill="both", expand=False, padx=5)
  n_ent.pack(fill="both", expand=False, padx=5, pady=5)

  start_btn = ttk.Button(master=root, text="Start",
                         command=lambda: Thread(target=start_minecraft).start())
  start_btn.pack(fill="both", expand=False, padx=5, pady=5)

  def show_ta():
    global debug
    debug = True
    ta.pack(fill="both", expand=False, padx=5, pady=5)
    sl.configure(command=hide_ta)

  def hide_ta():
    global debug
    debug = False
    ta.pack_forget(); sl.configure(command=show_ta)

  sl = ttk.Checkbutton(master=root, style="Switch.TCheckbutton", text="show debug log",
                       command=show_ta)
  sl.pack(fill="both", expand=False, padx=5, pady=5)

  progressv = tkinter.IntVar()
  progress = ttk.Progressbar(mode='determinate', master=root, variable=progressv)
  progress.pack(fill="both", pady=5)

  ta = tkinter.Text(master=root, state=tkinter.DISABLED)
  common._ta = ta

  mb = tkinter.Menu(root)
  root.config(menu=mb)

  optsm = tkinter.Menu(mb, tearoff=0)
  optsm.add_command(label="Help", command=open_readme)
  optsm.add_command(label="Authenticate with a Microsoft account", command=auth.ms)
  optsm.add_command(label="Clear cache", command=clear_cache)
  optsm.add_command(label="Open mods folder", command=lambda: opend(os.path.join(get_mc_location(), "mods")))
  optsm.add_command(label="Open minecraft folder", command=lambda: opend(get_mc_location()))
  optsm.add_command(label="Open pmc-gui folder", command=lambda: opend(base_dir))
  optsm.add_command(label="Set jvm options", command=setjopts)

  modsm = tkinter.Menu(mb, tearoff=0)
  modsm.add_command(label="Mod menu", command=moddl.openwindow)

  miscm = tkinter.Menu(mb, tearoff=0)
  miscm.add_command(label="Reauthorize", command=cfauth.reauth)

  mb.add_cascade(label='Options', menu=optsm)
  # mb.add_cascade(label='Mods', menu=modsm)
  # mb.add_cascade(label='Misc.', menu=miscm)

  sv_ttk.set_theme("dark")
  common.loadicon(root)
  write_lp_json()
  root.protocol("WM_DELETE_WINDOW", lambda: [save_prefs(), sys.exit()])
  load_prefs()

  log("READY")
  root.mainloop()

if __name__ == "__main__":
  main()
