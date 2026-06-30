# 阶段 5.5 HTTP API 层实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为现有分析服务增加最小 JSON HTTP API，让 Web 和桌面后续可以真实调用后端。

**架构：** 新增 dependency-free `HttpApiApp` dispatcher，测试直接调用 `handle()`；新增标准库 `run_http_server()` 适配器；Web 工作台增加 `?api=` HTTP service 边界，默认仍使用 mock。

**技术栈：** Python 标准库 `http.server`、`json`、`urllib.parse`、pytest、浏览器 JavaScript。

---

## 文件结构

- 创建：`services/api/money_api/api/http.py`
  定义 `HttpResponse`、`HttpApiApp`、`run_http_server()`。
- 创建：`services/api/tests/test_http_api.py`
  覆盖 health、analysis、reports、report detail、400、404。
- 修改：`services/api/money_api/main.py`
  暴露 `run_http_server()`。
- 修改：`apps/web/src/app.js`
  增加 `?api=` HTTP service，失败时回退 mock。
- 修改：`services/api/tests/test_web_workbench.py`
  检查 HTTP service 边界。
- 修改：`apps/web/README.md`
  记录 `?api=` 用法。
- 修改：`README.md`、`docs/stages.md`、`docs/improvement-backlog.md`、`docs/agent-handoff.md`、`docs/information-map.md`
  记录阶段完成、信息入口和后续建议。

---

### 任务 1：HTTP dispatcher

**文件：**

- 创建：`services/api/money_api/api/http.py`
- 创建：`services/api/tests/test_http_api.py`

- [ ] **步骤 1：编写失败的测试**

创建 `services/api/tests/test_http_api.py`：

```python
import json

from money_api.api.http import HttpApiApp
from money_api.api.v1.router import build_default_analysis_service
from money_api.domains.analysis.report_repository import InMemoryAnalysisReportRepository


def build_app() -> HttpApiApp:
    service = build_default_analysis_service(report_repository=InMemoryAnalysisReportRepository())
    return HttpApiApp(service=service)


def decode(response):
    return json.loads(response.body.decode("utf-8"))


def test_http_health() -> None:
    response = build_app().handle("GET", "/health", b"")

    assert response.status == 200
    assert decode(response)["status"] == "ok"


def test_http_create_analysis_and_get_report() -> None:
    app = build_app()
    response = app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))

    payload = decode(response)
    report = decode(app.handle("GET", f"/reports/{payload['task_id']}", b""))

    assert response.status == 200
    assert payload["stock"]["code"] == "600519"
    assert report["task_id"] == payload["task_id"]


def test_http_list_reports() -> None:
    app = build_app()
    app.handle("POST", "/analysis", json.dumps({"symbol": "贵州茅台", "message": "请全面分析"}).encode("utf-8"))

    response = app.handle("GET", "/reports?limit=5", b"")

    assert response.status == 200
    assert decode(response)[0]["stock"]["code"] == "600519"


def test_http_returns_400_for_invalid_analysis_payload() -> None:
    response = build_app().handle("POST", "/analysis", b"{}")

    assert response.status == 400
    assert decode(response)["error"] == "symbol and message are required"


def test_http_returns_404_for_missing_report() -> None:
    response = build_app().handle("GET", "/reports/missing", b"")

    assert response.status == 404
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_http_api.py -v`

预期：FAIL，`money_api.api.http` 不存在。

- [ ] **步骤 3：实现 dispatcher**

实现 `HttpResponse` 和 `HttpApiApp.handle(method, target, body)`：

- `GET /health`
- `POST /analysis`
- `GET /reports?limit=N`
- `GET /reports/{task_id}`
- JSON 错误响应 `{ "error": "..." }`

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_http_api.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/api/http.py services/api/tests/test_http_api.py
git commit -m "feat: add JSON HTTP API dispatcher" -m "Outline:
- Add a dependency-free HTTP API dispatcher for health, analysis, reports, and report detail routes.
- Keep tests focused on request/response contracts without starting a server.
- Cover invalid payload and missing report errors."
```

---

### 任务 2：标准库 server 启动入口

**文件：**

- 修改：`services/api/money_api/api/http.py`
- 修改：`services/api/money_api/main.py`
- 修改：`services/api/tests/test_http_api.py`

- [ ] **步骤 1：编写失败的测试**

追加：

```python
from money_api.main import run_http_server


