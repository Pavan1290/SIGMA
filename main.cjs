const {
  app,
  BrowserWindow,
  Tray,
  Menu,
  ipcMain,
  nativeImage,
  screen,
} = require("electron");
const path = require("path");
const fs = require("fs");
const os = require("os");
const { pathToFileURL } = require("url");
const { spawn } = require("child_process");

const BACKEND_HEALTH_URL =
  process.env.SIGMA_BACKEND_URL || "http://127.0.0.1:5000/health";
const BACKEND_WAIT_TIMEOUT_MS = 20000;
const SIDEBAR_PADDING = 12;
const PANEL_WIDTH_RATIO = 0.42;
const PANEL_MIN_WIDTH = 520;
const LAUNCHER_SIZE = 72;
const ICON_SIZE = 45;
const APP_DISPLAY_NAME = "SIGMA_OS";
const SIDEBAR_LOGO_PATH = path.join(__dirname, "logo.png");
const LAUNCH_MODE = process.argv.includes("--sidebar-mode")
  ? "sidebar"
  : "full";

let backendProcess = null;
let backendStartedByApp = false;
let mainWindow = null;
let panelWindow = null;
let launcherWindow = null;
let launcherManualPosition = null;
let tray = null;
let isQuitting = false;

const toPosixPath = (value) => value.replace(/\\/g, "/");

const writeToStreamSafely = (stream, message) => {
  if (!stream || stream.destroyed || !stream.writable) {
    return;
  }

  try {
    stream.write(message);
  } catch (error) {
    // Electron apps launched without an attached terminal can hit EPIPE.
    if (error?.code !== "EPIPE") {
      throw error;
    }
  }
};

const getPathCandidates = (...values) => {
  return [...new Set(values.filter(Boolean))];
};

const getLogoPath = () => {
  const appPath = app.getAppPath();
  const candidates = getPathCandidates(
    SIDEBAR_LOGO_PATH,
    path.join(appPath, "logo.png"),
    process.resourcesPath ? path.join(process.resourcesPath, "logo.png") : null,
  );

  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
};

const getLogoFileUrl = () => {
  const logoPath = getLogoPath();
  return logoPath ? pathToFileURL(logoPath).href : null;
};

const getLogoDataUrl = () => {
  const logoPath = getLogoPath();
  if (!logoPath) {
    return null;
  }

  try {
    const imageBuffer = fs.readFileSync(logoPath);
    return `data:image/png;base64,${imageBuffer.toString("base64")}`;
  } catch (error) {
    return null;
  }
};

const buildLauncherHtml = () => {
  const logoUrl = getLogoDataUrl() || getLogoFileUrl();
  const iconMarkup = logoUrl
    ? `<img class="launcher-icon" src="${logoUrl}" alt="${APP_DISPLAY_NAME}" />`
    : `<div class="launcher-fallback"></div>`;

  return `
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' data: file:; img-src 'self' data: file:; script-src 'self' 'unsafe-inline';" />
        <style>
          html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            overflow: hidden;
            background: transparent;
            font-family: Segoe UI, system-ui, sans-serif;
          }
          body {
            display: flex;
            align-items: center;
            justify-content: center;
            -webkit-app-region: no-drag;
            cursor: grab;
          }
          body:active {
            cursor: grabbing;
          }
          .shell {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
            cursor: pointer;
            -webkit-app-region: no-drag;
          }
          .launcher-icon {
            width: ${ICON_SIZE}px;
            height: ${ICON_SIZE}px;
            object-fit: contain;
            filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.35));
            user-select: none;
            pointer-events: none;
          }
          .launcher-fallback {
            width: ${ICON_SIZE}px;
            height: ${ICON_SIZE}px;
            border-radius: 14px;
            background: transparent;
          }
        </style>
      </head>
      <body>
        <div class="shell" id="launcherShell" aria-label="Open SIGMA sidebar">
          ${iconMarkup}
        </div>
        <script>
          const { ipcRenderer } = require('electron');
          const shell = document.getElementById('launcherShell');
          let dragStart = null;
          let hasDragged = false;

          shell.addEventListener('mousedown', (event) => {
            if (event.button !== 0) return;
            dragStart = {
              mouseX: event.screenX,
              mouseY: event.screenY,
            };
            hasDragged = false;
          });

          window.addEventListener('mousemove', (event) => {
            if (!dragStart) return;

            const deltaX = event.screenX - dragStart.mouseX;
            const deltaY = event.screenY - dragStart.mouseY;

            if (!hasDragged && (Math.abs(deltaX) > 2 || Math.abs(deltaY) > 2)) {
              hasDragged = true;
            }

            if (hasDragged) {
              ipcRenderer.send('sigma:move-launcher', {
                deltaX,
                deltaY,
              });
              dragStart.mouseX = event.screenX;
              dragStart.mouseY = event.screenY;
            }
          });

          window.addEventListener('mouseup', () => {
            if (!dragStart) return;

            if (!hasDragged) {
              ipcRenderer.send('sigma:toggle-sidebar');
            }

            dragStart = null;
            hasDragged = false;
          });

          shell.addEventListener('contextmenu', (event) => {
            event.preventDefault();
            ipcRenderer.send('sigma:toggle-sidebar');
          });
        </script>
      </body>
    </html>
  `;
};

