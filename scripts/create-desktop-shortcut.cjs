const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const projectRoot = path.resolve(__dirname, "..");
const desktopPath = path.join(os.homedir(), "Desktop");
const releasePath = path.join(projectRoot, "release");
const logoPath = path.join(projectRoot, "logo.png");
const logoIconPath = path.join(__dirname, "logo.ico");
const shortcutName = "\u00a0";
const blankOverlayIconPath = path.join(__dirname, "blank-overlay.ico");

const transparentPngBase64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/S3QAAAAASUVORK5CYII=";

const findFirstMatch = (rootDir, matcher) => {
  if (!fs.existsSync(rootDir)) {
    return null;
  }

  const entries = fs.readdirSync(rootDir, { withFileTypes: true });
  for (const entry of entries) {
    const entryPath = path.join(rootDir, entry.name);
    if (entry.isDirectory()) {
      const nestedMatch = findFirstMatch(entryPath, matcher);
      if (nestedMatch) {
        return nestedMatch;
      }
      continue;
    }

    if (matcher(entryPath)) {
      return entryPath;
    }
  }

  return null;
};

const ensureDesktopDir = () => {
  if (!fs.existsSync(desktopPath)) {
    throw new Error(`Desktop folder not found: ${desktopPath}`);
  }
};

const removePreviousShortcuts = () => {
  const previousShortcuts = [
    path.join(desktopPath, "SIGMA_OS.lnk"),
    path.join(desktopPath, `${shortcutName}.lnk`),
  ];

  for (const shortcutPath of previousShortcuts) {
    if (fs.existsSync(shortcutPath)) {
      fs.unlinkSync(shortcutPath);
    }
  }
};

const ensureBlankOverlayIcon = () => {
  if (fs.existsSync(blankOverlayIconPath)) {
    return blankOverlayIconPath;
  }

  const pngBuffer = Buffer.from(transparentPngBase64, "base64");
  const iconBuffer = Buffer.alloc(6 + 16 + pngBuffer.length);

  iconBuffer.writeUInt16LE(0, 0);
  iconBuffer.writeUInt16LE(1, 2);
  iconBuffer.writeUInt16LE(1, 4);

  iconBuffer.writeUInt8(1, 6);
  iconBuffer.writeUInt8(1, 7);
  iconBuffer.writeUInt8(0, 8);
  iconBuffer.writeUInt8(0, 9);
  iconBuffer.writeUInt16LE(1, 10);
  iconBuffer.writeUInt16LE(32, 12);
  iconBuffer.writeUInt32LE(pngBuffer.length, 14);
  iconBuffer.writeUInt32LE(22, 18);

  pngBuffer.copy(iconBuffer, 22);
  fs.writeFileSync(blankOverlayIconPath, iconBuffer);
  return blankOverlayIconPath;
};

const ensureLogoIcon = () => {
  if (!fs.existsSync(logoPath)) {
    throw new Error(`Logo file not found: ${logoPath}`);
  }

  if (fs.existsSync(logoIconPath)) {
    return logoIconPath;
  }

  const pythonCode = [
    "from pathlib import Path",
    "from PIL import Image",
    `source = Path(r'''${logoPath}''')`,
    `target = Path(r'''${logoIconPath}''')`,
    "image = Image.open(source).convert('RGBA')",
    "image.save(target, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])",
  ].join("; ");

  execFileSync("python", ["-c", pythonCode], {
    stdio: "inherit",
  });

  return logoIconPath;
};

const getPackagedAppPath = () => {
  if (process.platform === "win32") {
    return findFirstMatch(path.join(releasePath, "win-unpacked"), (filePath) =>
      filePath.toLowerCase().endsWith(".exe"),
    );
  }

  if (process.platform === "linux") {
    const appImage = findFirstMatch(releasePath, (filePath) =>
      filePath.endsWith(".AppImage"),
    );
    if (appImage) {
      return appImage;
    }

    return findFirstMatch(
      path.join(releasePath, "linux-unpacked"),
      (filePath) => {
        return (
          !filePath.endsWith(".desktop") &&
          fs.existsSync(filePath) &&
          fs.statSync(filePath).mode & 0o111
        );
      },
    );
  }

  return null;
};

const createWindowsShortcut = (targetPath) => {
  const shortcutPath = path.join(desktopPath, `${shortcutName}.lnk`);
  ensureLogoIcon();
  const iconLocation = targetPath;

  const script = [
    "$ws = New-Object -ComObject WScript.Shell",
    `$shortcut = $ws.CreateShortcut('${shortcutPath.replace(/'/g, "''")}')`,
    `$shortcut.TargetPath = '${targetPath.replace(/'/g, "''")}';`,
    `$shortcut.WorkingDirectory = '${path.dirname(targetPath).replace(/'/g, "''")}';`,
    `$shortcut.IconLocation = '${iconLocation.replace(/'/g, "''")},0';`,
    "$shortcut.Save()",
  ].join("; ");

  execFileSync(
    "powershell.exe",
    ["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
    {
      stdio: "inherit",
    },
  );

  console.log(`Created Windows shortcut: ${shortcutPath}`);
};

const removeWindowsShortcutArrowOverlay = () => {
  const iconPath = ensureBlankOverlayIcon();
  const registryPath =
    "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Icons";

  execFileSync(
    "reg.exe",
    ["ADD", registryPath, "/v", "29", "/t", "REG_SZ", "/d", iconPath, "/f"],
    { stdio: "inherit" },
  );

  try {
    execFileSync(
      "powershell.exe",
      [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "Stop-Process -Name explorer -Force; Start-Process explorer.exe",
      ],
      { stdio: "inherit" },
    );
  } catch (error) {
    console.warn(
      "Explorer refresh skipped; sign out and back in to apply the new icon overlay.",
    );
  }
};

const createLinuxShortcut = (targetPath) => {
  const shortcutPath = path.join(desktopPath, `${shortcutName}.desktop`);
  const contents = [
    "[Desktop Entry]",
    "Type=Application",
    `Name=${shortcutName}`,
    `Exec="${targetPath}"`,
    `Icon=${logoPath}`,
    "Terminal=false",
    "Categories=Utility;Application;",
  ].join("\n");

  fs.writeFileSync(shortcutPath, contents, "utf8");
  fs.chmodSync(shortcutPath, 0o755);
  console.log(`Created Linux shortcut: ${shortcutPath}`);
};

try {
  ensureDesktopDir();
  removePreviousShortcuts();

  const packagedAppPath = getPackagedAppPath();
  if (!packagedAppPath) {
    throw new Error(
      "Packaged app not found. Run `npm run electron:pack` first.",
    );
  }

  if (process.platform === "win32") {
    createWindowsShortcut(packagedAppPath);
    removeWindowsShortcutArrowOverlay();
  } else if (process.platform === "linux") {
    createLinuxShortcut(packagedAppPath);
  } else {
    throw new Error(`Unsupported platform: ${process.platform}`);
  }
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
