---
gleaned: 2025-11-16
url: https://www.sqlite.org/whentouse.html
tags: [gleaning, databases, sqlite]
source: "[[2025-11-16-Sa]]"
---

# Why SQLite Works for Local-First Apps

Official SQLite docs on when to use it. Key insight: Most apps don't need client-server databases.

Good fit for:
- Single-user applications
- Local data storage
- Embedded systems
- Simple file format

Not good for:
- High write concurrency
- Client-server applications
- Very large datasets (>1TB)

For personal knowledge management: SQLite or similar (file-based storage) is perfect. No server overhead.

[Link](https://www.sqlite.org/whentouse.html)
