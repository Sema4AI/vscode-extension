// Writes vscode-client/out/buildInfo.json with the git commit and build time,
// shown in the Control Room view. Runs as part of `npm run compile`.
const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function git(args) {
    try {
        return execSync("git " + args, { cwd: __dirname, stdio: ["ignore", "pipe", "ignore"] })
            .toString()
            .trim();
    } catch (err) {
        return "";
    }
}

let commit = git("rev-parse --short HEAD") || "unknown";
// Only mark local builds as dirty: the release workflows intentionally rewrite
// tracked files (set-version, codegen, fix-readme) before packaging.
if (commit !== "unknown" && !process.env.GITHUB_ACTIONS && git("status --porcelain --untracked-files=no")) {
    commit += "-dirty";
}

const outDir = path.join(__dirname, "..", "vscode-client", "out");
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(
    path.join(outDir, "buildInfo.json"),
    JSON.stringify({ "commit": commit, "buildTime": new Date().toISOString() }, null, 4) + "\n"
);
