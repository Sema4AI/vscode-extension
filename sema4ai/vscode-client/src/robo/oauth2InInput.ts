import { CancellationToken, Progress, ProgressLocation, commands, window } from "vscode";
import { readFromFile } from "../files";
import { SEMA4AI_OAUTH2_LOGIN_INTERNAL, SEMA4AI_OAUTH2_STATUS_INTERNAL } from "../robocorpCommands";
import { OUTPUT_CHANNEL } from "../channel";
import { downloadOrGetActionServerLocation } from "../actionServer";

export interface ITokenInfo {
    provider?: string;
    scopes?: string[];
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
    provider: string;
    scopes: string[];
}

export const loginToAuth2WhereRequired = async (targetInput: string): Promise<ISecretsInfo> => {
    const contents: string = await readFromFile(targetInput);
    if (!contents) {
        return;
    }

    const parsed = JSON.parse(contents);
    const secrets = {};
    const request = parsed["vscode:request:oauth2"];
    if (request) {
        const requiredLogins: IRequiredLogin[] = [];
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
                    requiredLogins.push({ "provider": key, "scopes": val["scopes"] });
                    parameterNameToProvider.set(key, val["provider"]);
                    OUTPUT_CHANNEL.appendLine(`OAuth2 login required for parameter: ${key}: ${val["provider"]}`);
                }
            }
        }

        if (requiredLogins.length > 0) {
            await window.withProgress(
                {
                    location: ProgressLocation.Notification,
                    title: "OAuth2 login required for OAuth2Secrets",
                    cancellable: false,
                },
                async (
                    progress: Progress<{ message?: string; increment?: number }>,
                    token: CancellationToken
                ): Promise<void> => {
                    const steps = requiredLogins.length + 1;
                    const actionServerLocation = await downloadOrGetActionServerLocation();
                    if (!actionServerLocation) {
                        return;
                    }
                
                    const providerToStatus: IProviderToTokenInfo = await commands.executeCommand(
                        SEMA4AI_OAUTH2_STATUS_INTERNAL, {action_server_location: actionServerLocation}
                    );

                    console.log(providerToStatus);


                    for (const requiredLogin of requiredLogins) {
                        const msg = `Waiting for login to: ${requiredLogin.provider}`;
                        OUTPUT_CHANNEL.appendLine(msg);
                        progress.report({ message: msg, increment: 100 / steps });

                        const providerToTokenInfo: IProviderToTokenInfo = await commands.executeCommand(
                            SEMA4AI_OAUTH2_LOGIN_INTERNAL,
                            requiredLogin
                        );
                        if (token.isCancellationRequested) {
                            return undefined;
                        }
                    }
                }
            );
        }
    }

    return { "secrets": secrets };
};
