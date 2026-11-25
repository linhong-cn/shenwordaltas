# 深词光 · SHEN WORD ALTAS

> 一词一画，快乐背词 —— 深圳小学 1–6 年级英语词库（默认六年级）

**本项目是基于开源项目 [Word Atlas](https://github.com/designfuchen/word-atlas) 修改而来的衍生应用。** 页面结构、样式、FSRS 间隔复习算法与配套素材来自上游；词表、年级划分、品牌文案、启动页语音和多年级支持为本项目改编与新增。

- **本项目仓库**：<https://github.com/linhong-cn/shenwordaltas>（Public，分支 `main`；应用内 GitHub 入口也指向这里）
- 上游仓库：<https://github.com/designfuchen/word-atlas>（素材来源，署名链接按 CC BY 4.0 保留）
- 上游在线版：<https://0xlei.tech/words/>
- 当前应用：React + Vite + TypeScript，纯静态 PWA，可打包为 Capacitor iOS 工程

---

## 一、来源与署名（请保留）

依据本目录 [`CONTENT_LICENSE.md`](CONTENT_LICENSE.md) 与 [`LICENSE`](LICENSE)：

| 内容 | 授权 | 权利人 |
| --- | --- | --- |
| 源代码与界面设计 | [MIT](LICENSE) | `Copyright (c) 2026 Word Atlas contributors` |
| 词库释义、例句、搭配、分级、分类；插画；发音与例句录音 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | **`Word Atlas contributors — CC BY 4.0`** |
| Fraunces 字体 | SIL Open Font License 1.1 | 字体作者 |
| 其余依赖 | 各自原有授权 | 各自权利人 |

**署名要求**：`Word Atlas contributors — CC BY 4.0`，附授权链接，并说明是否做过修改。本 README 与「关于」页即为该说明：**已修改**，修改内容见下一节。

上游素材的附加说明（完整原文见 `CONTENT_LICENSE.md`，不可改写）：

- 内容由 AI 模型按项目规范生成（文本为大语言模型，插画为图像模型，录音为 ElevenLabs 合成语音），经过自动校验、未逐条人工审校，按现状提供，不作准确性担保。
- 录音授权仅覆盖这些完成的音频文件，不含底层声音模型、声音身份或任何人的肖像、人格权，也不表示声音提供方为本项目背书（英音 Alice、美音 Sarah）。
- 单个英文单词与通用词表本身不主张专有权；上游素材与任何考试主办方均无关联。

本项目新生成的启动页欢迎语音使用 Microsoft Edge 在线语音合成，不属于上游录音。

## 二、相对 Word Atlas 做了哪些修改

1. **词表替换**：按沪教牛津版（深圳用）新版教材整理 1–6 年级上下册词表，按单元归类，替换上游词表。
2. **素材重新匹配**：从上游按「精确匹配 → 词形变化 → 短语近义映射」复制插画、释义、例句与英美发音，未匹配的词留空并在匹配报告中列出；部分短语复用同根词的配图与详解，已在词条详情注明。
3. **分年级架构**：六个年级各自独立的 `public/atlas/g1` … `g6` 目录；`settings.grade` 默认 6；顶栏可切换年级；学习进度按 `gradeN-atlas` 数据集隔离。
4. **离线缓存适配**：`public/sw.js` 改为识别 `atlas/gN/{img,thumb,audio}/` 路径，并避免把 HTML 兜底页当 JSON 缓存。
5. **品牌与文案**：主名「深词光」，英文副标题 `SHEN WORD ALTAS`（项目内约定拼写），六个年级词库名统一为「深词光 · {年级}」；启动页为「走进深圳小学英语词库」，欢迎语音为「欢迎打开深圳小学英语大门」。
6. **iOS 与构建**：`vite.config.ts` 使用相对 `base`，保证 Capacitor 本地 scheme 下可加载；新增 `ios/` Capacitor 8 工程。
7. **去除上游考试相关表述**：应用文案、词条说明与语音中的相关措辞已替换为「深圳小学英语」，代码中的类名/注释也一并中性化；`CONTENT_LICENSE.md` 的法律声明按许可要求保留原文。

词表与素材的原始汇总资料（词表 Markdown、图片、音频、匹配报告）位于同级上级目录 `../小学六年级英语单词/`。

## 三、数据规模（实测）

| 年级 | 词条 | 单元 | 插画 | 音频文件 |
| --- | ---: | ---: | ---: | ---: |
| 一年级 | 322 | 24 | 252 | 953 |
| 二年级 | 315 | 24 | 256 | 950 |
| 三年级 | 303 | 16 | 262 | 1,009 |
| 四年级 | 305 | 18 | 279 | 1,046 |
| 五年级 | 267 | 20 | 239 | 833 |
| 六年级 | 368 | 12 | 351 | 1,206 |
| **合计** | **1,880** | **114** | **1,639** | **5,997** |

`public/atlas/` 约 224 MB，全部为本地静态资源，无需后端、无需账号。

## 四、目录结构

```
shenwordaltas/
├─ index.html                 入口（含一次性缓存清理脚本、主题初始化）
├─ capacitor.config.ts        Capacitor 配置
├─ vite.config.ts             相对 base、构建与字体配置
├─ src/
│  ├─ grades.ts               年级列表、标签、默认年级、datasetId
│  ├─ atlas/data.ts           按年级加载词库与媒体路径
│  ├─ store/                  localStorage 设置、进度、FSRS、备份导入导出
│  ├─ pages/                  Today / Atlas / Learn / Practice / Me / About
│  ├─ ui/                     GradePicker、Splash、EntryView、分享图等
│  ├─ galaxy/                 星图布局与配色
│  └─ styles/app.css          全部样式
├─ public/
│  ├─ atlas/g{1..6}/
│  │  ├─ index.json           年级索引（id/name/count/topics/words 等）
│  │  ├─ entries/{n}.json     词条分片，每 100 词一片
│  │  ├─ img/{id}.webp        插画
│  │  ├─ thumb/{id}.webp      缩略图
│  │  └─ audio/{uk,us,ex,ex2}/{id}.mp3   英音、美音、例句、拓展例句
│  ├─ sfx/                    界面音效、环境音、启动页语音
│  ├─ brand/                  品牌图与图标
│  ├─ sw.js                   Service Worker
│  └─ manifest.webmanifest    PWA 清单
├─ dist/                      构建产物（gitignore，发布用）
└─ ios/App/App.xcodeproj      Capacitor iOS 工程
```

## 五、操作说明

### 5.1 环境

Node.js 20+（开发机为 v22.22.2 / npm 10.9.7）。无需数据库、无需服务端。

```bash
cd /Users/hong/WorkBuddy/shenwordaltas
npm install
```

### 5.2 常用命令

| 命令 | 作用 |
| --- | --- |
| `npm run dev` | 开发服务器，默认 <http://localhost:5173/>,`--host 0.0.0.0` |
| `npm test` | 单元测试（4 个测试文件 / 21 项） |
| `npx tsc -b` | TypeScript 类型检查 |
| `npm run build` | `tsc -b && vite build`，产物写入 `dist/` |
| `npm run preview -- --port 5188` | 预览构建产物，<http://localhost:5188/> |
| `npm run format` | Prettier 格式化源码与配置 |
| `npm run ios:build` | 构建并执行 `cap sync ios`（注意下方清空目录提示） |

> **构建注意**：Vite 清空 `dist/`、Capacitor 清空 iOS `public/` 时可能触发本机的批量删除保护。稳妥做法是先手动移走旧目录再执行，例如
> `mv dist /tmp/atlas-dist-old-$(date +%s)`，iOS 同步则先 `mv ios/App/App/public /tmp/atlas-ios-public-old-$(date +%s)`，再 `cp -R ../../dist App/public`（在 `ios/App` 目录下）。

### 5.3 使用应用

1. 启动页点击屏幕或按任意键进入（会播放欢迎语音，需用户手势才允许发声）。
2. 顶栏下拉切换一年级至六年级，**默认六年级**；各年级学习进度互相独立。
3. 页面为 hash 路由：`#/`（今日）、`#/atlas`（词汇图鉴）、`#/learn`、`#/practice`、`#/me`、`#/about`。
4. 词条详情可看插画、音标、释义、例句、搭配与词族，播放英音/美音及例句音频。
5. 设置里可开关音效、环境音、主题，导出/导入学习备份。进度保存在浏览器 `localStorage`：`grade6-atlas:settings` 与 `grade6-atlas:v2:{datasetId}`（`datasetId` 形如 `grade6-atlas`）。
6. iPhone 可用 Safari 打开线上链接后「添加到主屏幕」，作为 PWA 使用。

### 5.4 维护词库

- 新增或替换某年级素材时，保持 `public/atlas/gN/` 下的目录结构与 `index.json` 的 `count`、`illustrated`、`voiced`、`chunk`、`words` 一致；`entries/` 按 `chunk`（100）分片命名 `{n}.json`。
- 媒体文件以词条 `id` 命名；缺失插画或音频时应用会自动留空，不必放占位文件。
- **改过任何静态资源后，把 `public/sw.js` 的 `VERSION` 升一级**（当前 `atlas-g1to6-v4`）。Service Worker 对音效等资源是缓存优先的，不升版本时已安装 PWA 仍会拿旧文件；JS/CSS 因构建带内容哈希可例外，但按统一约定仍建议升级。
- 词条说明里的中性措辞为「参考词库词条」「未匹配到词库插画」，不要再写回上游品牌名。

### 5.5 iOS 工程

- 工程：`ios/App/App.xcodeproj`（Capacitor 8，SPM 依赖，无绝对路径引用，可整目录搬迁）。
- Bundle ID 保持 `com.hong.grade6atlas`，**不要改**，否则已安装设备上的学习进度会丢失。
- 交付压缩包：`/Users/hong/WorkBuddy/shenwordaltas-ios.zip`（约 209 MB，内含六个年级资源）。
- **限制**：交付物是 Xcode 工程包，不是可直接安装的 IPA。开发环境只有 Command Line Tools，没有完整 Xcode 与 iOS SDK；需在装有 Xcode 的 Mac 上打开工程 Archive 签名后安装。

### 5.6 线上 PWA

- **当前分享链接**：<https://sz-grade-atlas.app.workbuddy.host/?sharecode=2D3VMYQIBK>（含访问码，请勿公开转发）。
- **发布源目录与项目构建产物是分开的**：线上应用绑定在 `/Users/hong/WorkBuddy/sz-grade-atlas-workspace/dist`，不是项目的 `dist/`。每次 `npm run build` 后需先同步，再从该目录发布：

  ```bash
  cd /Users/hong/WorkBuddy/shenwordaltas
  rsync -a dist/ ../sz-grade-atlas-workspace/dist/   # 不带 --delete，避免触发批量删除保护
  ```

  直接从 `shenwordaltas/dist` 发布会命中旧应用标记，把已下线的旧域名重新上线，务必注意。
- **旧应用**：<https://grade6-atlas.app.workbuddy.host/?sharecode=XIC7P5V6DM> 已手动停止发布（404）。其本地标记 `.wbapp_u3My0aQoq4Vb62HT85nibn.genie` 仍保留在工作区根，便于后续恢复或删除；新应用标记为 `.wbapp_tL21RQKTwiUofW1buoZ3N6.genie`。
- **域名机制**：域名在应用**首次创建**时按 `domainPrefix` 分配，之后绑定在 sandbox 上；覆盖发布、换发布目录、单纯下线重发都不会改域名。本次成功换域名的做法是：先停止发布旧应用 → 临时移开工作区内的 `.*.genie` 与 `.workbuddy/applications.yaml` → 用全新目录作为发布源重新发布，平台才走「首次创建」流程，分配 `sz-grade-atlas` 与新访问码。
- 每次发布后建议核对：首页标题、`assets/index-*.js` 哈希、`atlas/g1..g6/index.json` 返回 `application/json`、`sw.js` 版本与 `sfx/splash-voice.mp3`。
- 在「设置—数据管理—应用」中停止发布后，链接会返回 404「链接已失效」，重新发布即可恢复，地址与访问码不变。

### 5.7 源码仓库与提交

- 远端：`origin = git@github.com:linhong-cn/shenwordaltas.git`，公开仓库 <https://github.com/linhong-cn/shenwordaltas>。
- 应用内 GitHub 链接由 `src/config.ts` 的 `REPO_URL` 控制；`UPSTREAM_REPO_URL` 是上游 Word Atlas 的署名链接，**不要混用或删除**（CC BY 4.0 要求）。`package.json` 的 `homepage` / `repository` / `bugs` 也指向本项目仓库。
- 日常提交：`git add -A && git commit -m "…" && git push`（`main` 已跟踪 `origin/main`）。
- 克隆后需自行生成构建产物：`npm ci && npm run build`；`dist/`、`ios/App/App/public/` 均为可再生产物，未入库。

## 六、已知限制与免责

- 词表按公开教材单元整理，教材版本请以学校发放的课本为准；本项目是学习用整理稿，**不是教材官方配套资源**，也不代表出版社立场。
- 上游素材按现状提供，未逐条人工审校；本项目同样不对释义、音标、例句的准确性作担保。
- 学习进度只存在本机浏览器，清除站点数据会丢失，请定期在设置里导出备份。
- 应用内已去除上游面向考试的表述；`CONTENT_LICENSE.md` 与 `LICENSE` 中的法律声明按授权要求保留原文。

---

感谢 [Word Atlas contributors](https://github.com/designfuchen/word-atlas) 以 MIT / CC BY 4.0 开放代码、插画与录音，使本项目得以在其基础上改编。
