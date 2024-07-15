import { CancellationToken, Progress, ProgressLocation, window } from "vscode";
import { readFromFile } from "../files";
import { OUTPUT_CHANNEL, logError } from "../channel";
import { downloadOrGetActionServerLocation } from "../actionServer";
import { ActionResult } from "../protocols";
import { langServer } from "../extension";
import { showSelectOneStrQuickPick } from "../ask";

export interface ITokenInfo {
    provider?: string;
    scopes?: string[];
    expires_at?: string;
    access_token: string;
    metadata?: any;
}

export interface IProviderToTokenInfo {
    [key: string]: ITokenInfo;
}

export interface ISecretsInfo {
    "secrets": IProviderToTokenInfo;
}

export interface IRequiredLogin {
    scopes: string[];
}

export interface IRequiredLogins {
    [key: string]: IRequiredLogin; // Provider name -> IRequiredLogin
}

export const oauth2Logout = async () => {
    await window.withProgress(
        {
            location: ProgressLocation.Notification,
            title: "OAuth2 login required for OAuth2Secrets",
            cancellable: true,
        },
        async (
            progress: Progress<{ message?: string; increment?: number }>,
            token: CancellationToken
        ): Promise<void> => {
            progress.report({ message: "Getting action server", increment: 10 });

            const actionServerLocation = await downloadOrGetActionServerLocation();
            if (!actionServerLocation) {
                window.showErrorMessage("Unable to make OAuth2 logout (unable to get action server executable).");
                return;
            }
            try {
                progress.report({ message: "Getting OAuth2 login status", increment: 50 });
                const providerToStatus = await langServer.sendRequest<ActionResult<IProviderToTokenInfo>>(
                    "oauth2Status",
                    {
                        action_server_location: actionServerLocation,
                        provide_access_token: false,
                    },
                    token
                );
                if (!providerToStatus.success) {
                    if (!providerToStatus.success) {
                        throw new Error(providerToStatus.message);
                    }
                }

                const providers = Object.keys(providerToStatus.result);
                if (providers.length === 0) {
                    window.showInformationMessage(
                        "Unable to make OAuth2 logout because there is no login information saved."
                    );
                    return;
                } else {
                    const selected = await showSelectOneStrQuickPick(
                        providers,
                        "Select from which provider to logout",
                        "OAuth2 logout"
                    );
                    if (!selected) {
                        return; // user cancelled.
                    }
                    progress.report({ message: "Logging out...", increment: 20 });
                    const logoutResult = await langServer.sendRequest<ActionResult<any>>("oauth2Logout", {
                        action_server_location: actionServerLocation,
                        provider: selected,
                    }, token);
                    if (!logoutResult.success) {
                        window.showErrorMessage(`Error making OAuth2 logout. Details: ${logoutResult.message}`);
                        return;
                    } else {
                        window.showInformationMessage(`Finished logging out for: ${selected}`);
                        return;
                    }
                }
            } catch (error) {
                window.showErrorMessage(`Unable to make OAuth2 logout. Details: ${error.message}`);
                logError("Error making OAuth2 logout", error, "ERR_OAUTH2_LOGOUT");
                return;
            }
        }
    );
};

export const loginToAuth2WhereRequired = async (targetInput: string): Promise<ISecretsInfo> => {
    const contents: string = await readFromFile(targetInput);
    if (!contents) {
        return;
    }

    const parsed = JSON.parse(contents);
    const secrets = {};
    const request = parsed["vscode:request:oauth2"];
    if (request) {
        const requiredLogins: IRequiredLogins = {};
        const parameterNameToProvider: Map<string, string> = new Map();

        for (const [key, val] of Object.entries(request)) {
            const keysInEntry = Object.keys(val);
            if (keysInEntry.includes("type") && keysInEntry.includes("scopes") && keysInEntry.includes("provider")) {
                if (
                    val["type"] === "OAuth2Secret" &&
                    Array.isArray(val["scopes"]) &&
                    typeof val["provider"] === "string"
                ) {
                    // Ok, we need to login.
                    const provider = val["provider"];
                    let requiredLogin = requiredLogins[provider];
                    if (requiredLogin === undefined) {
                        requiredLogins[provider] = { scopes: val["scopes"] };
                    } else {
                        for (const scope of val["scopes"]) {
                            if (!requiredLogin.scopes.includes(scope)) {
                                requiredLogin.scopes.push(scope);
                            }
                        }
                    }
                    parameterNameToProvider.set(key, val["provider"]);
                    OUTPUT_CHANNEL.appendLine(`OAuth2 login required for parameter: ${key}: ${val["provider"]}`);
                }
            }
        }

        const providerToInfoFinal = new Map<String, ITokenInfo>();

        const nRequiredLogins = Object.keys(requiredLogins).length;
        if (nRequiredLogins > 0) {
            await window.withProgress(
                {
                    location: ProgressLocation.Notification,
                    title: "OAuth2 login required for OAuth2Secrets",
                    cancellable: true,
                },
                async (
                    progress: Progress<{ message?: string; increment?: number }>,
                    token: CancellationToken
                ): Promise<void> => {
                    const steps = nRequiredLogins + 1;

                    const actionServerLocation = await downloadOrGetActionServerLocation();
                    if (!actionServerLocation) {
                        throw new Error("Unable to get action server executable.");
                    }

                    const providerToStatus = await langServer.sendRequest<ActionResult<IProviderToTokenInfo>>(
                        "oauth2Status",
                        { action_server_location: actionServerLocation },
                        token
                    );
                    if (!providerToStatus.success) {
                        throw new Error(providerToStatus.message);
                    }

                    // Ok, gotten status, let's see if we have some valid info at this point
                    for (const provider of Object.keys(requiredLogins)) {
                        const status = providerToStatus.result[provider];
                        if (status) {
                            providerToInfoFinal.set(provider, status);
                        }
                    }

                    for (const [provider, requiredLogin] of Object.entries(requiredLogins)) {
                        if (providerToInfoFinal.has(provider)) {
                            continue;
                        }
                        const msg = `Waiting for login to: ${provider} (a separate browser window should be opened).`;
                        OUTPUT_CHANNEL.appendLine(msg);
                        progress.report({ message: msg, increment: 100 / steps });

                        const providerToTokenInfo = await langServer.sendRequest<ActionResult<ITokenInfo>>(
                            "oauth2Login",
                            {
                                action_server_location: actionServerLocation,
                                provider: provider,
                                scopes: requiredLogin.scopes,
                            },
                            token
                        );
                        if (!providerToTokenInfo.success) {
                            throw new Error(providerToTokenInfo.message);
                        }

                        if (token.isCancellationRequested) {
                            throw new Error("Cancelled.");
                        }
                        providerToInfoFinal.set(provider, providerToTokenInfo.result);
                    }
                }
            );
        }

        for (const [paramName, provider] of parameterNameToProvider.entries()) {
            const providerInfo = providerToInfoFinal.get(provider);
            if (!providerInfo) {
                throw new Error(
                    `Expected the information on the provider: ${provider} to be already collected at this point.`
                );
            }
            secrets[paramName] = providerInfo;
        }
    }

    return { "secrets": secrets };
};
