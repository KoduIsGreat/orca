schema = {
    "$schema": "https://json-schema.org/schema#",
    "id": "orca_schema_v1",
    "type": "object",
    "required": ["version"],

    "properties": {
        "version": {"type": "string"},
        "steps": {
            "type": "array",
            "items": {"$ref": "#definitions/step"}
        }

    },

    "definitions": {
        "step": {
            "id": "#/definitions/step",
            "type": "object",
            "properties": {
                "config": {
                    "type": "array",
                    "items": {"$ref": "#definitions/configItem"}
                },
                "service": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                        "port": {"type": "string"},
                        "name": {"type": "string"}
                    }
                }
            }
        },

        "configItem": {
            "id": "#/definitions/configItem",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": ["number", "array", "string"]},
            }
        },
    }
}
