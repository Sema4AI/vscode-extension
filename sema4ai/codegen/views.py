import enum
from typing import Optional, Union


class TreeView:
    def __init__(self, id, name, contextual_title, menus, add_to_package_json=True):
        self.id = id
        self.name = name
        self.contextual_title = contextual_title
        self.menus = menus
        self.add_to_package_json = add_to_package_json


class TreeViewContainer:
    def __init__(self, id, title, icon, tree_views):
        self.id = id
        self.title = title
        self.icon = icon
        self.tree_views = tree_views


class MenuGroup(enum.Enum):
    # https://code.visualstudio.com/api/references/contribution-points#contributes.menus
    NAVIGATION = "navigation"
    INLINE = "inline"


class Menu:
    def __init__(
        self,
        command_id,
        group: Optional[Union[MenuGroup, str]] = None,
        when: Optional[str] = None,
    ):
        self.command_id = command_id
        self.group = group
        self.when = when


TREE_VIEW_CONTAINERS = [
    TreeViewContainer(
        id="sem4ai-packages",
        title="Sema4.ai",
        icon="images/sema4ai-outline.svg",
        tree_views=[
            TreeView(
                id="sema4ai-task-packages-tree",
                name="Task/Action Packages",
                contextual_title="Task/Action Packages",
                menus={
                    # See: https://code.visualstudio.com/api/references/contribution-points#contributes.menus
                    # for targets
                    "view/title": [
                        Menu("sema4ai.refreshRobotsView", MenuGroup.NAVIGATION),
                        Menu("sema4ai.createTaskOrActionPackage", MenuGroup.NAVIGATION),
                    ],
                    "view/item/context": [
                        # Task run as context menus
                        Menu(
                            "sema4ai.robotsViewTaskRun",
                            "inline@1",
                            "viewItem == taskItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewTaskDebug",
                            "inline@2",
                            "viewItem == taskItem",
                        ),
                        # Action run as context menus
                        Menu(
                            "sema4ai.robotsViewActionOpen",
                            "inline@1",
                            "viewItem == actionItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewActionEditInput",
                            "inline@2",
                            "viewItem == actionItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewActionRun",
                            "inline@3",
                            "viewItem == actionItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewActionDebug",
                            "inline@4",
                            "viewItem == actionItem",
                        ),
                        # Inline in actions
                        Menu(
                            "sema4ai.openRobotTreeSelection",
                            MenuGroup.INLINE,
                            "viewItem == actionsInRobotItem",
                        ),
                        Menu(
                            "sema4ai.openRobotCondaTreeSelection",
                            MenuGroup.INLINE,
                            "viewItem == actionsInRobotItem",
                        ),
                        Menu(
                            "sema4ai.rccTerminalCreateRobotTreeSelection",
                            MenuGroup.INLINE,
                            "viewItem == actionsInRobotItem",
                        ),
                        Menu(
                            "sema4ai.cloudUploadRobotTreeSelection",
                            MenuGroup.INLINE,
                            "viewItem == actionsInRobotItem",
                        ),
                        Menu(
                            "sema4ai.openFlowExplorerTreeSelection",
                            MenuGroup.INLINE,
                            "viewItem == actionsInRobotItem",
                        ),
                        # Tasks: Needs right click (duplicating above + new actions)
                        Menu(
                            "sema4ai.robotsViewTaskRun",
                            MenuGroup.NAVIGATION,
                            "viewItem == taskItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewTaskDebug",
                            MenuGroup.NAVIGATION,
                            "viewItem == taskItem",
                        ),
                        # Actions: Needs right click (duplicating above + new actions)
                        Menu(
                            "sema4ai.robotsViewActionRun",
                            MenuGroup.NAVIGATION,
                            "viewItem == actionItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewActionDebug",
                            MenuGroup.NAVIGATION,
                            "viewItem == actionItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewActionEditInput",
                            MenuGroup.NAVIGATION,
                            "viewItem == actionItem",
                        ),
                        Menu(
                            "sema4ai.robotsViewActionOpen",
                            MenuGroup.NAVIGATION,
                            "viewItem == actionItem",
                        ),
                        # New action: reveal in explorer.
                        Menu(
                            "sema4ai.revealRobotInExplorer",
                            MenuGroup.NAVIGATION,
                            when="viewItem == robotItem",
                        ),
                        Menu(
                            "sema4ai.openRobotTreeSelection",
                            MenuGroup.NAVIGATION,
                            when="viewItem == robotItem",
                        ),
                        Menu(
                            "sema4ai.rccTerminalCreateRobotTreeSelection",
                            MenuGroup.NAVIGATION,
                            when="viewItem == robotItem",
                        ),
                        Menu(
                            "sema4ai.cloudUploadRobotTreeSelection",
                            MenuGroup.NAVIGATION,
                            when="viewItem == robotItem",
                        ),
                    ],
                },
            ),
            TreeView(
                id="sema4ai-package-content-tree",
                name="Package Content",
                contextual_title="Package Content",
                menus={
                    "view/title": [
                        Menu(
                            "sema4ai.newFileInRobotContentView",
                            MenuGroup.NAVIGATION,
                            when="sema4ai:single-robot-selected && viewItem == directoryItem",
                        ),
                        Menu(
                            "sema4ai.newFolderInRobotContentView",
                            MenuGroup.NAVIGATION,
                            when="sema4ai:single-robot-selected && viewItem == directoryItem",
                        ),
                        Menu("sema4ai.refreshRobotContentView", MenuGroup.NAVIGATION),
                    ],
                    "view/item/context": [
                        Menu(
                            "sema4ai.newFileInRobotContentView",
                            "0_new",
                            when="sema4ai:single-robot-selected && viewItem == directoryItem",
                        ),
                        Menu(
                            "sema4ai.newFolderInRobotContentView",
                            "0_new",
                            when="sema4ai:single-robot-selected && viewItem == directoryItem",
                        ),
                        Menu(
                            "sema4ai.openExternally",
                            "1_open",
                            when="sema4ai:single-robot-selected && viewItem == fileItem",
                        ),
                        Menu(
                            "sema4ai.openInVSCode",
                            "1_open",
                            when="sema4ai:single-robot-selected && viewItem == fileItem",
                        ),
                        Menu(
                            "sema4ai.revealInExplorer",
                            "1_open",
                            when="sema4ai:single-robot-selected",
                        ),
                        Menu(
                            "sema4ai.renameResourceInRobotContentView",
                            "2_change",
                            when="sema4ai:single-robot-selected",
                        ),
                        Menu(
                            "sema4ai.deleteResourceInRobotContentView",
                            "2_change",
                            when="sema4ai:single-robot-selected",
                        ),
                    ],
                },
            ),
            TreeView(
                id="sema4ai-package-resources-tree",
                name="Package Resources",
                contextual_title="Package Resources",
                menus={
                    "view/item/context": [
                        # Locators (root)
                        Menu(
                            "sema4ai.newRobocorpInspectorBrowser",
                            MenuGroup.INLINE,
                            "sema4ai:single-robot-selected && viewItem == newBrowserLocator",
                        ),
                        Menu(
                            "sema4ai.newRobocorpInspectorWindows",
                            MenuGroup.INLINE,
                            "sema4ai:single-robot-selected && viewItem == newWindowsLocator",
                        ),
                        Menu(
                            "sema4ai.newRobocorpInspectorImage",
                            MenuGroup.INLINE,
                            "sema4ai:single-robot-selected && viewItem == newImageLocator",
                        ),
                        Menu(
                            "sema4ai.newRobocorpInspectorJava",
                            MenuGroup.INLINE,
                            "sema4ai:single-robot-selected && viewItem == newJavaLocator",
                        ),
                        # Locators (root)
                        Menu(
                            "sema4ai.openLocatorsJson",
                            MenuGroup.INLINE,
                            "viewItem == locatorsRoot",
                        ),
                        # Locators (entries)
                        Menu(
                            "sema4ai.editRobocorpInspectorLocator",
                            MenuGroup.INLINE,
                            when="sema4ai:single-robot-selected && viewItem == locatorEntry",
                        ),
                        Menu(
                            "sema4ai.copyLocatorToClipboard.internal",
                            MenuGroup.INLINE,
                            when="sema4ai:single-robot-selected && viewItem == locatorEntry",
                        ),
                        Menu(
                            "sema4ai.removeLocatorFromJson",
                            MenuGroup.INLINE,
                            when="sema4ai:single-robot-selected && viewItem == locatorEntry",
                        ),
                        # Work items (root)
                        Menu(
                            "sema4ai.helpWorkItems",
                            MenuGroup.INLINE,
                            when="sema4ai:single-robot-selected && viewItem == workItemsRoot",
                        ),
                        # Work items (new)
                        Menu(
                            "sema4ai.newWorkItemInWorkItemsView",
                            MenuGroup.INLINE,
                            when="sema4ai:single-robot-selected && viewItem == inputWorkItemDir",
                        ),
                        # Work items (entries)
                        Menu(
                            "sema4ai.deleteWorkItemInWorkItemsView",
                            MenuGroup.INLINE,
                            when="viewItem == outputWorkItem || viewItem == inputWorkItem",
                        ),
                        Menu(
                            "sema4ai.convertOutputWorkItemToInput",
                            MenuGroup.INLINE,
                            when="viewItem == outputWorkItem",
                        ),
                    ]
                },
            ),
            TreeView(
                id="sema4ai-cloud-tree",
                name="Control Room",
                contextual_title="Sema4.ai",
                menus={
                    "view/item/context": [
                        Menu(
                            "sema4ai.cloudLogin",
                            MenuGroup.INLINE,
                            when="viewItem == cloudLoginItem",
                        ),
                        Menu(
                            "sema4ai.cloudLogout",
                            MenuGroup.INLINE,
                            when="viewItem == cloudLogoutItem",
                        ),
                        Menu(
                            "sema4ai.openCloudHome",
                            MenuGroup.INLINE,
                            when="viewItem == cloudLogoutItem",
                        ),
                        Menu(
                            "sema4ai.connectWorkspace",
                            MenuGroup.INLINE,
                            when="viewItem == workspaceDisconnected",
                        ),
                        Menu(
                            "sema4ai.disconnectWorkspace",
                            MenuGroup.INLINE,
                            when="viewItem == workspaceConnected",
                        ),
                        Menu(
                            "sema4ai.profileImport",
                            MenuGroup.INLINE,
                            when="viewItem == profileItem",
                        ),
                        Menu(
                            "sema4ai.profileSwitch",
                            MenuGroup.INLINE,
                            when="viewItem == profileItem",
                        ),
                    ]
                },
            ),
        ],
    )
]