const getTrayIcon = () => {
  const logoPath = getLogoPath();
  if (!logoPath) {
    return null;
  }

  const trayIcon = nativeImage.createFromPath(logoPath);
  if (trayIcon.isEmpty()) {
    return null;
  }

  return trayIcon;
};

const getProjectRootFromExecutable = () => {
  const executableDir = path.dirname(process.execPath);
  return path.resolve(executableDir, "..", "..");
};

const getBackendScriptPath = () => {
  const explicitPath = process.env.SIGMA_BACKEND_PATH;
  const unpackedBackendPath = process.resourcesPath
    ? path.join(process.resourcesPath, "app.asar.unpacked", "backend", "app.py")
    : null;
  const appPath = app.getAppPath();
  const projectRoot = getProjectRootFromExecutable();

  const candidates = getPathCandidates(
    explicitPath,
    path.join(__dirname, "backend", "app.py"),
    path.join(appPath, "backend", "app.py"),
    unpackedBackendPath,
    path.join(projectRoot, "backend", "app.py"),
  );

  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
};

const getPythonCommandCandidates = () => {
  const explicitPath = process.env.SIGMA_PYTHON_PATH;
  const appPath = app.getAppPath();
  const projectRoot = getProjectRootFromExecutable();
  const unpackedRoot = process.resourcesPath
    ? path.join(process.resourcesPath, "app.asar.unpacked")
    : null;

  const roots = getPathCandidates(
    __dirname,
    appPath,
    unpackedRoot,
    projectRoot,
  );
  const venvCandidates = roots.flatMap((rootPath) => [
    path.join(rootPath, ".venv", "Scripts", "python.exe"),
    path.join(rootPath, ".venv", "bin", "python"),
  ]);

  const existingVenvCandidates = venvCandidates.filter((candidate) =>
    fs.existsSync(candidate),
  );

  return getPathCandidates(
    explicitPath,
    ...existingVenvCandidates,
    "python3",
    "python",
  );
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const isBackendHealthy = async () => {
  try {
    const response = await fetch(BACKEND_HEALTH_URL, { method: "GET" });
    return response.ok;
  } catch (error) {
    return false;
  }
};

const waitForBackendReady = async (timeoutMs) => {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await isBackendHealthy()) {
      return true;
    }
    await sleep(500);
  }
  return false;
};

