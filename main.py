#!/usr/bin/env python3

"""
A simple YouTube video downloader.
"""

import certifi
import customtkinter
import os
import platform
import re
import ssl
import threading
import tkinter
import yt_dlp

from tkinter import filedialog as tk_filedialog
from PIL import Image

PROGRESS_UI_INTERVAL_MS = 100  # UI refresh interval (ms).
APP_TITLE = "YT Downloader"

# Check if the current system is macOS and modify SSL context if true.
if platform.system() == "Darwin":
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
        print("SSL verification disabled on macOS")
    except Exception as e:
        print("Could not disable SSL verification:", e)


def has_ffmpeg():
    """
    Return True if ffmpeg is available in PATH.
    """
    from shutil import which
    found = which("ffmpeg")

    if found is None:
        return False

    return True


def seconds_to_mmss(total_seconds):
    """
    Convert seconds to 'MM:SS'.
    """
    if total_seconds is None:
        return "00:00"

    minutes = int(total_seconds) // 60
    seconds = int(total_seconds) % 60

    return f"{minutes:02d}:{seconds:02d}"


def format_upload_date(yyyymmdd):
    """
    Convert YYYYMMDD to 'YYYY/MM/DD' or 'unknown'.
    """
    if yyyymmdd is None:
        return "unknown"

    s = str(yyyymmdd)

    if len(s) != 8:
        return "unknown"

    return f"{s[0:4]}/{s[4:6]}/{s[6:8]}"


def looks_like_url(s):
    """
    Return True if string looks like an HTTP/HTTPS URL.
    """
    if s is None:
        return False

    return bool(re.match(r'https?://', s.strip()))


# Shared dict for current download progress (value + label text).
progress_state = {"value": 0.0, "text": "0%"}

# Show "Download in progress..." only once per download.
shown_progress_msg = False


def set_progress(mapped_percent_float):
    """
    Update shared progress state with clamped percent.
    """
    if mapped_percent_float < 0.0:
        mapped_percent_float = 0.0

    if mapped_percent_float > 100.0:
        mapped_percent_float = 100.0

    progress_state["value"] = mapped_percent_float / 100.0
    progress_state["text"] = f"{int(mapped_percent_float)}%"


def yt_progress_hook(d):
    """
    Update progress state from yt-dlp status dict.
    """
    try:
        status = d.get("status")

        if status == "downloading":
            downloaded = d.get("downloaded_bytes")
            total = d.get("total_bytes")

            if downloaded is None:
                downloaded = 0
            if total is None:
                total = d.get("total_bytes_estimate")

            if total:
                percent = downloaded * 100.0 / total

                # Show the message once when progress starts.
                global shown_progress_msg

                if percent > 0 and not shown_progress_msg:
                    shown_progress_msg = True
                    ui_set_message("Download in progress...")

                info = d.get("info_dict")

                if info and info.get("vcodec") != "none":
                    mapped = percent * 0.8
                else:
                    mapped = 80.0 + percent * 0.19

                if mapped > 99.0:
                    mapped = 99.0

                set_progress(mapped)

        if status == "postprocessing" or status == "finished":
            set_progress(100.0)

    except Exception:
        pass


def select_format_string(file_format, quality_choice):
    """
    Return yt-dlp format string based on format and quality.
    """
    if file_format == "MP3":
        return "bestaudio/best"

    v_h264 = "[vcodec^=avc1]"
    a_aac = "[acodec^=mp4a]"

    if quality_choice == "Highest":
        return (
            "bestvideo[ext=mp4]" + v_h264 + "[height<=1080]+bestaudio[ext=m4a]" + a_aac + "/" +
            "best[ext=mp4]" + v_h264 + "[height<=1080][acodec!=none]/" +
            "bestvideo+bestaudio/best"
        )

    try:
        height = int(quality_choice.replace("p", ""))
    except Exception:
        return (
            "bestvideo[ext=mp4]" + v_h264 + "[height<=1080]+bestaudio[ext=m4a]" + a_aac + "/" +
            "best[ext=mp4]" + v_h264 + "[height<=1080][acodec!=none]/" +
            "bestvideo+bestaudio/best"
        )

    if height <= 1080:
        return (
            "bestvideo[ext=mp4]" + v_h264 + f"[height={height}]+bestaudio[ext=m4a]" + a_aac + "/" +
            "best[ext=mp4]" + v_h264 + f"[height={height}][acodec!=none]/" +
            "bestvideo[ext=mp4]" + v_h264 + "+bestaudio[ext=m4a]" + a_aac + "/" +
            "best[ext=mp4]" + v_h264 + "[acodec!=none]/" +
            "bestvideo+bestaudio/best"
        )

    return f"bestvideo[height={height}]+bestaudio/best"


