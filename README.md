# 个性化 · OhMyMeme 官方插件

启动动画、背景、字体与顶栏按钮布局的个性化定制（OhMyMeme ≥ 0.7.0）。

## 安装

1. 下载本仓库文件夹，放入 **插件目录**（设置 → 插件 → 「打开插件目录」），确保最终路径为 `<插件目录>/personalized/plugin.json`。
2. 重启 OhMyMeme，设置 → 插件 中应看到「个性化 · v1.1.0 · 已启用」。

开发期也可把本仓库路径加入 `config.json` 的 `plugin_dirs` 数组直连，免复制。

## 功能与生效时机

| 设置项 | 键名 | 生效时机 |
| --- | --- | --- |
| 启动动画（视频/图片/动图） | `intro_video` | 重启后生效（选择文件自动复制到插件数据目录，存 `data/intro.<ext>`；留空 = 默认动画） |
| 启动动画底色 | `intro_bg` | 重启后生效（RGBA+HEX 颜色控件，留空 = 默认） |
| 背景颜色 | `bg_color` | **立即生效**（RGBA+HEX 颜色控件，同时覆盖主题 `--bg` 变量与 html/body 背景；留空 = 不修改） |
| 字体 | `font_family` | **立即生效**（常用中文字体下拉，选择器可滚动；自定义值以「（自定义）」选项保留） |
| 字号 | `font_size` | **立即生效**（px，仅影响未单独设置字号的元素；0 = 不修改） |
| 隐藏顶栏按钮 | `hide_sort/select/upload/download/import/refresh` | 重启后生效 |
| 自定义按钮顺序 | `btn_order` | 重启后生效（`key:order` 逗号分隔，如 `settings:10,import:90`；核心 key：`sort` `select` `upload` `download` `import` `refresh` `settings` `close`，默认 10/20/30/40/50/60/70/1000） |

设置页入口：设置 → 左栏「插件」→ 点击「个性化」展开折叠栏 → 修改 → 「保存插件设置」（右侧开关可停用本插件）。

窗口大小不再由本插件设置：设置 → 「窗口」→ 打开「允许调整窗口大小」后，直接拖动主窗口/设置窗口边框调整，尺寸自动持久化。

## 自定义启动动画

在「启动动画」行点「选择文件」，选视频（mp4/webm 等）或图片（png/jpg/gif/webp）。文件会自动复制到插件数据目录 `<数据目录>/plugins_data/personalized/`，无需手动管理；选择对话框由宿主 `plugin_pick_file` 提供（按媒体类型过滤）。视频播完自动收起；图片/动图按实际时长（GIF 逐帧解析，上限 15s）只播一遍后收起。「恢复默认」可清回内置动画。视频不可用时宿主最多 6s 后自动跳过，不会卡住启动。

## 实现说明

- `main.py` 在 `on_load` 时按设置注册启动动画（`startup` 权限）与按钮约束（`buttons` 权限）；启动媒体时长/类型（`startup_media_duration_ms`/`startup_media_type`）随 `get_init_data` 下发供前端定时收起。
- `assets/apply.js` 注入主窗口，通过 `pywebview.api.plugin_call('personalized', 'get_prefs', [])` 读取设置并生成样式；宿主在设置保存后推送 `omm-plugin-refresh` 事件与 `get_prefs` 一并驱动重新应用。
- `assets/settings.js` + `assets/settings.css` 注入设置窗口：颜色控件 RGBA 滑杆/数字与 HEX 输入双向联动、色块实时预览，字体下拉补存自定义值，启动动画预览（视频/图片内嵌播放）；宿主回填区块后派发 `omm-plugin-section-filled` 事件触发同步。
- 插件设置保存在 `%APPDATA%/OhMyMeme/plugins/personalized/settings.json`（宿主按插件 id 建文件夹，随用户配置），与插件代码分离，卸载前可单独备份该文件。

## 卸载

设置 → 插件 → 关闭开关即可停用；删除插件文件夹后重启即彻底移除（`%APPDATA%/OhMyMeme/plugins/personalized/` 设置与数据目录下 `plugins_data/personalized/` 可一并删除）。
