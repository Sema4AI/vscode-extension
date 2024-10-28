import * as fs from "fs";
import * as path from "path";
import * as pathModule from "path";
import * as os from "os";
import { configure as configureXHR } from "./requestLight";
import { fileExists, getExtensionRelativeFile } from "./files";
import { CancellationToken, extensions, Progress, ProgressLocation, window, workspace } from "vscode";
import { logError, OUTPUT_CHANNEL } from "./channel";
import { Timing } from "./time";
import { execFilePromise, ExecFileReturn, mergeEnviron } from "./subprocess";
import * as roboConfig from "./robocorpSettings";
import { getProceedwithlongpathsdisabled } from "./robocorpSettings";
import { runAsAdminWin32 } from "./extensionCreateEnv";
import { GLOBAL_STATE } from "./extension";
import { downloadWithProgress, DownloadProgress } from "./http";

let lastPrintedRobocorpHome: string = "";

export enum Metrics {
    VSCODE_CODE_ERROR = "vscode.code.error",
    CONVERTER_USED = "vscode.converter.used",
    CONVERTER_ERROR = "vscode.converter.error",
}

export async function getRobocorpHome(): Promise<string> {
    let home: string = roboConfig.getHome();
    let details = " (found in settings)";

    if (!home || home.length == 0) {
        const sema4aiHome = process.env["SEMA4AI_HOME"];
        if (sema4aiHome) {
            if (lastPrintedRobocorpHome != sema4aiHome) {
                lastPrintedRobocorpHome = sema4aiHome;
                OUTPUT_CHANNEL.appendLine("SEMA4AI_HOME: " + sema4aiHome + " (found in SEMA4AI_HOME env var)");
            }
            return sema4aiHome;
        }

        home = process.env["ROBOCORP_HOME"];
        if (!home) {
            // Default from RCC (maybe it should provide an API to get it before creating an env?)
            details = " (default)";
            if (process.platform == "win32") {
                home = path.join(process.env.LOCALAPPDATA, "sema4ai");
            } else {
                home = path.join(process.env.HOME, ".sema4ai");
            }
        } else {
            details = " (found in ROBOCORP_HOME env var)";
        }
    }
    if (lastPrintedRobocorpHome != home) {
        lastPrintedRobocorpHome = home;
        OUTPUT_CHANNEL.appendLine("SEMA4AI_HOME: " + home + details);
    }
    return home;
}

export function createEnvWithRobocorpHome(robocorpHome: string): { [key: string]: string } {
    const base = { "ROBOCORP_HOME": robocorpHome, "SEMA4AI_HOME": robocorpHome };
    if (getProceedwithlongpathsdisabled()) {
        base["ROBOCORP_OVERRIDE_SYSTEM_REQUIREMENTS"] = "1";
    }

    let env: { [key: string]: string } = mergeEnviron(base);
    return env;
}

function envArrayToEnvMap(envArray: [], robocorpHome: string): { [key: string]: string | null } {
    let env = createEnvWithRobocorpHome(robocorpHome);
    for (let index = 0; index < envArray.length; index++) {
        const element = envArray[index];
        let key: string = element["key"];
        if (process.platform == "win32") {
            key = key.toUpperCase();
        }
        env[key] = element["value"];
    }
    return env;
}

