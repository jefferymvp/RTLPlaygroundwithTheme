# RTLPlayground 固件界面 Argon 主题补丁使用指南

本指南旨在帮助开发者与固件定制爱好者，在官方原版 [logicog/RTLPlayground](https://github.com/logicog/RTLPlayground) 仓库或任何基于其派生的固件源码中，**一键植入高颜值的 Argon 现代双主题界面**。

通过内置的全自动补丁工具，您可以零门槛完成主题的打入、切换、本地实时预览以及一键无损还原。

---

## 🎨 主题特性概览

打上本补丁后，固件 Web 管理界面将具备以下增强特性：

1. **Argon 现代设计语言**：
   - 科技感暗色渐变导航顶栏与紧凑卡片化布局；
   - 现代化无衬线系统字体栈，告别过时的复古排版；
   - 全新设计的毛玻璃质感与高对比度端口悬浮气泡（Tooltip），光口 DDM、温度、收发光功率与速率统计一目了然；
   - 重新设计的居中卡片式登录界面与统一表单控件。
2. **原生 / Argon 双主题实时热切换**：
   - 无论在登录页面还是登录后的后台顶栏，均提供即时主题切换器；
   - 支持在 **经典原版 (Default)** 与 **现代主题 (Argon)** 之间秒级平滑切换；
   - 主题偏好自动保存在浏览器本地（`localStorage`），无需重复选择。
3. **中文语义精校**：
   - 全面润色系统设置、管理 VLAN 提示、固件升级等界面的中文翻译与排版对齐。

---

## 📂 补丁工具清单

所有补丁相关工具及离线资源均集中在项目的 `tools/` 目录下：

```text
tools/
├── apply_theme_patch.bat       # [推荐] Windows 双击快捷运行引导脚本
├── apply_theme_patch.ps1       # 跨平台 / PowerShell 核心交互式管理脚本
├── argon_theme.patch           # 标准 Git Patch 补丁文件 (对上游 0 冲突)
├── sim_server.py               # 免硬件/免固件编译的 Python 本地仿真服务器
└── argon_theme/                # 离线主题静态资源包
    └── html/
        ├── main.js             # 增强版前端逻辑 (含主题调度引擎与双语词表)
        └── style.css           # 完整 CSS 样式 (含 Argon 主题全套样式集)
```

---

## 🚀 补丁使用步骤

### 方式一：Windows 用户双击运行（最简便）

1. 进入 `tools/` 目录，鼠标双击运行 **`apply_theme_patch.bat`**。
2. 脚本会自动弹出操作控制台，并提示输入目标 RTLPlayground 源码目录：
   - **若直接在当前仓库内运行**：直接按 **回车**，脚本会自动选中当前根目录。
   - **若为外部其他 RTLPlayground 源码打补丁**：将目标仓库的根目录绝对路径复制粘贴进来后回车。
3. 在弹出的交互菜单中，输入数字 **`1`**（或直接回车，默认为 1）即可完成主题植入。

---

### 方式二：PowerShell 终端命令行运行

支持 Windows PowerShell、PowerShell Core (Windows / Linux / macOS)：

```powershell
# 1. 交互式启动（自动引导输入路径）
pwsh ./tools/apply_theme_patch.ps1

# 2. 或直接传参指定目标仓库路径（支持带空格路径，用双引号包裹）
pwsh ./tools/apply_theme_patch.ps1 "D:\develop\RTLPlayground"
```

---

### 方式三：纯 Git 命令行打入

如果您熟悉 Git 命令行，且目标仓库是一个纯净的 Git 工作树，可在目标仓库根目录直接执行：

```bash
# 检查兼容性（应无任何输出或冲突）
git apply --check /path/to/tools/argon_theme.patch

# 打入补丁
git apply /path/to/tools/argon_theme.patch
```

---

## 📋 菜单功能详解

在运行交互式脚本（`apply_theme_patch.bat` 或 `apply_theme_patch.ps1`）时，系统提供 5 项核心功能：

```text
========================================================
       RTLPlayground 现代双主题一键补丁管理工具
========================================================

当前目标仓库: C:\develop\RTLPlayground

请选择要执行的操作:
  1. [推荐] 一键应用 Argon 现代主题 (安全替换并自动生成 .bak 备份)
  2. 使用 Git Patch 补丁应用 (适合干净的 Git 分支)
  3. 一键还原官方原版 (从 .bak 备份恢复或 Git 还原)
  4. 启动本地模拟服务器 (启动 Python 调试服务进行实时预览)
  5. 退出
```

### 1. [选项 1] 一键应用 Argon 现代主题
- **机制**：直接将离线静态资源 `tools/argon_theme/html/` 下的 `main.js` 与 `style.css` 安全部署到目标仓库的 `html/` 目录。
- **安全备份**：如果目标文件存在，脚本会自动在同级目录生成 `html/main.js.bak` 和 `html/style.css.bak`，锁定并保护最原始的代码版本。
- **适用场景**：任何环境，即使没有安装 Git 或脱离版本控制的目录也能 100% 成功。

### 2. [选项 2] 使用 Git Patch 补丁应用
- **机制**：通过 `git apply` 指令合入 `argon_theme.patch`。如果目标仓库存在微小变动，会自动启动 `git apply -3`（3-way merge）进行自适应合入。
- **适用场景**：标准的 Git 开发分支，便于生成纯净的 Git Commit 记录。

### 3. [选项 3] 一键还原官方原版
- **机制**：如果之前是通过选项 1 替换并生成了 `.bak` 备份，脚本会自动将备份恢复并清理缓存；若没有备份文件，则会自动通过 `git checkout` 检出官方原版文件。
- **作用**：完全无损、秒级恢复，不破坏任何其他工程代码。

### 4. [选项 4] 启动本地模拟服务器 (仿真预览)
- **机制**：自动通过 Python 后台拉起内置的 `tools/sim_server.py` 服务，并自动在默认浏览器中打开 `http://127.0.0.1:8088/`。
- **优势**：
  - **零等待**：无需编译固件，无需准备 SDCC 交叉编译环境。
  - **零风险**：无需烧录交换机硬件，1:1 模拟交换机全套 API 行为（登录、端口状态、统计计数、SFP 信息、配置保存等）。

---

## 🔨 打补丁后编译与固件生效

当补丁打入成功后，您只需按照正常的固件构建流程编译即可：

```bash
# 1. 确认 machine.h 中机型宏与 config.txt 中 IP 已按需配置
# 2. 执行编译
make

# 或使用 Docker 编译：
docker run --rm -v $(pwd):/workspace rtlplayground-dev make
```

生成的固件（位于 `output/rtlplayground_*.bin`）已内嵌最新 Argon 双主题前端代码，刷入交换机后直接生效！

---

## ❓ 常见问题排查 (FAQ)

### Q1: 打上补丁编译后，在浏览器中打开仍然是旧版界面？
- **原因**：浏览器的强缓存机制缓存了旧版的 `main.js` 或 `style.css`。
- **解决办法**：在浏览器页面按 **Ctrl + F5**（Mac 用户按 **Cmd + Shift + R**）进行强制刷新，或清除浏览器缓存。

### Q2: 打补丁时提示“未找到 html 目录”？
- **原因**：选择的目标路径不是 RTLPlayground 仓库的根目录。
- **解决办法**：请确认所输入的路径下直接包含 `html`、`tools`、`machine.h` 等核心文件。

### Q3: 还原后本地修改的配置会丢失吗？
- **解答**：不会。主题补丁及还原仅作用于前端展示文件（`html/main.js`、`html/style.css`），不会改动交换机驱动、寄存器配置、`machine.h` 或 `config.txt`。
