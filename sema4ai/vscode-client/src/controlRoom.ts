/**
 * Choosing which Control Room to link to when no rcc profile is active.
 *
 * Every Control Room (Sema4.ai and Robocorp) publishes the rcc profile that points
 * rcc at it in `<origin>/.well-known/rcc-profile.yaml`. Linking to a Control Room
 * other than rcc's default (Robocorp) downloads that profile, imports it and makes
 * it the active rcc profile, so the credential, publishing, workspaces, Vault and
 * work items all go to that Control Room. Robocorp Control Room is rcc's default,
 * so choosing it changes nothing.
 */
import * as fs from "fs";
import * as path from "path";
import { commands, QuickPickItem, Uri, window } from "vscode";
import { GLOBAL_STATE } from "./extension";
import { logError } from "./channel";
import { ActionResult } from "./protocols";
import { getEndpointUrl } from "./rcc";
import {
    SEMA4AI_PROFILE_DOWNLOAD_INTERNAL,
    SEMA4AI_PROFILE_IMPORT_INTERNAL,
    SEMA4AI_PROFILE_LIST_INTERNAL,
    SEMA4AI_PROFILE_SWITCH_INTERNAL,
} from "./robocorpCommands";
import { getRccEndpoint } from "./robocorpSettings";

export interface IKnownControlRoom {
    label: string;
    origin: string;
    // Robocorp Control Room is what rcc uses without a profile: no profile is needed.
    usesRccDefaults?: boolean;
}

// The first entry is the default. Adding a Control Room (e.g. a region) is one entry here.
export const KNOWN_CONTROL_ROOMS: IKnownControlRoom[] = [
    { "label": "Sema4.ai (US3)", "origin": "https://us3.sema4.ai" },
    { "label": "Robocorp Control Room", "origin": "https://cloud.robocorp.com", "usesRccDefaults": true },
];

// The rcc profile name rcc reports when no profile is active.
const RCC_NO_PROFILE = "default";
const RCC_SWITCH_TO_DEFAULTS = "<remove-current-back-to-defaults>";
const ROBOCORP_CONTROL_ROOM_LABEL = "Robocorp Control Room";

// The rcc profile the extension activated when linking (so unlinking can switch back).
const STATE_KEY_ACTIVATED_PROFILE = "sema4ai.controlRoom.activatedProfile";

interface IProfileList {
    current: string;
    profiles: { [name: string]: string };
}

interface IProfileDownloadResult {
    profileUri: string;
}

interface IControlRoomPickItem extends QuickPickItem {
    controlRoom?: IKnownControlRoom;
}

async function getProfileList(): Promise<IProfileList | undefined> {
    const result: ActionResult<IProfileList> = await commands.executeCommand(SEMA4AI_PROFILE_LIST_INTERNAL);
    if (!result?.success || !result.result) {
        return undefined;
    }
    return result.result;
}

function isNoProfile(current: string | undefined): boolean {
    return !current || current === RCC_NO_PROFILE;
}

/**
 * The name of the Control Room rcc points to, to show next to the linked account.
 */
export function getLinkedControlRoomLabel(profileList?: IProfileList): string | undefined {
    if (getRccEndpoint()) {
        return undefined; // Custom setup: the endpoint setting decides.
    }
    if (!profileList) {
        return undefined;
    }
    const current = profileList.current;
    if (isNoProfile(current)) {
        return ROBOCORP_CONTROL_ROOM_LABEL;
    }
    const description = profileList.profiles?.[current];
    return description ? description : current;
}

/**
 * Only ask which Control Room to link to when rcc is on its defaults: an active
 * profile (or the `sema4ai.rcc.endpoint` setting) already says which Control Room to use.
 */
async function shouldAskForControlRoom(): Promise<boolean> {
    if (getRccEndpoint()) {
        return false;
    }
    const profileList = await getProfileList();
    if (!profileList) {
        return false; // Unable to tell: keep the previous behavior.
    }
    return isNoProfile(profileList.current);
}

function normalizeOrigin(value: string): string | undefined {
    value = value.trim();
    if (!value) {
        return undefined;
    }
    if (!value.includes("://")) {
        value = "https://" + value;
    }
    try {
        const url = new URL(value);
        if ((url.protocol !== "https:" && url.protocol !== "http:") || !url.hostname) {
            return undefined;
        }
        return url.origin;
    } catch (err) {
        return undefined;
    }
}

async function askForOtherControlRoomOrigin(): Promise<string | undefined> {
    const value = await window.showInputBox({
        "title": "Link to another Control Room",
        "prompt": "Enter the address of the Control Room, for example https://us3.sema4.ai",
        "placeHolder": "https://us3.sema4.ai",
        "ignoreFocusOut": true,
        "validateInput": (text: string) => {
            if (!text.trim()) {
                return "Enter the Control Room address.";
            }
            return normalizeOrigin(text) ? undefined : "Enter an address such as https://us3.sema4.ai";
        },
    });
    if (value === undefined) {
        return undefined;
    }
    return normalizeOrigin(value);
}

/**
 * Asks which Control Room to link to (when no rcc profile is active) and returns the
 * URL of its UI to create the credential in (as https://us3.sema4.ai/), or undefined
 * if the user cancelled.
 */