async function checkCachedEnvValid(env): Promise<boolean> {
    let pythonExe = env["PYTHON_EXE"];

    if (!pythonExe || !fs.existsSync(pythonExe)) {
        OUTPUT_CHANNEL.appendLine("Error. PYTHON_EXE not valid in env cache.");
        return false;
    }
    let condaPrefix = env["CONDA_PREFIX"];
    if (!condaPrefix || !fs.existsSync(condaPrefix)) {
        OUTPUT_CHANNEL.appendLine("Error. CONDA_PREFIX not valid in env cache.");
        return false;
    }
    let condaPrefixIdentityYaml = path.join(condaPrefix, "identity.yaml");
    if (!fs.existsSync(condaPrefixIdentityYaml)) {
        OUTPUT_CHANNEL.appendLine("Error. " + condaPrefixIdentityYaml + " no longer exists.");
        return false;
    }

    let execFileReturn: ExecFileReturn = await execFilePromise(pythonExe, ["-c", 'import threading;print("OK")'], {
        env: env,
    });
    if (execFileReturn.stderr) {
        OUTPUT_CHANNEL.appendLine(
            "Expected no output in stderr from cached python (" + pythonExe + "). Found:\n" + execFileReturn.stderr
        );
        return false;
    }
    if (!execFileReturn.stdout) {
        OUTPUT_CHANNEL.appendLine("No output received when checking cached python (" + pythonExe + ").");
        return false;
    }
    if (!execFileReturn.stdout.includes("OK")) {
        OUTPUT_CHANNEL.appendLine(
            "Expected 'OK' in output from cached python (" + pythonExe + "). Found:\n" + execFileReturn.stdout
        );
        return false;
    }
    return true;
}

async function downloadRcc(
    progress: Progress<{ message?: string; increment?: number }>,
    token: CancellationToken
): Promise<string | undefined> {
    // Configure library with http settings.
    // i.e.: https://code.visualstudio.com/docs/setup/network
    let httpSettings = workspace.getConfiguration("http");
    configureXHR(httpSettings.get<string>("proxy"), httpSettings.get<boolean>("proxyStrictSSL"));
    let location = getExpectedRccLocation();
    let relativePath: string;
    if (process.platform == "win32") {
        if (process.arch === "x64" || process.env.hasOwnProperty("PROCESSOR_ARCHITEW6432")) {
            // Check if node is a 64 bit process or if it's a 32 bit process running in a 64 bit processor.
            relativePath = "/windows64/rcc.exe";
        } else {
            throw new Error("Currently only Windows amd64 is supported.");
        }
    } else if (process.platform == "darwin") {
        relativePath = "/macos64/rcc";
    } else {
        // Linux
        if (process.arch == "x64") {
            relativePath = "/linux64/rcc";
        } else {
            throw new Error("Currently only Linux amd64 is supported.");
        }
    }
    const RCC_VERSION = "v18.5.0";
    const prefix = "https://cdn.sema4.ai/rcc/releases/" + RCC_VERSION;
    const url: string = prefix + relativePath;
    return await downloadWithProgress(url, progress, token, location);
}

// Note: python tests scan this file and get these constants, so, if the format
// changes the (failing) test also needs to change.
const BASENAME_PREBUILT_WIN_AMD64 = "ffb5eee1a191f326_windows_amd64.zip";
const BASENAME_PREBUILT_DARWIN = "3b0e7686450769fe_darwin_amd64.zip";
const BASENAME_PREBUILT_LINUX_AMD64 = "def1f9df7f786b9e_linux_amd64.zip";

function getBaseAsZipBasename() {
    let basename: string;
    if (process.platform == "win32") {
        if (process.arch === "x64" || process.env.hasOwnProperty("PROCESSOR_ARCHITEW6432")) {
            // Check if node is a 64 bit process or if it's a 32 bit process running in a 64 bit processor.
            basename = BASENAME_PREBUILT_WIN_AMD64;
        } else {
            throw new Error("Currently only Windows amd64 is supported.");
        }
    } else if (process.platform == "darwin") {
        basename = BASENAME_PREBUILT_DARWIN;
    } else {
        // Linux
        if (process.arch === "x64") {
            basename = BASENAME_PREBUILT_LINUX_AMD64;
        } else {
            throw new Error("Currently only Linux amd64 is supported.");
        }
    }
    return basename;
}

/**
 * Provides the place where the zip with the base environment should be downloaded.
 */
async function getBaseAsZipDownloadLocation(): Promise<string> {
    const robocorpHome = await getRobocorpHome();
    let robocorpCodePath = path.join(robocorpHome, ".sema4ai_code");
    return path.join(robocorpCodePath, getBaseAsZipBasename());
}