const startBackend = async () => {
  if (await isBackendHealthy()) {
    console.log("Backend already running, skipping app-managed startup.");
    return true;
  }

  const backendScriptPath = getBackendScriptPath();
  if (!backendScriptPath) {
    console.error(
      "Backend script not found. Set SIGMA_BACKEND_PATH if needed.",
    );
    return false;
  }

  const pythonCandidates = getPythonCommandCandidates();
  const projectRoot = path.dirname(path.dirname(backendScriptPath));

  for (const pythonCommand of pythonCandidates) {
    try {
      console.log(`Trying backend startup using: ${pythonCommand}`);

      const child = spawn(
        pythonCommand,
        ["-u", toPosixPath(backendScriptPath)],
        {
          cwd: projectRoot,
          env: {
            ...process.env,
            PYTHONUNBUFFERED: "1",
            PYTHONUTF8: "1",
            PYTHONIOENCODING: "utf-8",
          },
          windowsHide: true,
        },
      );

      child.stdout?.on("data", (chunk) => {
        writeToStreamSafely(process.stdout, `[backend] ${chunk}`);
      });

      child.stderr?.on("data", (chunk) => {
        writeToStreamSafely(process.stderr, `[backend] ${chunk}`);
      });

      child.on("error", (error) => {
        console.error(
          `Backend process error (${pythonCommand}):`,
          error.message,
        );
      });

      backendProcess = child;
      backendStartedByApp = true;

      const ready = await waitForBackendReady(BACKEND_WAIT_TIMEOUT_MS);
      if (ready) {
        console.log("Backend started successfully.");
        return true;
      }

      if (!child.killed) {
        child.kill();
      }

      backendProcess = null;
      backendStartedByApp = false;
    } catch (error) {
      console.error(
        `Failed to start backend with ${pythonCommand}:`,
        error.message,
      );
    }
  }

  console.error("Unable to start backend automatically.");
  return false;
};

const stopBackend = () => {
  if (!backendStartedByApp || !backendProcess || backendProcess.killed) {
    return;
  }

  try {
    backendProcess.kill();
  } catch (error) {
    console.error("Error while stopping backend:", error.message);
  }

  backendProcess = null;
  backendStartedByApp = false;
};

const isDevServerAvailable = async (url) => {
  try {
    const response = await fetch(url, { method: "GET" });
    return response.ok;
  } catch (error) {
    return false;
  }
};

const withSidebarParam = (urlValue, sidebarMode) => {
  if (!sidebarMode) {
    return urlValue;
  }

  return `${urlValue}${urlValue.includes("?") ? "&" : "?"}sidebar=1`;
};

const loadHomePage = async (targetWindow, options = {}) => {
  const { sidebarMode = false } = options;
  const devUrl = process.env.ELECTRON_START_URL || "http://localhost:5173";
  const productionIndex = path.join(app.getAppPath(), "dist", "index.html");
  const fallbackIndex = path.join(__dirname, "dist", "index.html");

  if (process.env.ELECTRON_START_URL) {
    await targetWindow.loadURL(withSidebarParam(devUrl, sidebarMode));
    return;
  }

  if (fs.existsSync(productionIndex)) {
    if (sidebarMode) {
      await targetWindow.loadURL(
        withSidebarParam(pathToFileURL(productionIndex).toString(), true),
      );
    } else {
      await targetWindow.loadFile(productionIndex);
    }
    return;
  }

  if (await isDevServerAvailable(devUrl)) {
    await targetWindow.loadURL(withSidebarParam(devUrl, sidebarMode));
    return;
  }

  if (sidebarMode) {
    await targetWindow.loadURL(
      withSidebarParam(pathToFileURL(fallbackIndex).toString(), true),
    );
    return;
  }

  await targetWindow.loadFile(fallbackIndex);
};

const focusOrCreateMainWindow = async () => {
  if (!mainWindow || mainWindow.isDestroyed()) {
    await createWindow();
    return;
  }

  if (mainWindow.isMinimized()) {
    mainWindow.restore();
  }

  mainWindow.show();
  mainWindow.focus();
};

