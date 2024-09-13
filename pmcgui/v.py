# -*- mode: python; python-indent-offset: 2 -*-

import re
from portablemc.standard import *
from portablemc.forge import *
import pmcgui.cfauth as cfauth
import pmcgui.common as common
from pmcgui.common import log
import pmcgui.moddl  as moddl
import pmcgui.cfscrape as cfscrape
import pmcgui.modpack as mp
import requests
import bs4 as bs

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

  path = os.path.join(common.get_base_dir(), version)
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
  run = os.path.join(common.get_base_dir(), thing)
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

def get_version(v_text, set_progress) -> Version:
  common.save_data(None, None)
  if v_text == "newest" or v_text == "latest":
    return Version()
  elif v_text == "optifine:newest" or v_text == "optifine:latest":
    return get_optifine_newest()
  elif v_text == "forge:newest" or v_text == "forge:latest":
    return ForgeVersion()
  elif m := re.search("^forge:(.*)$", v_text):
    s = m.group(1)
    if s.find("-") != -1:
      log(f"good luck - you're on your own. i hope `{v_text}' contains a valid ForgeVersion")
      return ForgeVersion(s)
    else:
      sm = re.search("(\\d+\\.\\d+(?:\\.\\d+)?)", s)
      return ForgeVersion(f"{sm.group(1)}-recommended")
  elif m := re.search("^optifine:(\\d+\\.\\d+(?:\\.\\d+)?)$", v_text):
    return get_optifine(m.group(1))
  elif m := re.search("^mod:(.*):(.*)$", v_text):
    ubase = m.group(1)
    name = m.group(2)
    return mp.get_modpack(ubase, name, set_progress)
  else:
    return Version(v_text)
