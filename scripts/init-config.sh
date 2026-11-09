#!/bin/bash
# Compatibility entrypoint; new callers should use bin/init-config.sh.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 1
exec "$SCRIPT_DIR/../bin/init-config.sh" "$@"
