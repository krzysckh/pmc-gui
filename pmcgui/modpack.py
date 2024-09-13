# -*- mode: python; python-indent-offset: 2 -*-

import typing
import requests
import sys
import os.path
import portablemc
import zipfile
import shutil

import pmcgui.common as common
import pmcgui.v as v
from pmcgui.common import log
from distutils.dir_util import copy_tree

resolvable = {
  "kpm": "kpm.bsd.tilde.team/pmc-modpacks"
}

def get_modpack(ubase: str, name: str, cb) -> portablemc.standard.Version:
  data = common.get_data()
  log(f'{data}')
  if 'loaded-modpack' in data.keys():
    if data['loaded-modpack'] == name:
      log(f'modpack {name} already loaded, launching game')
      return v.get_version(data['modpack-game-version'], cb)

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
      log(f"will download to {fname}")
      siz = 0
      for chunk in r.iter_content(chunk_size=2<<18):
        if chunk:
          siz += len(chunk)
          cb(siz, total)
          f.write(chunk)

      log("OK, downloaded")

  with zipfile.ZipFile(fname, mode="r") as z:
    version = z.read('VERSION').rstrip().decode('utf-8')
    mods = list(filter(lambda s: s.startswith("mods") and zipfile.Path(z, s).is_file(), z.namelist()))
    additional = list(filter(lambda s: s.startswith("additional-files") and zipfile.Path(z, s).is_file(), z.namelist()))

    log(f'found {len(mods)} mods')
    log(f'found {len(additional)} additional files')

    mc = common.get_mc_location()
    modpath = os.path.join(mc, "mods")
    modpath_bak = os.path.join(mc, "mods.bak")

    if os.path.exists(modpath):
      if os.path.exists(modpath_bak):
        shutil.rmtree(modpath_bak)
      try:
        copy_tree(modpath, modpath_bak)
      except Exception as e:
        log(f'failed to backup {modpath}, continuing anyway')
    else:
      os.mkdir(modpath)

    for i, mod in enumerate(mods):
      with open(os.path.join(modpath, os.path.basename(mod)), 'wb') as f:
        f.write(z.read(mod))

      cb(i+1, len(mods))

    for i, a in enumerate(additional):
      nam = os.path.normpath(os.path.join(mc, a[17:]))
      if not os.path.exists(os.path.dirname(nam)):
        os.makedirs(os.path.dirname(nam))

      p = os.path.join(mc, nam)
      if not os.path.exists(p):
        with open(p, 'wb') as f:
          f.write(z.read(a))

      cb(i+1, len(additional))

    common.save_data(name, version)
    return v.get_version(version, cb)
