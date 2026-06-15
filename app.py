# Modules
from tkinter import *
from tkinter import ttk, filedialog
from pytubefix import YouTube
from threading import Thread
import os

# App window
app = Tk()
app.title("YT Downloader")
app.geometry("680x570")
app.resizable(False, False)
app.config(bg="#0f0f0f")

try:
    app.iconbitmap("icon/icon.ico")
except Exception:
    pass

# Colour & font tokens
BG = "#0f0f0f"
SURFACE = "#1a1a1a"
SURFACE2 = "#252525"
ACCENT = "#ff0000"
ACCENT2 = "#cc0000"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"
TEXT = "#ffffff"
SUBTEXT = "#a0a0a0"

FONT_H1 = ("Segoe UI", 22, "bold")
FONT_H2 = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SM = ("Segoe UI", 9)
FONT_MONO = ("Consolas", 10)

# State
url = StringVar()
status_var = StringVar(value="Paste a YouTube URL to get started")
mode_var = StringVar(value="video")
fetched_yt = None
video_streams = []
audio_streams = []


# Helpers
def set_status(msg, color=SUBTEXT):
    status_var.set(msg)
    status_label.config(fg=color)


def show_progress():
    progress_frame.pack(fill=X, padx=40, pady=(0, 6))


def hide_progress():
    progress_frame.pack_forget()
    progress_bar["value"] = 0
    pct_label.config(text="0 %")
    app.update_idletasks()


def on_progress(stream, chunk, bytes_remaining):
    total = stream.filesize
    done = total - bytes_remaining
    pct = (done / total) * 100
    progress_bar["value"] = pct
    pct_label.config(text=f"{pct:.0f} %")
    app.update_idletasks()


# Fetch streams
def fetch_streams():
    global fetched_yt, video_streams, audio_streams

    link = url.get().strip()
    if not link:
        set_status("Please enter a YouTube URL first.", ERROR)
        return

    def _fetch():
        global fetched_yt, video_streams, audio_streams
        app.after(0, lambda: set_status("Fetching video info…", WARNING))
        app.after(0, lambda: fetch_btn.config(state=DISABLED))

        try:
            yt = YouTube(link, on_progress_callback=on_progress)
            fetched_yt = yt

            # Progressive streams (video+audio combined)
            prog = yt.streams.filter(progressive=True).order_by("resolution").desc()
            # Adaptive video-only streams (higher resolutions like 1080p+)
            adapt = (
                yt.streams.filter(adaptive=True, only_video=True)
                .order_by("resolution")
                .desc()
            )

            seen_res = set()
            video_streams = []
            for s in prog:
                ext = s.mime_type.split("/")[1].upper()
                label = f"  {s.resolution:<8}  {ext:<5}  [video + audio]"
                if s.resolution not in seen_res:
                    video_streams.append((label, s))
                    seen_res.add(s.resolution)
            for s in adapt:
                ext = s.mime_type.split("/")[1].upper()
                label = f"  {s.resolution:<8}  {ext:<5}  [video only — no audio]"
                if s.resolution not in seen_res:
                    video_streams.append((label, s))
                    seen_res.add(s.resolution)

            # Audio streams sorted by bitrate descending
            audio_only = yt.streams.filter(only_audio=True).order_by("abr").desc()
            seen_abr = set()
            audio_streams = []
            for s in audio_only:
                ext = s.mime_type.split("/")[1].upper()
                abr = s.abr or "?"
                label = f"  {abr:<10}  {ext}"
                if abr not in seen_abr:
                    audio_streams.append((label, s))
                    seen_abr.add(abr)

            app.after(0, lambda: _populate_ui(yt.title))

        except Exception as e:
            err = str(e)
            msg = (
                "Invalid YouTube URL."
                if "regex" in err
                else (
                    "No internet connection."
                    if "Connection" in err
                    else f"Error: {err[:80]}"
                )
            )
            app.after(0, lambda: set_status(msg, ERROR))
        finally:
            app.after(0, lambda: fetch_btn.config(state=NORMAL))

    Thread(target=_fetch, daemon=True).start()


