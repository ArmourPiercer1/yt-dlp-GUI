import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import json
import ctypes
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
DEFAULT_COOKIE_FILE = ""
LEGACY_COOKIE_FILES = []
COOKIE_NOT_SET_SENTINEL = "__COOKIE_NOT_SET__"

SUPPORTED_LANGUAGES = {"zh_cn", "en_us"}
LANGUAGE_DISPLAY = {
    "zh_cn": "简体中文",
    "en_us": "English",
}

I18N = {
    "zh_cn": {
        "app_title": "yt-dlp 下载队列管理器",
        "waiting": "等待中",
        "idle_download": "当前无下载",
        "ready": "就绪",
        "downloading": "下载中...",
        "done": "完成",
        "queue_info": "队列信息",
        "queue_count": "队列中的链接数:",
        "download_status": "下载状态:",
        "current_download": "当前下载:",
        "list_progress": "列表总进度:",
        "add_link": "添加链接",
        "url": "URL:",
        "add": "添加",
        "from_clipboard": "从剪贴板",
        "default_download_path": "默认下载路径:",
        "choose_dir": "选择目录",
        "save_default": "保存默认",
        "cookie_file": "Cookie文件:",
        "choose_cookie": "选择Cookie",
        "language": "界面语言:",
        "apply_language": "切换",
        "queue_list": "下载队列 (每条自带操作按钮)",
        "actions": "操作",
        "refresh": "刷新列表",
        "download_first": "下载第一个",
        "download_all": "下载全部",
        "stop_download": "停止下载",
        "clear_queue": "清空队列",
        "logs": "日志",
        "link": "链接",
        "save_path": "保存路径",
        "action": "操作",
        "default_prefix": "默认",
        "cookie_not_set": "未指明cookie文件",
        "warn": "警告",
        "info": "提示",
        "error": "错误",
        "confirm": "确认",
        "input_url_required": "请输入链接",
        "clipboard_empty": "剪贴板为空",
        "cannot_read_clipboard": "无法读取剪贴板: {error}",
        "manage_queue_item": "管理队列项",
        "link_label": "链接:",
        "save_path_hint": "保存路径 (留空使用默认)",
        "choose_save_location": "选择保存位置",
        "save": "保存",
        "delete_link": "删除该链接",
        "close": "关闭",
        "update_save_path_ok": "✓ 已更新保存路径: {path}",
        "default_path_label": "默认路径",
        "confirm_delete_link": "确定要删除该链接吗？",
        "confirm_clear_queue": "确定要清空整个队列吗？",
        "queue_cleared": "✓ 队列已清空",
        "choose_cookie_title": "选择Cookie文件",
        "cookie_copied": "✓ Cookie已复制到配置目录: {path}",
        "cookie_using_existing": "✓ 使用配置目录中的Cookie: {path}",
        "cannot_set_cookie": "无法设置Cookie文件: {error}",
        "choose_default_download_dir": "选择默认下载目录",
        "default_download_path_updated": "✓ 默认下载路径已更新: {path}",
        "cannot_save_default_path": "无法保存默认路径: {error}",
        "default_download_path_empty": "默认下载路径不能为空",
        "cannot_set_default_path": "无法设置默认路径: {error}",
        "cookie_missing_skip": "⚠ Cookie文件不存在，跳过cookies参数: {path}",
        "cookie_not_set_skip": "ℹ 未指明Cookie文件，按无Cookie模式继续",
        "yt_dlp_not_found": "❌ 未找到 yt-dlp，请确认已安装",
        "download_failed_title": "下载失败",
        "download_failed_debug_retry": "下载失败，是否进行一次 debugging 下载？\n将自动添加 -v 以输出详细错误信息。",
        "preparing": "准备中",
        "detecting": "识别中",
        "download_failed": "❌ 下载失败",
        "debug_retry_start": "▶ 开始 debugging 下载（-v）",
        "debug_retrying": "调试重试中",
        "failed": "失败",
        "busy_downloading": "正在下载中，请稍候",
        "queue_empty_no_download": "队列为空，没有链接可下载",
        "download_complete_removed": "✓ 下载完成，已从队列中移除",
        "download_failed_keep": "❌ 下载失败，链接保留在队列中",
        "confirm_download_all": "确定要下载队列中的全部 {count} 个链接吗？",
        "download_failed_stop_queue": "❌ 下载失败，已停止队列下载",
        "all_downloads_done": "\n✓ 所有链接下载完毕！",
        "confirm_stop_download": "确定要停止下载吗？",
        "download_stopped": "\n⚠ 下载已停止",
        "queue_refreshed": "✓ 队列已刷新，共 {count} 个链接",
        "language_switched": "✓ 界面语言已切换为: {language}",
        "queue_msg_empty_link": "链接为空",
        "queue_msg_exists": "链接已存在: {value}",
        "queue_msg_added": "已添加: {value}",
        "queue_msg_removed": "已移除: {value}",
        "queue_msg_invalid_index": "无效的索引",
        "queue_msg_save_path_updated": "保存路径已更新",
    },
    "en_us": {
        "app_title": "yt-dlp Download Queue Manager",
        "waiting": "Waiting",
        "idle_download": "No active download",
        "ready": "Ready",
        "downloading": "Downloading...",
        "done": "Done",
        "queue_info": "Queue Info",
        "queue_count": "Queued Links:",
        "download_status": "Status:",
        "current_download": "Current:",
        "list_progress": "Playlist Progress:",
        "add_link": "Add Link",
        "url": "URL:",
        "add": "Add",
        "from_clipboard": "From Clipboard",
        "default_download_path": "Default Download Path:",
        "choose_dir": "Choose Folder",
        "save_default": "Save Default",
        "cookie_file": "Cookie File:",
        "choose_cookie": "Choose Cookie",
        "language": "Language:",
        "apply_language": "Apply",
        "queue_list": "Download Queue (Per-item actions)",
        "actions": "Actions",
        "refresh": "Refresh",
        "download_first": "Download First",
        "download_all": "Download All",
        "stop_download": "Stop",
        "clear_queue": "Clear Queue",
        "logs": "Logs",
        "link": "Link",
        "save_path": "Save Path",
        "action": "Action",
        "default_prefix": "Default",
        "cookie_not_set": "Cookie file not specified",
        "warn": "Warning",
        "info": "Info",
        "error": "Error",
        "confirm": "Confirm",
        "input_url_required": "Please enter a URL",
        "clipboard_empty": "Clipboard is empty",
        "cannot_read_clipboard": "Cannot read clipboard: {error}",
        "manage_queue_item": "Manage Queue Item",
        "link_label": "Link:",
        "save_path_hint": "Save path (empty = use default)",
        "choose_save_location": "Choose Save Folder",
        "save": "Save",
        "delete_link": "Delete Link",
        "close": "Close",
        "update_save_path_ok": "✓ Save path updated: {path}",
        "default_path_label": "default path",
        "confirm_delete_link": "Delete this link?",
        "confirm_clear_queue": "Clear the whole queue?",
        "queue_cleared": "✓ Queue cleared",
        "choose_cookie_title": "Choose Cookie File",
        "cookie_copied": "✓ Cookie copied to config folder: {path}",
        "cookie_using_existing": "✓ Using cookie from config folder: {path}",
        "cannot_set_cookie": "Cannot set cookie file: {error}",
        "choose_default_download_dir": "Choose default download folder",
        "default_download_path_updated": "✓ Default download path updated: {path}",
        "cannot_save_default_path": "Cannot save default path: {error}",
        "default_download_path_empty": "Default download path cannot be empty",
        "cannot_set_default_path": "Cannot set default path: {error}",
        "cookie_missing_skip": "⚠ Cookie file not found, skip cookies argument: {path}",
        "cookie_not_set_skip": "ℹ No cookie file specified, continue without cookies",
        "yt_dlp_not_found": "❌ yt-dlp not found. Please install it first",
        "download_failed_title": "Download Failed",
        "download_failed_debug_retry": "Download failed. Run one debug retry?\n-v will be added automatically for detailed logs.",
        "preparing": "Preparing",
        "detecting": "Detecting",
        "download_failed": "❌ Download failed",
        "debug_retry_start": "▶ Start debug retry (-v)",
        "debug_retrying": "Retrying with debug",
        "failed": "Failed",
        "busy_downloading": "A download is already in progress",
        "queue_empty_no_download": "Queue is empty, nothing to download",
        "download_complete_removed": "✓ Download complete and removed from queue",
        "download_failed_keep": "❌ Download failed, item remains in queue",
        "confirm_download_all": "Download all {count} links in queue?",
        "download_failed_stop_queue": "❌ Download failed, queue processing stopped",
        "all_downloads_done": "\n✓ All downloads completed!",
        "confirm_stop_download": "Stop current download?",
        "download_stopped": "\n⚠ Download stopped",
        "queue_refreshed": "✓ Queue refreshed, total {count} links",
        "language_switched": "✓ UI language switched to: {language}",
        "queue_msg_empty_link": "Link is empty",
        "queue_msg_exists": "Link already exists: {value}",
        "queue_msg_added": "Added: {value}",
        "queue_msg_removed": "Removed: {value}",
        "queue_msg_invalid_index": "Invalid index",
        "queue_msg_save_path_updated": "Save path updated",
    },
}