const positionLauncherWindow = () => {
  if (!launcherWindow || launcherWindow.isDestroyed()) {
    return;
  }

  const [windowWidth, windowHeight] = launcherWindow.getSize();
  const sourcePoint = launcherManualPosition
    ? { x: launcherManualPosition.x, y: launcherManualPosition.y }
    : screen.getCursorScreenPoint();
  const display = screen.getDisplayNearestPoint(sourcePoint);
  const { workArea } = display;
  const defaultX = workArea.x + workArea.width - windowWidth - SIDEBAR_PADDING;
  const defaultY =
    workArea.y + Math.floor((workArea.height - windowHeight) / 2);
  const x = launcherManualPosition?.x ?? defaultX;
  const y = launcherManualPosition?.y ?? defaultY;
  const minX = workArea.x + SIDEBAR_PADDING;
  const maxY = workArea.y + workArea.height - windowHeight - SIDEBAR_PADDING;
  const maxX = workArea.x + workArea.width - windowWidth - SIDEBAR_PADDING;

  const clampedX = Math.max(minX, Math.min(x, maxX));
  const clampedY = Math.max(workArea.y + SIDEBAR_PADDING, Math.min(y, maxY));

  launcherManualPosition = { x: clampedX, y: clampedY };

  launcherWindow.setBounds({
    x: clampedX,
    y: clampedY,
    width: windowWidth,
    height: windowHeight,
  });
};

const positionSidebarPanel = () => {
  if (!panelWindow || panelWindow.isDestroyed()) {
    return;
  }

  const display = screen.getDisplayNearestPoint(screen.getCursorScreenPoint());
  const { workArea } = display;
  const computedWidth = Math.max(
    PANEL_MIN_WIDTH,
    Math.floor(workArea.width * PANEL_WIDTH_RATIO),
  );
  const panelWidth = Math.min(
    computedWidth,
    workArea.width - LAUNCHER_SIZE - SIDEBAR_PADDING * 3,
  );
  const panelHeight = workArea.height - SIDEBAR_PADDING * 2;
  const x =
    workArea.x +
    workArea.width -
    panelWidth -
    LAUNCHER_SIZE -
    SIDEBAR_PADDING * 2;
  const maxY = workArea.y + workArea.height - panelHeight - SIDEBAR_PADDING;
  const y = workArea.y + SIDEBAR_PADDING;

  panelWindow.setBounds({
    x,
    y: Math.max(workArea.y + SIDEBAR_PADDING, Math.min(y, maxY)),
    width: panelWidth,
    height: panelHeight,
  });
};

const ensureWindowAbove = (targetWindow) => {
  if (!targetWindow || targetWindow.isDestroyed()) {
    return;
  }

  targetWindow.setAlwaysOnTop(true, "screen-saver");
  if (typeof targetWindow.setVisibleOnAllWorkspaces === "function") {
    targetWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  }
};

const createLauncherWindow = async () => {
  if (launcherWindow && !launcherWindow.isDestroyed()) {
    positionLauncherWindow();
    launcherWindow.showInactive();
    ensureWindowAbove(launcherWindow);
    return launcherWindow;
  }

  launcherWindow = new BrowserWindow({
    width: LAUNCHER_SIZE,
    height: LAUNCHER_SIZE,
    show: false,
    frame: false,
    transparent: true,
    resizable: false,
    movable: true,
    minimizable: false,
    maximizable: false,
    fullscreenable: false,
    skipTaskbar: true,
    hasShadow: false,
    backgroundColor: "#00000000",
    alwaysOnTop: true,
    focusable: true,
    webPreferences: {
      contextIsolation: false,
      nodeIntegration: true,
      sandbox: false,
    },
  });

  launcherWindow.loadURL(
    `data:text/html;charset=UTF-8,${encodeURIComponent(buildLauncherHtml())}`,
  );
  positionLauncherWindow();
  ensureWindowAbove(launcherWindow);

  launcherWindow.on("closed", () => {
    launcherWindow = null;
  });

  launcherWindow.on("close", (event) => {
    if (!isQuitting) {
      event.preventDefault();
      launcherWindow.showInactive();
      ensureWindowAbove(launcherWindow);
    }
  });

  launcherWindow.on("blur", () => {
    ensureWindowAbove(launcherWindow);
  });

  launcherWindow.once("ready-to-show", () => {
    positionLauncherWindow();
    launcherWindow.show();
  });

  return launcherWindow;
};

