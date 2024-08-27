import typing
from functools import lru_cache

if typing.TYPE_CHECKING:
    from sema4ai_code.agents.agent_spec_handler import Entry


@lru_cache
def load_v2_spec() -> dict[str, "Entry"]:
    """
    Creates a dict from the agent spec v2.

    Note: the result is cached (so, the spec should not be changed).
    """
    from sema4ai_code.agents.agent_spec import AGENT_SPEC_V2
    from sema4ai_code.agents.agent_spec_handler import load_spec

    return load_spec(AGENT_SPEC_V2)