async function downloadBaseAsZip(
    progress: Progress<DownloadProgress>,
    token: CancellationToken,
    zipDownloadLocation: string
) {
    let timing = new Timing();
    let httpSettings = workspace.getConfiguration("http");
    configureXHR(httpSettings.get<string>("proxy"), httpSettings.get<boolean>("proxyStrictSSL"));
    const basename = getBaseAsZipBasename();
    const url: string = "https://cdn.sema4.ai/holotree/sema4ai/" + basename;
    const ret = await downloadWithProgress(url, progress, token, zipDownloadLocation);

    OUTPUT_CHANNEL.appendLine(
        "Took: " + timing.getTotalElapsedAsStr() + " to download base environment (" + zipDownloadLocation + ")."
    );

    return ret;
}

function getExpectedRccLocation(): string {
    let location: string;
    if (process.platform == "win32") {
        location = getExtensionRelativeFile("../../bin/rcc.exe", false);
    } else {
        location = getExtensionRelativeFile("../../bin/rcc", false);
    }
    return location;
}

// We can't really ship rcc per-platform right now (so, we need to either
// download it or ship it along).
// See: https://github.com/microsoft/vscode/issues/6929
// See: https://github.com/microsoft/vscode/issues/23251
// In particular, if we download things, we should use:
// https://www.npmjs.com/package/request-light according to:
// https://github.com/microsoft/vscode/issues/6929#issuecomment-222153748

export async function getRccLocation(): Promise<string | undefined> {
    const location = getExpectedRccLocation();

    if (!(await fileExists(location))) {
        await window.withProgress(
            {
                location: ProgressLocation.Notification,
                title: "Download conda manager (rcc).",
                cancellable: false,
            },
            downloadRcc
        );
    }
    return location;
}

export const STATUS_OK = "ok";
export const STATUS_FATAL = "fatal";
export const STATUS_FAIL = "fail";
export const STATUS_WARNING = "warning";

// RCC categories:
// https://github.com/robocorp/rcc/blob/master/common/categories.go#L4-L14

const CategoryUndefined: number = 0;
const CategoryLongPath: number = 1010;
const CategoryLockFile: number = 1020;
const CategoryLockPid: number = 1021;
const CategoryPathCheck: number = 1030;
const CategoryHolotreeShared: number = 2010;
const CategoryRobocorpHome: number = 3010;
const CategoryNetworkDNS: number = 4010;
const CategoryNetworkLink: number = 4020;
const CategoryNetworkHEAD: number = 4030;
const CategoryNetworkCanary: number = 4040;

export interface CheckDiagnostic {
    type: string;
    status: string; // ok | fatal | fail | warning
    message: string;
    url: string;
    category: number; // See CategoryXXX constants above.
}

export class RCCDiagnostics {
    failedChecks: CheckDiagnostic[];
    holotreeShared: boolean;
    private roboHomeOk: boolean;

    constructor(checks: CheckDiagnostic[], details: Map<string, string>) {
        this.roboHomeOk = true;
        this.failedChecks = [];
        this.holotreeShared = details["holotree-shared"] == "true";

        for (const check of checks) {
            if (check.status != STATUS_OK) {
                if (check.status === STATUS_WARNING) {
                    if (check.category === CategoryLockFile || check.category === CategoryLockPid) {
                        // We ignore warnings for Locks because they may happen as part of the
                        // regular operation (because RCC may leave those around as leftovers when RCC
                        // is killed).
                        continue;
                    }
                }

                if (check.category === CategoryLockFile) {
                    // We ignore all errors related to lock files (even errors)
                    // due to: https://github.com/robocorp/rcc/issues/43
                    // -- Running rcc.exe config diagnostics in a clean machine gives errors related to locks.
                    continue;
                }

                if (check.category === CategoryLongPath) {
                    // We deal with long paths as a part of the startup process.
                    continue;
                }
                this.failedChecks.push(check);
                if (check.category === CategoryRobocorpHome) {
                    this.roboHomeOk = false;
                }
            }
        }
    }

    isRobocorpHomeOk(): boolean {
        return this.roboHomeOk;
    }
}

