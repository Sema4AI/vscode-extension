_callback = None


def set_get_sema4ai_oauth2_config_callback(callback):
    global _callback
    _callback = callback


def get_sema4ai_provided_oauth2_config() -> str:
    assert _callback is not None, "Callback to get sema4ai oauth2 config not set!"
    return _callback()
