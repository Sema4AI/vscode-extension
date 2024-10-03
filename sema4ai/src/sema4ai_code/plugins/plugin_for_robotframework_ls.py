def get_resolve_interpreter_for_robotframework_ls():
    import os
    import sys

    try:
        import sema4ai_code
    except ImportError:
        # Automatically add it to the path if __main__ is being executed.
        sys.path.append(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        import sema4ai_code  # @UnusedImport
    sema4ai_code.import_robocorp_ls_core()

    from sema4ai_code.resolve_interpreter import RobocorpResolveInterpreter

    return RobocorpResolveInterpreter


def register_plugins(pm):  # The name is important, it must be register_plugins!
    import weakref

    from robocorp_ls_core.ep_resolve_interpreter import EPResolveInterpreter

    pm.register(
        EPResolveInterpreter,
        get_resolve_interpreter_for_robotframework_ls(),
        kwargs={"weak_pm": weakref.ref(pm)},
    )
