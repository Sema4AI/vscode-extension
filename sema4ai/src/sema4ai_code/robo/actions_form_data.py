from enum import Enum
from typing import Any, Dict, List, Union


class InputPropertyType(Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


class InputProperty:
    def __init__(
        self,
        title: str,
        description: str,
        type: InputPropertyType,
        enum: List[str] | None = None,
    ):
        self.title = title
        self.description = description
        self.type = type
        self.enum = enum


PropertyFormDataType = Union[str, int, float, bool, List["PropertyFormData"]]


class PropertyFormData:
    def __init__(
        self,
        name: str,
        prop: InputProperty,
        required: bool,
        value: PropertyFormDataType,
        title: str | None = None,
        options: List[str] | None = None,
    ):
        self.name = name
        self.prop = prop
        self.required = required
        self.value = value
        self.title = title
        self.options = options

    def value_as_str(self) -> str:
        if self.prop.enum:
            if self.prop.description:
                return f"{self.prop.enum} ({self.prop.description})"
            return f"{self.prop.enum}"

        if self.prop.description:
            return f"{self.prop.type.value}: {self.prop.description}"

        return f"{self.prop.type.value}"

    def __str__(self):
        return f"{self.name} [{self.value_as_str()}]"

    __repr__ = __str__


def get_default_value(
    property_type: str, enum: List[str] | None = None
) -> PropertyFormDataType:
    if property_type == "number":
        return 0.0
    elif property_type == "boolean":
        return False
    elif property_type == "integer":
        return 0
    elif property_type == "array":
        return "[]"
    elif property_type == "object":
        return "{}"
    else:
        if enum:
            return enum[0]
        return ""


def set_array_item_title(item: PropertyFormData) -> None:
    new_title = item.prop.title
    if new_title.endswith("*"):
        new_title = new_title[:-1]
    if not new_title.endswith(" (item)"):
        new_title += " (item)"
    item.prop.title = new_title


def properties_to_form_data(
    schema: Dict[str, Any], parents: List[str] | None = None
) -> List[PropertyFormData]:
    if parents is None:
        parents = []

    if "properties" not in schema:
        return []

    entries = []
    for name, prop in schema["properties"].items():
        property_name = parents + [name]

        if "$ref" in prop:
            continue

        if "properties" in prop:
            entries.extend(properties_to_form_data(prop, property_name))
            continue

        if "allOf" in prop:
            first_child = prop["allOf"][0]
            if "enum" in first_child:
                entry = PropertyFormData(
                    name=".".join(property_name),
                    prop=InputProperty(
                        title=prop.get("title", property_name[-1]),
                        description=prop.get("description", ""),
                        type=InputPropertyType.ENUM,
                    ),
                    required=name in schema.get("required", []),
                    value=prop.get(
                        "default", first_child["enum"][0] if first_child["enum"] else ""
                    ),
                    options=first_child["enum"],
                )
                entries.append(entry)
            else:
                for item in prop["allOf"]:
                    entries.extend(properties_to_form_data(item, property_name))
            continue

        if isinstance(prop.get("type"), list) or prop.get("type") == "array":
            row_entry = PropertyFormData(
                name=".".join(property_name),
                title=prop.get("title", property_name[-1]),
                prop=InputProperty(
                    title=prop.get("title", property_name[-1]),
                    description=prop.get("description", ""),
                    type=InputPropertyType.ARRAY,
                ),
                required=name in schema.get("required", []),
                value=get_default_value(prop.get("type", "string")),
            )

            if "items" in prop:
                if "properties" in prop["items"]:
                    row_properties = properties_to_form_data(
                        prop["items"], property_name + ["0"]
                    )
                    row_entry.value = row_properties
                    entries.append(row_entry)
                    entries.extend(row_properties)
                else:
                    enum = prop["items"].get("enum")
                    row_property = PropertyFormData(
                        name=f"{'.'.join(property_name)}.0",
                        prop=InputProperty(
                            title=prop.get("title", property_name[-1]),
                            description=prop.get("description", ""),
                            type=InputPropertyType(prop["items"].get("type", "string")),
                            enum=enum,
                        ),
                        required=name in schema.get("required", []),
                        value=get_default_value(
                            prop["items"].get("type", "string"), enum
                        ),
                    )
                    row_entry.value = [row_property]
                    set_array_item_title(row_property)
                    entries.extend([row_entry, row_property])
            else:
                entries.append(row_entry)
            continue

        enum = prop.get("enum")
        entry = PropertyFormData(
            name=".".join(property_name),
            prop=InputProperty(
                title=prop.get("title", property_name[-1]),
                description=prop.get("description", ""),
                type=InputPropertyType(prop.get("type", "string")),
                enum=enum,
            ),
            required=name in schema.get("required", []),
            value=get_default_value(prop.get("type", "string"), enum),
        )

        if schema.get("title") and entries:
            entry.title = schema["title"]

        entries.append(entry)

    return entries


Payload = Dict[str, Any]


def form_data_to_payload(data: List[PropertyFormData]) -> Payload:
    import json

    root: Payload = {}

    for item in data:
        levels = item.name.split(".")
        property_name = levels[-1]

        current_level = parent = root
        proceed = True
        for i, level in enumerate(levels[:-1]):
            try:
                if isinstance(parent, list):
                    if parent:
                        current_level = parent[-1]
                    else:
                        if (
                            len(levels) > i + 1 and levels[i + 1] == "0"
                        ):  # This means list[list] -- in which case we just create one empty list.
                            proceed = False
                            break
                        else:
                            parent.append({})
                            current_level = parent[-1]
                elif isinstance(parent, dict):
                    if parent.get(level) is None:
                        parent[level] = {}
                    current_level = parent[level]
                else:
                    raise Exception(f"Unexpected type: {type(current_level)}")
            except Exception:
                raise Exception(
                    f"Error setting {level} for {item.name}. Built defaults so far:\n{json.dumps(root, indent=2)}"
                )
            parent = current_level

        if not proceed:
            continue

        if item.prop.type == InputPropertyType.OBJECT:
            if isinstance(current_level, list):
                current_level.append(json.loads(str(item.value)))
            else:
                current_level[property_name] = json.loads(str(item.value))
        elif item.prop.type == InputPropertyType.ARRAY:
            if isinstance(current_level, dict):
                if property_name not in current_level:
                    current_level[property_name] = []
        elif isinstance(current_level, list):
            if not current_level:
                current_level.append(item.value)
            else:
                current_level[0] = item.value
        else:
            current_level[property_name] = item.value

    return root


def payload_to_form_data(
    payload: Payload, form_data: List[PropertyFormData], path: str = ""
) -> List[PropertyFormData]:
    result: List[PropertyFormData] = []

    for key, val in payload.items():
        full_path = f"{path}.{key}" if path else key
        if isinstance(val, dict):
            result.extend(payload_to_form_data(val, form_data, full_path))
        elif isinstance(val, list):
            found_data = next(
                (elem for elem in form_data if elem.name == full_path), None
            )
            if found_data:
                result.append(found_data)
            for index, elem_value in enumerate(val):
                found_elem = next(
                    (elem for elem in form_data if elem.name == f"{full_path}.{index}"),
                    None,
                )
                if found_elem:
                    result.append(
                        PropertyFormData(**{**found_elem.__dict__, "value": elem_value})
                    )
                else:
                    prev = next(
                        (elem for elem in form_data if elem.name == f"{full_path}.0"),
                        None,
                    )
                    if prev:
                        result.append(
                            PropertyFormData(
                                **{
                                    **prev.__dict__,
                                    "value": elem_value,
                                    "name": f"{full_path}.{index}",
                                }
                            )
                        )
        else:
            found_data = next(
                (elem for elem in form_data if elem.name == full_path), None
            )
            if found_data:
                result.append(PropertyFormData(**{**found_data.__dict__, "value": val}))

    return result
