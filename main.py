import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from threading import Thread


def download_website(url, folder_path, download_all=False, callback=None):
    # Download website HTML file
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    html_file = os.path.join(folder_path, 'index.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    # Download media files
    media_links = []
    total_size = 0
    for tag in soup.find_all():
        if tag.name == 'img':
            media_links.append(tag['src'])
        elif tag.name == 'link' and tag.has_attr('href') and 'stylesheet' in tag['rel']:
            media_links.append(tag['href'])

    for i, link in enumerate(media_links):
        if link.startswith('http'):
            file_url = link
        else:
            file_url = urljoin(url, link)
        response = requests.get(file_url, stream=True)
        filename = os.path.join(folder_path, os.path.basename(urlparse(file_url).path))
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
                    if callback is not None:
                        progress = int(total_size / 1024)  # convert to KB
                        callback(progress)

    # Follow internal links
    if download_all:  # if download_all is True, download all pages on the website
        internal_links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href is not None and 'http' not in href:
                internal_links.append(urljoin(url, href))

        for link in internal_links:
            # Download each page recursively
            page_folder = os.path.join(folder_path, urlparse(link).path.strip('/'))
            os.makedirs(page_folder, exist_ok=True)
            page_url = urljoin(url, urlparse(link).path)
            download_website(page_url, page_folder, download_all=True, callback=callback)
    else:
        pass

    return total_size






class DownloadFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)

        self.url_label = ttk.Label(self, text="Website URL:")
        self.url_text = ttk.Entry(self)
        self.folder_label = ttk.Label(self, text="Save to folder:")
        self.folder_text = ttk.Entry(self)
        self.folder_button = ttk.Button(self, text="Browse", command=self.on_folder_button)
        self.download_button = ttk.Button(self, text="Download", command=self.on_download_button)
        self.check_var = tk.BooleanVar(value=False)  # initialize checkbox to unchecked
        self.check_button = ttk.Checkbutton(self, text="Download entire website", variable=self.check_var)
        self.status_label = ttk.Label(self, text="")

        self.progress = ttk.Progressbar(self, orient="horizontal", length=200, mode="determinate")
        self.progress.grid(row=4, column=0, columnspan=3, padx=5, pady=5)


        self.url_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_text.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        self.folder_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.folder_text.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        self.folder_button.grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.check_button.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.download_button.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        self.status_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")

    def on_folder_button(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.folder_text.delete(0, tk.END)
            self.folder_text.insert(0, folder_path)

    def on_download_button(self):
        url = self.url_text.get()
        folder_path = self.folder_text.get()
        if not url:
            self.status_label.config(text="Please enter a website URL.")
            return
        if not folder_path:
            self.status_label.config(text="Please choose a folder to save the website.")
            return

        self.download_button.config(state="disabled")
        self.status_label.config(text="Downloading website...")

        # Define a function that will download the website in a thread
        def download_website_thread():
            try:
                def update_progress(progress):
                    self.progress["value"] = progress
                    self.progress.update()
                if self.check_var.get():
                    download_website(url, folder_path, download_all=True, callback=update_progress)
                else:
                    page_folder = os.path.join(folder_path, urlparse(url).path.strip('/'))
                    os.makedirs(page_folder, exist_ok=True)
                    page_url = urljoin(url, urlparse(url).path)  # Use the base URL of the page
                    download_website(page_url, page_folder, callback=update_progress)
                self.status_label.config(text="Website downloaded successfully!")
            except Exception as e:
                self.status_label.config(text="An error occurred while downloading the website.")
                print(e)
            self.progress["value"] = 0
            self.download_button.config(state="normal")

        # Start the thread
        thread = Thread(target=download_website_thread)
        thread.start()

        # Define a function that will update the progress bar
        def update_progress():
            total_size = download_website(url, folder_path, download_all=self.check_var.get())
            downloaded_size = 0
            while thread.is_alive():
                # Calculate the progress as a percentage
                if total_size > 0:
                    progress = int(100 * downloaded_size / total_size)
                else:
                    progress = 0
                self.progressbar_var.set(progress)
                self.update_idletasks()
                downloaded_size = sum(os.path.getsize(os.path.join(folder_path, f)) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f)))

        # Start the progress bar update thread
        progress_thread = Thread(target=update_progress)
        progress_thread.start()





if __name__ == "__main__":
    root = tk.Tk()
    root.title("Download website")
    DownloadFrame(root).pack(expand=True, fill="both")
    root.mainloop()