/**
 * @param robocorpHome if given, this will be passed as the ROBOCORP_HOME environment variable.
 */
export async function runConfigDiagnostics(
    rccLocation: string,
    robocorpHome: string | undefined
): Promise<RCCDiagnostics | undefined> {
    let configureLongpathsOutput: ExecFileReturn | undefined = undefined;
    let timing = new Timing();
    try {
        let env = mergeEnviron({ "ROBOCORP_HOME": robocorpHome, "SEMA4AI_HOME": robocorpHome });
        configureLongpathsOutput = await execFilePromise(
            rccLocation,
            ["configure", "diagnostics", "-j", "--bundled", "--sema4ai", "--controller", "Sema4aiCode"],
            { env: env }
        );
        let outputAsJSON = JSON.parse(configureLongpathsOutput.stdout);
        let checks: CheckDiagnostic[] = outputAsJSON.checks;
        let details: Map<string, string> = outputAsJSON.details;

        const ret = new RCCDiagnostics(checks, details);

        // Ok, we've been able to parse the JSON. Let's print the output in a format that's not
        // difficult to visually parse afterwards.
        OUTPUT_CHANNEL.appendLine("RCC Diagnostics:");
        for (const [key, value] of Object.entries(outputAsJSON)) {
            if (key === "checks") {
                OUTPUT_CHANNEL.appendLine("  RCC Checks:");
                for (const check of checks) {
                    OUTPUT_CHANNEL.appendLine(
                        `    ${check.type.padEnd(10)} - ${check.status.padEnd(7)} - ${check.message} (${
                            check.category
                        })`
                    );
                }
            } else if (key === "details") {
                OUTPUT_CHANNEL.appendLine("  RCC Details:");
                for (const [detailsKey, detailsValue] of Object.entries(details)) {
                    OUTPUT_CHANNEL.appendLine(`    ${detailsKey.padEnd(40)} - ${detailsValue}`);
                }
            } else {
                OUTPUT_CHANNEL.appendLine(`  RCC ${JSON.stringify(key)}:`);
                // We didn't expect this, let's just print it as json.
                OUTPUT_CHANNEL.appendLine(`    ${JSON.stringify(value)}`);
            }
        }
        return ret;
    } catch (error) {
        logError("Error getting RCC diagnostics.", error, "RCC_DIAGNOSTICS");
        OUTPUT_CHANNEL.appendLine(
            "RCC Diagnostics:" +
                "\nStdout:\n" +
                configureLongpathsOutput.stdout +
                "\nStderr:\n" +
                configureLongpathsOutput.stderr
        );
        return undefined;
    } finally {
        OUTPUT_CHANNEL.appendLine("\nTook " + timing.getTotalElapsedAsStr() + " to obtain diagnostics.");
    }
}

export interface CollectedLogs {
    logsRootDir: string;
    logFiles: string[];
}

export async function collectIssueLogs(logPath: string): Promise<CollectedLogs> {
    function acceptLogFile(f: string): boolean {
        let lower = path.basename(f).toLowerCase();
        if (!lower.endsWith(".log")) {
            return false;
        }
        // Whitelist what we want so that we don't gather unwanted info.
        if (
            lower.includes("robocorp code") ||
            lower.includes("robot framework") ||
            lower.includes("exthost") ||
            lower.includes("sema4.ai")
        ) {
            return true;
        }
        return false;
    }

    // This should be parent directory for the logs.
    let logsRootDir: string = path.dirname(logPath);
    OUTPUT_CHANNEL.appendLine("Log path: " + logsRootDir);
    let logFiles: string[] = [];

    const stat = await fs.promises.stat(logsRootDir);
    if (stat.isDirectory()) {
        // Get the .log files under the logsRootDir and subfolders.
        const files: string[] = await fs.promises.readdir(logsRootDir);
        for (const fileI of files) {
            let f: string = path.join(logsRootDir, fileI);
            const stat = await fs.promises.stat(f);
            if (acceptLogFile(f) && stat.isFile()) {
                logFiles.push(f);
            } else if (stat.isDirectory()) {
                // No need to recurse (we just go 1 level deep).
                let currDir: string = f;
                const innerFiles: string[] = await fs.promises.readdir(currDir);
                for (const fileI of innerFiles) {
                    let f: string = path.join(currDir, fileI);
                    const stat = await fs.promises.stat(f);
                    if (acceptLogFile(f) && stat.isFile()) {
                        logFiles.push(f);
                    }
                }
            }
        }
    }

    return {
        "logsRootDir": logsRootDir,
        "logFiles": logFiles,
    };
}

