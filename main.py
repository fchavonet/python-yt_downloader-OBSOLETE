#!/usr/bin/env python3

"""
A simple YouTube video downloader.
"""

import customtkinter
import PIL
import pytube


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


def download():
    """
    Downloads the highest resolution video from a YouTube URL.

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

        yt_object = pytube.YouTube(video_url, on_progress_callback=on_progress)
        video = yt_object.streams.get_highest_resolution()

        video.download()
        message_label.configure(text="Download complete!", text_color="green")

    except pytube.exceptions.RegexMatchError:
        message_label.configure(text="Invalid URL, please enter a valid YouTube video URL.", text_color="red")
    except pytube.exceptions.VideoUnavailable:
        message_label.configure(text="Video not available, may be private or deleted.", text_color="red")
    except pytube.exceptions.PytubeError as e:
        message_label.configure(text=f"An error occurred: {e}", text_color="red")
    except ValueError as e:
        message_label.configure(text=str(e), text_color="red")
    except Exception as e:
        message_label.configure(text="An unexpected error occurred, please try again later.", text_color="red")


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
    message_label.configure(text="")


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

# Add download button.
download_button = customtkinter.CTkButton(app, text="DOWNLOAD", cursor="hand2", command=download)
download_button.pack(padx=0, pady=20)

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
message_label.pack(expand=True, fill="both")

# Add mode switch for toggling between light and dark mode.
mode_switch = customtkinter.CTkSwitch(app, text="Dark mode", command=change_mode)
mode_switch.pack(padx=0, pady=(0, 20))

# Start the application's main loop.
app.mainloop()