def _populate_ui(title):
    short = title[:72] + ("…" if len(title) > 72 else "")
    video_title_label.config(text=f"  🎬  {short}")
    info_frame.pack(fill=X, padx=0, pady=(0, 10))
    _refresh_quality_list()
    set_status("Select a quality and hit Download.", SUCCESS)


def _refresh_quality_list(*_):
    quality_listbox.delete(0, END)
    streams = video_streams if mode_var.get() == "video" else audio_streams
    for label, _ in streams:
        quality_listbox.insert(END, label)
    if streams:
        quality_listbox.selection_set(0)


# Download
def start_download():
    if fetched_yt is None:
        set_status("Fetch a video first.", ERROR)
        return

    sel = quality_listbox.curselection()
    if not sel:
        set_status("Select a quality first.", ERROR)
        return

    idx = sel[0]
    streams = video_streams if mode_var.get() == "video" else audio_streams
    _, stream = streams[idx]

    directory = filedialog.askdirectory(title="Choose save folder")
    if not directory:
        set_status("Cancelled.", SUBTEXT)
        return

    def _dl():
        app.after(0, lambda: download_btn.config(state=DISABLED))
        app.after(0, lambda: fetch_btn.config(state=DISABLED))
        app.after(0, show_progress)
        app.after(0, lambda: set_status("Downloading…", WARNING))

        try:
            out_path = stream.download(output_path=directory)

            # Rename audio to .mp3 for convenience
            if mode_var.get() == "audio" and not out_path.endswith(".mp3"):
                new_path = os.path.splitext(out_path)[0] + ".mp3"
                try:
                    os.rename(out_path, new_path)
                    out_path = new_path
                except OSError:
                    pass

            fname = os.path.basename(out_path)
            app.after(0, lambda: set_status(f"✔  Saved: {fname}", SUCCESS))

        except Exception as e:
            app.after(0, lambda: set_status(f"Error: {str(e)[:80]}", ERROR))
        finally:
            app.after(0, hide_progress)
            app.after(0, lambda: download_btn.config(state=NORMAL))
            app.after(0, lambda: fetch_btn.config(state=NORMAL))

    Thread(target=_dl, daemon=True).start()


# Reset
def reset_all():
    global fetched_yt, video_streams, audio_streams
    fetched_yt = None
    video_streams = []
    audio_streams = []
    url.set("")
    quality_listbox.delete(0, END)
    info_frame.pack_forget()
    hide_progress()
    set_status("Paste a YouTube URL to get started", SUBTEXT)


# UI — Header stripe
Frame(app, bg=ACCENT, height=4).pack(fill=X)

title_frame = Frame(app, bg=BG)
title_frame.pack(fill=X, padx=40, pady=(22, 18))
Label(title_frame, text="▶  YT Downloader", font=FONT_H1, bg=BG, fg=TEXT).pack(
    side=LEFT
)
Label(
    title_frame, text="All qualities · Video & Audio", font=FONT_SM, bg=BG, fg=SUBTEXT
).pack(side=LEFT, padx=(12, 0), pady=(8, 0))

# URL row
url_frame = Frame(app, bg=BG)
url_frame.pack(fill=X, padx=40, pady=(0, 12))

url_entry = Entry(
    url_frame,
    textvariable=url,
    font=FONT_BODY,
    bg=SURFACE2,
    fg=TEXT,
    insertbackground=TEXT,
    relief=FLAT,
    bd=0,
)
url_entry.pack(side=LEFT, fill=X, expand=True, ipady=9, ipadx=10)
url_entry.bind("<Return>", lambda e: fetch_streams())

Frame(url_frame, bg=BG, width=8).pack(side=LEFT)

fetch_btn = Button(
    url_frame,
    text="Fetch",
    font=FONT_H2,
    bg=ACCENT,
    fg=TEXT,
    activebackground=ACCENT2,
    activeforeground=TEXT,
    relief=FLAT,
    bd=0,
    padx=18,
    pady=9,
    cursor="hand2",
    command=fetch_streams,
)
fetch_btn.pack(side=LEFT)

Frame(url_frame, bg=BG, width=6).pack(side=LEFT)