# 默认保存路径
def get_system_downloads_path():
    """获取系统当前 Downloads 目录，兼容用户在 Windows 属性中重定位后的路径。"""
    if os.name != "nt":
        return str(Path.home() / "Downloads")

    # 优先读取 Windows Known Folder，能够跟随“位置”页签的实际重定向路径。
    try:
        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", ctypes.c_uint32),
                ("Data2", ctypes.c_uint16),
                ("Data3", ctypes.c_uint16),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        def _guid_from_string(value):
            import uuid

            u = uuid.UUID(value)
            data4 = (ctypes.c_ubyte * 8)(*u.bytes[8:])
            return GUID(
                (u.time_low & 0xFFFFFFFF),
                (u.time_mid & 0xFFFF),
                (u.time_hi_version & 0xFFFF),
                data4,
            )

        path_ptr = ctypes.c_wchar_p()
        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32
        downloads_guid = _guid_from_string("374DE290-123F-4565-9164-39C4925E467B")

        hr = shell32.SHGetKnownFolderPath(
            ctypes.byref(downloads_guid),
            0,
            None,
            ctypes.byref(path_ptr),
        )
        if hr == 0 and path_ptr.value:
            result = str(Path(path_ptr.value))
            ole32.CoTaskMemFree(path_ptr)
            return result
    except Exception:
        pass

    # 兜底：读取用户目录下 Downloads。
    return str(Path.home() / "Downloads")


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
        self.language = self._load_language()
        self.root.title(self.tr("app_title"))
        self.root.geometry("1000x780")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")

        self.queue = DownloadQueue()
        self.is_downloading = False
        self.current_download_thread = None
        self.current_process = None
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text = tk.StringVar(value=self.tr("waiting"))
        self.list_progress_var = tk.DoubleVar(value=0.0)
        self.list_progress_text = tk.StringVar(value=self.tr("waiting"))
        self.current_url_var = tk.StringVar(value=self.tr("idle_download"))
        self.default_save_path_var = tk.StringVar(value=self._load_default_save_path())
        self.cookie_file_var = tk.StringVar(value=self._normalize_cookie_display_text(self._load_cookie_file()))
        self.language_display_var = tk.StringVar(value=LANGUAGE_DISPLAY.get(self.language, "简体中文"))
        self._playlist_detected = False
        self.main_frame = None

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.refresh_queue_display()

    def tr(self, key, **kwargs):
        table = I18N.get(self.language, I18N["zh_cn"])
        fallback = I18N["zh_cn"].get(key, key)
        text = table.get(key, fallback)
        if kwargs:
            return text.format(**kwargs)
        return text

    def _load_language(self):
        settings_path = CONFIG_DIR / SETTINGS_FILE
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    value = (data.get("language") or "").strip().lower()
                    if value in SUPPORTED_LANGUAGES:
                        return value
            except Exception:
                pass
        return "zh_cn"

    def _is_cookie_placeholder(self, text):
        value = (text or "").strip()
        return value in {
            "",
            COOKIE_NOT_SET_SENTINEL,
            I18N["zh_cn"]["cookie_not_set"],
            I18N["en_us"]["cookie_not_set"],
        }

    def _normalize_cookie_display_text(self, raw_cookie_value):
        if self._is_cookie_placeholder(raw_cookie_value):
            return self.tr("cookie_not_set")
        return raw_cookie_value

    def _localize_queue_message(self, msg):
        if self.language != "en_us":
            return msg
        text = (msg or "").strip()
        if text == "链接为空":
            return self.tr("queue_msg_empty_link")
        if text.startswith("链接已存在: "):
            return self.tr("queue_msg_exists", value=text[len("链接已存在: "):])
        if text.startswith("已添加: "):
            return self.tr("queue_msg_added", value=text[len("已添加: "):])
        if text.startswith("已移除: "):
            return self.tr("queue_msg_removed", value=text[len("已移除: "):])
        if text == "无效的索引":
            return self.tr("queue_msg_invalid_index")
        if text == "保存路径已更新":
            return self.tr("queue_msg_save_path_updated")
        return msg

    def _apply_language(self):
        selected_display = self.language_display_var.get()
        new_language = "zh_cn"
        for code, label in LANGUAGE_DISPLAY.items():
            if label == selected_display:
                new_language = code
                break

        if new_language == self.language:
            return

        if self._is_cookie_placeholder(self.cookie_file_var.get()):
            self.cookie_file_var.set(COOKIE_NOT_SET_SENTINEL)

        self.language = new_language
        self.cookie_file_var.set(self._normalize_cookie_display_text(self.cookie_file_var.get()))
        self.progress_text.set(self.tr("waiting"))
        self.list_progress_text.set(self.tr("waiting"))
        self.current_url_var.set(self.tr("idle_download"))
        self._save_settings()
        self.root.title(self.tr("app_title"))
        self.setup_ui(rebuild=True)
        self.refresh_queue_display()
        self.update_ui_state()
        self.log_message(self.tr("language_switched", language=LANGUAGE_DISPLAY.get(self.language, self.language)))

    def setup_ui(self, rebuild=False):
        if rebuild and self.main_frame is not None:
            self.main_frame.destroy()

        main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame = main_frame
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        info_frame = ttk.LabelFrame(main_frame, text=self.tr("queue_info"), padding="10")
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for c in range(4):
            info_frame.columnconfigure(c, weight=1)

        ttk.Label(info_frame, text=self.tr("queue_count")).grid(row=0, column=0, sticky="w")
        self.info_label = ttk.Label(info_frame, text="0", foreground="blue", font=("Arial", 12, "bold"))
        self.info_label.grid(row=0, column=1, sticky="w", padx=(6, 0))

        ttk.Label(info_frame, text=self.tr("download_status")).grid(row=0, column=2, sticky="e")
        self.status_label = ttk.Label(info_frame, text=self.tr("ready"), foreground="green", font=("Arial", 12, "bold"))
        self.status_label.grid(row=0, column=3, sticky="w", padx=(6, 0))

        ttk.Label(info_frame, text=self.tr("current_download")).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.current_label = ttk.Label(info_frame, textvariable=self.current_url_var, foreground="black")
        self.current_label.grid(row=1, column=1, columnspan=3, sticky="w", pady=(6, 0))

        self.progress_bar = ttk.Progressbar(info_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))
        self.progress_label = ttk.Label(info_frame, textvariable=self.progress_text, foreground="gray")
        self.progress_label.grid(row=2, column=3, sticky="w", padx=(6, 0))

        ttk.Label(info_frame, text=self.tr("list_progress")).grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.list_progress_bar = ttk.Progressbar(info_frame, variable=self.list_progress_var, maximum=100)
        self.list_progress_bar.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(6, 0))
        self.list_progress_label = ttk.Label(info_frame, textvariable=self.list_progress_text, foreground="gray")
        self.list_progress_label.grid(row=3, column=3, sticky="w", padx=(6, 0), pady=(6, 0))

        input_frame = ttk.LabelFrame(main_frame, text=self.tr("add_link"), padding="10")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text=self.tr("url")).grid(row=0, column=0, sticky="w")
        self.url_entry = ttk.Entry(input_frame)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=(10, 10))
        self.url_entry.bind("<Return>", lambda e: self.add_url_from_entry())

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        ttk.Button(button_frame, text=self.tr("add"), width=8, command=self.add_url_from_entry).pack(side="left", padx=2)
        ttk.Button(button_frame, text=self.tr("from_clipboard"), width=12, command=self.add_from_clipboard).pack(side="left", padx=2)

        ttk.Label(input_frame, text=self.tr("default_download_path")).grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.default_path_entry = ttk.Entry(input_frame, textvariable=self.default_save_path_var)
        self.default_path_entry.grid(row=1, column=1, sticky="ew", padx=(10, 10), pady=(10, 0))

        default_path_btn_frame = ttk.Frame(input_frame)
        default_path_btn_frame.grid(row=1, column=2, sticky="ew", padx=(5, 0), pady=(10, 0))
        ttk.Button(default_path_btn_frame, text=self.tr("choose_dir"), width=12, command=self.choose_default_dir).pack(side="left", padx=2)
        ttk.Button(default_path_btn_frame, text=self.tr("save_default"), width=12, command=self.apply_default_save_path).pack(side="left", padx=2)

        ttk.Label(input_frame, text=self.tr("cookie_file")).grid(row=2, column=0, sticky="w", pady=(10, 0))
        self.cookie_entry = ttk.Entry(input_frame, textvariable=self.cookie_file_var)
        self.cookie_entry.grid(row=2, column=1, sticky="ew", padx=(10, 10), pady=(10, 0))

        cookie_btn_frame = ttk.Frame(input_frame)
        cookie_btn_frame.grid(row=2, column=2, sticky="ew", padx=(5, 0), pady=(10, 0))
        ttk.Button(cookie_btn_frame, text=self.tr("choose_cookie"), width=12, command=self.choose_cookie_file).pack(side="left", padx=2)

        ttk.Label(input_frame, text=self.tr("language")).grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.lang_combobox = ttk.Combobox(
            input_frame,
            textvariable=self.language_display_var,
            values=[LANGUAGE_DISPLAY["zh_cn"], LANGUAGE_DISPLAY["en_us"]],
            state="readonly",
            width=20,
        )
        self.lang_combobox.grid(row=3, column=1, sticky="w", padx=(10, 10), pady=(10, 0))
        ttk.Button(input_frame, text=self.tr("apply_language"), width=12, command=self._apply_language).grid(row=3, column=2, sticky="w", padx=(5, 0), pady=(10, 0))

        queue_frame = ttk.LabelFrame(main_frame, text=self.tr("queue_list"), padding="10")
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

        action_frame = ttk.LabelFrame(main_frame, text=self.tr("actions"), padding="10")
        action_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        btn_col = 0
        ttk.Button(action_frame, text=self.tr("refresh"), command=self.refresh_queue_display).grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        ttk.Button(action_frame, text=self.tr("download_first"), command=self.download_first, style="Accent.TButton").grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        ttk.Button(action_frame, text=self.tr("download_all"), command=self.download_all, style="Accent.TButton").grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        self.stop_button = ttk.Button(action_frame, text=self.tr("stop_download"), command=self.stop_download, state="disabled")
        self.stop_button.grid(row=0, column=btn_col, padx=5, pady=5)
        btn_col += 1
        ttk.Button(action_frame, text=self.tr("clear_queue"), command=self.clear_queue).grid(row=0, column=btn_col, padx=5, pady=5)

        log_frame = ttk.LabelFrame(main_frame, text=self.tr("logs"), padding="10")
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
        ttk.Label(header, text=self.tr("link"), width=70).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text=self.tr("save_path"), width=30).grid(row=0, column=2, sticky="w")
        ttk.Label(header, text=self.tr("action"), width=10).grid(row=0, column=3, sticky="w")

        for i, item in enumerate(self.queue.queue, 1):
            row = ttk.Frame(self.queue_container, padding=(0, 2))
            row.grid(row=i, column=0, sticky="ew")
            row.columnconfigure(1, weight=1)

            ttk.Label(row, text=f"{i}", width=4).grid(row=0, column=0, sticky="w")
            ttk.Label(row, text=item.get("url"), width=70, wraplength=600, anchor="w").grid(row=0, column=1, sticky="w")
            default_path_text = self.default_save_path_var.get().strip() or get_system_downloads_path()
            path_text = item.get("save_path") or f"{self.tr('default_prefix')}: {self._short_path(default_path_text)}"
            ttk.Label(row, text=path_text, width=30, anchor="w", foreground="gray").grid(row=0, column=2, sticky="w")
            ttk.Button(row, text=self.tr("action"), command=lambda idx=i-1: self.open_item_actions(idx)).grid(row=0, column=3, padx=4)

        self.info_label.config(text=str(self.queue.size()))
        self.log_message(self.tr("queue_refreshed", count=self.queue.size()))

    def add_url_from_entry(self):
        url = self.url_entry.get().strip()
        if url:
            success, msg = self.queue.add_link(url)
            display_msg = self._localize_queue_message(msg)
            self.log_message(display_msg)
            if success:
                self.url_entry.delete(0, tk.END)
                self.refresh_queue_display()
            else:
                messagebox.showwarning(self.tr("warn"), display_msg)
        else:
            messagebox.showwarning(self.tr("warn"), self.tr("input_url_required"))

    def add_from_clipboard(self):
        try:
            url = str(cb.paste()).strip()
            if url:
                success, msg = self.queue.add_link(url)
                display_msg = self._localize_queue_message(msg)
                self.log_message(display_msg)
                if success:
                    self.refresh_queue_display()
                else:
                    messagebox.showinfo(self.tr("info"), display_msg)
            else:
                messagebox.showwarning(self.tr("warn"), self.tr("clipboard_empty"))
        except Exception as e:
            messagebox.showerror(self.tr("error"), self.tr("cannot_read_clipboard", error=e))

    def open_item_actions(self, index):
        item = self.queue.get_link(index)
        if not item:
            return

        win = tk.Toplevel(self.root)
        win.title(self.tr("manage_queue_item"))
        win.geometry("620x240")
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text=self.tr("link_label")).pack(anchor="w", padx=10, pady=(10, 2))
        ttk.Label(win, text=item.get("url"), wraplength=580, foreground="blue").pack(anchor="w", padx=10)

        ttk.Label(win, text=self.tr("save_path_hint")).pack(anchor="w", padx=10, pady=(12, 2))
        path_var = tk.StringVar(value=item.get("save_path") or "")
        path_entry = ttk.Entry(win, textvariable=path_var, width=80)
        path_entry.pack(anchor="w", padx=10, fill="x")

        def choose_dir():
            directory = filedialog.askdirectory(title=self.tr("choose_save_location"))
            if directory:
                path_var.set(directory)

        ttk.Button(win, text=self.tr("choose_dir"), command=choose_dir).pack(anchor="w", padx=10, pady=6)

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", pady=10, padx=10)

        def save_changes():
            new_path = path_var.get().strip() or None
            ok, msg = self.queue.update_save_path(index, new_path)
            if ok:
                self.log_message(self.tr("update_save_path_ok", path=(new_path or self.tr("default_path_label"))))
                self.refresh_queue_display()
                win.destroy()
            else:
                messagebox.showerror(self.tr("error"), self._localize_queue_message(msg))

        def delete_item():
            if messagebox.askyesno(self.tr("confirm"), self.tr("confirm_delete_link")):
                ok, msg = self.queue.remove_link(index)
                self.log_message(self._localize_queue_message(msg))
                self.refresh_queue_display()
                win.destroy()

        ttk.Button(btn_frame, text=self.tr("save"), style="Accent.TButton", command=save_changes).pack(side="left", padx=4)
        ttk.Button(btn_frame, text=self.tr("delete_link"), command=delete_item).pack(side="left", padx=4)
        ttk.Button(btn_frame, text=self.tr("close"), command=win.destroy).pack(side="right", padx=4)

    def clear_queue(self):
        if messagebox.askyesno(self.tr("confirm"), self.tr("confirm_clear_queue")):
            self.queue.queue = []
            self.queue.save_queue()
            self.log_message(self.tr("queue_cleared"))
            self.refresh_queue_display()

    def _load_default_save_path(self):
        settings_path = CONFIG_DIR / SETTINGS_FILE
        system_downloads = get_system_downloads_path()
        legacy_downloads = str(Path.home() / "Downloads")
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    path = (data.get("default_save_path") or "").strip()
                    if path:
                        # 兼容历史配置：如果保存的是旧的 Home/Downloads 且已失效，自动切换到系统真实 Downloads。
                        if path == legacy_downloads and path != system_downloads and not os.path.exists(path):
                            return system_downloads
                        return path
            except Exception as e:
                print(f"加载设置失败: {e}")
        return system_downloads

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

        return COOKIE_NOT_SET_SENTINEL

    def _save_settings(self):
        settings_path = CONFIG_DIR / SETTINGS_FILE
        cookie_text = (self.cookie_file_var.get() or "").strip()
        if self._is_cookie_placeholder(cookie_text):
            cookie_value = DEFAULT_COOKIE_FILE
        else:
            cookie_path = Path(cookie_text)
            if cookie_path.is_absolute() and cookie_path.parent == CONFIG_DIR:
                cookie_value = cookie_path.name
            else:
                cookie_value = str(cookie_path)
        payload = {
            "default_save_path": self.default_save_path_var.get().strip() or get_system_downloads_path(),
            "cookie_file": cookie_value,
            "language": self.language,
            "last_updated": datetime.now().isoformat(),
        }
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def choose_cookie_file(self):
        file_path = filedialog.askopenfilename(
            title=self.tr("choose_cookie_title"),
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        src = Path(file_path)
        dst = CONFIG_DIR / src.name
        try:
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
                self.log_message(self.tr("cookie_copied", path=dst))
            else:
                self.log_message(self.tr("cookie_using_existing", path=dst))
            self.cookie_file_var.set(str(dst))
            self._save_settings()
        except Exception as e:
            messagebox.showerror(self.tr("error"), self.tr("cannot_set_cookie", error=e))

    def choose_default_dir(self):
        directory = filedialog.askdirectory(title=self.tr("choose_default_download_dir"))
        if directory:
            self.default_save_path_var.set(directory)
            try:
                os.makedirs(directory, exist_ok=True)
                self._save_settings()
                self.log_message(self.tr("default_download_path_updated", path=directory))
            except Exception as e:
                messagebox.showerror(self.tr("error"), self.tr("cannot_save_default_path", error=e))

    def apply_default_save_path(self):
        new_path = self.default_save_path_var.get().strip()
        if not new_path:
            messagebox.showwarning(self.tr("warn"), self.tr("default_download_path_empty"))
            return
        try:
            os.makedirs(new_path, exist_ok=True)
            self._save_settings()
            self.log_message(self.tr("default_download_path_updated", path=new_path))
        except Exception as e:
            messagebox.showerror(self.tr("error"), self.tr("cannot_set_default_path", error=e))

    def _stream_download(self, url, save_path, progress_callback, debug_mode=False):
        ensure_yt_dlp_updated()
        cmd = ["yt-dlp", "--newline", "-4", url]

        cookie_text = (self.cookie_file_var.get() or "").strip()
        if not self._is_cookie_placeholder(cookie_text):
            cookie_path = Path(cookie_text)
            if cookie_path.exists():
                cmd.extend(["--cookies", str(cookie_path)])
            else:
                progress_callback(self.tr("cookie_missing_skip", path=cookie_path))
        else:
            progress_callback(self.tr("cookie_not_set_skip"))

        cmd.extend(["-P", save_path, "--js-runtimes", "node"])
        if debug_mode:
            cmd.append("-v")

        # 在日志中显示完整命令，便于复现与排查
        progress_callback(f"$ {subprocess.list2cmdline(cmd)}")
        try:
            proc = subprocess.Popen(cmd, cwd=SCRIPT_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        except FileNotFoundError:
            progress_callback(self.tr("yt_dlp_not_found"))
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
                self.tr("download_failed_title"),
                self.tr("download_failed_debug_retry"),
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
        save_to = item.get("save_path") or self.default_save_path_var.get().strip() or get_system_downloads_path()
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
        self.root.after(0, self.progress_text.set, self.tr("preparing"))
        self.root.after(0, self.list_progress_var.set, 0)
        self.root.after(0, self.list_progress_text.set, self.tr("detecting"))
        success = self._stream_download(url, save_to, self._progress_handler)
        if (not success) and self.is_downloading:
            self.log_message(self.tr("download_failed"))
            if self._ask_debug_retry():
                self.log_message(self.tr("debug_retry_start"))
                self.root.after(0, self.progress_text.set, self.tr("debug_retrying"))
                success = self._stream_download(url, save_to, self._progress_handler, debug_mode=True)
        if not self._playlist_detected:
            if success:
                self.root.after(0, self.list_progress_var.set, 100)
                self.root.after(0, self.list_progress_text.set, "1/1")
            else:
                self.root.after(0, self.list_progress_text.set, self.tr("failed"))
        return success

    def download_first(self):
        if self.is_downloading:
            messagebox.showwarning(self.tr("warn"), self.tr("busy_downloading"))
            return
        item = self.queue.get_first_link()
        if not item:
            messagebox.showwarning(self.tr("warn"), self.tr("queue_empty_no_download"))
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
            self.log_message(self.tr("download_complete_removed"))
        else:
            self.log_message(self.tr("download_failed_keep"))
        self.is_downloading = False
        self.refresh_queue_display()
        self.update_ui_state()

    def download_all(self):
        if self.is_downloading:
            messagebox.showwarning(self.tr("warn"), self.tr("busy_downloading"))
            return
        if self.queue.is_empty():
            messagebox.showwarning(self.tr("warn"), self.tr("queue_empty_no_download"))
            return
        if messagebox.askyesno(self.tr("confirm"), self.tr("confirm_download_all", count=self.queue.size())):
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
                self.log_message(self.tr("download_complete_removed"))
            else:
                self.log_message(self.tr("download_failed_stop_queue"))
                break
            self.refresh_queue_display()
        self.is_downloading = False
        if self.queue.is_empty():
            self.log_message(self.tr("all_downloads_done"))
        self.update_ui_state()

    def stop_download(self):
        if not self.is_downloading:
            return
        if messagebox.askyesno(self.tr("confirm"), self.tr("confirm_stop_download")):
            self.is_downloading = False
            if self.current_process:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass
            self.log_message(self.tr("download_stopped"))
            self.update_ui_state()

    def update_ui_state(self):
        self.root.after(0, self._update_ui_state)

    def _update_ui_state(self):
        if self.is_downloading:
            self.status_label.config(text=self.tr("downloading"), foreground="orange")
            self.stop_button.config(state="normal")
        else:
            self.status_label.config(text=self.tr("ready"), foreground="green")
            self.stop_button.config(state="disabled")
            self.current_url_var.set(self.tr("idle_download"))
            if self.progress_var.get() >= 100:
                self.progress_text.set(self.tr("done"))

    def log_message(self, msg):
        self.root.after(0, self._log_message, msg)

    def _log_message(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def on_close(self):
        # 程序退出前保存默认路径，避免未点击“保存默认”导致配置丢失
        current_path = self.default_save_path_var.get().strip() or get_system_downloads_path()
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
