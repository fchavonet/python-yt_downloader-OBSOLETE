#!/usr/bin/env python3

"""
A simple YouTube video downloader.
"""

import customtkinter
import os
import PIL
import platform
import pytube
import ssl
import tkinter

# Check if the current system is macOS and modify SSL context if true.
if platform.system() == "Darwin":
    ssl._create_default_https_context = ssl._create_unverified_context
    print("Running on macOS: SSL verification is disabled.")
else:
    print("Running on Linux or Windows: SSL verification is enabled.")


def on_format_change(choice):
    """
    Enables or disables the quality menu based on the selected file format.

    Args:
        choice: the selected file format (MP3 or MP4).
    """
    if choice == "MP3":
        quality_menu.configure(state="disabled")
    else:
        quality_menu.configure(state="normal")


def download():
    """
    Initiates the download process for the YouTube video or audio based on user inputs.

    Raises:
        ValueError: if the URL field is empty.
        pytube.exceptions.RegexMatchError: if the URL format is invalid.
        pytube.exceptions.VideoUnavailable: if the video is not available.
        pytube.exceptions.PytubeError: if a general Pytube error occurs.
        Exception: for any other unexpected errors.
    """
    try:
        video_url = url_entry.get()
        if not video_url.strip():
            raise ValueError("The URL field is empty, please enter a valid YouTube video URL.")

        download_folder = folder_var.get()
        file_format = file_format_menu.get()
        quality = quality_menu.get()

        reset_progress()
        yt_object = pytube.YouTube(video_url, on_progress_callback=on_progress)

        # Download video in MP4 format.
        if file_format == "MP4":
            if quality == "Highest":
                video = yt_object.streams.get_highest_resolution()
            else:
                video = yt_object.streams.filter(res=quality, file_extension="mp4").first()

            if not video:
                raise pytube.exceptions.PytubeError("The requested quality is not available.")

            video.download(output_path=download_folder, filename_prefix=f"Video - ")

        # Download audio in MP3 format.
        elif file_format == "MP3":
            audio = yt_object.streams.filter(only_audio=True).first()
            audio_file = audio.download(output_path=download_folder, filename_prefix=f"Audio - ")

            # Convert to .mp3 extension
            base, ext = os.path.splitext(audio_file)
            new_file = base + ".mp3"

            # Overwrite the existing file if it exists
            if os.path.exists(new_file):
                os.remove(new_file)

            os.rename(audio_file, new_file)

        message_label.configure(text="Download complete!", text_color="green")

    except pytube.exceptions.RegexMatchError:
        message_label.configure(text="Invalid URL, please enter a valid YouTube video URL.", text_color="red")
    except pytube.exceptions.VideoUnavailable:
        message_label.configure(text="Video not available, may be private or deleted.", text_color="red")
    except pytube.exceptions.PytubeError as e:
        message_label.configure(text=str(e), text_color="red")
    except ValueError as e:
        message_label.configure(text=str(e), text_color="red")
    except Exception as e:
        message_label.configure(text="An unexpected error occurred, please try again later.", text_color="red")
        print(e)


def on_progress(stream, chunk, bytes_remaining):
    """
    Updates the progress bar and percentage label during the download process.

    Args:
        stream: the stream object being downloaded.
        chunk: the data chunk downloaded.
        bytes_remaining: the number of bytes remaining to be downloaded.
    """
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining

    percentage_of_completion = bytes_downloaded / total_size * 100
    percentage = str(int(percentage_of_completion))

    percentage_label.configure(text=f"{percentage}%")
    percentage_label.update()

    progress_bar.set(float(percentage_of_completion) / 100)


def reset_progress(event=None):
    """
    Resets the progress bar and percentage label to 0.
    """
    progress_bar.set(0)
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
    if platform.system() == "Windows":
        return os.path.join(os.environ["USERPROFILE"], "Downloads")
    elif platform.system() == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Downloads")
    else:
        print("ERROR")