Button(
    url_frame,
    text="✕",
    font=FONT_H2,
    bg=SURFACE2,
    fg=SUBTEXT,
    activebackground=SURFACE,
    activeforeground=TEXT,
    relief=FLAT,
    bd=0,
    padx=12,
    pady=9,
    cursor="hand2",
    command=reset_all,
).pack(side=LEFT)

# Video info strip (hidden until fetch)
info_frame = Frame(app, bg=SURFACE, pady=9)
video_title_label = Label(
    info_frame,
    text="",
    font=FONT_BODY,
    bg=SURFACE,
    fg=TEXT,
    anchor=W,
    wraplength=620,
    justify=LEFT,
)
video_title_label.pack(fill=X, padx=14)

# Mode selector
mode_frame = Frame(app, bg=BG)
mode_frame.pack(fill=X, padx=40, pady=(8, 4))

Label(mode_frame, text="Download as:", font=FONT_H2, bg=BG, fg=SUBTEXT).pack(
    side=LEFT, padx=(0, 14)
)

for lbl, val in (("🎬  Video", "video"), ("🎵  Audio (MP3)", "audio")):
    Radiobutton(
        mode_frame,
        text=lbl,
        variable=mode_var,
        value=val,
        font=FONT_BODY,
        bg=BG,
        fg=TEXT,
        selectcolor=BG,
        activebackground=BG,
        activeforeground=ACCENT,
        cursor="hand2",
        command=_refresh_quality_list,
    ).pack(side=LEFT, padx=(0, 22))

# Quality listbox
Label(app, text="Quality / Format", font=FONT_H2, bg=BG, fg=SUBTEXT).pack(
    anchor=W, padx=40, pady=(10, 4)
)

list_frame = Frame(app, bg=SURFACE2)
list_frame.pack(fill=X, padx=40)

sb = Scrollbar(list_frame, bg=SURFACE2, troughcolor=SURFACE2, relief=FLAT, bd=0)
sb.pack(side=RIGHT, fill=Y)

quality_listbox = Listbox(
    list_frame,
    font=FONT_MONO,
    bg=SURFACE2,
    fg=TEXT,
    selectbackground=ACCENT,
    selectforeground=TEXT,
    activestyle="none",
    relief=FLAT,
    bd=0,
    height=7,
    yscrollcommand=sb.set,
    highlightthickness=0,
)
quality_listbox.pack(fill=X, side=LEFT, expand=True)
sb.config(command=quality_listbox.yview)

# Progress bar (hidden by default)
progress_frame = Frame(app, bg=BG)

style = ttk.Style()
style.theme_use("default")
style.configure(
    "YT.Horizontal.TProgressbar",
    background=ACCENT,
    troughcolor=SURFACE2,
    thickness=5,
    borderwidth=0,
)

progress_bar = ttk.Progressbar(
    progress_frame,
    mode="determinate",
    style="YT.Horizontal.TProgressbar",
)
progress_bar.pack(side=LEFT, fill=X, expand=True)

pct_label = Label(progress_frame, text="0 %", font=FONT_SM, bg=BG, fg=SUBTEXT, width=5)
pct_label.pack(side=LEFT, padx=(10, 0))

# Download button
download_btn = Button(
    app,
    text="⬇  Download",
    font=("Segoe UI", 12, "bold"),
    bg=ACCENT,
    fg=TEXT,
    activebackground=ACCENT2,
    activeforeground=TEXT,
    relief=FLAT,
    bd=0,
    padx=34,
    pady=11,
    cursor="hand2",
    command=start_download,
)
download_btn.pack(pady=(18, 6))

# Status label
status_label = Label(app, textvariable=status_var, font=FONT_SM, bg=BG, fg=SUBTEXT)
status_label.pack(pady=(4, 10))

# Footer
Frame(app, bg=SURFACE2, height=1).pack(fill=X, side=BOTTOM)
Label(
    app,
    text="pytubefix  ·  threaded  ·  all resolutions",
    font=("Segoe UI", 8),
    bg=BG,
    fg="#333333",
).pack(side=BOTTOM, pady=4)

app.mainloop()
