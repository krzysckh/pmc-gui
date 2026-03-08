# -*- mode: python; python-indent-offset: 2 -*-
import typing
import os
import os.path
import json
import portablemc.standard
from pathlib import Path

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

# def get_mc_location() -> str:
#   return os.path.join(os.getenv("HOME"), ".minecraft") if os.name != 'nt' else \
#     os.path.join(os.getenv("APPDATA"), ".minecraft")

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
  if _ta is not None:
    _ta.config(state=tkinter.NORMAL)
    _ta.insert("end", f"{s}\n")
    _ta.config(state=tkinter.DISABLED)
  else:
    print(f"LOG: {s}")

def get_prefs_path() -> str:
  return os.path.join(get_base_dir(), "pmc-prefs.json")

def get_data_path() -> str:
  return os.path.join(get_base_dir(), "pmc-data.json")

def get_auth_database_path():
  return os.path.join(get_base_dir(), "AUTHDB")

def save_data(mpack: str|None=None, version: str|None=None, jvm_opts: str|None=None, base_folder: str|None=None) -> None:
  j = get_data()
  dp = get_data_path()
  with open(dp, "w") as f:
    if mpack is not None:
      j['loaded-modpack'] = mpack
    if version is not None:
      j['modpack-game-version'] = version
    if jvm_opts is not None:
      j['jvm-opts'] = jvm_opts
    if base_folder is not None:
      j['base-folder'] = base_folder

    log(f'saving {dp}: {json.dumps(j)}')
    f.write(json.dumps(j))

def get_data() -> dict:
  dp = get_data_path()
  if os.path.exists(dp):
    with open(dp, "r") as f:
      return json.loads(f.read())
  return {}

default_jvm_opts = "-Xmx2G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"

_jvm_opts: str = default_jvm_opts
_base_folder: str|None = None

def get_jvm_opts() -> str:
  return _jvm_opts

def set_jvm_opts(s: str) -> None:
  global _jvm_opts
  _jvm_opts = s
  # save_data(jvm_opts=s)

def get_base_game_folder() -> str:
  if _base_folder is None:
    return portablemc.standard.get_minecraft_dir()
  return _base_folder

def set_base_game_folder(s: str|None) -> None:
  global _base_folder
  _base_folder = s

def get_mc_location() -> str:
  return Path(get_base_game_folder())
