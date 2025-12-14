#!/bin/bash
# Run test queries with hybrid search + tag boosting

echo "Running queries with HYBRID SEARCH + TAG BOOSTING..."
echo ""

queries=(
  "python tools"
  "semantic search projects"
  "productivity systems"
  "zettelkasten books"
  "smart notes"
  "obsidian plugins"
  "pkm learning"
  "writing books"
)

for query in "${queries[@]}"; do
  echo "Query: $query"
  uv run temoa search "$query" --limit 3 --vault test-vault --hybrid --json 2>/dev/null | jq -r '.results[] | "  [\(.similarity_score | tonumber | . * 100 | floor / 100)] \(.relative_path)"'
  echo ""
done
