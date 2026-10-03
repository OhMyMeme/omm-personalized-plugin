"""OhMyMeme 个性化插件：启动动画 / 背景 / 字体 / 顶栏按钮布局。

- 背景与字体：保存后立即生效（宿主推送 omm-plugin-refresh，apply.js 重新拉取设置）
- 启动动画 / 按钮布局：在 on_load 时注册，需重启软件生效
- 窗口大小由宿主「基础设置 → 窗口 → 允许调整窗口大小」控制（拖动边框调整）
"""

import shutil
from pathlib import Path

DEFAULTS = {
    "intro_video": "",
    "intro_duration": 0,
    "intro_bg": "",
    "bg_color": "",
    "font_family": "",
    "font_size": 0,
    "hide_sort": False,
    "hide_select": False,
    "hide_upload": False,
    "hide_download": False,
    "hide_import": False,
    "hide_refresh": False,
    "btn_order": "",
}

_VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".avi"}
_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".avif"}
_MAX_INTRO_BYTES = 100 * 1024 * 1024

_HIDE_KEYS = ("sort", "select", "upload", "download", "import", "refresh")
_RESTART_KEYS = frozenset(["intro_video", "intro_bg", "btn_order"] + [
    "hide_" + k for k in _HIDE_KEYS
])

_FONT_OPTIONS = [
    ("", "默认（跟随系统）"),
    ("Microsoft YaHei", "微软雅黑"),
    ("Microsoft YaHei UI", "微软雅黑 UI"),
    ("SimHei", "黑体"),
    ("SimSun", "宋体"),
    ("KaiTi", "楷体"),
    ("FangSong", "仿宋"),
    ("DengXian", "等线"),
    ("Microsoft JhengHei", "微软雅黑繁体"),
    ("PingFang SC", "苹方（macOS）"),
    ("Noto Sans CJK SC", "思源黑体"),
    ("Source Han Sans SC", "Source Han Sans"),
    ("HarmonyOS Sans SC", "HarmonyOS Sans"),
    ("MiSans", "MiSans"),
    ("Arial", "Arial"),
    ("Segoe UI", "Segoe UI"),
    ("Consolas", "Consolas"),
    ("JetBrains Mono", "JetBrains Mono"),
    ("Cascadia Code", "Cascadia Code"),
]

_ctx = None


def _int(value, lo, hi):
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return 0
    return n if lo <= n <= hi else 0


def _prefs():
    d = dict(DEFAULTS)
    if _ctx is not None:
        d.update(_ctx.settings)
    return d


def get_prefs():
    """主窗口 API：apply.js 读取后应用背景/字体"""
    return _prefs()


def _is_image(ext):
    return ext in _IMAGE_EXTS


def _media_duration(path: Path, ext: str) -> int:
    """图片/动图在启动时的展示时长（ms）；视频返回 0 由 ended 触发收起"""
    if ext == ".gif":
        try:
            from PIL import Image, ImageSequence

            with Image.open(path) as im:
                total = 0
                for frame in ImageSequence.Iterator(im):
                    total += int(frame.info.get("duration") or 100)
                return max(total, 500)
        except Exception:
            return 6000
    if ext in _IMAGE_EXTS:
        return 2500
    return 0


def set_intro(path):
    """设置窗口 API：把选中的视频/图片/动图复制到插件数据目录并写入设置"""
    if _ctx is None:
        return {"ok": False, "error": "not_loaded"}
    src = Path(str(path))
    ext = src.suffix.lower()
    if ext not in _VIDEO_EXTS | _IMAGE_EXTS:
        return {"ok": False, "error": "unsupported_type"}
    if not src.is_file():
        return {"ok": False, "error": "file_not_found"}
    try:
        if src.stat().st_size > _MAX_INTRO_BYTES:
            return {"ok": False, "error": "too_large"}
    except OSError:
        return {"ok": False, "error": "file_not_found"}
    data_dir = _ctx.data_dir
    for old in data_dir.glob("intro.*"):
        try:
            old.unlink()
        except OSError:
            pass
    dst = data_dir / ("intro" + ext)
    try:
        shutil.copy2(src, dst)
    except OSError as e:
        return {"ok": False, "error": f"copy_failed: {e}"}
    duration = _media_duration(dst, ext)
    rel = "data/" + dst.name
    _ctx.save_settings({"intro_video": rel, "intro_duration": duration})
    return {"ok": True, "path": rel, "duration": duration}