def get_views_containers():
    activity_bar_contents = [
        {
            "id": tree_view_container.id,
            "title": tree_view_container.title,
            "icon": tree_view_container.icon,
        }
        for tree_view_container in TREE_VIEW_CONTAINERS
    ]
    return {
        "activitybar": activity_bar_contents,
        "panel": [
            {
                "id": "sema4ai-python-view-output",
                "title": "Task/Action Output",
                "icon": "$(output)",
            },
        ],
    }


def get_tree_views_for_package_json():
    ret = {}

    for tree_view_container in TREE_VIEW_CONTAINERS:
        ret[tree_view_container.id] = [
            {"id": tree.id, "name": tree.name, "contextualTitle": tree.contextual_title}
            for tree in tree_view_container.tree_views
            if tree.add_to_package_json
        ]

    ret["sema4ai-python-view-output"] = [
        {
            "type": "webview",
            "id": "sema4ai.python.view.output",
            "name": "Task/Action Output",
            "contextualTitle": "Task/Action Output",
        }
    ]

    return ret


def get_activation_events_for_json():
    activation_events = []

    for tree_view_container in TREE_VIEW_CONTAINERS:
        for tree_viewer in tree_view_container.tree_views:
            if not tree_viewer.add_to_package_json:
                continue
            activation_events.append("onView:" + tree_viewer.id)

    return activation_events


def get_menus():
    menus = {}

    for tree_view_container in TREE_VIEW_CONTAINERS:
        for tree_viewer in tree_view_container.tree_views:
            if not tree_viewer.add_to_package_json:
                continue
            menu: Menu
            for menu_id, menu_lst in tree_viewer.menus.items():
                for menu in menu_lst:
                    when = f"view == {tree_viewer.id}"
                    if menu.when:
                        when += f" && {menu.when}"
                    item = {"command": menu.command_id, "when": when}
                    if menu.group:
                        if isinstance(menu.group, str):
                            item["group"] = menu.group
                        else:
                            item["group"] = menu.group.value
                    menus.setdefault(menu_id, []).append(item)

    return menus
