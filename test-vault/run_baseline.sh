#!/bin/bash
# Run baseline queries and save results

echo "Running baseline queries (no frontmatter weighting)..."
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
  uv run temoa search "$query" --limit 3 --vault test-vault --json 2>/dev/null | jq -r '.results[] | "  [\(.similarity_score | tonumber | . * 100 | floor / 100)] \(.relative_path)"'
  echo ""
done
