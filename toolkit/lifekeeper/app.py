#!/usr/bin/env python3
"""Lifekeeper as a window: choose your exports folder, press one button, and your page opens in the browser.
Then ask questions about your life in the same window. The window is a small web page (pywebview); without
a web engine it falls back to a plain Tk window.

    python app.py                         # the window
    python app.py EXPORTS --out my.html   # no window: the same as lifekeeper.py

.github/workflows/release.yml builds this into a double-click app for Windows and Mac. Nothing is sent anywhere unless you choose Google Gemini for answers.
"""
import json
import sys
import threading
import webbrowser
from pathlib import Path

try:  # installed with pip: part of the lifekeeper package
    from . import lifekeeper
except ImportError:  # run as a script from this folder
    import lifekeeper


def page_path(folder):
    """The page goes next to the exports folder, never inside it: the originals stay untouched."""
    for place in (Path(folder).parent, Path.home() / "Documents", Path.home()):
        try:
            test = place / ".lifekeeper-write-test"
            test.write_text("", encoding="utf-8")
            test.unlink()
            return place / "my-life.html"
        except OSError:
            continue
    raise OSError("There's nowhere to save the page. Try a folder you can write to.")


def make_page(folder, name):
    life = lifekeeper.build(folder, [name] if name.strip() else [])
    page = lifekeeper.render(life, "My life at a glance")
    if page is None:
        raise ValueError("Nothing with a date was found in that folder. Check that it holds your exports "
                         "(the guide is in docs/download-your-data).")
    out = page_path(folder)
    out.write_text(page, encoding="utf-8")
    return out, life


