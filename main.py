#!/usr/bin/env python3

"""
A simple YouTube video downloader.
"""

import customtkinter

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
download_button = customtkinter.CTkButton(app, text="DOWNLOAD", cursor="hand2")
download_button.pack(padx=0, pady=20)

# Start the application's main loop.
app.mainloop()