async function collectIssueBaseMetadata(): Promise<any> {
    let version = extensions.getExtension("sema4ai.sema4ai").packageJSON.version;
    const metadata = {
        platform: os.platform(),
        osRelease: os.release(),
        nodeVersion: process.version,
        version: version,
        controller: "rcc.sema4aicode",
    };
    return metadata;
}

export async function submitIssue(
    dialogMessage: string,
    email: string,
    errorName: string,
    errorCode: string,
    errorMessage: string,
    files: string[] // See also: collectIssueLogs(logPath);
): Promise<undefined> {
    let errored: boolean = false;
    try {
        let rccLocation: string | undefined = await getRccLocation();
        if (rccLocation) {
            if (!fs.existsSync(rccLocation)) {
                let msg = "Unable to send issue report (" + rccLocation + ") does not exist.";
                OUTPUT_CHANNEL.appendLine(msg);
                window.showErrorMessage(msg);
                return;
            }

            const metadata = await collectIssueBaseMetadata();

            // Add required metadata info from parameters.
            metadata["dialogMessage"] = dialogMessage;
            metadata["email"] = email;
            metadata["errorName"] = errorName;
            metadata["errorCode"] = errorCode;
            metadata["errorMessage"] = errorMessage;

            const robocorpHome = await getRobocorpHome();

            const reportPath: string = path.join(os.tmpdir(), `robocode_issue_report_${Date.now()}.json`);
            fs.writeFileSync(reportPath, JSON.stringify(metadata, null, 4), { encoding: "utf-8" });
            let args: string[] = [
                "feedback",
                "issue",
                "-r",
                reportPath,
                "--bundled",
                "--sema4ai",
                "--controller",
                "Sema4aiCode",
            ];
            for (const file of files) {
                args.push("-a");
                args.push(file);
            }

            const env = createEnvWithRobocorpHome(robocorpHome);

            await execFilePromise(rccLocation, args, { "env": env });
        }
    } catch (err) {
        errored = true;
        logError("Error sending issue.", err, "RCC_SEND_ISSUE");
        window.showErrorMessage("The issue report was not sent. Please see the OUTPUT for more information.");
        OUTPUT_CHANNEL.show();
    }
    if (!errored) {
        OUTPUT_CHANNEL.appendLine("Issue sent.");
        window.showInformationMessage(
            "Thank you for your issue report. Please check you e-mail (" + email + ") for confirmation."
        );
    }
    return;
}

interface IEnvInfo {
    env: { [key: string]: string | null };
    robocorpHome: string | undefined;
    rccLocation: string;
}

export async function feedback(name: string, value: string = "+1") {
    const rccLocation = await getRccLocation();
    let args: string[] = ["feedback", "metric", "--bundled", "--sema4ai", "-t", "vscode", "-n", name, "-v", value];

    const robocorpHome = await getRobocorpHome();
    const env = createEnvWithRobocorpHome(robocorpHome);

    await execFilePromise(rccLocation, args, { "env": env }, { "hideCommandLine": true });
}

export async function feedbackRobocorpCodeError(errorCode: string) {
    await feedbackAnyError(Metrics.VSCODE_CODE_ERROR, errorCode);
}

const reportedErrorCodes = new Set();

/**
 * Submit feedback on some predefined error code.
 *
 * @param errorType Something as "vscode.code.error"
 * @param errorCode The error code to be shown.
 */
