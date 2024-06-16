#!/usr/bin/env python3

"""
A simple YouTube video downloader.
"""

import customtkinter
import pytube


def download():
    """
    Downloads the highest resolution video from a YouTube URL.

    Raises:
        Exception: if there is an error during the download process.
    """
    try:
        url = url_entry.get()
        yt_object = pytube.YouTube(url)
        video = yt_object.streams.get_highest_resolution()
        video.download()
        print("Download complete.")
    except Exception as e:
        print(f"{e}")


# Set the appearance mode and default color theme.
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

# Create the main application window.
app = customtkinter.CTk()
app.resizable(False, False)

# Add instructions label.
instructions = customtkinter.CTkLabel(app, text="Paste the YouTube video link you want to download in the field below.")
instructions.pack(padx=0, pady=(20, 0))

# Add URL entry field.
url_entry = customtkinter.CTkEntry(app, width=600, height=35)
url_entry.pack(padx=20, pady=0)

# Add download button.
download_button = customtkinter.CTkButton(app, text="DOWNLOAD", cursor="hand2", command=download)
download_button.pack(padx=0, pady=20)

# Start the application's main loop.
app.mainloop()
