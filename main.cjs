const { app, BrowserWindow } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");

const BACKEND_HEALTH_URL =
  process.env.SIGMA_BACKEND_URL || "http://127.0.0.1:5000/health";
const BACKEND_WAIT_TIMEOUT_MS = 20000;

let backendProcess = null;
let backendStartedByApp = false;

const toPosixPath = (value) => value.replace(/\\/g, "/");

const getPathCandidates = (...values) => {
  return [...new Set(values.filter(Boolean))];
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
        process.stdout.write(`[backend] ${chunk}`);
      });

      child.stderr?.on("data", (chunk) => {
        process.stderr.write(`[backend] ${chunk}`);
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

const createWindow = async () => {
  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    minWidth: 1200,
    minHeight: 780,
    backgroundColor: "#0b1020",
    icon: path.join(__dirname, "logo.png"),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  const devUrl = process.env.ELECTRON_START_URL || "http://localhost:5173";
  const productionIndex = path.join(app.getAppPath(), "dist", "index.html");

  if (process.env.ELECTRON_START_URL) {
    await window.loadURL(devUrl);
    return window;
  }

  if (fs.existsSync(productionIndex)) {
    await window.loadFile(productionIndex);
    return window;
  }

  if (await isDevServerAvailable(devUrl)) {
    await window.loadURL(devUrl);
    return window;
  }

  await window.loadFile(path.join(__dirname, "dist", "index.html"));
  return window;
};

app.whenReady().then(async () => {
  await createWindow();
  startBackend().catch((error) => {
    console.error("Background backend startup failed:", error.message);
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    stopBackend();
    app.quit();
  }
});

app.on("before-quit", () => {
  stopBackend();
});
