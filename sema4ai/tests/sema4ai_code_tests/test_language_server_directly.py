import pytest
from sema4ai_code_tests.fixtures import RccPatch


def test_cloud_list_workspaces_cache_invalidate(
    rcc_patch: RccPatch,
    ws_root_path: str,
    rcc_location: str,
    ci_endpoint: str,
    rcc_config_location: str,
):
    from sema4ai_ls_core.constants import NULL

    from sema4ai_code.rcc import AccountInfo
    from sema4ai_code.robocorp_language_server import RobocorpLanguageServer

    rcc_patch.apply()

    read_stream = NULL
    write_stream = NULL
    language_server = RobocorpLanguageServer(read_stream, write_stream)
    initialization_options = {"do-not-track": True}

    language_server.m_initialize(
        rootPath=ws_root_path, initialization_options=initialization_options
    )
    language_server.m_workspace__did_change_configuration(
        {
            "sema4ai": {
                "rcc": {
                    "location": rcc_location,
                    "endpoint": ci_endpoint,
                    "config_location": rcc_config_location,
                }
            }
        }
    )

    rcc = language_server._rcc
    rcc._last_verified_account_info = AccountInfo("default account", "123", "", "")

    assert language_server._cloud_list_workspaces({"refresh": False})(monitor=NULL)[
        "success"
    ]
    rcc_patch.disallow_calls()
    assert language_server._cloud_list_workspaces({"refresh": False})(monitor=NULL)[
        "success"
    ]

    rcc._last_verified_account_info = AccountInfo("another account", "123", "", "")

    # As account changed, the data should be fetched (as we can't due to the patching
    # the error is expected).
    result = language_server._cloud_list_workspaces({"refresh": False})(monitor=NULL)
    assert not result["success"]

    assert "This should not be called at this time (data should be cached)." in str(
        result["message"]
    )