export async function feedbackAnyError(errorType: string, errorCode: string) {
    if (!errorCode) {
        return;
    }
    // Make sure that only one error is reported per error code.
    const errorCodeKey = `${errorType}.${errorCode}`;
    if (reportedErrorCodes.has(errorCodeKey)) {
        return;
    }
    reportedErrorCodes.add(errorCodeKey);

    const rccLocation = await getRccLocation();
    let args: string[] = [
        "feedback",
        "metric",
        "-t",
        "vscode",
        "-n",
        errorType,
        "-v",
        errorCode,
        "--bundled",
        "--sema4ai",
    ];

    const robocorpHome = await getRobocorpHome();
    const env = createEnvWithRobocorpHome(robocorpHome);

    await execFilePromise(rccLocation, args, { "env": env }, { "hideCommandLine": true });
}

/**
 * Note: it's possible that even after enabling this function the holotree isn't shared
 * if the user doesn't have permissions and can't run as admin.
 */
async function enableHolotreeShared(rccLocation: string, env) {
    const IGNORE_HOLOTREE_SHARED_ENABLE_FAILURE = "IGNORE_HOLOTREE_SHARED_ENABLE_FAILURE";

    try {
        // Enable the holotree shared mode: this changes permissions so that more than one
        // user may write to the holotree (usually in C:\ProgramData\robocorp\ht).
        try {
            const execFileReturn: ExecFileReturn = await execFilePromise(
                rccLocation,
                ["holotree", "shared", "--enable", "--once", "--bundled", "--sema4ai"],
                { "env": env },
                { "showOutputInteractively": true }
            );
            OUTPUT_CHANNEL.appendLine("Enabled shared holotree");
        } catch (err) {
            if (!GLOBAL_STATE.get(IGNORE_HOLOTREE_SHARED_ENABLE_FAILURE)) {
                if (process.platform == "win32") {
                    const RETRY_AS_ADMIN = "Retry as admin";
                    const IGNORE = "Ignore (don't ask again)";
                    let response = await window.showWarningMessage(
                        "It was not possible to enable the holotree shared mode. How do you want to proceed?",
                        {
                            "modal": true,
                            "detail":
                                "It is Ok to ignore if environments won't be shared with other users in this machine.",
                        },
                        RETRY_AS_ADMIN,
                        IGNORE
                    );
                    if (response === RETRY_AS_ADMIN) {
                        await runAsAdminWin32(rccLocation, ["holotree", "shared", "--enable", "--once"], env);
                    } else if (response === IGNORE) {
                        await GLOBAL_STATE.update(IGNORE_HOLOTREE_SHARED_ENABLE_FAILURE, true);
                    }
                }
            }
        }
    } catch (err) {
        logError("Error while enabling shared holotree.", err, "ERROR_ENABLE_SHARED_HOLOTREE");
    }
}

async function initHolotree(rccLocation: string, env): Promise<boolean> {
    try {
        const execFileReturn = await execFilePromise(
            rccLocation,
            ["holotree", "init", "--bundled", "--sema4ai"],
            { "env": env },
            { "showOutputInteractively": true }
        );
        OUTPUT_CHANNEL.appendLine("Set user to use shared holotree");
        return true;
    } catch (err) {
        logError("Error while initializing shared holotree.", err, "ERROR_INITIALIZE_SHARED_HOLOTREE");
        return false;
    }
}

/**
 * This function creates the base holotree space with RCC and then returns its info
 * to start up the language server.
 *
 * @param robocorpHome usually roboConfig.getHome()
 */