def clear_intro():
    """设置窗口 API：移除自定义启动动画，恢复默认"""
    if _ctx is None:
        return {"ok": False, "error": "not_loaded"}
    for old in _ctx.data_dir.glob("intro.*"):
        try:
            old.unlink()
        except OSError:
            pass
    _ctx.save_settings({"intro_video": "", "intro_duration": 0})
    return {"ok": True}


def on_load(ctx):
    global _ctx
    _ctx = ctx
    p = _prefs()

    video = str(p.get("intro_video") or "").strip().replace("\\", "/").lstrip("/")
    if video and ".." not in video.split("/"):
        ext = Path(video).suffix.lower()
        ctx.set_startup_override(
            video_src="/plugins/" + ctx.id + "/" + video,
            duration_ms=_int(p.get("intro_duration"), 0, 600000) or None,
            media_type="image" if _is_image(ext) else "video" if ext else None,
        )
    intro_bg = str(p.get("intro_bg") or "").strip()
    if intro_bg:
        ctx.set_startup_override(bg_color=intro_bg)

    hide = [k for k in _HIDE_KEYS if p.get("hide_" + k)]
    order = {}
    for pair in str(p.get("btn_order") or "").split(","):
        if ":" not in pair:
            continue
        key, val = pair.split(":", 1)
        key = key.strip()
        if not key:
            continue
        try:
            order[key] = int(val.strip())
        except ValueError:
            continue
    if hide or order:
        ctx.register_button_constraints(hide=hide, order=order)

    ctx.register_settings_section(_section(ctx.id))
    ctx.register_main_api("get_prefs", get_prefs)
    ctx.register_settings_api("set_intro", set_intro)
    ctx.register_settings_api("clear_intro", clear_intro)
    ctx.register_js("main", "assets/apply.js")
    ctx.register_js("settings", "assets/settings.js")
    ctx.register_css("settings", "assets/settings.css")
    ctx.log("个性化设置已应用（背景/字体立即生效，其余需重启）")