def build_common_ydl_opts():
    """
    Return common yt-dlp options.
    """
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ignoreerrors": True,
        "socket_timeout": 15,
        "progress_hooks": [yt_progress_hook],
        "cacertfile": certifi.where(),
        "overwrites": True,
        "nopart": True,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 3,
    }


def build_ydl_opts_for_mp3(folder, prefix):
    """
    Return yt-dlp options for MP3 download.
    """
    opts = build_common_ydl_opts()
    opts.update({
        "outtmpl": os.path.join(folder, f"{prefix}%(title).200B.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",
            }
        ],
    })

    return opts


def build_ydl_opts_for_mp4(folder, prefix, format_string):
    """
    Return yt-dlp options for MP4 download.
    """
    opts = build_common_ydl_opts()
    opts.update({
        "outtmpl": os.path.join(folder, f"{prefix}%(title).200B.%(ext)s"),
        "merge_output_format": "mp4",
        "format": format_string,
    })

    return opts


def ui_set_message(text, color=None):
    """
    Update message label safely from any thread.
    """
    def _apply():
        if color is None:
            message_label.configure(text=text, text_color=default_text_color)
        else:
            message_label.configure(text=text, text_color=color)

    app.after(0, _apply)


def ui_set_info_labels(title, author, duration, pubdate, views):
    """
    Update info labels safely from any thread.
    """
    def _apply():
        title_label.configure(text=title)
        author_label.configure(text=author)
        duration_label.configure(text=duration)
        publish_date_label.configure(text=pubdate)
        views_label.configure(text=views)

    app.after(0, _apply)


def ui_enable_download_button(enable):
    """
    Enable or disable the DOWNLOAD button safely.
    """
    def _apply():
        if enable:
            download_button.configure(state="normal")
        else:
            download_button.configure(state="disabled")

    app.after(0, _apply)


def fetch_info_worker(video_url):
    """
    Fetch video metadata in a worker thread.
    """
    try:
        ui_set_message("Fetching video info...")
        ui_enable_download_button(False)

        ydl_opts = build_common_ydl_opts()
        ydl_opts.update({"skip_download": True, "simulate": True})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        if not info:
            raise Exception("Unable to extract info")

        title_str = f"Title: {info.get('title', 'unknown')}"
        author_str = f"Author: {info.get('uploader', 'unknown')}"
        duration_str = f"Duration: {seconds_to_mmss(info.get('duration'))}"
        pubdate_str = f"Publish date: {format_upload_date(info.get('upload_date'))}"

        views = info.get("view_count")

        if views is None:
            views_str = "Views: unknown"
        else:
            views_str = f"Views: {views}"

        ui_set_info_labels(title_str, author_str, duration_str, pubdate_str, views_str)
        ui_set_message("Video info loaded!", color="green")
        ui_enable_download_button(True)

    except SystemExit:
        pass
    except Exception as e:
        ui_set_info_labels("Title: none", "Author: none", "Duration: none", "Publish date: none", "Views: none")
        ui_set_message("Error fetching info", color="red")
        print(e)
        ui_enable_download_button(False)


def get_video_infos(event=None):
    """
    Launch metadata fetch if URL is valid.
    """
    video_url = url_entry.get().strip()

    if not looks_like_url(video_url):
        return

    t = threading.Thread(target=fetch_info_worker, args=(video_url,))
    t.daemon = True
    t.start()


def on_format_change(choice):
    """
    Enables or disables the quality menu based on the selected file format.
    """
    if choice == "MP3":
        quality_menu.configure(state="disabled")
    else:
        quality_menu.configure(state="normal")


def download_worker(video_url, download_folder, file_format, quality):
    """
    Run download and post-processing in background.
    """
    try:
        if file_format == "MP4":
            fmt = select_format_string(file_format, quality)
            ydl_opts = build_ydl_opts_for_mp4(download_folder, "Video - ", fmt)
        else:
            ydl_opts = build_ydl_opts_for_mp3(download_folder, "Audio - ")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        ui_set_message("Download complete!", color="green")
        set_progress(100.0)

    except yt_dlp.utils.DownloadError as e:
        ui_set_message(str(e), color="red")
    except SystemExit:
        ui_set_message("A download error occurred.", color="red")
    except Exception as e:
        ui_set_message("An unexpected error occurred, please try again later.", color="red")
        print(e)
    finally:
        ui_enable_download_button(True)


