import os
import sys
import logging

logger = logging.getLogger("formja-mcp")

FORMJA_BASE_URL = os.getenv("FORMJA_BASE_URL", "https://app.formja.com.br")
FORMJA_API_KEY = os.getenv("FORMJA_API_KEY", "")


def validate_config():
    if not FORMJA_API_KEY:
        print("ERROR: FORMJA_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    if not FORMJA_BASE_URL:
        print(
            "ERROR: FORMJA_BASE_URL environment variable is required", file=sys.stderr
        )
        sys.exit(1)
