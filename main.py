import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import sys
import requests
from PIL import Image, ImageTk
from io import BytesIO
import yt_dlp
import webbrowser
import time

# --- وظيفة جلب المسارات الصحيحة عند التحويل لـ EXE ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- الإعدادات الثابتة ---
APP_NAME = "HamzxaDL"
APP_VERSION = "1.0"
UPDATE_URL = "https://pastebin.com/raw/bV04wUce"
REPO_URL = "https://github.com/alzyood95/HamzxaDL"
DEFAULT_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

COLORS = {
    "bg": "#0b0e14", "card": "#161b22", "input": "#0d1117",
    "primary": "#667eea", "secondary": "#764ba2", "success": "#00b09b",
    "danger": "#ff5f6d", "text": "#f0f6fc", "accent": "#fbbf24"
}

LANGS = {
    "ar": {
        "dir": "rtl", "update_btn": "تحديث", "paste": "لصق", "fetch": "تحليل",
        "size": "الحجم المتوقع: ", "dl_btn": "بدء التحميل", "search_ph": "ابحث هنا أو ضع رابطاً...",
        "back": "⬅ رجوع", "select": "اختر", "lang_btn": "English", "finish": "اكتمل التحميل!",
        "cancel": "إلغاء", "open_folder": "فتح المجلد؟"
    },
    "en": {
        "dir": "ltr", "update_btn": "Update", "paste": "Paste", "fetch": "Analyze",
        "size": "Est. Size: ", "dl_btn": "Download Now", "search_ph": "Search or paste link...",
        "back": "Back ➡", "select": "Select", "lang_btn": "العربية", "finish": "Done!",
        "cancel": "Cancel", "open_folder": "Open Folder?"
    }
}

