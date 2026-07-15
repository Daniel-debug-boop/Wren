"""Dump the Wren config schema as JSON to stdout."""

import json

from wren.app_server.config import get_global_config

if __name__ == '__main__':
    config = get_global_config()
    schema = config.model_json_schema()
    print(json.dumps(schema, indent=2))
