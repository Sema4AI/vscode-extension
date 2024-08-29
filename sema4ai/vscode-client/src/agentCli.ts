import { Tool, getToolVersion, downloadTool } from "./tools";

let globalLocation: string | undefined = undefined;

export const getAgentCliLocation = async (): Promise<string> => {
    if (globalLocation) {
        return globalLocation;
    }
    // The download will properly check if it's there (and if not it'll download it).
    globalLocation = await downloadAgentCli();
    return globalLocation;
};

export const downloadAgentCli = (): Thenable<string> => {
    return downloadTool(Tool.AgentCli);
};

export const getAgentCliVersion = (): Promise<string> => {
    return getToolVersion(Tool.AgentCli);
};
