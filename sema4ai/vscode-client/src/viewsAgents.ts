import * as vscode from "vscode";
import {
    TreeDataProvider,
    TreeItem,
    TreeItemCollapsibleState
} from "vscode";
import * as roboCommands from "./robocorpCommands";
import {
    ActionResult,
    LocalAgentPackageMetadataInfo,
} from "./protocols";
import { OUTPUT_CHANNEL } from "./channel";
import {
    AgentEntry,
    AgentEntryType
} from "./viewsCommon";

export class AgentPackagesTreeDataProvider implements TreeDataProvider<AgentEntry> {
    private _onDidChangeTreeData = new vscode.EventEmitter<AgentEntry | null>();
    public readonly onDidChangeTreeData: vscode.Event<AgentEntry | null> = this._onDidChangeTreeData.event;

    public fireRootChange() {
        this._onDidChangeTreeData.fire(null);
    }

    public getTreeItem(element: AgentEntry): TreeItem {
        const treeItem = new TreeItem(element.label, TreeItemCollapsibleState.Collapsed);
        if (element.type === AgentEntryType.Organization) {
            treeItem.collapsibleState = TreeItemCollapsibleState.None;
        }

        if (element.iconPath) {
            treeItem.iconPath = new vscode.ThemeIcon(element.iconPath);
        }

        if (element.tooltip) {
            treeItem.tooltip = element.tooltip;
        }

        /* We need to check for undefined specifically, as to not set CollapsibleState for not collapsible items. */
        if (element.collapsed !== undefined) {
            treeItem.collapsibleState = element.collapsed
                ? vscode.TreeItemCollapsibleState.Collapsed
                : vscode.TreeItemCollapsibleState.Expanded;
        }

        return treeItem;
    }

    public async getChildren(parent?: AgentEntry): Promise<AgentEntry[]> {
        const children = await this.computeChildren(parent);

        if (!children?.length) {

        }

        return children;
    }

    private async computeChildren(parent?: AgentEntry): Promise<AgentEntry[]> {
        /* If there is a parent element, calculate appropriate children. */
        if (parent) {
            if (parent.type === AgentEntryType.AgentPackage) {
                const agentActionOrganizations = parent.packageInfo?.organizations;

                return agentActionOrganizations.map(organization => ({
                    type: AgentEntryType.Organization,
                    label: organization.name,
                    uri: vscode.Uri.file(`${parent.packageInfo?.directory}/${organization.name}`),
                    iconPath: "circle"
                }));
            }
            return [];
        }

        /* Otherwise, get root elements. */
        return await this.getRootElements();
    }

    private async getRootElements(): Promise<AgentEntry[]> {
        const listAgentsResult: ActionResult<LocalAgentPackageMetadataInfo[]> = await vscode.commands.executeCommand(
            roboCommands.SEMA4AI_LOCAL_LIST_AGENT_PACKAGES_INTERNAL,
        );

        if (!listAgentsResult.success) {
            OUTPUT_CHANNEL.appendLine(listAgentsResult.message);
            return [];
        }

        const agentPackages = listAgentsResult.result;

        if (!agentPackages?.length) {
            return [];
        }

        const collapsed = !!agentPackages?.length;

        return agentPackages.map(agentPackage => ({
            type: AgentEntryType.AgentPackage,
            label: agentPackage.name,
            uri: vscode.Uri.file(agentPackage.filePath),
            iconPath: "package",
            packageInfo: agentPackage,
            collapsed,
        }));
    }
}
