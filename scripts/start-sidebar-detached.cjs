const fs = require("fs");
const path = require("path");
const { spawn, execSync } = require("child_process");

const projectRoot = path.resolve(__dirname, "..");

const runFrontendBuild = () => {
  execSync("npm run build", {
    cwd: projectRoot,
    stdio: "inherit",
    shell: true,
  });
};

const resolveElectronBinary = () => {
  const explicit = process.env.SIGMA_ELECTRON_PATH;
  if (explicit && fs.existsSync(explicit)) {
    return explicit;
  }

  if (process.platform === "win32") {
    const winBinary = path.join(
      projectRoot,
      "node_modules",
      "electron",
      "dist",
      "electron.exe",
    );
    if (fs.existsSync(winBinary)) {
      return winBinary;
    }
  }

  if (process.platform === "linux") {
    const linuxBinary = path.join(
      projectRoot,
      "node_modules",
      "electron",
      "dist",
      "electron",
    );
    if (fs.existsSync(linuxBinary)) {
      return linuxBinary;
    }
  }

  return "electron";
};

const electronBinary = resolveElectronBinary();
const args = [".", "--sidebar-mode"];

runFrontendBuild();

const child = spawn(electronBinary, args, {
  cwd: projectRoot,
  detached: true,
  stdio: "ignore",
  windowsHide: true,
  env: {
    ...process.env,
  },
});

child.unref();
console.log("Sidebar launcher started in detached mode.");
