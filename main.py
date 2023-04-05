import wx
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin


def download_website(url, folder_path):
    # Download website HTML file
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    html_file = os.path.join(folder_path, 'index.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    # Download media files
    media_links = []
    for tag in soup.find_all():
        if tag.name == 'img':
            media_links.append(tag['src'])
        elif tag.name == 'link' and tag.has_attr('href') and 'stylesheet' in tag['rel']:
            media_links.append(tag['href'])

    for link in media_links:
        if link.startswith('http'):
            file_url = link
        else:
            file_url = urljoin(url, link)
        response = requests.get(file_url)
        filename = os.path.join(folder_path, os.path.basename(urlparse(file_url).path))
        with open(filename, 'wb') as f:
            f.write(response.content)


class DownloadFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Website Downloader")

        panel = wx.Panel(self)

        url_label = wx.StaticText(panel, label="Website URL:")
        self.url_text = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        folder_label = wx.StaticText(panel, label="Save to folder:")
        self.folder_text = wx.TextCtrl(panel)
        folder_button = wx.Button(panel, label="Browse")
        self.download_button = wx.Button(panel, label="Download")
        self.status_label = wx.StaticText(panel, label="")

        self.Bind(wx.EVT_BUTTON, self.on_folder_button, folder_button)
        self.Bind(wx.EVT_BUTTON, self.on_download_button, self.download_button)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_download_button, self.url_text)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(url_label, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.url_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(folder_label, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.folder_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(folder_button, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.download_button, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.status_label, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        self.Show()

    def on_folder_button(self, event):
        dialog = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            self.folder_text.SetValue(dialog.GetPath())
        dialog.Destroy()

    def on_download_button(self, event):
        url = self.url_text.GetValue()
        folder_path = self.folder_text.GetValue()
        if not url:
            self.status_label.SetLabel("Please enter a website URL.")
            return
        if not folder_path:
            self.status_label.SetLabel("Please choose a folder to save the website.")
            return

        self.download_button.Disable()
        self.status_label.SetLabel("Downloading website...")
        try:
            download_website(url, folder_path)
            self.status_label.SetLabel("Website downloaded successfully!")
        except Exception as e:
            self.status_label.SetLabel("An error occurred while downloading the website.")
            print(e)
        self.download_button.Enable()


if __name__ == "__main__":
    app = wx.App()
    frame = DownloadFrame(None)
    app.MainLoop()