export async function collectBaseEnv(
    condaFilePath: string,
    robotCondaHash: string,
    robocorpHome: string | undefined,
    rccDiagnostics: RCCDiagnostics
): Promise<IEnvInfo | undefined> {
    let spaceName = "vscode-base-v01-" + robotCondaHash.substring(0, 6);

    let robocorpCodePath = path.join(robocorpHome, ".sema4ai_code");
    let spaceInfoPath = path.join(robocorpCodePath, spaceName);
    const spaceInfoPathExists = fs.existsSync(spaceInfoPath);
    OUTPUT_CHANNEL.appendLine("Found base environment info on: " + spaceInfoPathExists);
    let rccEnvInfoCachePath = path.join(spaceInfoPath, "rcc_env_info_sema4ai.json");
    try {
        if (!spaceInfoPathExists) {
            fs.mkdirSync(spaceInfoPath, { "recursive": true });
        }
    } catch (err) {
        logError("Error creating directory: " + spaceInfoPath, err, "RCC_COLLECT_BASE_ENV_MKDIR");
    }

    const rccLocation = await getRccLocation();
    if (!rccLocation) {
        window.showErrorMessage("Unable to find RCC.");
        return;
    }
    const USE_PROGRAM_DATA_SHARED = true;
    if (USE_PROGRAM_DATA_SHARED) {
        const env = createEnvWithRobocorpHome(robocorpHome);

        if (!rccDiagnostics.holotreeShared) {
            // i.e.: if the shared mode is still not enabled, enable it, download the
            // base environment .zip and import it.
            await enableHolotreeShared(rccLocation, env);

            const holotreeInitOk: boolean = await initHolotree(rccLocation, env);
            if (holotreeInitOk) {
                await makeSharedHolotreeEnvImport(rccLocation, env);
            }
        } else {
            // It was already shared once
            if (!spaceInfoPathExists) {
                // On new env do the shared holotree import
                await makeSharedHolotreeEnvImport(rccLocation, env);
            }
        }
    }

    let envArray = undefined;
    try {
        if (fs.existsSync(rccEnvInfoCachePath)) {
            let contents = fs.readFileSync(rccEnvInfoCachePath, { "encoding": "utf-8" });
            envArray = JSON.parse(contents);
            let cachedEnv = envArrayToEnvMap(envArray, robocorpHome);
            try {
                // Ok, we have the python exe and the env seems valid. Let's make sure it actually works.
                let cachedPythonOk: boolean = await checkCachedEnvValid(cachedEnv);
                if (!cachedPythonOk) {
                    envArray = undefined;
                }
            } catch (error) {
                logError("Error: error verifying if env is still valid.", error, "RCC_VERIFY_ENV_STILL_VALID");
                envArray = undefined;
            }

            if (envArray) {
                OUTPUT_CHANNEL.appendLine("Loading base environment from: " + rccEnvInfoCachePath);
            }
        }
    } catch (err) {
        logError("Unable to use cached environment info (recomputing)...", err, "RCC_UNABLE_TO_USE_CACHED");
        envArray = undefined;
    }

    // If the env array is undefined, compute it now and cache the info to be reused later.
    if (!envArray) {
        // If the robot is located in a directory that has '/devdata/env.json', we must automatically
        // add the -e /path/to/devdata/env.json.

        let robotDirName = pathModule.dirname(condaFilePath);
        let envFilename = pathModule.join(robotDirName, "devdata", "env.json");
        let args = ["holotree", "variables", "--space", spaceName, "--json", condaFilePath];
        if (await fileExists(envFilename)) {
            args.push("-e");
            args.push(envFilename);
        }
        args.push("--sema4ai");
        args.push("--bundled");
        args.push("--controller");
        args.push("Sema4aiCode");

        let execFileReturn: ExecFileReturn = await execFilePromise(
            rccLocation,
            args,
            { "env": createEnvWithRobocorpHome(robocorpHome) },
            { "showOutputInteractively": true }
        );
        if (!execFileReturn.stdout) {
            feedbackRobocorpCodeError("RCC_NO_RCC_ENV_STDOUT");
            OUTPUT_CHANNEL.appendLine("Error: Unable to collect environment from RCC.");
            return undefined;
        }
        try {
            envArray = JSON.parse(execFileReturn.stdout);
        } catch (error) {
            logError("Error parsing env from RCC: " + execFileReturn.stdout, error, "RCC_NO_RCC_ENV_STDOUT");
        }
        if (!envArray) {
            OUTPUT_CHANNEL.appendLine("Error: Unable to collect env array.");
            return undefined;
        }
        try {
            fs.writeFileSync(rccEnvInfoCachePath, JSON.stringify(envArray));
        } catch (err) {
            logError("Error writing environment cache.", err, "RCC_ERROR_WRITE_ENV_CACHE");
        }
    }

    let timestampPath = path.join(spaceInfoPath, "last_usage");
    try {
        fs.writeFileSync(timestampPath, "" + Date.now());
    } catch (err) {
        logError("Error writing last usage time to: " + timestampPath, err, "RCC_UPDATE_FILE_USAGE");
    }

    let finalEnv: { [key: string]: string | null } = envArrayToEnvMap(envArray, robocorpHome);
    let tempDir = finalEnv["TEMP"];
    if (tempDir) {
        try {
            // Try to remove the file related to recycling this dir (we don't want to
            // recycle the TEMP dir of this particular env).
            fs.unlink(path.join(tempDir, "recycle.now"), (err) => {});
        } catch (err) {}
        try {
            // Create the temp dir (if not there)
            fs.mkdir(tempDir, { "recursive": true }, (err) => {});
        } catch (err) {}
    }

    return { "env": finalEnv, "robocorpHome": robocorpHome, "rccLocation": rccLocation };
}

