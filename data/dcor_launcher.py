"""Lançador do Demon's Crest Open Randomizer.exe: a única parte compilada (build_dcor.ps1).

Não tem lógica do rando: põe a pasta data (ao lado do exe) no caminho do Python e abre o dcor_gui de lá, então
mexer em qualquer .py da data vale na próxima vez que o exe abrir, sem compilar de novo.
O PyInstaller só embute os módulos da biblioteca padrão que este arquivo importa; por isso a lista abaixo inclui
tudo que o código da data usa (e alguns a mais, de folga). Módulo padrão novo no código da data = acrescentar aqui
e compilar uma vez.
"""
import os
import sys
import traceback

# biblioteca padrão usada pelo código da data (e folga)
import argparse, bisect, collections, copy, ctypes, ctypes.wintypes, datetime, functools, hashlib, heapq, io  # noqa
import itertools, json, math, random, re, string, struct, subprocess, threading, time, zlib  # noqa
import tkinter, tkinter.filedialog, tkinter.messagebox, tkinter.font  # noqa

HOME = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
DATA = os.path.join(HOME, 'data') if getattr(sys, 'frozen', False) else HOME


def main():
    sys.dont_write_bytecode = True               # não enche a data de __pycache__
    sys.path.insert(0, DATA)
    try:
        import dcor_gui
        dcor_gui.main()
    except Exception:                            # exe sem console: o erro aparece numa janela e num arquivo
        err = traceback.format_exc()
        try:
            open(os.path.join(HOME, 'dcor_erro.txt'), 'w', encoding='utf-8').write(err)
        except OSError:
            pass
        if '--seed' not in sys.argv:
            root = tkinter.Tk()
            root.withdraw()
            tkinter.messagebox.showerror('DCOR', f'Erro ao abrir o DCOR (pasta data: {DATA}):\n\n{err[-1500:]}')
        sys.exit(1)


if __name__ == '__main__':
    main()