class HamzxaDL(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cur_lang = "ar"
        self.T = LANGS[self.cur_lang]
        
        # Variables
        self.url_var = ctk.StringVar()
        self.path_var = ctk.StringVar(value=DEFAULT_PATH)
        self.format_var = ctk.StringVar(value="mp4")
        self.quality_var = ctk.StringVar(value="Best")
        self.size_var = ctk.StringVar(value="")
        self.status_var = ctk.StringVar(value="Ready")
        self.video_info = None
        self.stop_download = False

        self.setup_main_window()
        self.set_app_icon() 
        self.render_home()

    def set_app_icon(self):
        # تم تعديل المسار ليقرأ icon.ico
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                # وضع الأيقونة في التايتل بار
                self.iconbitmap(icon_path)
            except Exception as e:
                print(f"Error loading icon: {e}")

    def setup_main_window(self):
        self.title(f"{APP_NAME} Pro Max v{APP_VERSION}")
        self.geometry("1100x850")
        self.configure(fg_color=COLORS["bg"])
        self.grid_columnconfigure(0, weight=1)

    def clear_screen(self):
        for widget in self.winfo_children(): widget.destroy()

    def render_home(self):
        self.clear_screen()
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=15)

        # --- Header Section (اسمك بالنص بدون لوجو) ---
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(10, 20))
        
        ctk.CTkLabel(header, text=APP_NAME, font=("Impact", 45), text_color=COLORS["primary"]).pack()
        
        top_btns = ctk.CTkFrame(header, fg_color="transparent")
        top_btns.place(relx=1.0, rely=0.5, anchor="e") 
        
        self.upd_btn = ctk.CTkButton(top_btns, text=self.T["update_btn"], width=90, fg_color=COLORS["card"], 
                                     hover_color=COLORS["secondary"], command=self.check_updates)
        self.upd_btn.pack(side="right", padx=5)
        ctk.CTkButton(top_btns, text=self.T["lang_btn"], width=80, fg_color=COLORS["card"], command=self.switch_lang).pack(side="right")

        # --- منطقة المدخلات ---
        input_f = ctk.CTkFrame(container, fg_color=COLORS["card"], corner_radius=20, border_width=1, border_color="#2d333b")
        input_f.pack(fill="x", pady=15)
        self.url_entry = ctk.CTkEntry(input_f, textvariable=self.url_var, placeholder_text=self.T["search_ph"], 
                                      height=55, fg_color=COLORS["input"], border_width=0, font=("Arial", 14))
        self.url_entry.pack(side="left", fill="x", expand=True, padx=20, pady=20)

        btn_row = ctk.CTkFrame(input_f, fg_color="transparent")
        btn_row.pack(side="right", padx=15)
        ctk.CTkButton(btn_row, text=self.T["paste"], width=65, fg_color=COLORS["secondary"], command=self.paste_link).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🔍", width=55, fg_color=COLORS["danger"], font=("Arial", 18), command=self.render_search_page).pack(side="left", padx=2)
        self.fetch_btn = ctk.CTkButton(btn_row, text=self.T["fetch"], fg_color=COLORS["primary"], font=("Arial", 14, "bold"), command=self.fetch_data)
        self.fetch_btn.pack(side="left", padx=2)

        self.info_card = ctk.CTkFrame(container, fg_color=COLORS["card"], corner_radius=20)
        self.info_card.pack(fill="x", pady=10)
        self.thumb_lbl = ctk.CTkLabel(self.info_card, text="Waiting for URL...", width=320, height=180, 
                                      fg_color=COLORS["input"], corner_radius=15)
        self.thumb_lbl.pack(side="left" if self.cur_lang=="en" else "right", padx=25, pady=25)

        det = ctk.CTkFrame(self.info_card, fg_color="transparent")
        det.pack(side="left" if self.cur_lang=="en" else "right", fill="both", expand=True, pady=25)
        self.title_lbl = ctk.CTkLabel(det, text="---", font=("Arial", 18, "bold"), wraplength=450, justify="left")
        self.title_lbl.pack(anchor="w", padx=15)
        ctk.CTkLabel(det, textvariable=self.size_var, font=("Arial", 25, "bold"), text_color=COLORS["success"]).pack(anchor="w", pady=20, padx=15)

        set_row = ctk.CTkFrame(container, fg_color="transparent")
        set_row.pack(fill="x", pady=10)
        ctk.CTkSegmentedButton(set_row, values=["mp4", "mp3"], variable=self.format_var, 
                               command=self.update_quals, selected_color=COLORS["primary"]).pack(side="left", padx=10)
        self.qual_menu = ctk.CTkOptionMenu(set_row, variable=self.quality_var, values=["Best"], command=self.calc_size)
        self.qual_menu.pack(side="left", padx=10)
        ctk.CTkButton(set_row, text="📁", width=40, fg_color=COLORS["card"], command=self.choose_path).pack(side="right", padx=10)

        dl_f = ctk.CTkFrame(container, fg_color=COLORS["card"], corner_radius=20)
        dl_f.pack(fill="x", pady=15)
        ctk.CTkEntry(dl_f, textvariable=self.path_var, width=500, height=40).pack(side="left", padx=25, pady=25)
        self.dl_btn = ctk.CTkButton(dl_f, text=self.T["dl_btn"], fg_color=COLORS["success"], 
                                    height=55, width=250, font=("Arial", 16, "bold"), state="disabled", command=self.start_dl)
        self.dl_btn.pack(side="right", padx=25)

        prog_box = ctk.CTkFrame(container, fg_color="transparent")
        prog_box.pack(fill="x", pady=10)
        self.prog = ctk.CTkProgressBar(prog_box, height=18, progress_color=COLORS["primary"])
        self.prog.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.prog.set(0)
        
        self.cancel_btn = ctk.CTkButton(prog_box, text="✖", width=45, height=35, fg_color=COLORS["danger"], 
                                         state="disabled", command=self.cancel_download_action)
        self.cancel_btn.pack(side="right")
        
        self.status_lbl = ctk.CTkLabel(container, textvariable=self.status_var, font=("Arial", 13), text_color="gray")
        self.status_lbl.pack()

    def progress_hook(self, d):
        if self.stop_download: raise Exception("CANCELLED")
        if d['status'] == 'downloading':
            try:
                p_raw = d.get('_percent_str', '0%').replace('%','').strip()
                p_val = float(p_raw) / 100
                speed = d.get('_speed_str', 'N/A')
                self.after(0, lambda: self.prog.set(p_val))
                self.after(0, lambda: self.status_var.set(f"⬇ {p_raw}% | Speed: {speed}"))
            except Exception:
                pass

    def render_search_page(self):
        self.clear_screen()
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)
        nav = ctk.CTkFrame(container, fg_color="transparent")
        nav.pack(fill="x")
        ctk.CTkButton(nav, text=self.T["back"], fg_color=COLORS["danger"], width=100, command=self.render_home).pack(side="left")
        s_bar = ctk.CTkFrame(container, fg_color=COLORS["card"], corner_radius=15)
        s_bar.pack(fill="x", pady=15)
        self.s_ent = ctk.CTkEntry(s_bar, placeholder_text=self.T["search_ph"], height=50, border_width=0)
        self.s_ent.pack(side="left", fill="x", expand=True, padx=15, pady=10)
        self.s_ent.bind("<Return>", lambda e: self.execute_search())
        ctk.CTkButton(s_bar, text="Search", width=120, height=40, command=self.execute_search).pack(side="right", padx=10)
        self.res_scroll = ctk.CTkScrollableFrame(container, fg_color=COLORS["bg"], height=580)
        self.res_scroll.pack(fill="both", expand=True)

    def execute_search(self):
        q = self.s_ent.get()
        if not q: return
        for w in self.res_scroll.winfo_children(): w.destroy()
        threading.Thread(target=self._search_thread, args=(q,), daemon=True).start()

    def _search_thread(self, q):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, 'no_warnings': True}) as ydl:
                res = ydl.extract_info(f"ytsearch20:{q}", download=False)['entries']
            for item in res:
                threading.Thread(target=self._load_search_item, args=(item,), daemon=True).start()
        except: pass

    def _load_search_item(self, item):
        try:
            r = requests.get(item['thumbnails'][0]['url'], timeout=5)
            img = ctk.CTkImage(Image.open(BytesIO(r.content)), size=(140, 78))
            self.after(0, lambda: self._draw_res_card(item, img))
        except: self.after(0, lambda: self._draw_res_card(item, None))

    def _draw_res_card(self, item, img):
        card = ctk.CTkFrame(self.res_scroll, fg_color=COLORS["card"], corner_radius=12)
        card.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(card, text="", image=img, corner_radius=8).pack(side="left", padx=10, pady=10)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info, text=item['title'][:70], font=("Arial", 14, "bold"), wraplength=450, justify="left").pack(anchor="w", pady=(10,0))
        ctk.CTkLabel(info, text=f"⏱ {item.get('duration_string','N/A')}", text_color="gray").pack(anchor="w")
        ctk.CTkButton(card, text=self.T["select"], width=80, fg_color=COLORS["primary"], command=lambda u=item['url']: self.select_vid(u)).pack(side="right", padx=15)

    def select_vid(self, url):
        self.url_var.set(url)
        self.render_home()
        self.fetch_data()

    def start_dl(self):
        self.stop_download = False
        self.dl_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        threading.Thread(target=self._dl_worker, daemon=True).start()

    def cancel_download_action(self):
        self.stop_download = True
        self.status_var.set("Stopping...")

    def _dl_worker(self):
        url = self.url_var.get()
        path = self.path_var.get()
        opts = {
            'outtmpl': f'{path}/%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
            'quiet': True, 'nocheckcertificate': True, 'no_warnings': True
        }
        if self.format_var.get() == "mp3":
            opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
        else:
            opts['format'] = 'bestvideo+bestaudio/best'

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            if not self.stop_download:
                self.after(0, self._finish_sequence)
        except Exception as e:
            if "CANCELLED" in str(e): self.after(0, lambda: self.status_var.set("Cancelled"))
            else: self.after(0, lambda: messagebox.showerror("Error", "Check your connection or update yt-dlp"))
        finally:
            self.after(0, lambda: self.dl_btn.configure(state="normal"))
            self.after(0, lambda: self.cancel_btn.configure(state="disabled"))

    def _finish_sequence(self):
        self.status_var.set(self.T["finish"])
        if messagebox.askyesno(APP_NAME, f"{self.T['finish']}\n{self.T['open_folder']}"):
            os.startfile(self.path_var.get())

    def fetch_data(self):
        url = self.url_var.get()
        if not url: return
        self.fetch_btn.configure(state="disabled")
        self.status_var.set("Analyzing...")
        threading.Thread(target=self._fetch_task, args=(url,), daemon=True).start()

    def _fetch_task(self, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)
            self.video_info = info
            r = requests.get(info['thumbnail'], timeout=10)
            img = ctk.CTkImage(Image.open(BytesIO(r.content)), size=(320, 180))
            self.after(0, lambda: self._apply_info(info, img))
        except: self.after(0, lambda: messagebox.showerror("Error", "Link Not Supported"))
        finally: self.after(0, lambda: self.fetch_btn.configure(state="normal"))

    def _apply_info(self, info, img):
        self.thumb_lbl.configure(image=img, text="")
        self.title_lbl.configure(text=info['title'])
        self.dl_btn.configure(state="normal")
        self.update_quals()
        if 'entries' in info or 'playlist' in info.get('webpage_url', ''):
            messagebox.showinfo("Note", "Playlist detected! Only first video will be processed.")

    def update_quals(self, *args):
        if not self.video_info: return
        if self.format_var.get() == "mp3": q = ["320kbps", "192kbps", "128kbps"]
        else:
            fmts = self.video_info.get('formats', [])
            q = sorted(list(set([f"{f.get('height')}p" for f in fmts if f.get('height')])), key=lambda x: int(x[:-1]), reverse=True)
        self.qual_menu.configure(values=q)
        self.qual_menu.set(q[0] if q else "Best")
        self.calc_size()

    def calc_size(self, *args):
        if not self.video_info: return
        dur = self.video_info.get('duration', 0)
        mb = (dur * 0.006 * 720) if self.format_var.get()=="mp4" else (dur * 192 / 8000)
        self.size_var.set(f"{self.T['size']} {mb:.1f} MB")

    def switch_lang(self):
        self.cur_lang = "en" if self.cur_lang == "ar" else "ar"
        self.T = LANGS[self.cur_lang]
        self.render_home()

    def choose_path(self):
        p = filedialog.askdirectory()
        if p: self.path_var.set(p)

    def check_updates(self):
        threading.Thread(target=self._update_logic, daemon=True).start()

    def _update_logic(self):
        try:
            v = requests.get(UPDATE_URL, timeout=5).text.strip()
            msg = "New version!" if v != APP_VERSION else "Latest version!"
            self.after(0, lambda: messagebox.showinfo("HamzxaDL", msg))
        except: pass

    def paste_link(self):
        try: self.url_var.set(self.clipboard_get())
        except: pass

if __name__ == "__main__":
    app = HamzxaDL()
    app.mainloop()