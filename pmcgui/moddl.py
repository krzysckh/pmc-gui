# -*- mode: python; python-indent-offset: 2 -*-

import typing
from threading import Thread
from portablemc.standard import *
from portablemc.forge import *
import requests
import bs4 as bs
import re
import os.path
import os
import json
import sys
import subprocess
from functools import cmp_to_key

import sqlite3

import tkinter
from tkinter import ttk
import sv_ttk

import pmcgui.cfauth as cfauth
import pmcgui.common as common
import pmcgui.cfscrape as cfscrape

def jars_popup(u) -> None:
  w = tkinter.Toplevel()
  w.resizable(width=False, height=False)
  lst = ttk.Treeview(master=w, columns=('fname', 'vs', 'url'), show='headings')

  lst.heading('fname', text='File Name')
  lst.heading('vs',   text='Minecraft version')
  lst.heading('url',  text='URL')

  lst.pack(fill="both", expand=False, padx=5)

  def _load(n):
    jdata = cfscrape.get_jars(u, n)
    n += 1
    for v in jdata:
      lst.insert('', tkinter.END, values=(v['filename'], v['version'], v['url']))
  def load(n):
    Thread(target=lambda: _load(n)).start()

  page = 1
  load(page)

def openwindow() -> None:
  w = tkinter.Toplevel()
  w.resizable(width=False, height=False)
  lst = ttk.Treeview(master=w, columns=('name', 'vs', 'url'), show='headings')

  lst.heading('name', text='Name')
  lst.heading('vs',   text='Versions')
  lst.heading('url',  text='URL')

  lst.pack(fill="both", expand=False, padx=5)

  def _showjars(_):
    for i in lst.selection():
      url = lst.item(i)['values'][2]
      jars_popup(url)

  lst.bind('<Double-1>', _showjars)

  def load():
    vs = cfscrape.get_page(1)
    for v in vs:
      lst.insert('', tkinter.END, values=(v['name'], v['versions'], v['url']))

  Thread(target=load).start()
