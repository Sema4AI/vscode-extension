import { readFromFile } from "../files";

export const loginToAuth2WhereRequired = async (targetInput: string) => {
    const contents: string = await readFromFile(targetInput);
    if (!contents) {
        return;
    }

    const parsed = JSON.parse(contents);
    for (const [key, val] of Object.entries(parsed)) {
        const keysInEntry = Object.keys(val);
        if (keysInEntry.includes("type") && keysInEntry.includes("scopes") && keysInEntry.includes("provider")) {
            if (val["type"] === "OAuth2Secret" && Array.isArray(val["scopes"]) && typeof val["provider"] === "string") {
                // Ok, we need to login 
            }
        }
    }
};
