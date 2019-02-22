schema = {
    "$schema": "https://json-schema.org/schema#",
    "id": "orca_schema_v1",
    "type": "object",
    "required": ["version", "job"],

    "properties": {
        "version": {"type": "string"},
        "var": {
            "type": "object",
            "patternProperties": {
                "[a-zA-Z0-9]*$": {
                    "type": ["string", "number", "array"]
                }
            },
            "additionalProperties": False
        },
        "name": {"type": "string"},
        "description": {"type": "string"},
        "job": {
            "type": "array",
            "items": {"$ref": "#definitions/task"}
        }

    },

    "definitions": {
        "task": {
            "id": "#/definitions/task",
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "inputs": {
                    "type": "object",
                    "patternProperties": {
                        "[a-zA-Z0-9]*$": {
                            "type": ["string", "number", "array"]
                        }
                    }
                },
                "config": {
                    "type": "object",
                    "patternProperties": {
                        "[a-zA-Z0-9]*$": {
                            "type": ["string", "number", "array"]
                        }
                    }
                },
                "outputs": {
                    "type": "array",
                    "items": ["string"]
                }
            }
        },
    }
}
