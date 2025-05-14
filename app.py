# Modules
from tkinter import *
from tkinter import ttk, filedialog
from pytubefix import YouTube
from time import sleep
from threading import Thread

# The main app window
app = Tk()
app.iconbitmap("icon/icon.ico")
app.geometry("600x400")
app.resizable(False, False)
app.title("YouTube Downloader")
app.config(bg="#1e1e1e")

# Title
title = Label(
    app,
    text="YouTube Downloader",
    font=("Arial", 24, "bold"),
    bg="#1e1e1e",
    fg="#ff3333",
)
title.pack(pady=(20, 30))

# URL Entry
url = StringVar()
url_label = Label(
    app, text="Enter Video URL:", font=("Arial", 12), bg="#1e1e1e", fg="#ffffff"
)
url_label.pack(pady=(0, 10))
url_entry = Entry(
    app,
    width=50,
    font=("Arial", 12),
    bg="#2d2d2d",
    fg="#ffffff",
    insertbackground="#ffffff",
    textvariable=url,
)
url_entry.pack(pady=(0, 10))

# Progress Bar
progress_frame = Frame(app, bg="#1e1e1e")
progress_frame.pack(pady=(0, 10))
progress_frame.pack_forget()
style = ttk.Style()
style.theme_use("default")
style.configure(
    "Custom.Horizontal.TProgressbar",
    background="#40c057",
    troughcolor="#2d2d2d",
    thickness=20,
)
progress = ttk.Progressbar(
    progress_frame,
    length=400,
    mode="determinate",
    style="Custom.Horizontal.TProgressbar",
)
progress.pack(side=LEFT, padx=(0, 20))
progress_label = Label(
    progress_frame, text="0%", font=("Arial", 10), bg="#1e1e1e", fg="#ffffff"
)
progress_label.pack(side=LEFT)


# Function to update status
def update_status(message, color="#a0a0a0"):
    status.set(message)
    status_label.config(fg=color)


# Progress callback function
def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    progress["value"] = percentage
    progress_label.config(text=f"{percentage:.1f}%")
    app.update_idletasks()


# Function to reset progress
def reset_progress():
    progress_frame.pack_forget()
    progress["value"] = 0
    progress_label.config(text="0%")
    app.update_idletasks()


# Get download directory function
def get_download_directory():
    directory = filedialog.askdirectory(title="Choose Download Location")
    return directory if directory else None


# Download video function
def video_download():
    def download_thread():
        try:
            link = url.get()
            if not link:
                update_status("Error: Please enter a URL", "#ff3333")
                return
            reset_progress()
            progress_frame.pack(pady=(0, 10))
            directory = get_download_directory()
            if not directory:
                update_status("Download cancelled", "#ff3333")
                return
            update_status("Getting video information...", "#ffa500")
            app.update_idletasks()
            yt_object = YouTube(link)
            yt_object.register_on_progress_callback(on_progress)
            video = yt_object.streams.get_highest_resolution()
            if not video:
                update_status("Error: No suitable video stream found", "#ff3333")
                return
            url_label.configure(text=yt_object.title)
            update_status("Starting download...", "#ffa500")
            app.update_idletasks()
            video.download(directory)
            update_status("Download complete!", "#00ff00")
            sleep(1)
        except Exception as e:
            error_msg = str(e)
            if "regex_search" in error_msg:
                update_status("Error: Invalid YouTube URL", "#ff3333")
            elif "Connection" in error_msg:
                update_status(
                    "Error: Connection failed. Check your internet", "#ff3333"
                )
            else:
                update_status(f"Error: {error_msg}", "#ff3333")
        finally:
            reset_progress()
            url.set("")
            url_label.configure(text="Enter Video URL:")

    Thread(target=download_thread, daemon=True).start()


# Download audio function
def audio_download():
    def download_thread():
        try:
            link = url.get()
            if not link:
                update_status("Error: Please enter a URL", "#ff3333")
                return
            reset_progress()
            progress_frame.pack(pady=(0, 10))
            directory = get_download_directory()
            if not directory:
                update_status("Download cancelled", "#ff3333")
                return
            update_status("Getting audio information...", "#ffa500")
            app.update_idletasks()
            yt_object = YouTube(link)
            yt_object.register_on_progress_callback(on_progress)
            audio = yt_object.streams.filter(only_audio=True).first()
            if not audio:
                update_status("Error: No suitable audio stream found", "#ff3333")
                return
            url_label.configure(text=yt_object.title)
            update_status("Starting download...", "#ffa500")
            app.update_idletasks()
            audio.download(directory)
            update_status("Download complete!", "#00ff00")
            sleep(1)
        except Exception as e:
            error_msg = str(e)
            if "regex_search" in error_msg:
                update_status("Error: Invalid YouTube URL", "#ff3333")
            elif "Connection" in error_msg:
                update_status(
                    "Error: Connection failed. Check your internet", "#ff3333"
                )
            else:
                update_status(f"Error: {error_msg}", "#ff3333")
        finally:
            reset_progress()
            url.set("")
            url_label.configure(text="Enter Video URL:")

    Thread(target=download_thread, daemon=True).start()


# Download video Button
download_video_btn = Button(
    app,
    text="Download Video",
    font=("Arial", 12, "bold"),
    bg="#ff3333",
    fg="#ffffff",
    width=20,
    relief="flat",
    activebackground="#cc2929",
    activeforeground="#ffffff",
    command=video_download,
)
download_video_btn.pack(pady=(20, 10))

# Download audio Button
download_audio_btn = Button(
    app,
    text="Download Audio",
    font=("Arial", 12, "bold"),
    bg="#ff3333",
    fg="#ffffff",
    width=20,
    relief="flat",
    activebackground="#cc2929",
    activeforeground="#ffffff",
    command=audio_download,
)
download_audio_btn.pack(pady=(0, 20))

# Status Label
status = StringVar()
status.set("Ready to download")
status_label = Label(
    app, textvariable=status, font=("Arial", 10), bg="#1e1e1e", fg="#a0a0a0"
)
status_label.pack(pady=(10, 10))

# Run app
app.mainloop()
