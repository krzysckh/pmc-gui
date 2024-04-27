#/usr/bin/env python3
# -*- mode: python; python-indent-offset: 2 -*-

import typing
from threading import Thread
from portablemc.standard import *
from portablemc.forge import *
import requests
import bs4 as bs
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
import pmcgui.moddl  as moddl
import pmcgui.cfscrape as cfscrape

default_jvm_opts = "-Xmx2G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"

v_ent: ttk.Entry
n_ent: ttk.Entry
start_btn: ttk.Button
clear_cache_b: ttk.Button
ta: tkinter.Text
sl: ttk.Checkbutton
jvm_opts: str = default_jvm_opts

base_dir: str

launcher_profiles_json = '{"profiles": {}, "settings": {}, "version": 3, "selectedProfile": "OptiFine"}'

class PMCRunner(StreamRunner):
  def process_stream_event(self, event: Any) -> None:
    if isinstance(event, XmlStreamEvent):
      # log(f"Minecraft XML-Log: {repr(event)}")
      pass
    else:
      log(f"PortableMC: {event}")

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

def get_mc_location() -> str:
  return os.path.join(os.getenv("HOME"), ".minecraft") if os.name != 'nt' else \
    os.path.join(os.getenv("APPDATA"), ".minecraft")

def write_lp_json() -> None:
  mc_location = get_mc_location()
  lp_json_location = os.path.join(mc_location, "launcher_profiles.json")

  if not os.path.exists(mc_location):
    os.mkdir(mc_location)

  if not os.path.exists(lp_json_location):
    log(f"writing to {lp_json_location}")
    with open(lp_json_location, "w") as f:
      f.write(launcher_profiles_json)

def get_all_optifine_versions() -> Version:
  log("GET https://optifine.net/downloads")
  html = requests.get("https://optifine.net/downloads").text;
  log("OK")
  s = bs.BeautifulSoup(html, features='lxml')
  els = map(lambda v: re.search('(?<=\\?f=)(.*\\.jar)', v["href"]).group(1), s.select("td.colDownload > a"))

  return els

def dl_optifine_version(version: str) -> bool:
  log(f"GET https://optifine.net/adloadx?f={version}");
  dl = requests.get(f"https://optifine.net/adloadx?f={version}").text;
  log("OK")
  url = "https://optifine.net/{}".format(
    bs.BeautifulSoup(dl).select(".downloadButton > a")[0]["href"]
  );

  path = os.path.join(base_dir, version)
  if not os.path.exists(path):
    log(f"GET {url}")
    log(f"downloading to {path}")
    with requests.get(url, stream=True) as r:
      r.raise_for_status()
      with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
          f.write(chunk)
    log("OK")
    return True
  return False

def get_optifine_version_type(s: str) -> list:
  m = re.search('OptiFine_(\\d+\\.\\d+(?:\\.\\d+)?)_(.*).jar', s)
  return [m.group(1), m.group(2)]

def get_optifine(version: str) -> Version:
  log(f"get_optifine {version}")
  els = get_all_optifine_versions()

  chosen = list(filter(lambda s: s.find(f"{version}_") != -1, els))[0]

  # install chosen version without optifine
  log(f"installing version {version} (without optifine)")
  temp = Version(version)
  temp.set_auth_offline("", None)
  temp.install()

  log(f"installing version {chosen} (with optifine)")
  if dl_optifine_version(chosen):
    java_run(chosen)

  v, T = get_optifine_version_type(chosen)
  name = "{}-OptiFine_{}".format(v, T)
  log(f"get_optifine version name: {name}")
  return Version(name)

def find_java() -> str:
  if os.name == 'nt':
    base = os.path.join(os.getenv("APPDATA"), ".minecraft", "jvm")
    fs = list(filter(lambda s: s.find('.json') == -1, os.listdir(base)))
    log(f'available jres: {fs} -- choosing {fs[0]}')
    fs.sort(key=cmp_to_key(lambda a, b: -1 if b == 'jre-legacy' else 1))
    return os.path.join(base, fs[0], "bin", "java.exe")
  return "java"

