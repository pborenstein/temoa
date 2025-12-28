#!/bin/bash
# Helper script to view temoa logs

case "$1" in
  temoa|app|a)
    echo "=== temoa Logs (stdout) ==="
    tail -f ~/Library/Logs/temoa.log
    ;;
  error|err|e)
    echo "=== temoa Errors (stderr) ==="
    tail -f ~/Library/Logs/temoa.error.log
    ;;
  all|*)
    echo "=== All temoa Logs ==="
    tail -f ~/Library/Logs/temoa*.log
    ;;
esac
