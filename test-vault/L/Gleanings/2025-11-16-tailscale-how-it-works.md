---
gleaned: 2025-11-16
url: https://tailscale.com/blog/how-tailscale-works/
tags: [gleaning, networking, tailscale]
source: "[[2025-11-16-Sa]]"
---

# Tailscale for Personal Projects

Deep dive into how Tailscale works. Built on Wireguard, handles NAT traversal automatically.

Why it's great for personal projects:
- Creates mesh VPN without manual config
- Encrypted by default (Wireguard)
- Works through most firewalls/NAT
- Each device gets stable IP (100.x.x.x)

Perfect for accessing home server from mobile without exposing to internet.

Security model: Trust the Tailscale network. Don't need auth/HTTPS if only accessing via Tailscale.

[Link](https://tailscale.com/blog/how-tailscale-works/)
