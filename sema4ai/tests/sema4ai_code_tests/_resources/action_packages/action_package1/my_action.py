from sema4ai.actions import action


@action
def my_action(arg1: str) -> str:
    """
    My docstring

    Args:
        arg1: this is argument...
    """
    return arg1
