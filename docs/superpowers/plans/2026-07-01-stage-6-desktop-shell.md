# 阶段 6 桌面端与本地体验实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 建立 Electron 桌面壳，把现有 Web 工作台打包成可构建的 macOS `.app`。

**架构：** `apps/desktop` 成为独立 npm/Electron 包。Electron main 进程加载 `apps/web/index.html`，打包时通过 `extraResources` 带上 Web 静态资源。默认不内嵌 Python API；如设置 `MNS_DESKTOP_API_URL`，则向 Web 传入 `?api=`。

**技术栈：** Electron、electron-builder、Node/npm、pytest。

---

## 文件结构

- 创建：`apps/desktop/package.json`
- 创建：`apps/desktop/src/main.js`
- 创建：`apps/desktop/src/preload.js`
- 修改：`apps/desktop/README.md`
- 创建：`services/api/tests/test_desktop_shell.py`
- 修改：`README.md`
- 修改：`docs/stages.md`
- 修改：`docs/improvement-backlog.md`
- 修改：`docs/agent-handoff.md`
- 修改：`docs/information-map.md`

---

### 任务 1：Desktop package 配置

**文件：**

- 创建：`apps/desktop/package.json`
- 创建：`services/api/tests/test_desktop_shell.py`

- [ ] **步骤 1：编写失败测试**

创建 `services/api/tests/test_desktop_shell.py`：

```python
import json
from pathlib import Path


DESKTOP_ROOT = Path("apps/desktop")


def read_package() -> dict:
    return json.loads((DESKTOP_ROOT / "package.json").read_text(encoding="utf-8"))


def test_desktop_package_has_electron_scripts() -> None:
    package = read_package()

    assert package["main"] == "src/main.js"
    assert package["scripts"]["start"] == "electron ."
    assert package["scripts"]["build:mac"] == "electron-builder --mac dir"


def test_desktop_package_includes_web_resources() -> None:
    package = read_package()
    extra_resources = package["build"]["extraResources"]

    assert {"from": "../web", "to": "web", "filter": ["**/*"]} in extra_resources
```

- [ ] **步骤 2：运行测试确认失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_desktop_shell.py -v`

预期：FAIL，`package.json` 不存在。

- [ ] **步骤 3：创建 package.json**

创建 Electron package，包含 `electron`、`electron-builder` devDependencies 和 macOS dir target。

- [ ] **步骤 4：运行测试通过**

同上，预期 PASS。

- [ ] **步骤 5：Commit**

```bash
git add apps/desktop/package.json services/api/tests/test_desktop_shell.py
git commit -m "feat: add desktop electron package" -m "Outline:
- Add Electron package scripts for start and macOS directory builds.
- Configure electron-builder to include the Web workbench as extra resources.
- Cover package scripts and resource configuration with tests."
```

---

### 任务 2：Electron main/preload 壳

**文件：**

- 创建：`apps/desktop/src/main.js`
- 创建：`apps/desktop/src/preload.js`
- 修改：`services/api/tests/test_desktop_shell.py`

- [ ] **步骤 1：编写失败测试**

追加：

```python
def test_desktop_main_loads_web_workbench() -> None:
    main_js = (DESKTOP_ROOT / "src/main.js").read_text(encoding="utf-8")

    assert "BrowserWindow" in main_js
    assert "index.html" in main_js
    assert "MNS_DESKTOP_API_URL" in main_js
    assert "process.resourcesPath" in main_js


def test_desktop_preload_exposes_versions() -> None:
    preload_js = (DESKTOP_ROOT / "src/preload.js").read_text(encoding="utf-8")

    assert "contextBridge" in preload_js
    assert "moneyNeverSleep" in preload_js
```

- [ ] **步骤 2：运行测试确认失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_desktop_shell.py -v`

预期：FAIL，JS 文件不存在。

- [ ] **步骤 3：实现 main/preload**

`main.js` 创建 BrowserWindow、加载 Web index、支持 `MNS_DESKTOP_API_URL` query。

`preload.js` 使用 `contextBridge.exposeInMainWorld()` 暴露版本信息。

- [ ] **步骤 4：验证**

运行：`node --check apps/desktop/src/main.js && node --check apps/desktop/src/preload.js`

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_desktop_shell.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add apps/desktop/src/main.js apps/desktop/src/preload.js services/api/tests/test_desktop_shell.py
git commit -m "feat: add desktop web shell" -m "Outline:
- Add Electron main process that loads the Web workbench in development and packaged modes.
- Add preload boundary for desktop metadata.
- Cover Web loading and preload structure with tests."
```

---

### 任务 3：安装依赖并构建 macOS

**文件：**

- 创建：`apps/desktop/package-lock.json`

- [ ] **步骤 1：安装依赖**

运行：`cd apps/desktop && npm install`

预期：生成 `package-lock.json`，`node_modules/` 被忽略。

- [ ] **步骤 2：构建 macOS app**

运行：`cd apps/desktop && npm run build:mac`

预期：生成 `apps/desktop/dist/mac*/Money Never Sleep.app` 或等价 `.app` 目录。

- [ ] **步骤 3：Commit**

```bash
git add apps/desktop/package-lock.json
git commit -m "chore: lock desktop electron dependencies" -m "Outline:
- Install Electron desktop dependencies.
- Commit npm lockfile for reproducible desktop builds.
- Verify macOS app directory build with npm run build:mac."
```

---

### 任务 4：文档与最终验证

**文件：**

- 修改：`apps/desktop/README.md`
- 修改：`README.md`
- 修改：`docs/stages.md`
- 修改：`docs/improvement-backlog.md`
- 修改：`docs/agent-handoff.md`
- 修改：`docs/information-map.md`

- [ ] **步骤 1：更新文档**

记录 Electron 选型、启动命令、构建命令、macOS 产物位置和未做事项。

- [ ] **步骤 2：最终验证**

运行：

```bash
PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v
node --check apps/web/src/app.js apps/web/src/mockData.js apps/desktop/src/main.js apps/desktop/src/preload.js
cd apps/desktop && npm run build:mac
```

- [ ] **步骤 3：Commit**

```bash
git add apps/desktop/README.md README.md docs/stages.md docs/improvement-backlog.md docs/agent-handoff.md docs/information-map.md
git commit -m "docs: document desktop shell" -m "Outline:
- Document Electron desktop selection, start command, and macOS build command.
- Mark stage 6 complete and record validation evidence.
- Update backlog, handoff, and information map with desktop entrypoints."
```

---

## 自检结果

- 覆盖 backlog `MNS-BL-002`。
- 第一版选择 Electron，Tauri/Wails 暂缓。
- 默认不内嵌 Python API server，避免进程管理复杂度。
- 产物目录 `dist/` 已被 `.gitignore` 忽略。
