# GitHub Gleaning Transformation Example

## BEFORE (Current Format)

```yaml
---
created: 2024-12-30 00:13
description: Websites, web apps, portfolios that look like desktop operating systems
domain: github.com
gleaning_id: f81bb4d2075f
source: Daily/2024/12-December/2024-12-30-Mo.md
status: active
title: 'syxanash/awesome-web-desktops: Websites, web apps, portfolios that look like
  desktop operating systems'
type: gleaning
url: https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file
github_language: Ruby
github_stars: 1843
github_topics:
- awesome
- awesome-list
- classic-mac-os
- cloud-os
- design
- desktop
- desktop-environment
- directory
- list
- retro
- web-desktop
- web-os
- webdesign
- webtop
- windows-xp
- windows11
- windows11-web
- windows98
github_archived: false
github_last_push: 2025-12-23 15:09:19+00:00
---

# syxanash/awesome-web-desktops: Websites, web apps, portfolios that look like desktop operating systems

#webdesktops #awesome #portfolios
- Curated directory of websites and web apps that mimic desktop OS.
- Includes portfolios and experimental web desktops.
- Actively monitored for link validity and contributions are welcome.

## Link

[syxanash/awesome-web-desktops: Websites, web apps, portfolios which look like desktop operating systems](https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file)

## Source

Gleaned from [[2024-12-30-Mo]] on 2024-12-30 00:13
```

**Issues**:
- ❌ H1 heading (forbidden)
- ❌ Tags in body text (#webdesktops #awesome #portfolios)
- ❌ Long repetitive title with YAML line wrapping
- ❌ Generic GitHub API description (not from README)

---

## AFTER (Option 2 Format)

```yaml
---
created: 2024-12-30 00:13
description: Curated directory of websites and web apps that mimic desktop operating
  systems. Includes portfolios, experimental web desktops, and window manager projects.
  Features classic designs (Windows 98, Mac OS, Windows XP) and modern implementations.
  All links actively monitored for validity. Contributions welcome.
domain: github.com
gleaning_id: f81bb4d2075f
source: Daily/2024/12-December/2024-12-30-Mo.md
status: active
tags:
- webdesktops
- awesome
- portfolios
- design
- retro
- windows98
- classic-mac-os
title: syxanash/awesome-web-desktops
type: gleaning
url: https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file
github_language: Ruby
github_stars: 1843
github_topics:
- awesome
- awesome-list
- classic-mac-os
- cloud-os
- design
- desktop
- desktop-environment
- directory
- list
- retro
- web-desktop
- web-os
- webdesign
- webtop
- windows-xp
- windows11
- windows11-web
- windows98
github_archived: false
github_last_push: 2025-12-23 15:09:19+00:00
---

Curated directory of websites and web apps that mimic desktop operating systems. Includes portfolios, experimental web desktops, and window manager projects. Features classic designs (Windows 98, Mac OS, Windows XP) and modern implementations. All links actively monitored for validity. Contributions welcome.

**1843 ★** · Ruby · Last updated 2025-12-23

## Link

[syxanash/awesome-web-desktops](https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file)

## Source

Gleaned from [[2024-12-30-Mo]] on 2024-12-30 00:13
```

**Improvements**:
- ✅ No H1 heading (starts with description paragraph)
- ✅ All tags in YAML frontmatter (selected from github_topics)
- ✅ Clean short title: `syxanash/awesome-web-desktops`
- ✅ Rich description extracted from README (not just API tagline)
- ✅ Compact GitHub metadata line
- ✅ Clean link text (no repetition)

---

## Implementation Strategy

To transform all GitHub gleanings:

1. **Title**: Change to just `owner/repo` (remove description suffix)

2. **Description**: Extract meaningful content from README
   - Use first few sentences from README
   - Include key features/highlights
   - Make it 2-4 sentences, informative and searchable

3. **Tags**:
   - Select 5-7 most relevant topics from `github_topics`
   - Add to `tags:` field in frontmatter
   - Remove any hashtags from body

4. **Clean up frontmatter**:
   - **DELETE** `github_readme_excerpt` field entirely
   - It's usually HTML/images, not useful text
   - Real description goes in `description:` field

5. **Body**:
   - Remove H1 heading entirely
   - Start with description as first paragraph
   - Add metadata line: `**{stars} ★** · {language} · Last updated {date}`
   - Keep Link and Source sections (H2)
   - Remove any other body content (currently the bullet points)

This creates a clean, consistent format that's easy to scan and search.
