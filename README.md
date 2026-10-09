# 🚴 Cycling Route Video (骑行路书动态视频生成器)

> **Universal Cycling Route Video Generator** · 将任意骑行 GPX 路书与照片、短视频素材，一键转换为专业级双屏全景回顾视频。支持单日短途、周边刷山、多日长途以及环岛远征！

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Web%20%7C%20macOS%20(.dmg)%20%7C%20CLI-rose)](https://github.com/hy4015/cycling-route-video)
[![Cloudflare Pages](https://img.shields.io/badge/Deploy-Cloudflare%20Pages-orange)](https://pages.cloudflare.com/)

---

## ✨ 核心特性

- 🗺️ **左屏动态轨迹与遥测仪表盘 (960x1080)**：
  - **高清真实地图底图切换**：内置 4 种免 Key 高清地理底图（🛰️ 卫星实景、🌑 暗黑极简、🏔️ 等高地形、🗺️ 明亮街道），采用 Web Mercator 投影与 GPX 轨迹实现 1:1 像素级地理注册；
  - **自定义路线抬头文字**：支持在左上角 HUD 药丸标签中自由输入中英文标题（如“环千岛湖骑行”、“台湾环岛·DAY 01”），药丸宽度与字号自适应缩放；
  - 自动 Bounding-Box 自适应投影，无论是 20km 城市夜骑还是 1,100km 环岛，底图与轨迹均自适应最佳视口；
  - 实时发光渐进路线、脉冲骑行指示标、动态速度/海拔/爬升/里程 HUD；
  - 终点胜利冲线金色徽章 (`★ XX.X km 骑行达成！`)。
- 🎞️ **右屏经典 35mm 胶卷画报卷轴 (960x1080)**：
  - **4 款经典胶卷风格随心切换**：
    1. **方案 1 柯达 Portra 400**：暖黄色调 `#ebb428`，经典人像纪实；
    2. **方案 2 柯达 Gold 200**：浓郁金黄 `#f59e0b`，阳光街道漫游；
    3. **方案 3 富士 Superia 400**：清透青绿 `#10b981`，山林海风巡航；
    4. **方案 4 依尔福 HP5 Plus**：纯正黑白 `#f1f5f9`，硬朗光影公路；
  - **纯正 44px 间隙胶片标印字**：严格位于素材接缝之间（胶卷品牌、安全片基标识、胶卷流水号与实心箭头），**画面内容 100% 纯净零遮挡**；
  - 自动识别横竖构图：横幅大片单幅全宽展示 (872x484)，竖幅素材自动双联杂志拼贴 (428x484 x 2)；
  - 自动 EXIF 纠偏，杜绝旋转倒立。
- 🎵 **智能背景音乐 (BGM) 与视频原声混音**：
  - 内置 3 首高品质免商业版权预设曲目（公路风原声吉他、海滨公路电音、山野热血远征）；
  - 支持试听播放与自定义上传 MP3 / M4A；
  - 素材视频原声保留并以 80% 音量播放，首尾带有 0.3s 平滑淡入淡出。
- 🛡️ **双端架构支持 (Web 端防崩溃保护 + 桌面端满血加速)**：
  - **Web 端 (Cloudflare Pages)**：图片单张 $\le 10\text{MB}$，视频单个 $\le 100\text{MB}$ 且时长 $\le 10\text{s}$，保护浏览器内存不闪退；
  - **macOS 桌面端 (.dmg)**：突破大小限制，直接跑满 Apple Silicon / GPU 原生硬件加速。

---

## 🏗️ 架构模式对比

| 模式 | 运行环境 | 适用场景 | 优势 |
| :--- | :--- | :--- | :--- |
| **方案 B：Web 端 (Cloudflare Pages)** | 纯浏览器端 (HTML5 / Canvas / WebCodecs) | 日常短途、几十公里周末骑行、快速分享 | 零安装，打开网页就能用，零服务器成本 |
| **方案 C：macOS 桌面端 (.dmg)** | 本地原生 App (Electron / Tauri) | 摄影爱好者、几百公里长途、大量高清素材 | 原片直读，无素材大小时长限制，GPU 硬件满血加速 |
| **CLI 核心引擎** | Python 3 + FFmpeg | 自动化批量脚本、车队专属定制、极客调优 | 参数高度可定制，渲染效率最高 |

---

## 🚀 快速开始

### 1. Web 端本地预览与 Cloudflare Pages 部署

网页端代码位于 `web/` 目录，完全静态化，无需打包构建，即开即用：

```bash
# 本地预览测试
cd web
npx serve .
# 浏览器访问 http://localhost:3000
```

#### ☁️ 部署到 Cloudflare Pages（30秒完成）：
1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/) ➔ 进入 **Workers & Pages**；
2. 点击 **Create application** ➔ 选择 **Pages** ➔ **Connect to Git**；
3. 选择本仓库 `hy4015/cycling-route-video`；
4. 在构建配置中填写：
   - **Framework preset**: None
   - **Build command**: (留空)
   - **Build output directory**: `web`
5. 点击 **Save and Deploy**，即可获得永久免费、全球 CDN 极速访问的在线视频生成器！

---

### 2. 本地 CLI 硬件加速极速生成 (Python)

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 一键生成你的骑行回顾大片
python3 -m engine.pipeline \
  --gpx "/path/to/your_route.gpx" \
  --media "/path/to/your_photos_and_videos" \
  --output "./my_cycling_recap.mp4"

# 进阶参数：指定背景音乐与总时长
python3 -m engine.pipeline \
  --gpx "./sample.gpx" \
  --media "./media_folder" \
  --output "./recap.mp4" \
  --bgm coastal \
  --duration 60.0
```

#### 支持的 `--bgm` 选项：
- `default`: 公路风原声吉他扫弦（默认，轻快自由）
- `coastal`: 海滨公路节奏电音（活力刷街）
- `epic`: 山野热血史诗（攻顶挑战）
- 或直接传入本地自选音频路径：`--bgm "/path/to/my_song.mp3"`

---

### 3. 构建 macOS 桌面安装包 (.dmg)

```bash
cd desktop
npm install
npm run dist
```
构建完成后，在 `desktop/dist/` 目录下将生成 `Cycling Route Video Installer.dmg` 安装包，双击拖入应用程序文件夹即可使用。

---

## 🤖 Antigravity Skill 智能体技能集成

本项目已预置 Antigravity Skill 规格定义（位于 `.agents/skills/cycling-route-video/SKILL.md`）。在 Antigravity 中只需给出一句指令，例如：

> *“帮我把这趟千岛湖骑行的 gpx 和照片生成一段 90 秒的柯达胶片风回顾视频”*

助手即可自动激活该技能并调用底层引擎自动完成全流程制作与样帧交付。

---

## 📂 项目结构

```text
cycling-route-video/
├── .agents/skills/cycling-route-video/
│   └── SKILL.md             # Antigravity 技能指南 (Prompt & Runbook)
├── engine/                  # Python 通用渲染引擎内核
│   ├── gpx_parser.py        # GPX 轨迹分析、高程计算与视口自适应
│   ├── map_engine.py        # 动态轨迹线、脉冲光标、HUD 数据仪表盘
│   ├── filmstrip_engine.py  # 柯达 Portra 400 胶片标与双联拼贴排版
│   ├── media_processor.py   # 智能方向校正、比例缩放与安全留白裁切
│   ├── audio_mixer.py       # 视频原声 80% 淡入淡出、BGM 混音避让
│   └── pipeline.py          # 端到端 CLI 执行主入口
├── web/                     # Cloudflare Pages 纯前端网页 (即开即用)
│   ├── index.html           # 现代深色骑行主题交互界面
│   └── public/audio/        # 预设免商用 BGM 音频库
├── desktop/                 # macOS 桌面端应用打包配置 (.dmg)
│   ├── package.json
│   └── main.js              # Electron 原生窗口桥接
├── resources/               # 共享音频与字体资源
│   └── bgm/
├── requirements.txt         # Python 依赖项
├── LICENSE                  # MIT 开源协议
└── README.md                # 项目文档
```

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。欢迎骑友与开发者 Star、Fork 与提 PR！
