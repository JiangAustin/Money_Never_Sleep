const { contextBridge } = require("electron");

function parseStartupContext() {
  const prefix = "--mns-startup=";
  const raw = process.argv.find((arg) => arg.startsWith(prefix));
  if (!raw) {
    return {
      mode: "browser-offline",
      apiUrl: "",
      managed: false,
      diagnostics: ["未检测到桌面启动上下文，当前按浏览器离线模式处理。"],
      lastError: "",
    };
  }
  try {
    return JSON.parse(decodeURIComponent(raw.slice(prefix.length)));
  } catch (error) {
    return {
      mode: "browser-offline",
      apiUrl: "",
      managed: false,
      diagnostics: ["桌面启动上下文解析失败，已回退到浏览器离线模式。"],
      lastError: error.message || "invalid startup payload",
    };
  }
}

contextBridge.exposeInMainWorld("moneyNeverSleep", {
  platform: process.platform,
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron,
  },
  startup: parseStartupContext(),
});
