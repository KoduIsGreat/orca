schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "id": "orca_schema_v1",
    "type": "object",
    "required": ["version", "job"],

    "properties": {
        "apiversion": {"type": "string"},
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
        "job": {"$ref": "#definitions/job"}

    },

    "definitions": {
        "job": {
            "type": "array",
            "items": {
                "anyOf": [
                    {"$ref": "#definitions/task"},
                    {"$ref": "#definitions/if"},
                    {"$ref": "#definitions/for"},
                    {"$ref": "#definitions/switch"},
                    {"$ref": "#definitions/fork"},
                ]
            }
        },
        "if": {
            "id": "#/definitions/if",
            "type": "object",
            "required": ["if", "do"],
            "properties": {
                "if": {"type": "string"},
                "description": {"type": "string"},
                "do": {"$ref": "#/definitions/job"}
            }
        },
        "for": {
            "id": "#/definitions/for",
            "required": ["for", "do"],
            "type": "object",
            "properties": {
                "for": {"type": "string"},
                "do": {"$ref": "#/definitions/job"}
            }
        },
        "switch": {
            "id": "#/definitions/switch",
            "type": "object",
            "required": ["switch", "default"],
            "properties": {
                "switch": {"type": "string"},
                "default": {"$ref": "#definitions/job"}
            },
            "patternProperties": {
                "[a-zA-Z0-9]*$": {"$ref": "#definitions/job"}
            },
            "additionalProperties": True
        },
        "fork": {
            "id": "#/definitions/fork",
            "type": "array",
            "items": {"$ref": "#/definitions/job"}
        },
        "task": {
            "id": "#/definitions/task",
            "type": "object",
            "oneOf": [
                {"required": ["python"]},
                {"required": ["csip"]},
                {"required": ["bash"]},
                {"required": ["http"]}
            ],
            "properties": {
                "task": {"type": "string"},
                "python": {"type": "string"},
                "bash": {"type": "string"},
                "http": {"type": "string"},
                "csip": {"type": "string"},

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
                    "items": [{"type": "string"}],
                    "uniqueItems": True
                }
            },
            "additionalProperties": False
        },
    }
}
