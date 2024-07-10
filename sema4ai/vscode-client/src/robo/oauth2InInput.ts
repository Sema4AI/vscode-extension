import { readFromFile } from "../files";

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

export const loginToAuth2WhereRequired = async (targetInput: string): Promise<ISecretsInfo> => {
    const contents: string = await readFromFile(targetInput);
    if (!contents) {
        return;
    }

    const parsed = JSON.parse(contents);
    const secrets = {};
    const request = parsed["vscode:request:oauth2"];
    if(request){
        for (const [key, val] of Object.entries(request)) {
            const keysInEntry = Object.keys(val);
            if (keysInEntry.includes("type") && keysInEntry.includes("scopes") && keysInEntry.includes("provider")) {
                if (val["type"] === "OAuth2Secret" && Array.isArray(val["scopes"]) && typeof val["provider"] === "string") {
                    // Ok, we need to login.
                    secrets[key] = { "access_token": "foobar" };
                }
            }
        }
    }

    return { "secrets": secrets };
};