def _section(pid):
    """设置页「插件 → 个性化」区块（字体下拉 / RGBA+HEX 颜色 / 启动动画文件选择）"""

    def chk(key, label):
        return (
            f'<div class="check-row"><label><input type="checkbox" '
            f'data-plugin="{pid}" data-key="{key}"> {label}</label></div>'
        )

    def color_widget(key, label, placeholder):
        return (
            f'<label style="display:block;font-size:12px;color:var(--fg-secondary);'
            f'margin-top:8px">{label}</label>'
            f'<div class="p-color" data-pcolor="{key}">'
            '<div class="p-color-top">'
            '<input type="color" class="p-cpick" value="#000000" tabindex="-1">'
            f'<input type="text" class="p-chex" data-plugin="{pid}" data-key="{key}" '
            f'placeholder="{placeholder}" spellcheck="false">'
            '<span class="p-cswatch"></span>'
            "</div>"
            '<div class="p-color-rgba">'
            '<span class="p-clab">R</span><input type="number" class="p-cr" min="0" max="255">'
            '<span class="p-clab">G</span><input type="number" class="p-cg" min="0" max="255">'
            '<span class="p-clab">B</span><input type="number" class="p-cb" min="0" max="255">'
            '<span class="p-clab">A</span><input type="range" class="p-ca" min="0" max="255">'
            '<span class="p-caval">255</span>'
            "</div>"
            "</div>"
        )

    font_select = (
        f'<select data-plugin="{pid}" data-key="font_family" class="p-font-select" '
        'style="width:100%;margin:4px 0 10px">'
        + "".join(
            f'<option value="{v}">{label}</option>' for v, label in _FONT_OPTIONS
        )
        + "</select>"
    )

    return (
        f'<div class="section" data-group="plugin" data-plugin="{pid}">'
        "<h3>个性化</h3>"
        '<p style="font-size:12px;color:var(--fg-secondary);line-height:1.6;'
        'margin-bottom:12px">背景与字体保存后立即生效；启动动画与按钮布局需重启。'
        "窗口大小请在「基础设置 → 窗口」开启「允许调整窗口大小」后拖动边框调整。</p>"
        '<label style="display:block;font-size:12px;color:var(--fg-secondary)">字体</label>'
        + font_select
        + '<label style="display:block;font-size:12px;color:var(--fg-secondary)">'
        "字号 px（0 = 不修改，仅影响未单独设置字号的元素）</label>"
        '<input type="number" data-plugin="'
        + pid
        + '" data-key="font_size" placeholder="0" style="width:100%;margin:4px 0 10px">'
        + color_widget("bg_color", "背景颜色（留空 = 不修改）", "#RRGGBB 或 #RRGGBBAA")
        + '<label style="display:block;font-size:12px;color:var(--fg-secondary);'
        'margin-top:12px">启动动画（视频 / 图片 / 动图，只播放一遍）</label>'
        '<div class="p-intro-row">'
        f'<input type="hidden" data-plugin="{pid}" data-key="intro_video" '
        'id="p-intro-value">'
        '<span class="p-intro-name" id="p-intro-name">未设置（默认动画）</span>'
        '<button class="btn btn-secondary btn-sm" type="button" '
        f"onclick=\"pIntroPick('video')\">选择视频</button>"
        '<button class="btn btn-secondary btn-sm" type="button" '
        f"onclick=\"pIntroPick('image')\">选择图片/动图</button>"
        '<button class="btn btn-secondary btn-sm" type="button" '
        'onclick="pIntroClear()">清除</button>'
        "</div>"
        '<div class="p-intro-preview" id="p-intro-preview"></div>'
        '<p style="font-size:11.5px;color:var(--muted);margin:4px 0 0;line-height:1.6">'
        "选择后自动复制到插件数据目录（<code>plugins_data/personalized/</code>）"
        "，源文件不受影响；视频播放完或图片展示结束后自动收起。</p>"
        + color_widget("intro_bg", "启动动画底色（留空 = 默认）", "#000000")
        + "<h4>按钮布局</h4>"
        + "".join(
            chk("hide_" + k, label)
            for k, label in [
                ("sort", "隐藏「拖拽排序」"),
                ("select", "隐藏「多选」"),
                ("upload", "隐藏「上传」"),
                ("download", "隐藏「下载」"),
                ("import", "隐藏「导入」"),
                ("refresh", "隐藏「刷新」"),
            ]
        )
        + '<label style="display:block;font-size:12px;color:var(--fg-secondary);'
        'margin-top:6px">自定义按钮顺序（key:order，逗号分隔）</label>'
        '<input type="text" data-plugin="'
        + pid
        + '" data-key="btn_order" placeholder="settings:10,import:90" '
        'style="width:100%;margin:4px 0 10px">'
        '<button class="btn" '
        f'onclick="pluginSaveSection(\'{pid}\')">保存插件设置</button>'
        "</div>"
    )


def on_settings_changed(delta):
    """设置页保存后调用（delta 为本次保存的增量）"""
    if _ctx is None:
        return
    if _RESTART_KEYS & set(delta):
        _ctx.log("启动动画/按钮布局已更新，重启软件后生效")


def on_unload():
    global _ctx
    _ctx = None
