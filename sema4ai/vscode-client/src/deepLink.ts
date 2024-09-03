import { btoa } from "buffer";

export const DL_APP_PROTOCOL_URI = "sema4.ai.studio";
export const DL_APP_PROTOCOL_URI_FULL = `${DL_APP_PROTOCOL_URI}://`;

export const DL_APP_CONTROLLER_VSCODE = "vscode.sema4.ai";
export const DL_APP_BASE_URI_CONTROLLER_VSCODE = `${DL_APP_PROTOCOL_URI_FULL}${DL_APP_CONTROLLER_VSCODE}/`;

export const DL_API_ID_IMPORT_ACTION_PACKAGE_FROM_FOLDER = "import-package/folder-path/";
export const DL_API_ID_IMPORT_ACTION_PACKAGE_FROM_ZIP = "import-package/zip-path/";
export const DL_API_ID_IMPORT_AGENT_PACKAGE_FROM_ZIP = "import-agent/zip-path/";

export const getSema4AIStudioURLForFolderPath = (path: string): string => {
    const url = `${DL_APP_BASE_URI_CONTROLLER_VSCODE}${DL_API_ID_IMPORT_ACTION_PACKAGE_FROM_FOLDER}${btoa(path)}`;
    return url;
};

export const getSema4AIStudioURLForAgentZipPath = (path: string) => {
    return `${DL_APP_BASE_URI_CONTROLLER_VSCODE}${DL_API_ID_IMPORT_AGENT_PACKAGE_FROM_ZIP}${btoa(path)}`;
};
