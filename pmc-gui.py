#/usr/bin/env python3
# -*- mode: python; python-indent-offset: 2 -*-

import typing
from threading import Thread
from portablemc.standard import Version, Environment, Context, Watcher
import requests
import bs4 as bs
import re
import os.path
import os

import tkinter
from tkinter import ttk
import sv_ttk

v_ent: ttk.Entry
n_ent: ttk.Entry
start_btn: ttk.Button
ta: tkinter.Text
sl: ttk.Checkbutton

download_dir: str

if os.name == 'nt':
  download_dir = os.path.join(os.getenv("APPDATA"), "pmc-gui")
  if not os.path.exists(download_dir):
    os.mkdir(download_dir)
else:
  download_dir = os.path.join(os.getenv("HOME"), ".local", "share", "pmc-gui")
  if not os.path.exists(download_dir):
    os.mkdir(download_dir)

def log(s: str) -> None:
  ta.config(state=tkinter.NORMAL)
  ta.insert("end", f"{s}\n")
  ta.config(state=tkinter.DISABLED)

def get_all_optifine_versions() -> Version:
  log("GET https://optifine.net/downloads")
  html = requests.get("https://optifine.net/downloads").text;
  log("OK")
  s = bs.BeautifulSoup(html)
  els = map(lambda v: re.search('(?<=\\?f=)(.*\\.jar)', v["href"]).group(1), s.select("td.colDownload > a"))

  return els

def dl_optifine_version(version: str) -> bool:
  log(f"GET https://optifine.net/adloadx?f={version}");
  dl = requests.get(f"https://optifine.net/adloadx?f={version}").text;
  log("OK")
  url = "https://optifine.net/{}".format(
    bs.BeautifulSoup(dl).select(".downloadButton > a")[0]["href"]
  );

  path = os.path.join(download_dir, version)
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
    return os.path.join(os.getenv("APPDATA"), ".minecraft", "jvm", "jre-legacy", "bin", "java.exe")
  return "java"

def java_run(thing) -> None:
  java = find_java()
  run = os.path.join(download_dir, thing)
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
  start_btn.config(state="disabled")
  v_text: str = v_ent.get()
  nick: str = n_ent.get()
  log(f"loading minecraft: v: {v_text}, nick: {nick} (\"OFFLINE\" MODE)")
  v: Version = None
  if v_text == "newest":
    v = Version()
  elif v_text == "optifine:newest":
    v = get_optifine_newest()
  elif m := re.search("^optifine:(\\d+\\.\\d+(?:\\.\\d+)?)$", v_text):
    v = get_optifine(m.group(1))
  else:
    v = Version(v_text)

  v.set_auth_offline(nick, None)
  log("installing...")
  env: Environment = v.install()
  log(f"starting Minecraft {v_text}...")
  env.run()
  start_btn.config(state="normal")

def main():
  global v_ent, n_ent, info_text, start_btn, ta

  root = tkinter.Tk()

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

  sv_ttk.set_theme("dark")
  log("started correctly")
  try:
    if os.name == 'nt':
      root.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
  except:
    print("ups")
    pass
  root.mainloop()

if __name__ == "__main__":
  main()

