# -*- mode: python; python-indent-offset: 2 -*-

import typing
from portablemc.auth import MicrosoftAuthSession
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from uuid import uuid4
import urllib.parse
import webbrowser
from pmcgui.common import log
from portablemc.auth import AuthDatabase, AuthSession
import portablemc.cli
import portablemc.cli.output
import portablemc.cli.parse as p
import tkinter.simpledialog
import pmcgui.common as c
from pathlib import Path

def maybe_get_session() -> typing.Optional[AuthSession]:
  redirect_uri = "https://www.theorozier.fr/portablemc/auth"
  app_id = portablemc.cli.MICROSOFT_AZURE_APP_ID
  db = AuthDatabase(Path(c.get_auth_database_path()))
  db.load()
  c.log(f"sessions: {db.sessions.items()}")
  try:
    e = None
    s = None
    for auth_type, auth_type_sessions in db.sessions.items():
      for email, sess in auth_type_sessions.items():
        return sess
  except Exception as e:
    c.log(f"error occured while trying to get session: {e}")
    return None
  return None

def ms() -> AuthSession:
  ns = typing.cast(p.RootNs, p.register_arguments().parse_args([]))
  ns.auth_no_browser = False
  ns.out = portablemc.cli.output.Output()
  ns.out.task = lambda x, y: None
  ns.auth_database = AuthDatabase(Path(c.get_auth_database_path()))
  email = tkinter.simpledialog.askstring("MS e-mail address", "Please input the e-mail address associated with your Microsoft account")
  session = portablemc.cli.prompt_microsoft_authenticate(ns, email)
  ns.auth_database.put(email, session)
  ns.auth_database.save()
  return session
