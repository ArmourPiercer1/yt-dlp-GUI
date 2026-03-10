import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import json
from pathlib import Path
from datetime import datetime
import pandas.io.clipboard as cb
import threading
import subprocess
import re
import shutil

# 队列文件配置
QUEUE_FILE = "download_queue.json"
SETTINGS_FILE = "gui_settings.json"
SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR / "config"
DEFAULT_COOKIE_FILE = "www.youtube.com_cookies.txt"
LEGACY_COOKIE_FILES = ["www.youtube.com_cookies.txt", "youtube-cookies.txt", "cookies.txt"]

# 默认保存路径
save_path_default = "I:\\videos"
save_path_compilation = "I:\\videos\\compilations\\Nuestra_Familia_Feliz"
save_path = "E:\\Entertainment\\Videos\\Others\\PB\\Well_Sorted\\同一作者合集\\菲律宾系列"

progress_re = re.compile(r"(\d{1,3}(?:\.\d+)?)%")
playlist_progress_re = re.compile(r"Downloading (?:item|video)\s+(\d+)\s+of\s+(\d+)", re.IGNORECASE)


def ensure_config_layout():
    """确保配置子目录存在，并迁移历史配置文件。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    for name in [QUEUE_FILE, SETTINGS_FILE, *LEGACY_COOKIE_FILES]:
        src = SCRIPT_DIR / name
        dst = CONFIG_DIR / name
        if src.exists() and not dst.exists():
            try:
                shutil.move(str(src), str(dst))
            except Exception as e:
                print(f"迁移配置文件失败: {src} -> {dst}, 错误: {e}")


ensure_config_layout()


def ensure_yt_dlp_updated():
    """尝试更新 yt-dlp，不影响后续流程"""
    try:
        subprocess.run(["yt-dlp", "-U"], cwd=SCRIPT_DIR, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pass


class DownloadQueue:
    """下载队列管理类"""

    def __init__(self, queue_file=QUEUE_FILE):
        self.queue_file = CONFIG_DIR / queue_file
        self.queue = self.load_queue()

    def _normalize_item(self, item):
        if isinstance(item, str):
            return {"url": item, "save_path": None}
        if isinstance(item, dict):
            url = item.get("url") or item.get("link") or item.get("href")
            return {"url": url, "save_path": item.get("save_path")}
        return None

    def load_queue(self):
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_list = data.get("links", data if isinstance(data, list) else [])
                    result = []
                    for item in raw_list:
                        norm = self._normalize_item(item)
                        if norm and norm.get("url"):
                            result.append(norm)
                    return result
            except Exception as e:
                print(f"加载队列失败: {e}")
                return []
        return []

    def save_queue(self):
        try:
            with open(self.queue_file, "w", encoding="utf-8") as f:
                json.dump({"links": self.queue, "last_updated": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存队列失败: {e}")
            return False

    def add_link(self, link, save_path_override=None):
        link = (link or "").strip()
        if not link:
            return False, "链接为空"
        if any(item.get("url") == link for item in self.queue):
            return False, f"链接已存在: {link}"
        self.queue.append({"url": link, "save_path": save_path_override})
        self.save_queue()
        return True, f"已添加: {link}"

    def remove_link(self, index):
        if 0 <= index < len(self.queue):
            removed = self.queue.pop(index)
            self.save_queue()
            return True, f"已移除: {removed.get('url')}"
        return False, "无效的索引"

    def update_save_path(self, index, new_path):
        if 0 <= index < len(self.queue):
            self.queue[index]["save_path"] = new_path or None
            self.save_queue()
            return True, "保存路径已更新"
        return False, "无效的索引"

    def get_link(self, index=0):
        if 0 <= index < len(self.queue):
            return self.queue[index]
        return None

    def get_first_link(self):
        return self.get_link(0) if self.queue else None

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)


class DownloadGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("yt-dlp 下载队列管理器")
        self.root.geometry("1000x780")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")

        self.queue = DownloadQueue()
        self.is_downloading = False
        self.current_download_thread = None
        self.current_process = None
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text = tk.StringVar(value="等待中")
        self.list_progress_var = tk.DoubleVar(value=0.0)
        self.list_progress_text = tk.StringVar(value="等待中")
        self.current_url_var = tk.StringVar(value="当前无下载")
        self.default_save_path_var = tk.StringVar(value=self._load_default_save_path())
        self.cookie_file_var = tk.StringVar(value=self._load_cookie_file())
        self._playlist_detected = False

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_queue_display()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        info_frame = ttk.LabelFrame(main_frame, text="队列信息", padding="10")
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for c in range(4):
            info_frame.columnconfigure(c, weight=1)

        ttk.Label(info_frame, text="队列中的链接数:").grid(row=0, column=0, sticky="w")
        self.info_label = ttk.Label(info_frame, text="0", foreground="blue", font=("Arial", 12, "bold"))
        self.info_label.grid(row=0, column=1, sticky="w", padx=(6, 0))

        ttk.Label(info_frame, text="下载状态:").grid(row=0, column=2, sticky="e")
        self.status_label = ttk.Label(info_frame, text="就绪", foreground="green", font=("Arial", 12, "bold"))
        self.status_label.grid(row=0, column=3, sticky="w", padx=(6, 0))

        ttk.Label(info_frame, text="当前下载:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.current_label = ttk.Label(info_frame, textvariable=self.current_url_var, foreground="black")
        self.current_label.grid(row=1, column=1, columnspan=3, sticky="w", pady=(6, 0))

        self.progress_bar = ttk.Progressbar(info_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.progress_label = ttk.Label(info_frame, textvariable=self.progress_text, foreground="gray")
        self.progress_label.grid(row=2, column=3, sticky="w", padx=(6, 0))

        ttk.Label(info_frame, text="列表总进度:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.list_progress_bar = ttk.Progressbar(info_frame, variable=self.list_progress_var, maximum=100)
        self.list_progress_bar.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(6, 0))
        self.list_progress_label = ttk.Label(info_frame, textvariable=self.list_progress_text, foreground="gray")
        self.list_progress_label.grid(row=3, column=3, sticky="w", padx=(6, 0), pady=(6, 0))

        input_frame = ttk.LabelFrame(main_frame, text="添加链接", padding="10")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="URL:").grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(input_frame)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(10, 10))
        self.url_entry.bind("<Return>", lambda e: self.add_url_from_entry())

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        ttk.Button(button_frame, text="添加", width=8, command=self.add_url_from_entry).pack(side="left", padx=2)
        ttk.Button(button_frame, text="从剪贴板", width=10, command=self.add_from_clipboard).pack(side="left", padx=2)

        ttk.Label(input_frame, text="默认下载路径:").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.default_path_entry = ttk.Entry(input_frame, textvariable=self.default_save_path_var)
        self.default_path_entry.grid(row=1, column=1, sticky="ew", padx=(10, 10), pady=(10, 0))

        default_path_btn_frame = ttk.Frame(input_frame)
        default_path_btn_frame.grid(row=1, column=2, sticky="ew", padx=(5, 0), pady=(10, 0))
        ttk.Button(default_path_btn_frame, text="选择目录", width=10, command=self.choose_default_dir).pack(side="left", padx=2)
        ttk.Button(default_path_btn_frame, text="保存默认", width=10, command=self.apply_default_save_path).pack(side="left", padx=2)

        ttk.Label(input_frame, text="Cookie文件:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.cookie_entry = ttk.Entry(input_frame, textvariable=self.cookie_file_var)
        self.cookie_entry.grid(row=2, column=1, sticky="ew", padx=(10, 10), pady=(10, 0))

        cookie_btn_frame = ttk.Frame(input_frame)
        cookie_btn_frame.grid(row=2, column=2, sticky="ew", padx=(5, 0), pady=(10, 0))
        ttk.Button(cookie_btn_frame, text="选择Cookie", width=10, command=self.choose_cookie_file).pack(side="left", padx=2)

        queue_frame = ttk.LabelFrame(main_frame, text="下载队列 (每条自带操作按钮)", padding="10")
        queue_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(0, weight=1)

        self.queue_canvas = tk.Canvas(queue_frame, highlightthickness=0, bg="#ffffff")
        self.queue_container = ttk.Frame(self.queue_canvas)
        self.queue_scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_canvas.yview)
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)

        self.queue_canvas.grid(row=0, column=0, sticky="nsew")
        self.queue_scrollbar.grid(row=0, column=1, sticky="ns")

        self.queue_window = self.queue_canvas.create_window((0, 0), window=self.queue_container, anchor="nw")

        def _configure_container(event):
            self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))
            self.queue_canvas.itemconfigure(self.queue_window, width=self.queue_canvas.winfo_width())

        self.queue_container.bind("<Configure>", _configure_container)

        action_frame = ttk.LabelFrame(main_frame, text="操作", padding="10")
        action_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        btn_col = 0
        ttk.Button(action_frame, text="刷新列表", command=self.refresh_queue_display).grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        ttk.Button(action_frame, text="下载第一个", command=self.download_first, style="Accent.TButton").grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        ttk.Button(action_frame, text="下载全部", command=self.download_all, style="Accent.TButton").grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        self.stop_button = ttk.Button(action_frame, text="停止下载", command=self.stop_download, state="disabled")
        self.stop_button.grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        ttk.Button(action_frame, text="清空队列", command=self.clear_queue).grid(row=0, column=btn_col, padx=5, pady=5)

        log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
        log_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=("Courier New", 9), bg="#f8f8f8", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

    def _short_path(self, path_text, max_len=40):
        text = (path_text or "").strip()
        if len(text) <= max_len:
            return text
        keep = max_len - 3
        return text[:keep] + "..."

    def refresh_queue_display(self):
        self.queue.queue = self.queue.load_queue()

        for child in self.queue_container.winfo_children():
            child.destroy()

        header = ttk.Frame(self.queue_container)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="#", width=4).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="链接", width=70).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text="保存路径", width=30).grid(row=0, column=2, sticky="w")
        ttk.Label(header, text="操作", width=10).grid(row=0, column=3, sticky="w")

        for i, item in enumerate(self.queue.queue, 1):
            row = ttk.Frame(self.queue_container, padding=(0, 2))
            row.grid(row=i, column=0, sticky="ew")
            row.columnconfigure(1, weight=1)

            ttk.Label(row, text=f"{i}", width=4).grid(row=0, column=0, sticky="w")
            ttk.Label(row, text=item.get("url"), width=70, wraplength=600, anchor="w").grid(row=0, column=1, sticky="w")
            default_path_text = self.default_save_path_var.get().strip() or save_path_default
            path_text = item.get("save_path") or f"默认: {self._short_path(default_path_text)}"
            ttk.Label(row, text=path_text, width=30, anchor="w", foreground="gray").grid(row=0, column=2, sticky="w")
            ttk.Button(row, text="操作", command=lambda idx=i-1: self.open_item_actions(idx)).grid(row=0, column=3, padx=4)

        self.info_label.config(text=str(self.queue.size()))
        self.log_message(f"✓ 队列已刷新，共 {self.queue.size()} 个链接")

    def add_url_from_entry(self):
        url = self.url_entry.get().strip()
        if url:
            success, msg = self.queue.add_link(url)
            self.log_message(msg)
            if success:
                self.url_entry.delete(0, tk.END)
                self.refresh_queue_display()
            else:
                messagebox.showwarning("警告", msg)
        else:
            messagebox.showwarning("警告", "请输入链接")

    def add_from_clipboard(self):
        try:
            url = str(cb.paste()).strip()
            if url:
                success, msg = self.queue.add_link(url)
                self.log_message(msg)
                if success:
                    self.refresh_queue_display()
                else:
                    messagebox.showinfo("提示", msg)
            else:
                messagebox.showwarning("警告", "剪贴板为空")
        except Exception as e:
            messagebox.showerror("错误", f"无法读取剪贴板: {e}")

    def open_item_actions(self, index):
        item = self.queue.get_link(index)
        if not item:
            return

        win = tk.Toplevel(self.root)
        win.title("管理队列项")
        win.geometry("620x240")
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="链接:").pack(anchor="w", padx=10, pady=(10, 2))
        ttk.Label(win, text=item.get("url"), wraplength=580, foreground="blue").pack(anchor="w", padx=10)

        ttk.Label(win, text="保存路径 (留空使用默认)").pack(anchor="w", padx=10, pady=(12, 2))
        path_var = tk.StringVar(value=item.get("save_path") or "")
        path_entry = ttk.Entry(win, textvariable=path_var, width=80)
        path_entry.pack(anchor="w", padx=10, fill="x")

        def choose_dir():
            directory = filedialog.askdirectory(title="选择保存位置")
            if directory:
                path_var.set(directory)

        ttk.Button(win, text="选择目录", command=choose_dir).pack(anchor="w", padx=10, pady=6)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", pady=10, padx=10)

        def save_changes():
            new_path = path_var.get().strip() or None
            ok, msg = self.queue.update_save_path(index, new_path)
            if ok:
                self.log_message(f"✓ 已更新保存路径: {new_path or '默认路径'}")
                self.refresh_queue_display()
                win.destroy()
            else:
                messagebox.showerror("错误", msg)

        def delete_item():
            if messagebox.askyesno("确认", "确定要删除该链接吗？"):
                ok, msg = self.queue.remove_link(index)
                self.log_message(msg)
                self.refresh_queue_display()
                win.destroy()

        ttk.Button(btn_frame, text="保存", style="Accent.TButton", command=save_changes).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="删除该链接", command=delete_item).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="关闭", command=win.destroy).pack(side="right", padx=4)

    def clear_queue(self):
        if messagebox.askyesno("确认", "确定要清空整个队列吗？"):
            self.queue.queue = []
            self.queue.save_queue()
            self.log_message("✓ 队列已清空")
            self.refresh_queue_display()

    def _load_default_save_path(self):
        settings_path = CONFIG_DIR / SETTINGS_FILE
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    path = (data.get("default_save_path") or "").strip()
                    if path:
                        return path
            except Exception as e:
                print(f"加载设置失败: {e}")
        return save_path_default

    def _load_cookie_file(self):
        settings_path = CONFIG_DIR / SETTINGS_FILE
        cookie_value = ""
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cookie_value = (data.get("cookie_file") or "").strip()
            except Exception as e:
                print(f"加载Cookie设置失败: {e}")

        if cookie_value:
            cookie_path = Path(cookie_value)
            if not cookie_path.is_absolute():
                cookie_path = CONFIG_DIR / cookie_path
            if cookie_path.exists():
                return str(cookie_path)

        for name in LEGACY_COOKIE_FILES:
            candidate = CONFIG_DIR / name
            if candidate.exists():
                return str(candidate)

        return str(CONFIG_DIR / DEFAULT_COOKIE_FILE)

    def _save_settings(self):
        settings_path = CONFIG_DIR / SETTINGS_FILE
        cookie_text = (self.cookie_file_var.get() or "").strip()
        if not cookie_text:
            cookie_value = DEFAULT_COOKIE_FILE
        else:
            cookie_path = Path(cookie_text)
            if cookie_path.is_absolute() and cookie_path.parent == CONFIG_DIR:
                cookie_value = cookie_path.name
            else:
                cookie_value = str(cookie_path)
        payload = {
            "default_save_path": self.default_save_path_var.get().strip() or save_path_default,
            "cookie_file": cookie_value,
            "last_updated": datetime.now().isoformat(),
        }
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def choose_cookie_file(self):
        file_path = filedialog.askopenfilename(
            title="选择Cookie文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        src = Path(file_path)
        dst = CONFIG_DIR / src.name
        try:
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
                self.log_message(f"✓ Cookie已复制到配置目录: {dst}")
            else:
                self.log_message(f"✓ 使用配置目录中的Cookie: {dst}")
            self.cookie_file_var.set(str(dst))
            self._save_settings()
        except Exception as e:
            messagebox.showerror("错误", f"无法设置Cookie文件: {e}")

    def choose_default_dir(self):
        directory = filedialog.askdirectory(title="选择默认下载目录")
        if directory:
            self.default_save_path_var.set(directory)
            try:
                os.makedirs(directory, exist_ok=True)
                self._save_settings()
                self.log_message(f"✓ 默认下载路径已更新: {directory}")
            except Exception as e:
                messagebox.showerror("错误", f"无法保存默认路径: {e}")

    def apply_default_save_path(self):
        new_path = self.default_save_path_var.get().strip()
        if not new_path:
            messagebox.showwarning("警告", "默认下载路径不能为空")
            return
        try:
            os.makedirs(new_path, exist_ok=True)
            self._save_settings()
            self.log_message(f"✓ 默认下载路径已更新: {new_path}")
        except Exception as e:
            messagebox.showerror("错误", f"无法设置默认路径: {e}")

    def _stream_download(self, url, save_path, progress_callback, debug_mode=False):
        ensure_yt_dlp_updated()
        cmd = ["yt-dlp", "--newline", "-4", url]

        cookie_text = (self.cookie_file_var.get() or "").strip()
        if cookie_text:
            cookie_path = Path(cookie_text)
            if cookie_path.exists():
                cmd.extend(["--cookies", str(cookie_path)])
            else:
                progress_callback(f"⚠ Cookie文件不存在，跳过cookies参数: {cookie_path}")
        else:
            progress_callback("⚠ 未设置Cookie文件，跳过cookies参数")

        cmd.extend(["-P", save_path, "--js-runtimes", "node"])
        if debug_mode:
            cmd.append("-v")

        # 在日志中显示完整命令，便于复现与排查
        progress_callback(f"$ {subprocess.list2cmdline(cmd)}")
        try:
            proc = subprocess.Popen(cmd, cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        except FileNotFoundError:
            progress_callback("❌ 未找到 yt-dlp，请确认已安装")
            return False

        self.current_process = proc
        for raw_line in proc.stdout:
            line = raw_line.strip()
            progress_callback(line)
        result = proc.wait() == 0
        self.current_process = None
        return result

    def _ask_debug_retry(self):
        answer = {"retry": False}
        done = threading.Event()

        def _prompt():
            answer["retry"] = messagebox.askyesno(
                "下载失败",
                "下载失败，是否进行一次 debugging 下载？\n将自动添加 -v 以输出详细错误信息。",
            )
            done.set()

        self.root.after(0, _prompt)
        done.wait()
        return answer["retry"]

    def _progress_handler(self, line):
        playlist_match = playlist_progress_re.search(line)
        if playlist_match:
            current_index = int(playlist_match.group(1))
            total_items = int(playlist_match.group(2))
            if total_items > 0:
                percent = min(100.0, (current_index / total_items) * 100)
                self._playlist_detected = True
                self.root.after(0, self.list_progress_var.set, percent)
                self.root.after(0, self.list_progress_text.set, f"{current_index}/{total_items}")

        match = progress_re.search(line)
        if match:
            percent = float(match.group(1))
            self.root.after(0, self.progress_var.set, percent)
            self.root.after(0, self.progress_text.set, f"{percent:.1f}%")
        else:
            self.root.after(0, self.progress_text.set, line[:80])
        self.log_message(line)

    def _download_item(self, item):
        url = item.get("url")
        save_to = item.get("save_path") or self.default_save_path_var.get().strip() or save_path_default
        # 下载前自动持久化当前默认路径，保证下次启动沿用最新值
        if not item.get("save_path"):
            try:
                os.makedirs(save_to, exist_ok=True)
                self._save_settings()
            except Exception:
                pass
        self._playlist_detected = False
        self.root.after(0, self.current_url_var.set, f"{url}")
        self.root.after(0, self.progress_var.set, 0)
        self.root.after(0, self.progress_text.set, "准备中")
        self.root.after(0, self.list_progress_var.set, 0)
        self.root.after(0, self.list_progress_text.set, "识别中")
        success = self._stream_download(url, save_to, self._progress_handler)
        if (not success) and self.is_downloading:
            self.log_message("❌ 下载失败")
            if self._ask_debug_retry():
                self.log_message("▶ 开始 debugging 下载（-v）")
                self.root.after(0, self.progress_text.set, "调试重试中")
                success = self._stream_download(url, save_to, self._progress_handler, debug_mode=True)
        if not self._playlist_detected:
            if success:
                self.root.after(0, self.list_progress_var.set, 100)
                self.root.after(0, self.list_progress_text.set, "1/1")
            else:
                self.root.after(0, self.list_progress_text.set, "失败")
        return success

    def download_first(self):
        if self.is_downloading:
            messagebox.showwarning("警告", "正在下载中，请稍候")
            return
        item = self.queue.get_first_link()
        if not item:
            messagebox.showwarning("警告", "队列为空，没有链接可下载")
            return
        thread = threading.Thread(target=self._download_first_worker, daemon=True)
        thread.start()
        self.current_download_thread = thread

    def _download_first_worker(self):
        self.is_downloading = True
        self.update_ui_state()
        item = self.queue.get_first_link()
        success = self._download_item(item)
        if success:
            self.queue.remove_link(0)
            self.log_message("✓ 下载完成，已从队列中移除")
        else:
            self.log_message("❌ 下载失败，链接保留在队列中")
        self.is_downloading = False
        self.refresh_queue_display()
        self.update_ui_state()

    def download_all(self):
        if self.is_downloading:
            messagebox.showwarning("警告", "正在下载中，请稍候")
            return
        if self.queue.is_empty():
            messagebox.showwarning("警告", "队列为空，没有链接可下载")
            return
        if messagebox.askyesno("确认", f"确定要下载队列中的全部 {self.queue.size()} 个链接吗？"):
            thread = threading.Thread(target=self._download_all_worker, daemon=True)
            thread.start()
            self.current_download_thread = thread

    def _download_all_worker(self):
        self.is_downloading = True
        self.update_ui_state()
        count = 0
        total = self.queue.size()
        while not self.queue.is_empty() and self.is_downloading:
            item = self.queue.get_first_link()
            count += 1
            self.log_message(f"\n[{count}/{total}] {item.get('url')}")
            success = self._download_item(item)
            if success:
                self.queue.remove_link(0)
                self.log_message("✓ 下载完成，已从队列中移除")
            else:
                self.log_message("❌ 下载失败，已停止队列下载")
                break
            self.refresh_queue_display()
        self.is_downloading = False
        if self.queue.is_empty():
            self.log_message("\n✓ 所有链接下载完毕！")
        self.update_ui_state()

    def stop_download(self):
        if not self.is_downloading:
            return
        if messagebox.askyesno("确认", "确定要停止下载吗？"):
            self.is_downloading = False
            if self.current_process:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass
            self.log_message("\n⚠ 下载已停止")
            self.update_ui_state()

    def update_ui_state(self):
        self.root.after(0, self._update_ui_state)

    def _update_ui_state(self):
        if self.is_downloading:
            self.status_label.config(text="下载中...", foreground="orange")
            self.stop_button.config(state="normal")
        else:
            self.status_label.config(text="就绪", foreground="green")
            self.stop_button.config(state="disabled")
            self.current_url_var.set("当前无下载")
            if self.progress_var.get() >= 100:
                self.progress_text.set("完成")

    def log_message(self, msg):
        self.root.after(0, self._log_message, msg)

    def _log_message(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def on_close(self):
        # 程序退出前保存默认路径，避免未点击“保存默认”导致配置丢失
        current_path = self.default_save_path_var.get().strip() or save_path_default
        try:
            os.makedirs(current_path, exist_ok=True)
            self._save_settings()
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    DownloadGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
