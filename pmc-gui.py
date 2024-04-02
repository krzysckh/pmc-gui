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

def log(s: str) -> None:
  ta.config(state=tkinter.NORMAL)
  ta.insert("end", f"{s}\n")
  ta.config(state=tkinter.DISABLED)

def get_all_optifine_versions() -> Version:
  html = requests.get("https://optifine.net/downloads").text;
  s = bs.BeautifulSoup(html)
  els = map(lambda v: re.search('(?<=\\?f=)(.*\\.jar)', v["href"]).group(1), s.select("td.colDownload > a"))

  return els

def dl_optifine_version(version: str) -> bool:
  dl = requests.get("https://optifine.net/adloadx?f={}".format(version)).text;
  url = "https://optifine.net/{}".format(
    bs.BeautifulSoup(dl).select(".downloadButton > a")[0]["href"]
  );

  if not os.path.exists(version):
    with requests.get(url, stream=True) as r:
      r.raise_for_status()
      with open(version, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
          f.write(chunk)
    return True
  return False

def get_optifine_version_type(s: str) -> list:
  m = re.search('OptiFine_(\\d+\\.\\d+(?:\\.\\d+)?)_(.*).jar', s)
  return [m.group(1), m.group(2)]

def get_optifine(version: str) -> Version:
  log("get_optifine")
  els = get_all_optifine_versions()

  chosen = list(filter(lambda s: s.find(f"{version}_") != -1, els))[0]

  # install chosen version without optifine
  log("install V w-out optifine")
  temp = Version(version)
  temp.set_auth_offline("", None)
  temp.install()

  log(f"install optifine {chosen}")
  if dl_optifine_version(chosen):
    java_run(chosen)

  v, T = get_optifine_version_type(chosen)
  name = "{}-OptiFine_{}".format(v, T)
  log(f"get_optifine with {name}")
  return Version(name)

def java_run(thing) -> None:
  v = Version()
  v._resolve_jvm(Watcher())
  java = v._jvm_path
  log(f"running: java -jar {thing}")
  os.system(f"java -jar {thing}")

def get_optifine_newest() -> Version:
  log("get_optifine_newest")
  els = get_all_optifine_versions()
  newest = list(filter(lambda s: s.find("preview") == -1, els))[0]

  v, T = get_optifine_version_type(newest)

  log("install V w-out optifine")
  temp = Version(v)
  temp.set_auth_offline("", None)
  temp.install()

  log(f"install optifine {newest}")
  if dl_optifine_version(newest):
    java_run(newest)

  name = "{}-OptiFine_{}".format(v, T)
  return Version(name)

  # vs = list(filter(lambda v: v.id == name, list(Context().list_versions())))
  # version = vs[0];

def start_minecraft():
  start_btn.config(state="disabled")
  v_text: str = v_ent.get()
  nick: str = n_ent.get()
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
  env: Environment = v.install()
  env.run()
  start_btn.config(state="normal")

def main():
  global v_ent, n_ent, info_text, start_btn, ta

  root = tkinter.Tk()

  root.title("pmc-gui")
  root.resizable(width=False, height=False)

  v_text: ttk.Label = ttk.Label(master=root, text="version: ")
  v_ent = ttk.Entry(master=root)
  v_ent.insert("end", "optifine:1.12.2")
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

  ta = tkinter.Text(master=root, state=tkinter.DISABLED)
  ta.pack(fill="both", expand=False, padx=5, pady=5)

  sv_ttk.set_theme("dark")
  root.mainloop()

if __name__ == "__main__":
  main()

