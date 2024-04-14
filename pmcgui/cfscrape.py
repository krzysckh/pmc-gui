# -*- mode: python; python-indent-offset: 2 -*-

import typing
from threading import Thread
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

session = None

pagebase = 'https://legacy.curseforge.com'
urlbase = f'{pagebase}/minecraft/mc-mods?page={{}}'

# assumes session != None
def get_versions(u) -> list:
  url = f'{u}/files/all'
  log(f'GET {url}')
  r = session.get(url)

  if r.status_code != 200:
    log(f"couldn't GET {url}")
    return

  log(f"OK {url}")

  c = r.text;
  sels = list(map(lambda v: re.sub(r'\s', '', v.text),
                  bs.BeautifulSoup(c, features="lxml").select("select#filter-game-version option")))
  vs = list(filter(lambda s: re.match('\\d+\\.\\d+(?:\\.\\d+)?', s), sels))

  return vs

def session_start() -> None:
  global session

  if session == None:
    session = cfauth.auth_as_user()

def get_jars(u, n) -> list:
  session_start()
  url = f"{u}/files/all?page={n}"

  r = session.get(url)

  if r.status_code != 200:
    log(f"couldn't GET {url}")
    return

  ret = []

  s = bs.BeautifulSoup(r.text, features="lxml")
  tbl = s.select('table.listing tbody')[0]
  for e in tbl.select('tr'):
    filename = e.select('td a')[0].text
    ident =    e.select('td a')[0]['href'].split('/')[-1]
    url = f"https://mediafilez.forgecdn.net/files/{ident[0:4]}/{ident[4:7]}/{filename}"
    version = e.select('td')[4].select('div.mr-2')[0].text.replace('\n', '')
    print(f"{filename}: {version}")
    ret.append({
      "filename": filename,
      "url": url,
      "version": version
    })

  return ret

def get_page(n) -> list:
  global session
  session_start()

  url = urlbase.format(n)
  log(f"GET {url}")
  r = session.get(url)

  if r.status_code == 403:
    session = cfauth.reauth()
    return get_page(n)

  if r.status_code != 200:
    return None

  b = bs.BeautifulSoup(r.text, features='lxml')
  els = b.select('.project-listing-row')

  ret = [None] * len(els)
  threads = []

  def el2dict(e, n):
    url = f"{pagebase}{e.select('a')[0]['href']}"
    ret[n] = {
      'name':     e.select('h3')[0].text,
      'url':      url,
      'versions': get_versions(url)
    }

  n = 0
  for e in els:
    t = Thread(target=lambda e=e, n=n: el2dict(e, n))
    threads.append(t)
    t.start()
    n += 1

  for t in threads:
    t.join()

  return list(ret)
