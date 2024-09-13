# -*- mode: python; python-indent-offset: 2 -*-
import typing
import os
import os.path
import json

import tkinter

_root = None
_ta  = None

def get_base_dir() -> str:
  ret = ""
  if os.name == 'nt':
    ret = os.path.join(os.getenv("APPDATA"), "pmc-gui")
  else:
    ret = os.path.join(os.getenv("HOME"), ".local", "share", "pmc-gui")

  if not os.path.exists(ret):
    os.mkdir(ret)

  return ret

def get_mc_location() -> str:
  return os.path.join(os.getenv("HOME"), ".minecraft") if os.name != 'nt' else \
    os.path.join(os.getenv("APPDATA"), ".minecraft")

def loadicon(el) -> None:
  try:
    if os.name == 'nt':
      el.iconbitmap(os.path.join(os.path.dirname(__file__), "..", "icon.ico"))
  except Exception as e:
    log(f"loadicon() failed: {str(e)}")
    pass

def get_root():
  return _root

def log(s: str) -> None:
  if _ta != None:
    _ta.config(state=tkinter.NORMAL)
    _ta.insert("end", f"{s}\n")
    _ta.config(state=tkinter.DISABLED)
  else:
    print(f"LOG: {s}")

def get_prefs_path() -> str:
  return os.path.join(get_base_dir(), "pmc-prefs.json")

def get_data_path() -> str:
  return os.path.join(get_base_dir(), "pmc-data.json")

def save_data(mpack: str, v: str) -> None:
  data = get_data_path()
  dp = get_data_path()
  with open(dp, "w") as f:
    j = {}
    if mpack != None:
      j['loaded-modpack'] = mpack
    if v != None:
      j['modpack-game-version'] = v
    f.write(json.dumps(j))

def get_data() -> dict:
  dp = get_data_path()
  if os.path.exists(dp):
    with open(dp, "r") as f:
      return json.loads(f.read())
  return {}