def download():
    """
    Initiates the download process for the YouTube video or audio based on user inputs.
    """
    try:
        video_url = url_entry.get()

        if video_url is None or not video_url.strip():
            raise ValueError("The URL field is empty, please enter a valid YouTube video URL.")
        
        if not looks_like_url(video_url):
            raise ValueError("Invalid URL, please enter a valid YouTube video URL.")

        download_folder = folder_var.get()

        if download_folder is None or download_folder.strip() == "":
            raise ValueError("Please choose a destination folder.")

        file_format = file_format_menu.get()
        quality = quality_menu.get()

        set_progress(0.0)
        progress_bar.set(0.0)
        percentage_label.configure(text="0%")
        ui_set_message("Starting download...")
        app.update_idletasks()

        # Reset the one-shot progress message flag.
        global shown_progress_msg
        shown_progress_msg = False

        ui_enable_download_button(False)

        needs_ffmpeg = (file_format == "MP3") or (file_format == "MP4")

        if needs_ffmpeg and not has_ffmpeg():
            ui_set_message("ffmpeg is required (not detected). Please install it and try again.", color="red")
            ui_enable_download_button(True)
            return

        t = threading.Thread(target=download_worker, args=(video_url, download_folder, file_format, quality))
        t.daemon = True
        t.start()

    except ValueError as e:
        ui_set_message(str(e), color="red")
        ui_enable_download_button(False)
    except Exception as e:
        ui_set_message("An unexpected error occurred, please try again later.", color="red")
        print(e)
        ui_enable_download_button(False)


def reset_infos(event=None):
    """
    Resets the displayed video information to default values.
    """
    title_label.configure(text="Title: ")
    author_label.configure(text="Author: ")
    duration_label.configure(text="Duration: ")
    publish_date_label.configure(text="Publish date: ")
    views_label.configure(text="Views: ")


def reset_progress(event=None):
    """
    Resets the progress bar and percentage label to their default state.
    """
    set_progress(0.0)
    progress_bar.set(0.0)
    percentage_label.configure(text="0%")
    message_label.configure(text=folder_var.get(), text_color=default_text_color)


def change_mode():
    """
    Changes the appearance mode based on the switch state.
    """
    if mode_switch.get() == 1:
        customtkinter.set_appearance_mode("dark")
        mode_switch.configure(text="Light mode")
    else:
        customtkinter.set_appearance_mode("light")
        mode_switch.configure(text="Dark mode")


def get_default_download_path():
    """
    Returns the default download path based on the operating system.
    """
    system_name = platform.system()
    home = os.path.expanduser("~")

    if system_name == "Windows":
        base = os.environ.get("USERPROFILE")

        if base is None:
            base = home

        return os.path.join(base, "Downloads")

    if system_name == "Darwin":
        return os.path.join(home, "Downloads")

    return os.path.join(home, "Downloads")


def browse_folder():
    """
    Opens a dialog to select a folder and updates the folder_var with the selected path.
    """
    folder_selected = tk_filedialog.askdirectory()

    if folder_selected:
        folder_var.set(folder_selected)

    message_label.configure(text=folder_var.get(), text_color=default_text_color)


# Set the appearance mode and default color theme.
customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("blue")

# Create the main application window.
app = customtkinter.CTk()
app.resizable(False, False)

# Set the application window title.
app.title(APP_TITLE)

# Set the base directory for the application.
base_dir = os.path.dirname(__file__)

# Set the application icon based on the operating system.
if platform.system() == "Windows":
    ico_path = os.path.join(base_dir, "resources/images/yt_downloader_icon.ico")

    if os.path.exists(ico_path):
        app.iconbitmap(ico_path)
else:
    png_icon_path = os.path.join(base_dir, "resources/images/yt_downloader_icon.png")

    if os.path.exists(png_icon_path):
        icon = tkinter.PhotoImage(file=png_icon_path)
        app.iconphoto(False, icon)

# Add the logo to the application window.
light_logo_path = os.path.join(base_dir, "resources/images/yt_downloader_logo_light.png")
dark_logo_path = os.path.join(base_dir, "resources/images/yt_downloader_logo_dark.png")

if os.path.exists(light_logo_path) and os.path.exists(dark_logo_path):
    logo_img = customtkinter.CTkImage(light_image=Image.open(light_logo_path), dark_image=Image.open(dark_logo_path), size=(250, 25))
else:
    logo_img = None

if logo_img is not None:
    logo_label = customtkinter.CTkLabel(app, image=logo_img, text="")
else:
    logo_label = customtkinter.CTkLabel(app, text=APP_TITLE)

logo_label.pack(padx=0, pady=20)

# Add instructions label.
instructions = customtkinter.CTkLabel(app, text="Paste the YouTube video link you want to download in the field below.")
instructions.pack()

# Add URL entry field.
url_entry = customtkinter.CTkEntry(app, width=600, height=35)
url_entry.pack(padx=20, pady=0)

# Debounce state.
info_job_id = None


