#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STDOUT_LOG="$HOME/Library/Logs/temoa.log"
STDERR_LOG="$HOME/Library/Logs/temoa.error.log"

function usage {
    echo "Usage: $0 [stdout|stderr|both|help]"
    echo ""
    echo "View Temoa service logs:"
    echo "  stdout - Show only standard output"
    echo "  stderr - Show only error output"
    echo "  both   - Show both (default)"
    echo "  help   - Show this message"
    echo ""
    echo "Examples:"
    echo "  $0              # Tail both logs"
    echo "  $0 stderr       # Tail only errors"
    exit 0
}

MODE="${1:-both}"

case "$MODE" in
    stdout)
        echo -e "${GREEN}Tailing stdout: $STDOUT_LOG${NC}"
        tail -f "$STDOUT_LOG"
        ;;
    stderr)
        echo -e "${YELLOW}Tailing stderr: $STDERR_LOG${NC}"
        tail -f "$STDERR_LOG"
        ;;
    both)
        echo -e "${GREEN}Tailing both logs${NC}"
        echo "Stdout: $STDOUT_LOG"
        echo "Stderr: $STDERR_LOG"
        echo ""
        tail -f "$STDOUT_LOG" "$STDERR_LOG"
        ;;
    help)
        usage
        ;;
    *)
        echo "Unknown option: $MODE"
        usage
        ;;
esac