export async function chooseControlRoomUi(): Promise<string | undefined> {
    if (!(await shouldAskForControlRoom())) {
        return await getEndpointUrl("cloud-ui");
    }

    while (true) {
        const items: IControlRoomPickItem[] = KNOWN_CONTROL_ROOMS.map((controlRoom) => ({
            "label": controlRoom.label,
            "description": Uri.parse(controlRoom.origin).authority,
            "controlRoom": controlRoom,
        }));
        items.push({
            "label": "Other Control Room...",
            "description": "Enter the address of another Control Room",
        });

        // The first item is active (preselected) by default.
        const selected: IControlRoomPickItem | undefined = await window.showQuickPick(items, {
            "title": "Link to Control Room",
            "placeHolder": "Which Control Room do you want to link to?",
            "ignoreFocusOut": true,
        });
        if (!selected) {
            return undefined;
        }

        let origin: string;
        let label: string;
        if (selected.controlRoom) {
            if (selected.controlRoom.usesRccDefaults) {
                return await getEndpointUrl("cloud-ui");
            }
            origin = selected.controlRoom.origin;
            label = selected.controlRoom.label;
        } else {
            origin = await askForOtherControlRoomOrigin();
            if (origin === undefined) {
                continue; // Back to the list.
            }
            label = Uri.parse(origin).authority;
        }

        const result = await activateControlRoomProfile(origin, label);
        if (result === "cancelled") {
            return undefined;
        }
        if (result === "failed") {
            continue; // The error was shown: let the user pick again.
        }
        return result;
    }
}

/**
 * Asks the user to confirm, then downloads the Control Room's rcc profile and activates it.
 *
 * Returns the Control Room UI URL, "cancelled" or "failed".
 */
async function activateControlRoomProfile(origin: string, label: string): Promise<string | "cancelled" | "failed"> {
    const host = Uri.parse(origin).authority;

    // Activating an rcc profile affects every tool that uses rcc, not just this extension.
    const ACTIVATE = "Activate profile and continue";
    const answer = await window.showWarningMessage(
        `Link to ${label}?`,
        {
            "modal": true,
            "detail":
                `To link to ${label}, the rcc profile published by ${host} is imported and made the active rcc profile.\n\n` +
                `The active rcc profile is shared by every tool on this computer that uses rcc (such as other editors, ` +
                `Assistants and the rcc command line). They will all use ${label} for Control Room, ` +
                `not only this extension.\n\n` +
                `To go back, unlink from Control Room or run "Sema4.ai: Switch Profile".`,
        },
        ACTIVATE
    );
    if (answer !== ACTIVATE) {
        return "cancelled";
    }

    const downloadResult: ActionResult<IProfileDownloadResult> = await commands.executeCommand(
        SEMA4AI_PROFILE_DOWNLOAD_INTERNAL,
        { "origin": origin }
    );
    if (!downloadResult?.success || !downloadResult.result) {
        await window.showErrorMessage(downloadResult?.message || `Unable to get the rcc profile from ${host}.`);
        return "failed";
    }

    // rcc validates the profile when importing it.
    const profileUri = downloadResult.result.profileUri;
    const importResult: ActionResult<{ name: string; description: string }> = await commands.executeCommand(
        SEMA4AI_PROFILE_IMPORT_INTERNAL,
        { "profileUri": profileUri }
    );
    // The download is only needed for the import.
    fs.rm(path.dirname(Uri.parse(profileUri).fsPath), { "recursive": true, "force": true }, () => {});

    if (!importResult?.success || !importResult.result?.name) {
        await window.showErrorMessage(importResult?.message || `Unable to import the rcc profile from ${host}.`);
        return "failed";
    }
    const profileName = importResult.result.name;

    const switchResult: ActionResult<any> = await commands.executeCommand(SEMA4AI_PROFILE_SWITCH_INTERNAL, {
        "profileName": profileName,
    });
    if (!switchResult?.success) {
        await window.showErrorMessage(switchResult?.message || `Unable to switch to the "${profileName}" profile.`);
        return "failed";
    }

    await GLOBAL_STATE?.update(STATE_KEY_ACTIVATED_PROFILE, profileName);

    // The active profile now points rcc at the chosen Control Room.
    return await getEndpointUrl("cloud-ui");
}

export async function switchBackToRccDefaults(profileName: string): Promise<void> {
    try {
        const result: ActionResult<any> = await commands.executeCommand(SEMA4AI_PROFILE_SWITCH_INTERNAL, {
            "profileName": RCC_SWITCH_TO_DEFAULTS,
        });
        if (!result?.success) {
            window.showWarningMessage(
                `Unable to switch rcc back from the "${profileName}" profile: ${result?.message}. ` +
                    `Run "Sema4.ai: Switch Profile" to change it.`
            );
            return;
        }
        await GLOBAL_STATE?.update(STATE_KEY_ACTIVATED_PROFILE, undefined);
    } catch (err) {
        logError(`Error switching rcc back from the "${profileName}" profile.`, err, "CONTROL_ROOM_SWITCH_BACK");
    }
}

/**
 * The rcc profile the extension activated to link to a Control Room, if it's still
 * the active profile (so that unlinking should switch back to rcc's defaults).
 */
export async function getProfileToSwitchBackOnUnlink(): Promise<string | undefined> {
    const activated: string | undefined = GLOBAL_STATE?.get(STATE_KEY_ACTIVATED_PROFILE);
    if (!activated) {
        return undefined;
    }
    const profileList = await getProfileList();
    if (!profileList || profileList.current !== activated) {
        // The user switched profiles in the meantime: leave their choice alone.
        await GLOBAL_STATE?.update(STATE_KEY_ACTIVATED_PROFILE, undefined);
        return undefined;
    }
    return activated;
}
