#!/bin/bash
# Helper script to view temoa logs

case "$1" in
  temoa|app|a)
    echo "=== Temoa Logs (stdout) ==="
    tail -f ~/Library/Logs/temoa.log
    ;;
  error|err|e)
    echo "=== Temoa Errors (stderr) ==="
    tail -f ~/Library/Logs/temoa.error.log
    ;;
  all|*)
    echo "=== All Temoa Logs ==="
    tail -f ~/Library/Logs/temoa*.log
    ;;
esac