def test_run_http_server_is_exported() -> None:
    assert callable(run_http_server)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_http_api.py::test_run_http_server_is_exported -v`

预期：FAIL，`run_http_server` 未导出。

- [ ] **步骤 3：实现 server 适配器**

在 `http.py` 中新增 `run_http_server(host="127.0.0.1", port=8000, app=None)`，使用 `ThreadingHTTPServer` 和 `BaseHTTPRequestHandler` 转发到 `HttpApiApp.handle()`。

在 `main.py` 中导出同名函数。

- [ ] **步骤 4：运行测试验证通过**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_http_api.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add services/api/money_api/api/http.py services/api/money_api/main.py services/api/tests/test_http_api.py
git commit -m "feat: expose HTTP server entrypoint" -m "Outline:
- Add a standard-library HTTP server adapter around HttpApiApp.
- Export run_http_server from the Python API boundary.
- Verify the server entrypoint is importable for future scripts and desktop integration."
```

---

### 任务 3：Web HTTP service 边界

**文件：**

- 修改：`apps/web/src/app.js`
- 修改：`apps/web/README.md`
- 修改：`services/api/tests/test_web_workbench.py`

- [ ] **步骤 1：编写失败的测试**

在 Web 测试中追加：

```python
def test_app_js_exposes_http_service_boundary() -> None:
    app_js = read_web_file("src/app.js")

    assert "function getApiBaseUrl" in app_js
    assert "async function createHttpAnalysis" in app_js
    assert "fetch(`${apiBaseUrl}/analysis`" in app_js
    assert "createLocalAnalysis" in app_js
```

- [ ] **步骤 2：运行测试验证失败**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py::test_app_js_exposes_http_service_boundary -v`

预期：FAIL，HTTP service 边界未实现。

- [ ] **步骤 3：实现 Web service 边界**

在 `app.js` 中：

- `getApiBaseUrl()` 从 `window.location.search` 读取 `api`。
- `createHttpAnalysis(apiBaseUrl, symbol, message)` POST `/analysis`。
- submit 时如果有 `api`，优先 HTTP；失败时生成 mock report，并在 diagnostics 中记录失败。
- 默认无 `api` 时保持现有 mock 行为。

更新 `apps/web/README.md` 记录：

```text
直接打开 index.html 为离线 mock；如果启动 HTTP API，可使用 index.html?api=http://127.0.0.1:8000。
```

- [ ] **步骤 4：运行验证**

运行：`node --check apps/web/src/app.js`

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests/test_web_workbench.py -v`

预期：PASS。

- [ ] **步骤 5：Commit**

```bash
git add apps/web/src/app.js apps/web/README.md services/api/tests/test_web_workbench.py
git commit -m "feat: add web HTTP service boundary" -m "Outline:
- Add optional ?api= HTTP service mode for the static Web workbench.
- Keep offline mock behavior as the default fallback.
- Document API mode and cover the service boundary in Web tests."
```

---

### 任务 4：文档、backlog 和最终验证

**文件：**

- 修改：`README.md`
- 修改：`docs/stages.md`
- 修改：`docs/improvement-backlog.md`
- 修改：`docs/agent-handoff.md`
- 修改：`docs/information-map.md`

- [ ] **步骤 1：更新文档**

- README：补充 HTTP API 能力和运行入口。
- stages：记录阶段 5.5 完成内容、验证结果、下一步建议。
- improvement backlog：将 `MNS-BL-001` 标为 `已完成`，新增 FastAPI/OpenAPI、任务队列等后续项。
- handoff：增加 HTTP API 层摘要、关键文件、验证命令。
- information map：增加 HTTP API 入口文件位置。

- [ ] **步骤 2：运行最终验证**

运行：`PYTHONPATH=services/api /Users/jxc/VS/Money_Never_sleep/.venv/bin/python -m pytest services/api/tests -v`

运行：`node --check apps/web/src/app.js && node --check apps/web/src/mockData.js`

运行：`git diff --check`

预期：全部 PASS。

- [ ] **步骤 3：Commit**

```bash
git add README.md docs/stages.md docs/improvement-backlog.md docs/agent-handoff.md docs/information-map.md
git commit -m "docs: document HTTP API layer" -m "Outline:
- Record the new JSON HTTP API layer and Web API mode.
- Update backlog and handoff notes with completed and deferred HTTP work.
- Add HTTP API locations to the information map."
```

---

## 自检结果

- 覆盖 backlog `MNS-BL-001`。
- 默认无外部依赖。
- Web 默认仍可离线打开。
- 后续 FastAPI、OpenAPI、异步任务队列保留到 backlog。