def java_run(thing) -> None:
  java = find_java()
  run = os.path.join(base_dir, thing)
  log(f"running: {java} -jar {run}")
  os.system(f"{java} -jar {run}")

def get_optifine_newest() -> Version:
  log("get_optifine_newest")
  els = get_all_optifine_versions()
  newest = list(filter(lambda s: s.find("preview") == -1, els))[0]

  v, T = get_optifine_version_type(newest)

  log(f"installing version {v} (without optifine)")
  temp = Version(v)
  temp.set_auth_offline("", None)
  temp.install()

  log(f"installing version {newest} (with optifine)")
  if dl_optifine_version(newest):
    java_run(newest)

  name = "{}-OptiFine_{}".format(v, T)
  log(f"get_optifine_newest version name: {name}")
  return Version(name)

  # vs = list(filter(lambda v: v.id == name, list(Context().list_versions())))
  # version = vs[0];

def start_minecraft():
  disable_btns()
  v_text: str = v_ent.get()
  nick: str = n_ent.get()
  log(f"loading minecraft: v: {v_text}, nick: {nick} (\"OFFLINE\" MODE)")
  v: Version = None
  try:
    if v_text == "newest" or v_text == "latest":
      v = Version()
    elif v_text == "optifine:newest" or v_text == "optifine:latest":
      v = get_optifine_newest()
    elif v_text == "forge:newest" or v_text == "forge:latest":
      v = ForgeVersion()
    elif m := re.search("^forge:(.*)$", v_text):
      s = m.group(1)
      if s.find("-") != -1:
        log(f"good luck - you're on your own. i hope `{v_text}' contains a valid ForgeVersion")
        v = ForgeVersion(s)
      else:
        sm = re.search("(\\d+\\.\\d+(?:\\.\\d+)?)", s)
        v = ForgeVersion(f"{sm.group(1)}-recommended")
    elif m := re.search("^optifine:(\\d+\\.\\d+(?:\\.\\d+)?)$", v_text):
      v = get_optifine(m.group(1))
    else:
      v = Version(v_text)
  except Exception as e:
    log(f"Couldn't start {v_text}: {str(e)}")
    reset_btns()
    return

  v.set_auth_offline(nick, None)
  log("installing...")
  env: Environment
  try:
    env = v.install()
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

def get_prefs_path() -> str:
  return os.path.join(base_dir, "pmc-prefs.json")

def save_prefs() -> None:
  pp = get_prefs_path()
  with open(pp, "w") as f:
    f.write(json.dumps({'uname': n_ent.get(), 'version': v_ent.get()}))

def load_prefs() -> None:
  pp = get_prefs_path()
  if os.path.exists(pp):
    with open(pp, "r") as f:
      p = json.loads(f.read())
      v_ent.delete(0, tkinter.END)
      v_ent.insert(0, p["version"])
      n_ent.delete(0, tkinter.END)
      n_ent.insert(0, p["uname"])

def clear_cache() -> None:
  disable_btns()

  fs = list(filter(lambda s: s.find('.jar') != -1, os.listdir(base_dir)))
  for f in fs:
    os.unlink(os.path.join(base_dir, f))

  reset_btns()

def main():
  global v_ent, n_ent, info_text, start_btn, ta, base_dir

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
    ta.pack(fill="both", expand=False, padx=5, pady=5)
    sl.configure(command=hide_ta)

  def hide_ta():
    ta.pack_forget(); sl.configure(command=show_ta)

  sl = ttk.Checkbutton(master=root, style="Switch.TCheckbutton", text="show debug log",
                       command=show_ta)
  sl.pack(fill="both", expand=False, padx=5, pady=5)

  ta = tkinter.Text(master=root, state=tkinter.DISABLED)
  common._ta = ta

  mb = tkinter.Menu(root)
  root.config(menu=mb)

  optsm = tkinter.Menu(mb, tearoff=0)
  optsm.add_command(label="Help", command=open_readme)
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
