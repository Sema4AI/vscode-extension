export interface LocalRobotMetadataInfo {
    name: string;
    directory: string;
    filePath: string;
    yamlContents: object;
}

export interface IVaultInfo {
    workspaceId: string;
    organizationName: string;
    workspaceName: string;
}

export interface WorkspaceInfo {
    organizationName: string;
    workspaceName: string;
    workspaceId: string;
    packages: PackageInfo[];
}

export interface PackageInfo {
    workspaceId: string;
    workspaceName: string;
    id: string;
    name: string;
    sortKey: string;
}

export interface IAccountInfo {
    fullname: string;
    email: string;
}

export interface Position {
    line: number; // Use number instead of int for consistency
    character: number;
}

export interface Range {
    start: Position;
    end: Position;
}

export interface IActionInfo {
    uri: string;
    name: string;
    range: Range;
}

export interface ActionResult<T> {
    success: boolean;
    message: string;
    result: T;
}

export interface InterpreterInfo {
    pythonExe: string;
    environ?: { [key: string]: string };
    additionalPythonpathEntries: string[];
}

export interface ListWorkspacesActionResult {
    success: boolean;
    message: string;
    result: WorkspaceInfo[];
}

export interface RobotTemplate {
    name: string;
    description: string;
}

export interface ActionTemplate {
    name: string;
    description: string;
}

export interface WorkItem {
    name: string;
    json_path: string;
}

export interface WorkItemsInfo {
    robot_yaml: string; // Full path to the robot which has these work item info

    // Full path to the place where input work items are located
    input_folder_path?: string;

    // Full path to the place where output work items are located
    output_folder_path?: string;

    input_work_items: WorkItem[];
    output_work_items: WorkItem[];

    new_output_workitem_path: string;
}

export interface ActionResultWorkItems {
    success: boolean;
    message: string;
    result?: WorkItemsInfo;
}

export interface LibraryVersionInfoDict {
    success: boolean;

    // if success == False, this can be some message to show to the user
    message?: string;
}

export interface File {
    content: string;
    filename: string;
    encoding?: string;
}

export enum ValidationStatus {
    ValidationSuccess = "ValidationSuccess",
    ValidationError = "ValidationError",
}

export interface ValidationSuccess<T> {
    status: ValidationStatus.ValidationSuccess;
    payload: T;
}

export interface ValidationError {
    status: ValidationStatus.ValidationError;
    messages: string[];
    stack?: string;
}

export type ValidationResult<T> = ValidationSuccess<T> | ValidationError;

export interface Options {
    objectImplFile?: string;
    projectFolderPath?: string;
}

export interface Progress {
    (amount: number, message: string): void;
}

export interface ActionServerVerifyLoginOutput {
    logged_in: boolean;
    hostname: string;
}

export interface ActionServerOrganization {
    id: string;
    name: string;
}

export interface ActionServerListOrganizationsOutput extends Array<ActionServerOrganization> {}

export interface ActionServerPackageBuildOutput {
    package_path: string;
}

export interface ActionServerPackageUploadStatusOutput {
    id: string;
    name: string;
    url: string;
    version?: string;
    changes?: string;
    status: "unknown" | "pending" | "validating" | "failed" | "completed" | "published";
    error?: {
        code: string;
        message: string;
    };
}
