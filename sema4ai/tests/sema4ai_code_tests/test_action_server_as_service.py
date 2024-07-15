import json


def manual_test_action_server_as_service(action_server_location: str, tmpdir) -> None:
    from sema4ai_code.action_server import ActionServerAsService

    port = 8080  # Needs to match the port in the redirectUri.
    cwd = tmpdir / "cwd"
    cwd.mkdir()
    action_server = ActionServerAsService(
        action_server_location,
        port=port,
        cwd=str(cwd),
        datadir=str(tmpdir / "datadir"),
        use_https=False,
        ssl_self_signed=False,
        ssl_keyfile="",
        ssl_certfile="",
    )

    try:
        action_server.start_for_oauth2()
        # Higher timeout on 1st request
        assert action_server.get_config(timeout=30) == {
            "expose_url": False,
            "auth_enabled": False,
        }

        reference_id = action_server.create_reference_id()
        future = action_server.oauth2_login(
            provider="google",
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            reference_id=reference_id,
        )

        result = future.result(60 * 5)
        body = result["body"]
        assert body
        loaded = json.loads(body)
        assert loaded["provider"]
        assert loaded["access_token"]
        assert isinstance(json.loads(loaded["scopes"]), list)

    finally:
        action_server.stop()
