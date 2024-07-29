import {
    TreeDataProvider,
    TreeItem,
    TreeItemCollapsibleState
} from "vscode";

export enum AgentEntryType {
    AgentPackage
}

export interface AgentEntry {
    type: AgentEntryType;
    label: string;
}

export class AgentPackagesTreeDataProvider implements TreeDataProvider<AgentEntry> {
    public getTreeItem(element: AgentEntry): TreeItem {
        const treeItem = new TreeItem(element.label, TreeItemCollapsibleState.Collapsed);
        if (element.type === AgentEntryType.AgentPackage) {

        }

        return treeItem;
    }

    public async getChildren(element?: AgentEntry): Promise<AgentEntry[]> {
        if (!element) {
            return [
                {
                    type: AgentEntryType.AgentPackage,
                    label: "Test package"
                }
            ];
        }

        return [];
    }

    private async computeChildren(element?: AgentEntry): Promise<AgentEntry[]> {
        return [];
    }
}
