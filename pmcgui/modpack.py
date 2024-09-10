# -*- mode: python; python-indent-offset: 2 -*-

import typing
import requests
import sys
import os.path
import portablemc
import zipfile

import pmcgui.common as common
import pmcgui.v as v
from pmcgui.common import log

resolvable = {
  "kpm": "krzych.tilde.institute/pmc-modpacks"
}

def get_modpack(ubase: str, name: str, cb) -> portablemc.standard.Version:
  url = None
  if ubase in resolvable:
    url = f"https://{resolvable[ubase]}/{name}.pmcpack"
    log(f"{ubase} is resolvable, using {url} as url")
  else:
    url = f"https://{ubase}/{name}.pmcpack"
    log(f"modpack: using {url} as url")

  base = common.get_base_dir()
  fname = os.path.join(base, f"{name}.pmcpack")

  # TODO: download a hash and check integrity
  # this would also be great if the modpack updated pozdr
  if not os.path.isfile(fname):
    r = requests.get(url, stream=True);
    total = int(r.headers.get('content-length', 0))

    with open(fname, 'wb') as f:
      log(f"will write to {fname}")
      siz = 0
      for chunk in r.iter_content(chunk_size=2<<18):
        if chunk:
          siz += len(chunk)
          cb(siz, total)
          f.write(chunk)

      log("OK")

  with zipfile.ZipFile(fname, mode="r") as z:
    version = z.read('VERSION').rstrip().decode('utf-8')
    mods = list(filter(lambda s: s.startswith("mods"), z.namelist()))
    return v.get_version(version, cb)