def tk_window():  # the plain window, for computers without a web engine
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    try:
        from . import ask
    except ImportError:
        import ask

    root = tk.Tk()
    root.title("Lifekeeper")
    try:  # the tree rings in the title bar and taskbar
        try:
            from . import icon_data
        except ImportError:
            import icon_data
        root.iconphoto(True, tk.PhotoImage(data="".join(icon_data.PNG)))
    except Exception:  # an icon is never worth failing over
        pass
    root.geometry("640x760")
    root.minsize(560, 640)
    base = ("Segoe UI", 12) if sys.platform == "win32" else ("Helvetica", 14)
    root.option_add("*Font", base)
    pad = {"padx": 24, "anchor": "w"}
    state = {"folder": None, "records": None}

    tk.Label(root, text="Your life on one page", font=(base[0], base[1] + 8, "bold")).pack(pady=(18, 2), **pad)
    tk.Label(root, text="Put your exports in one folder (zips can stay zipped). Making the page sends nothing anywhere.",
             wraplength=580, justify="left", fg="#555").pack(**pad)

    tk.Label(root, text="1. The folder with your exports").pack(pady=(14, 4), **pad)
    row = tk.Frame(root)
    row.pack(fill="x", padx=24)
    chosen = tk.Label(row, text="not chosen yet", fg="#777", anchor="w")

    def choose():
        folder = filedialog.askdirectory(title="Choose the folder with your exports")
        if folder:
            state["folder"], state["records"] = folder, None
            chosen.config(text=folder, fg="#1d1d1f")
            make.config(state="normal")
            ask_button.config(state="disabled")

    tk.Button(row, text="Choose…", command=choose, width=10).pack(side="left")
    chosen.pack(side="left", padx=10, fill="x", expand=True)

    tk.Label(root, text="2. Your name as it appears in your chats (you can leave it empty)").pack(pady=(12, 4), **pad)
    name = tk.Entry(root, width=40)
    name.pack(**pad)

    status = tk.Label(root, text="", wraplength=580, justify="left", fg="#555")
    progress = ttk.Progressbar(root, mode="indeterminate", length=580)

    def finished(result):
        progress.stop()
        progress.pack_forget()
        make.config(state="normal")
        if isinstance(result, Exception):
            status.config(text="")
            messagebox.showerror("Lifekeeper", str(result))
            return
        out, life = result
        state["records"] = ask.records(life)
        ask_button.config(state="normal")
        status.config(text=f"Done. Your page is saved as {out}. What was read is listed at the end of the page.")
        webbrowser.open(out.as_uri())

    def work(folder, who):
        try:
            result = make_page(folder, who)
        except Exception as error:  # shown to the person in plain words, not as a crash
            result = error
        root.after(0, finished, result)

    def start():
        if not state["folder"]:
            return
        make.config(state="disabled")
        status.config(text="Reading your exports… Big exports can take a few minutes.")
        progress.pack(pady=(8, 0), **pad)
        progress.start(12)
        threading.Thread(target=work, args=(state["folder"], name.get()), daemon=True).start()

    make = tk.Button(root, text="3. Make my page", command=start, state="disabled", width=18)
    make.pack(pady=(14, 0), **pad)
    status.pack(pady=(8, 0), **pad)

    # ---------- ask ----------
    ttk.Separator(root).pack(fill="x", padx=24, pady=(14, 0))
    tk.Label(root, text="4. Ask a question about your life (after the page is made)").pack(pady=(12, 4), **pad)
    question = tk.Entry(root)
    question.pack(fill="x", padx=24)

    WAYS = ["Show my records (no AI, nothing leaves this computer)",
            "Answer with a model on this computer (Ollama)",
            "Answer with Google Gemini (sends matching records to Google)"]
    way = ttk.Combobox(root, values=WAYS, state="readonly")
    way.current(0)
    way.pack(fill="x", padx=24, pady=(8, 0))
    extra_label = tk.Label(root, text="", fg="#555")
    extra = tk.Entry(root, width=44)

    def way_changed(_event=None):
        extra_label.pack_forget()
        extra.pack_forget()
        extra.delete(0, "end")
        if way.current() == 1:
            extra_label.config(text="The model's name in Ollama, for example gemma3")
            extra.config(show="")
        elif way.current() == 2:
            extra_label.config(text="Your Gemini API key (it isn't saved)")
            extra.config(show="•")
        if way.current():
            extra_label.pack(pady=(6, 2), before=ask_button, **pad)
            extra.pack(before=ask_button, **pad)

    way.bind("<<ComboboxSelected>>", way_changed)

    def answered(text):
        ask_button.config(state="normal")
        shown.config(state="normal")
        shown.delete("1.0", "end")
        shown.insert("1.0", text)
        shown.config(state="disabled")

    def think(found, asked, chosen, value):
        write = None
        if chosen == 1:
            write = lambda system, prompt: ask.ollama(system, prompt, value)  # noqa: E731
        elif chosen == 2:
            write = lambda system, prompt: ask.gemini(system, prompt, value)  # noqa: E731
        try:
            text = ask.answer(found, asked, write)
        except Exception as error:  # a wrong key, no connection, Ollama not running: said in plain words
            text = str(error)
        root.after(0, answered, text)

    def ask_now(_event=None):
        asked, value = question.get().strip(), extra.get().strip()
        if not state["records"] or not asked or str(ask_button["state"]) == "disabled":
            return
        if way.current() and not value:
            answered("Type the model's name first." if way.current() == 1 else "Paste your Gemini API key first. A free key: aistudio.google.com/apikey")
            return
        ask_button.config(state="disabled")
        answered("Looking through your records…")
        ask_button.config(state="disabled")
        threading.Thread(target=think, args=(state["records"], asked, way.current(), value), daemon=True).start()

    ask_button = tk.Button(root, text="Ask", command=ask_now, state="disabled", width=18)
    ask_button.pack(pady=(10, 0), **pad)
    question.bind("<Return>", ask_now)
    shown = scrolledtext.ScrolledText(root, height=9, wrap="word", state="disabled", font=(base[0], base[1] - 1))
    shown.pack(fill="both", expand=True, padx=24, pady=(10, 18))
    root.mainloop()


