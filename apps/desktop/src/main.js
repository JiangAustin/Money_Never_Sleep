const { app, BrowserWindow, shell } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const DEFAULT_API_HOST = process.env.MONEY_API_HOST || "127.0.0.1";
const DEFAULT_API_PORT = process.env.MONEY_API_PORT || "8000";
const STARTUP_ARG_PREFIX = "--mns-startup=";

let managedApiProcess = null;

function getWebIndexPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "web", "index.html");
  }
  return path.join(__dirname, "..", "..", "web", "index.html");
}

function getRepoRoot() {
  return path.resolve(__dirname, "..", "..", "..");
}

function getApiSourcePath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "services-api");
  }
  return path.join(getRepoRoot(), "services", "api");
}

function fileExists(targetPath) {
  try {
    return fs.existsSync(targetPath);
  } catch {
    return false;
  }
}

function getManagedApiUrl() {
  return `http://${DEFAULT_API_HOST}:${DEFAULT_API_PORT}`;
}

function getPythonCandidates() {
  const candidates = [];
  if (process.env.MNS_DESKTOP_PYTHON_BIN) {
    candidates.push(process.env.MNS_DESKTOP_PYTHON_BIN);
  }
  if (!app.isPackaged) {
    candidates.push(path.join(getRepoRoot(), ".venv", "bin", "python"));
  }
  candidates.push("python3", "python");
  return candidates;
}

function resolvePythonCommand() {
  return getPythonCandidates().find((candidate) => candidate === "python3" || candidate === "python" || fileExists(candidate));
}

function appendPythonPath(existingValue, sourcePath) {
  return existingValue ? `${sourcePath}${path.delimiter}${existingValue}` : sourcePath;
}

function getManagedApiEnv() {
  return {
    ...process.env,
    PYTHONPATH: appendPythonPath(process.env.PYTHONPATH, getApiSourcePath()),
    MONEY_API_HOST: DEFAULT_API_HOST,
    MONEY_API_PORT: DEFAULT_API_PORT,
    MONEY_MARKET_DATA_MODE: process.env.MONEY_MARKET_DATA_MODE || "tencent",
    MONEY_DEEP_ENGINE: process.env.MONEY_DEEP_ENGINE || "auto",
    MONEY_REPORTS_DIR: process.env.MONEY_REPORTS_DIR || path.join(app.getPath("userData"), "reports"),
  };
}

function waitForApiHealth(apiUrl, attempts = 40) {
  return new Promise((resolve, reject) => {
    let remaining = attempts;
    const tryRequest = () => {
      const request = http.get(`${apiUrl}/health`, (response) => {
        response.resume();
        if (response.statusCode === 200) {
          resolve();
          return;
        }
        retry(new Error(`health check returned ${response.statusCode}`));
      });
      request.on("error", retry);
    };

    const retry = (error) => {
      remaining -= 1;
      if (remaining <= 0) {
        reject(error);
        return;
      }
      setTimeout(tryRequest, 250);
    };

    tryRequest();
  });
}

function createStartupContext(overrides = {}) {
  return {
    mode: "desktop-offline",
    apiUrl: "",
    managed: false,
    diagnostics: [],
    lastError: "",
    ...overrides,
  };
}

async function ensureApiStartupContext() {
  if (process.env.MNS_DESKTOP_API_URL) {
    return createStartupContext({
      mode: "desktop-external-api",
      apiUrl: process.env.MNS_DESKTOP_API_URL,
      diagnostics: ["检测到 MNS_DESKTOP_API_URL，桌面已连接外部 HTTP API。"],
    });
  }

  const python = resolvePythonCommand();
  if (!python) {
    return createStartupContext({
      diagnostics: ["未找到可用 Python，可执行文件；桌面已回退到离线工作台。"],
      lastError: "python executable not found",
    });
  }

  const apiUrl = getManagedApiUrl();
  const serverCommand = `from money_api.main import run_http_server; run_http_server(host=${JSON.stringify(DEFAULT_API_HOST)}, port=${Number(DEFAULT_API_PORT)})`;
  managedApiProcess = spawn(python, ["-c", serverCommand], {
    cwd: app.isPackaged ? process.resourcesPath : getRepoRoot(),
    env: getManagedApiEnv(),
    stdio: "ignore",
  });

  try {
    await waitForApiHealth(apiUrl);
    return createStartupContext({
      mode: "desktop-managed-api",
      apiUrl,
      managed: true,
      diagnostics: [
        `桌面已托管本地 API：${apiUrl}`,
        `Python: ${python}`,
        `market data mode: ${getManagedApiEnv().MONEY_MARKET_DATA_MODE}`,
        `deep engine mode: ${getManagedApiEnv().MONEY_DEEP_ENGINE}`,
      ],
    });
  } catch (error) {
    console.error("Managed API server failed to start", error);
    if (managedApiProcess && !managedApiProcess.killed) {
      managedApiProcess.kill();
    }
    managedApiProcess = null;
    return createStartupContext({
      diagnostics: ["桌面尝试托管本地 API 失败，已回退到离线工作台。", `Python: ${python}`],
      lastError: error.message || "managed api startup failed",
    });
  }
}

function stopManagedApiServer() {
  if (managedApiProcess && !managedApiProcess.killed) {
    managedApiProcess.kill();
  }
  managedApiProcess = null;
}

function getLoadOptions(apiUrl) {
  if (!apiUrl) {
    return {};
  }
  return { query: { api: apiUrl } };
}

function getStartupArgument(startupContext) {
  return `${STARTUP_ARG_PREFIX}${encodeURIComponent(JSON.stringify(startupContext))}`;
}

function createWindow(startupContext) {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 980,
    minHeight: 680,
    title: "Money Never Sleep",
    backgroundColor: "#f6f4ef",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      additionalArguments: [getStartupArgument(startupContext)],
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.loadFile(getWebIndexPath(), getLoadOptions(startupContext.apiUrl));
}

app.whenReady().then(async () => {
  const startupContext = await ensureApiStartupContext();
  createWindow(startupContext);

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow(startupContext);
    }
  });
});

app.on("before-quit", () => {
  stopManagedApiServer();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    stopManagedApiServer();
    app.quit();
  }
});
