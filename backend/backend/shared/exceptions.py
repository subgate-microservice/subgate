from typing import Hashable, Type, Union


class ItemNotExist(LookupError):
    def __init__(self, item_type: Type, lookup_field_value: Hashable, lookup_field_key="id"):
        self.item_type = item_type
        self.lookup_field_key = lookup_field_key
        self.lookup_field_value = lookup_field_value

    def __str__(self):
        return f"The item of type '{self.item_type.__name__}' with {self.lookup_field_key} '{self.lookup_field_value}' does not exist."

    def to_json(self):
        return {
            "exception_code": "item_not_exist",
            "item_type": self.item_type.__name__,
            "lookup_field_key": self.lookup_field_key,
            "lookup_field_value": str(self.lookup_field_value),

        }


class ItemAlreadyExist(Exception):
    def __init__(self, item_type: Type, index_value: Hashable, index_key="id"):
        self.item_type = item_type
        self.index_key = index_key
        self.index_value = index_value

    def __str__(self):
        return f"The item of type '{self.item_type.__name__}' with {self.index_key} '{self.index_value}' already exists."

    def to_json(self):
        return {
            "exception_code": "item_already_exist",
            "item_type": self.item_type.__name__,
            "index_value": str(self.index_value),
            "index_key": self.index_key,
        }


class ValidationError(Exception):
    def __init__(
            self,
            field: str,
            value: Union[str, int, float, bool],
            value_type: str,
            message: str,
    ):
        self.field = field
        self.value = value
        self.value_type = value_type
        self.message = message

    def __str__(self):
        return (
            f"Validation error on field '{self.field}': {self.message}. "
            f"Received value: {self.value}. Value type: {self.value_type}"
        )

    def to_json(self):
        return {
            "exception_code": "validation_error",
            "field": self.field,
            "value": self.value,
            "value_type": self.value_type,
            "message": self.message,
        }

    @classmethod
    def from_json(cls, data):
        return cls(field=data["field"], value=data["value"], value_type=data["value_type"], message=data["message"])