class FacesApi:
    """The faces add-on, for the window. Without it, the window says how to add it."""

    def _faces(self):
        try:
            from . import faces
        except ImportError:
            import faces
        return faces

    def faces_known(self, folder):
        return lifekeeper.faces_file(folder).is_file()

    def faces_scan(self, folder, name):
        try:
            faces = self._faces()
            report = lambda text: self.window.evaluate_js(f"facesProgress({json.dumps(text)})")  # noqa: E731
            photos, found = faces.scan(folder, [name] if (name or "").strip() else [], progress=report)
            return {"photos": photos, "faces": found}
        except Exception as error:
            return {"error": str(error)}

    def faces_people(self, folder):
        import base64
        try:
            faces = self._faces()
            groups = faces.people(folder)[:60]
            pictures = faces.crops(folder, [face for group in groups for face in group["faces"][:6]])
            return {"groups": [{"person": group["person"], "name": group["name"], "photos": group["photos"],
                                "faces": ["data:image/jpeg;base64," + base64.b64encode(pictures[face]).decode()
                                          for face in group["faces"][:6] if face in pictures]} for group in groups]}
        except Exception as error:
            return {"error": str(error)}

    def faces_name(self, folder, person, name):
        return self._faces().name(folder, person, name or "")

    def faces_hide(self, folder, person):
        return self._faces().hide(folder, person)


class Api(FacesApi):
    """What the window's page can ask Python to do. Each call runs in its own thread, so the window stays responsive."""

    def __init__(self):
        self.window, self.out, self.records = None, None, None

    def choose_folder(self):
        import webview
        chosen = self.window.create_file_dialog(webview.FileDialog.FOLDER)
        return chosen[0] if chosen else None

    def make_page(self, folder, name):
        try:
            out, life = make_page(folder, name or "")
        except Exception as error:  # said in plain words in the window, not as a crash
            return {"error": str(error)}
        try:
            from . import ask
        except ImportError:
            import ask
        self.out, self.records = out, ask.records(life)
        webbrowser.open(out.as_uri())
        return {"out": str(out)}

    def open_page(self):
        if self.out:
            webbrowser.open(self.out.as_uri())

    def ask(self, question, mode, value):
        try:
            from . import ask
        except ImportError:
            import ask
        write = None
        if mode == "ollama":
            write = lambda system, prompt: ask.ollama(system, prompt, value)  # noqa: E731
        elif mode == "gemini":
            write = lambda system, prompt: ask.gemini(system, prompt, value)  # noqa: E731
        try:
            return {"text": ask.answer(self.records or [], question, write)}
        except Exception as error:  # a wrong key, Ollama not running, no connection
            return {"error": str(error)}


def web_window():
    """The window as a small web page in a native window: the same look as the page it makes."""
    import webview
    try:
        from . import webui
    except ImportError:
        import webui
    api = Api()
    api.window = webview.create_window("Lifekeeper", html=webui.PAGE, js_api=api, width=700, height=880,
                                       min_size=(560, 640))
    webview.start(windows_icon)


def windows_icon():
    """On Windows the window shows the program's icon, which is Python's when run as a script or installed with pip.
    Put the tree rings there instead. Anywhere else, or if anything goes wrong, nothing happens."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        import time
        icon = Path(__file__).with_name("icon.ico")
        if not icon.is_file():
            return
        user32 = ctypes.windll.user32
        for _ in range(50):  # the window appears a moment after start
            hwnd = user32.FindWindowW(None, "Lifekeeper")
            if hwnd:
                break
            time.sleep(0.1)
        for size, which in ((16, 0), (32, 1)):  # small and big icons (WM_SETICON = 0x80)
            handle = user32.LoadImageW(None, str(icon), 1, size, size, 0x10)  # IMAGE_ICON, LR_LOADFROMFILE
            if handle:
                user32.SendMessageW(hwnd, 0x80, which, handle)
    except Exception:
        pass


def window():
    try:
        web_window()
    except Exception:  # no web engine here (pywebview or WebView2 missing): the plain window still works
        tk_window()


def main():
    if len(sys.argv) > 1:  # with arguments it's the command line, exactly like lifekeeper.py
        lifekeeper.main()
    else:
        window()


if __name__ == "__main__":
    main()
