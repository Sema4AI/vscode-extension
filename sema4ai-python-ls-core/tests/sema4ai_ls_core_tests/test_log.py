import os


def test_log(tmpdir):
    from sema4ai_ls_core.core_log import get_logger, configure_logger
    from sema4ai_ls_core.unittest_tools.fixtures import wait_for_test_condition
    import io

    somedir = str(tmpdir.join("somedir"))
    configure_logger("test", 2, os.path.join(somedir, "foo.log"))

    log = get_logger("my_logger")
    log.info("something\nfoo\nbar")

    try:
        raise AssertionError("someerror")
    except:
        log.exception("rara: %s - %s", "str1", "str2")

    def get_log_files():
        log_files = [
            x for x in os.listdir(somedir) if x.startswith("foo") and x.endswith(".log")
        ]
        return log_files if log_files else None

    wait_for_test_condition(
        get_log_files, msg=lambda: f"Found: {get_log_files()} in {somedir}"
    )
    log_files = get_log_files()

    with open(os.path.join(somedir, log_files[0])) as stream:
        contents = stream.read()
        assert "someerror" in contents
        assert "something" in contents
        assert "rara" in contents
        assert "rara: str1 - str2" in contents

    log_file = io.StringIO()
    with configure_logger("", 2, log_file):
        log.info("in_context")

    log.info("out_of_context")

    with open(os.path.join(somedir, log_files[0])) as stream:
        contents = stream.read()
    assert "out_of_context" in contents
    assert "in_context" not in contents

    assert "out_of_context" not in log_file.getvalue()
    assert "in_context" in log_file.getvalue()
