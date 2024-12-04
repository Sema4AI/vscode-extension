from typing import Optional


def build_query_from_dict_params(
    query: str, params: Optional[dict[str, str | int | float]]
) -> str:
    """
    Replace all the $name in the query with the actual values from params.

    Args:
        query: The SQL query with placeholders.
        params: A dictionary of parameters to inject into the query.

    Returns:
        str: The query with parameters injected.
    """
    import math
    import re

    if not params and "$" not in query:
        return query

    new_params: dict[str, str] = {}
    if params:
        # Escape single quotes in parameters to prevent SQL injection
        C1 = "'"
        C2 = "''"
        for key, value in params.items():
            if isinstance(value, str):
                value = value.replace(C1, C2)
                new_params[key] = f"'{value}'"
            elif isinstance(value, (int, float)):
                if not math.isfinite(value):
                    raise ValueError(
                        f"Infinity or NaN is not supported as a query parameter. Parameters: {params}"
                    )
                new_params[key] = str(value)
            else:
                raise ValueError(f"Unsupported parameter: {value} type: {type(value)}")

    # Replace placeholders with actual values
    def replace_placeholder(match):
        key = match.group(1)
        if key in new_params:
            return new_params[key]
        raise ValueError(f"Missing parameter for placeholder: {key}")

    # Use regex to find all placeholders and replace them
    query = re.sub(r"\$(\w+)", replace_placeholder, query)

    return query


def build_query_from_list_params(
    query: str, params: Optional[list[str | int | float]]
) -> str:
    """
    Replace all the ? in the query with the actual values from params.

    Args:
        query: The SQL query with placeholders.
        params: A list of parameters to inject into the query.

    Returns:
        str: The query with parameters injected.
    """
    import math

    placeholder_count = query.count("?")
    params_len = len(params) if params else 0

    # Check if the number of placeholders matches the number of parameters
    if placeholder_count != params_len:
        raise ValueError(
            f"The number of placeholders ({placeholder_count}) does not match the number of parameters ({params_len})."
        )

    if not params:
        return query

    # Escape single quotes in parameters to prevent SQL injection
    C1 = "'"
    C2 = "''"
    escaped_params = []
    for param in params:
        if isinstance(param, str):
            new_param = param.replace(C1, C2)
            escaped_params.append(f"'{new_param}'")
        elif isinstance(param, (int, float)):
            # Assert that it's not infinity or NaN
            if not math.isfinite(param):
                raise ValueError(
                    f"Infinity or NaN is not supported as a query parameter. Parameters: {params}"
                )
            v = str(param)
            escaped_params.append(v)
        else:
            raise ValueError(f"Unsupported parameter: {param} type: {type(param)}")

    # Split the query by placeholders and interleave with parameters
    parts = query.split("?")
    query_with_params = "".join(
        part + param for part, param in zip(parts, escaped_params)
    )

    if parts[-1] != "":  # If the last part is not empty, add it too
        query_with_params += parts[-1]

    return query_with_params