def schedule_get_video_infos(delay_ms=600):
    """
    Debounce metadata fetching by delay_ms.
    """
    global info_job_id

    if info_job_id is not None:
        try:
            app.after_cancel(info_job_id)
        except Exception:
            pass

        info_job_id = None

    info_job_id = app.after(delay_ms, get_video_infos)


def on_url_key_release(event=None):
    """
    Reset UI and schedule metadata fetching on input.
    """
    reset_infos()
    reset_progress()
    ui_enable_download_button(False)
    current = url_entry.get()

    if looks_like_url(current):
        schedule_get_video_infos()


# Add a frame to display video information.
infos_frame = customtkinter.CTkFrame(app)
infos_frame.pack(fill="x", padx=20, pady=(20, 0))

title_label = customtkinter.CTkLabel(infos_frame, text="Title: ")
title_label.grid(row=0, column=0, sticky="w", padx=5)

author_label = customtkinter.CTkLabel(infos_frame, text="Author: ")
author_label.grid(row=1, column=0, sticky="w", padx=5)

duration_label = customtkinter.CTkLabel(infos_frame, text="Duration: ")
duration_label.grid(row=2, column=0, sticky="w", padx=5)

publish_date_label = customtkinter.CTkLabel(infos_frame, text="Publish date: ")
publish_date_label.grid(row=3, column=0, sticky="w", padx=5)

views_label = customtkinter.CTkLabel(infos_frame, text="Views: ")
views_label.grid(row=4, column=0, sticky="w", padx=5)

# Add a frame for download options.
options_frame = customtkinter.CTkFrame(app, fg_color=app.cget("fg_color"))
options_frame.pack(fill="x", padx=20, pady=20)

options_frame.grid_columnconfigure(0, weight=0)
options_frame.grid_columnconfigure(1, weight=0)
options_frame.grid_columnconfigure(2, weight=1)

file_format_menu = customtkinter.CTkOptionMenu(options_frame, width=150, values=["MP3", "MP4"], command=on_format_change)
file_format_menu.set("MP4")
file_format_menu.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

quality_menu = customtkinter.CTkOptionMenu(options_frame, width=150, values=["Highest", "1080p", "720p", "480p", "360p", "240p", "144p"])
quality_menu.set("Highest")
quality_menu.grid(row=0, column=1, sticky="nsew")

download_button = customtkinter.CTkButton(options_frame, width=200, text="DOWNLOAD", cursor="hand2", command=download, state="disabled")
download_button.grid(row=0, column=2, sticky="e")

# Add progress bar.
progress_bar = customtkinter.CTkProgressBar(app, width=600)
progress_bar.set(0.0)
progress_bar.pack()

# Add percentage label.
percentage_label = customtkinter.CTkLabel(app, text="0%")
percentage_label.pack()

# Add a frame for displaying status messages.
message_frame = customtkinter.CTkFrame(app, width=600, height=35)
message_frame.pack_propagate(False)
message_frame.pack(fill="x", padx=20, pady=(0, 20))

message_label = customtkinter.CTkLabel(message_frame, text="")
default_text_color = message_label.cget("text_color")
message_label.pack(expand=True, fill="both")

# Add a bottom frame for mode switch and folder selection.
bottom_frame = customtkinter.CTkFrame(app, fg_color=app.cget("fg_color"))
bottom_frame.pack(fill="x", padx=20, pady=(0, 20))

mode_switch = customtkinter.CTkSwitch(bottom_frame, text="Dark mode", command=change_mode)
mode_switch.pack(side="left")

folder_var = tkinter.StringVar()
folder_button = customtkinter.CTkButton(bottom_frame, width=200, text="DESTINATION  FOLDER", command=browse_folder)
folder_button.pack(side="right")

# Set default download folder path and display it in the message label.
folder_var.set(os.path.join(os.path.expanduser("~"), "Downloads"))

if platform.system() == "Windows":
    user_profile = os.environ.get("USERPROFILE")

    if user_profile is None:
        user_profile = os.path.expanduser("~")

    folder_var.set(os.path.join(user_profile, "Downloads"))

if platform.system() == "Darwin":
    folder_var.set(os.path.join(os.path.expanduser("~"), "Downloads"))

message_label.configure(text=folder_var.get(), text_color=default_text_color)

# Bind after widgets exist.
url_entry.bind("<KeyRelease>", on_url_key_release)


def ui_progress_loop():
    """
    Pull shared progress and refresh UI periodically.
    """
    try:
        percentage_label.configure(text=progress_state["text"])
        progress_bar.set(progress_state["value"])
    finally:
        app.after(PROGRESS_UI_INTERVAL_MS, ui_progress_loop)


# Start the application's main loop.
ui_progress_loop()
app.mainloop()
