const { app, BrowserWindow, shell } = require("electron");
const path = require("node:path");

function getWebIndexPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "web", "index.html");
  }
  return path.join(__dirname, "..", "..", "web", "index.html");
}

function getLoadOptions() {
  const apiUrl = process.env.MNS_DESKTOP_API_URL;
  if (!apiUrl) {
    return {};
  }
  return { query: { api: apiUrl } };
}

function createWindow() {
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
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  mainWindow.loadFile(getWebIndexPath(), getLoadOptions());
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
