import os
import threading

import yt_dlp
from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.utils import platform

Window.clearcolor = (0.12, 0.12, 0.12, 1)
CYAN = (0, 1, 0.92, 1)


def get_download_dir():
    """Public Download folder on Android, with a safe fallback."""
    if platform == "android":
        try:
            from android.storage import primary_external_storage_path

            path = os.path.join(primary_external_storage_path(), "Download")
            os.makedirs(path, exist_ok=True)
            test = os.path.join(path, ".write_test")
            with open(test, "w") as f:
                f.write("x")
            os.remove(test)
            return path
        except Exception:
            pass
        try:
            from jnius import autoclass

            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            return activity.getExternalFilesDir(None).getAbsolutePath()
        except Exception:
            pass
    path = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(path, exist_ok=True)
    return path


class DownloaderUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=15, **kwargs)

        self.add_widget(
            Label(
                text="YouTube Downloader",
                font_size="22sp",
                bold=True,
                color=CYAN,
                size_hint_y=None,
                height=50,
            )
        )

        self.url_input = TextInput(
            hint_text="Paste video URL",
            multiline=False,
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=CYAN,
            cursor_color=(1, 1, 1, 1),
        )
        self.add_widget(self.url_input)

        paste_btn = Button(
            text="Paste from clipboard",
            size_hint_y=None,
            height=45,
            background_color=(0.25, 0.25, 0.25, 1),
        )
        paste_btn.bind(on_release=self.paste_clipboard)
        self.add_widget(paste_btn)

        self.download_btn = Button(
            text="Download",
            font_size="18sp",
            bold=True,
            size_hint_y=None,
            height=60,
            background_color=(0, 0.9, 0.36, 1),
            color=(0.1, 0.1, 0.1, 1),
        )
        self.download_btn.bind(on_release=self.start_download)
        self.add_widget(self.download_btn)

        self.progress = ProgressBar(max=100, value=0, size_hint_y=None, height=25)
        self.add_widget(self.progress)

        self.status = Label(text="Idle", color=CYAN, halign="center", valign="middle")
        self.status.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.add_widget(self.status)

    # ---------- UI helpers (always run on the main thread) ----------
    def set_status(self, text):
        Clock.schedule_once(lambda dt: setattr(self.status, "text", text))

    def set_progress(self, value):
        Clock.schedule_once(lambda dt: setattr(self.progress, "value", value))

    def set_busy(self, busy):
        def _do(dt):
            self.download_btn.disabled = busy

        Clock.schedule_once(_do)

    # ---------- actions ----------
    def paste_clipboard(self, *_):
        text = (Clipboard.paste() or "").strip()
        if text.startswith("http"):
            self.url_input.text = text
        else:
            self.status.text = "Clipboard has no valid link"

    def start_download(self, *_):
        url = self.url_input.text.strip()
        if not url:
            text = (Clipboard.paste() or "").strip()
            if text.startswith("http"):
                url = text
                self.url_input.text = url
            else:
                self.status.text = "Please enter a valid URL"
                return
        self.set_busy(True)
        self.set_progress(0)
        threading.Thread(target=self.download_video, args=(url,), daemon=True).start()

    def download_video(self, url):
        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                done = d.get("downloaded_bytes", 0)
                if total:
                    pct = done / total * 100
                    speed = d.get("speed") or 0
                    self.set_progress(pct)
                    self.set_status(f"Downloading: {pct:.1f}%  ({speed / 1024 / 1024:.2f} MB/s)")
            elif d["status"] == "finished":
                self.set_progress(100)
                self.set_status("Finishing...")

        out_dir = get_download_dir()
        opts = {
            # single pre-merged file: Android has no ffmpeg to merge streams
            "format": "best[ext=mp4]/best",
            "outtmpl": os.path.join(out_dir, "%(title).80s.%(ext)s"),
            "restrictfilenames": True,
            "progress_hooks": [hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.set_status(f"Done! Saved to:\n{out_dir}")
        except Exception as e:
            self.set_status(f"Download failed:\n{str(e)[:200]}")
        finally:
            self.set_busy(False)


class YTDownloaderApp(App):
    def build(self):
        self.title = "YT Downloader"
        if platform == "android":
            try:
                from android.permissions import Permission, request_permissions

                request_permissions(
                    [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE]
                )
            except Exception:
                pass
        return DownloaderUI()


if __name__ == "__main__":
    YTDownloaderApp().run()