const createPanelWindow = async () => {
  if (panelWindow && !panelWindow.isDestroyed()) {
    positionSidebarPanel();
    ensureWindowAbove(panelWindow);
    return panelWindow;
  }

  const display = screen.getDisplayNearestPoint(screen.getCursorScreenPoint());
  const sidebarHeight = display.workArea.height - SIDEBAR_PADDING * 2;
  const sidebarWidth = Math.max(
    PANEL_MIN_WIDTH,
    Math.floor(display.workArea.width * PANEL_WIDTH_RATIO),
  );

  panelWindow = new BrowserWindow({
    width: sidebarWidth,
    height: sidebarHeight,
    show: false,
    frame: false,
    resizable: false,
    movable: false,
    minimizable: false,
    maximizable: false,
    fullscreenable: false,
    skipTaskbar: true,
    backgroundColor: "#10131a",
    alwaysOnTop: true,
    icon: getLogoPath() || undefined,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  await loadHomePage(panelWindow, { sidebarMode: true });
  positionSidebarPanel();
  ensureWindowAbove(panelWindow);

  panelWindow.on("blur", () => {
    if (panelWindow && !panelWindow.isDestroyed()) {
      panelWindow.hide();
    }
  });

  panelWindow.on("close", (event) => {
    if (!isQuitting) {
      event.preventDefault();
      panelWindow.hide();
    }
  });

  panelWindow.on("closed", () => {
    panelWindow = null;
  });

  return panelWindow;
};

const toggleSidebarPanel = async () => {
  const sidebarPanel = await createPanelWindow();
  if (sidebarPanel.isVisible()) {
    sidebarPanel.hide();
    return;
  }

  positionSidebarPanel();
  ensureWindowAbove(sidebarPanel);
  sidebarPanel.show();
  sidebarPanel.focus();
};

const openMainAppWindow = async () => {
  await createLauncherWindow();
  await focusOrCreateMainWindow();
};

const ensureLinuxDesktopEntries = () => {
  if (process.platform !== "linux") {
    return;
  }

  const homeDir = os.homedir();
  const autostartDir = path.join(homeDir, ".config", "autostart");
  const applicationsDir = path.join(homeDir, ".local", "share", "applications");
  const logoPath = getLogoPath();
  const launchCommand = app.isPackaged
    ? `"${process.execPath}" --sidebar-mode`
    : `"${process.execPath}" "${app.getAppPath()}" --sidebar-mode`;

  const desktopEntryContent = [
    "[Desktop Entry]",
    "Type=Application",
    `Name=${APP_DISPLAY_NAME}`,
    `Exec=${launchCommand}`,
    `Icon=${logoPath || "application-x-executable"}`,
    "Terminal=false",
    "Categories=Utility;",
    "StartupNotify=true",
  ].join("\n");

  fs.mkdirSync(autostartDir, { recursive: true });
  fs.mkdirSync(applicationsDir, { recursive: true });

  const autostartFile = path.join(autostartDir, "SIGMA_OS.desktop");
  const launcherFile = path.join(applicationsDir, "SIGMA_OS.desktop");

  fs.writeFileSync(autostartFile, `${desktopEntryContent}\n`, "utf8");
  fs.writeFileSync(launcherFile, `${desktopEntryContent}\n`, "utf8");
  fs.chmodSync(autostartFile, 0o755);
  fs.chmodSync(launcherFile, 0o755);
};

const configureStartupIntegration = () => {
  if (process.platform === "win32" && app.isPackaged) {
    app.setLoginItemSettings({
      openAtLogin: true,
      path: process.execPath,
      args: ["--sidebar-mode"],
    });
  }

  if (process.platform === "linux") {
    ensureLinuxDesktopEntries();
  }
};

const createTray = () => {
  if (tray) {
    return tray;
  }

  const trayIcon = getTrayIcon();
  if (!trayIcon) {
    console.warn("Tray icon could not be created from logo.png");
    return null;
  }

  tray = new Tray(trayIcon);
  tray.setToolTip(APP_DISPLAY_NAME);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: "Open SIGMA Home",
      click: () => {
        openMainAppWindow();
      },
    },
    {
      label: "Toggle Sidebar",
      click: () => {
        toggleSidebarPanel();
      },
    },
    { type: "separator" },
    {
      label: "Quit",
      click: () => {
        isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);

  tray.on("click", () => {
    toggleSidebarPanel();
  });

  tray.on("double-click", () => {
    openMainAppWindow();
  });

  return tray;
};

const createWindow = async () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.show();
    mainWindow.focus();
    return mainWindow;
  }

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1200,
    minHeight: 780,
    backgroundColor: "#0b1020",
    icon: getLogoPath() || path.join(__dirname, "logo.png"),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  await loadHomePage(mainWindow);

  mainWindow.on("close", (event) => {
    if (!isQuitting && tray) {
      event.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  return mainWindow;
};

const handleSecondInstance = async (_event, argv) => {
  const sidebarRequested = argv.includes("--sidebar-mode");

  await createLauncherWindow();

  if (sidebarRequested) {
    return;
  }

  await openMainAppWindow();
};

const registerIpcHandlers = () => {
  ipcMain.removeAllListeners("sigma:toggle-sidebar");
  ipcMain.removeAllListeners("sigma:move-launcher");

  ipcMain.on("sigma:toggle-sidebar", () => {
    toggleSidebarPanel().catch((error) => {
      console.error("Failed to toggle sidebar panel:", error.message);
    });
  });

  ipcMain.on("sigma:move-launcher", (_event, payload) => {
    if (!launcherWindow || launcherWindow.isDestroyed()) {
      return;
    }

    const deltaX = Number(payload?.deltaX || 0);
    const deltaY = Number(payload?.deltaY || 0);
    const [currentX, currentY] = launcherWindow.getPosition();

    launcherManualPosition = {
      x: currentX + deltaX,
      y: currentY + deltaY,
    };

    positionLauncherWindow();
  });
};

const requestSingleInstanceLock = () => {
  const lockAcquired = app.requestSingleInstanceLock();
  if (!lockAcquired) {
    app.quit();
    return false;
  }

  app.on("second-instance", handleSecondInstance);
  return true;
};

if (!requestSingleInstanceLock()) {
  process.exit(0);
}

app.whenReady().then(async () => {
  registerIpcHandlers();
  await createLauncherWindow();
  await createPanelWindow();

  screen.on("display-metrics-changed", () => {
    positionLauncherWindow();
    positionSidebarPanel();
  });

  if (LAUNCH_MODE !== "sidebar") {
    await createWindow();
    createTray();
  }
  configureStartupIntegration();

  startBackend().catch((error) => {
    console.error("Background backend startup failed:", error.message);
  });

  app.on("activate", () => {
    if (LAUNCH_MODE === "sidebar") {
      createLauncherWindow().catch((error) => {
        console.error("Failed to restore launcher:", error.message);
      });
      return;
    }

    if (!mainWindow || mainWindow.isDestroyed()) {
      focusOrCreateMainWindow();
      return;
    }

    mainWindow.show();
    mainWindow.focus();
  });
});

app.on("window-all-closed", () => {
  if ((launcherWindow || tray) && !isQuitting) {
    return;
  }

  if (process.platform !== "darwin" || isQuitting) {
    stopBackend();
    app.quit();
  }
});

app.on("before-quit", () => {
  isQuitting = true;

  if (panelWindow && !panelWindow.isDestroyed()) {
    panelWindow.destroy();
  }

  if (launcherWindow && !launcherWindow.isDestroyed()) {
    launcherWindow.destroy();
  }

  if (tray) {
    tray.destroy();
    tray = null;
  }

  stopBackend();
});