// Returns something as: https://cloud.robocorp.com/
// The baseUrl is something as: "cloud-ui" or "docs".
export async function getEndpointUrl(baseUrl): Promise<string> {
    try {
        const robocorpHome = await getRobocorpHome();
        const env = createEnvWithRobocorpHome(robocorpHome);

        const rccLocation = await getRccLocation();
        let args: string[] = ["config", "settings", "--bundled", "--sema4ai", "--json"];
        const execReturn: ExecFileReturn = await execFilePromise(
            rccLocation,
            args,
            { "env": env },
            { "hideCommandLine": true }
        );
        const stdout = execReturn.stdout;
        if (stdout) {
            const configSettings = JSON.parse(stdout);
            let url = configSettings["endpoints"][baseUrl];
            if (!url.endsWith("/")) {
                url += "/";
            }
            return url;
        } else {
            throw new Error("No stdout from rcc config settings. stderr: " + execReturn.stderr);
        }
    } catch (error) {
        logError("Error getting cloud base url.", error, "RCC_GET_CLOUD_BASE_URL");
    }

    if (baseUrl == "cloud-ui") {
        return "https://cloud.robocorp.com/";
    }
    if (baseUrl == "docs") {
        return "https://robocorp.com/docs/";
    }
    throw new Error("Unable to get endpoint url: " + baseUrl);
}

async function makeSharedHolotreeEnvImport(rccLocation: string, env: { [key: string]: string }) {
    // Download and import into holotree.
    const zipDownloadLocation = await getBaseAsZipDownloadLocation();
    let downloadOk: boolean = false;
    try {
        if (!(await fileExists(zipDownloadLocation))) {
            await window.withProgress(
                {
                    location: ProgressLocation.Notification,
                    title: "Download base environment.",
                    cancellable: false,
                },
                async (progress, token) => await downloadBaseAsZip(progress, token, zipDownloadLocation)
            );
        }
        downloadOk = await fileExists(zipDownloadLocation);
    } catch (err) {
        logError("Error while downloading shared holotree.", err, "ERROR_DOWNLOAD_BASE_ZIP");
    }
    if (downloadOk) {
        try {
            let execFileReturn: ExecFileReturn;
            let timing = new Timing();
            execFileReturn = await execFilePromise(
                rccLocation,
                ["holotree", "import", zipDownloadLocation, "--bundled", "--sema4ai"],
                { "env": env },
                { "showOutputInteractively": true }
            );
            OUTPUT_CHANNEL.appendLine("Took: " + timing.getTotalElapsedAsStr() + " to import base holotree.");
        } catch (err) {
            logError("Error while importing base zip into holotree.", err, "ERROR_IMPORT_BASE_ZIP_HOLOTREE");
        }
    }
}