def browse_folder():
    """
    Opens a dialog to select a folder and updates the folder_var with the selected path.
    """
    folder_selected = tkinter.filedialog.askdirectory()
    if folder_selected:
        folder_var.set(folder_selected)
    message_label.configure(text=folder_var.get(), text_color=default_text_color)


# Set the appearance mode and default color theme.
customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("blue")

# Create the main application window.
app = customtkinter.CTk()
app.resizable(False, False)
app.iconbitmap("./yt_downloader_icon.ico")
app.title("YT Downloader")

# Add the logo to the application window.
logo = customtkinter.CTkImage(light_image=PIL.Image.open("yt_downloader_logo_light.png"), dark_image=PIL.Image.open("yt_downloader_logo_dark.png"), size=(250, 25))
logo_label = customtkinter.CTkLabel(app, image=logo, text="")
logo_label.pack(padx=0, pady=20)

# Add instructions label.
instructions = customtkinter.CTkLabel(app, text="Paste the YouTube video link you want to download in the field below.")
instructions.pack()

# Add URL entry field.
url_entry = customtkinter.CTkEntry(app, width=600, height=35)
url_entry.bind("<KeyRelease>", reset_progress)
url_entry.pack(padx=20, pady=0)

# Add a frame at the middle of the application window.
middle_frame = customtkinter.CTkFrame(app, fg_color=app.cget("fg_color"))
middle_frame.pack(fill="x", padx=20, pady=20)

middle_frame.grid_columnconfigure(0, weight=0)
middle_frame.grid_columnconfigure(1, weight=0)
middle_frame.grid_columnconfigure(2, weight=1)

# Add file format menu to the middle frame.
file_format_menu = customtkinter.CTkOptionMenu(middle_frame, width=150, values=["MP3", "MP4"], command=on_format_change)
file_format_menu.set("MP4")
file_format_menu.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

# Add quality menu to the middle frame.
quality_menu = customtkinter.CTkOptionMenu(middle_frame, width=150, values=["Highest", "1080p", "720p", "480p", "360p", "240p", "144p"])
quality_menu.set("Highest")
quality_menu.grid(row=0, column=1, sticky="nsew")

# Add download button inside the middle frame.
download_button = customtkinter.CTkButton(middle_frame, width=200, text="DOWNLOAD", cursor="hand2", command=download)
download_button.grid(row=0, column=2, sticky="e")

# Add progress bar.
progress_bar = customtkinter.CTkProgressBar(app, width=600)
progress_bar.set(0)
progress_bar.pack()

# Add percentage label.
percentage_label = customtkinter.CTkLabel(app, text="0%")
percentage_label.pack()

# Add message frame for displaying status messages.
message_frame = customtkinter.CTkFrame(app, width=600, height=35)
message_frame.pack_propagate(False)
message_frame.pack(fill="x", padx=20, pady=(0, 20))

# Add message label inside the message frame.
message_label = customtkinter.CTkLabel(message_frame, text="")
default_text_color = message_label.cget("text_color")
message_label.pack(expand=True, fill="both")

# Add a frame at the bottom of the application window.
bottom_frame = customtkinter.CTkFrame(app, fg_color=app.cget("fg_color"))
bottom_frame.pack(fill="x", padx=20, pady=(0, 20))

# Add mode switch for toggling between light and dark mode.
mode_switch = customtkinter.CTkSwitch(bottom_frame, text="Dark mode", command=change_mode)
mode_switch.pack(side="left")

# Add button to select destination folder.
folder_var = tkinter.StringVar()
folder_button = customtkinter.CTkButton(bottom_frame, width=200, text="DESTINATION  FOLDER", command=browse_folder)
folder_button.pack(side="right")

# Set default download folder path and display it in the message label.
folder_var.set(get_default_download_path())
message_label.configure(text=folder_var.get(), text_color=default_text_color)

# Start the application's main loop.
app.mainloop()
