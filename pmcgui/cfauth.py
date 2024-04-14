# -*- mode: python; python-indent-offset: 2 -*-

import typing
import requests
import requests.cookies
import json
import sys
import webbrowser
import browser_cookie3
import time
from threading import Thread
import re
import http.server
import http.cookiejar
import os.path

import pmcgui.common as common
from pmcgui.common import log

_hs = {}
class HeadersGetter(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    global _hs

    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(bytes('ok', "utf-8"))

    for h in map(lambda s: s.split(': '), str(self.headers).split('\n')):
      if len(h) > 1:
        if not re.match('host', h[0], re.IGNORECASE):
          _hs[h[0]] = h[1]

def get_headers() -> dict:
  s = http.server.HTTPServer(("127.0.0.1", 6970), HeadersGetter)

  def w_open():
    time.sleep(1)
    webbrowser.open("127.0.0.1:6970")

  Thread(target=w_open).start()
  s.handle_request()

  return _hs

def get_auth_cache() -> dict:
  d = common.get_base_dir()
  with open(os.path.join(d, "auth-cache.json"), 'r') as f:
    return json.load(f)

def save_auth_cache(cookies: dict, headers: dict) -> None:
  d = common.get_base_dir()
  with open(os.path.join(d, "auth-cache.json"), 'w') as f:
    json.dump({'cookies': cookies, 'headers': headers}, f)

def has_auth_cache() -> bool:
  d = common.get_base_dir()
  return os.path.isfile(os.path.join(d, "auth-cache.json"))

def create_session(cr: dict, headers: dict) -> requests.Session:
  cj = requests.cookies.cookiejar_from_dict(cr)
  s = requests.Session()
  s.headers.update(headers)
  s.cookies = cj;

  return s

def invalidate_cache() -> None:
  d = common.get_base_dir()
  os.unlink(os.path.join(d, "auth-cache.json"))

def auth_as_user():
  if has_auth_cache():
    cache = get_auth_cache()
    return create_session(cache['cookies'], cache['headers'])
  else:
    log("re-auth")
    h = get_headers()
    webbrowser.open('https://legacy.curseforge.com')
    cookiesl = [
      browser_cookie3.firefox(domain_name='curseforge.com'),
      browser_cookie3.firefox(domain_name='.curseforge.com'),
      browser_cookie3.firefox(domain_name='legacy.curseforge.com')
    ]

    cs = {}
    for k in cookiesl:
      for c in k:
        cs[c.name] = c.value;

    save_auth_cache(cs, h)
    return create_session(cs, h)

def reauth() -> requests.Session:
  invalidate_cache()
  return auth_as_user()
