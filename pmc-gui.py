import typing
from threading import Thread
from portablemc.standard import Version, Environment

import tkinter
from tkinter import ttk
import sv_ttk

v_ent: ttk.Entry
n_ent: ttk.Entry
start_btn: ttk.Button

def start_minecraft():
  start_btn.config(state="disabled")
  v_text: str = v_ent.get()
  nick: str = n_ent.get()
  v: Version = Version(v_text) if v_text != "newest" else Version()
  v.set_auth_offline(nick, None)
  env: Environment = v.install()
  env.run()
  start_btn.config(state="normal")

def main():
  global v_ent, n_ent, info_text, start_btn
  root = tkinter.Tk()

  root.title("pmc-gui")
  root.resizable(width=False, height=False)

  v_text: ttk.Label = ttk.Label(master=root, text="version: ")
  v_ent = ttk.Entry(master=root)
  v_ent.insert("end", "newest")
  v_text.pack(fill="both", expand=False, padx=5)
  v_ent.pack(fill="both", expand=False, padx=5, pady=5)

  n_text: ttk.Label = ttk.Label(master=root, text="nick: ")
  n_ent = ttk.Entry(master=root)
  n_ent.insert("end", "epicgamer")
  n_text.pack(fill="both", expand=False, padx=5)
  n_ent.pack(fill="both", expand=False, padx=5, pady=5)

  start_btn = ttk.Button(master=root, text="Start",
                         command=Thread(target=start_minecraft).start)
  start_btn.pack(fill="both", expand=False, padx=5, pady=5)

  sv_ttk.set_theme("dark")
  root.mainloop()

if __name__ == "__main__":
  main()

