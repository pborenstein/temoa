# GitHub Gleaning Layout Options

This document shows different layout options for GitHub gleanings. All examples use the same gleaning (syxanash/awesome-web-desktops) to make comparison easier.

---

## Option 1: Current Format (Long Title)

**Title Pattern**: `owner/repo: {full description from GitHub}`

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
- web-desktop
- windows98
github_archived: false
github_last_push: 2025-12-23 15:09:19+00:00
github_readme_excerpt: '[<img src="assets/logo.png" align="right" width="120">](https://simone.computer/#/webdesktops)'
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

**Pros**:
- Title is descriptive and searchable
- Clear what the repo does at a glance
- Good for Obsidian search/links

**Cons**:
- Title is very long and repetitive with description
- Awkward line wrapping in YAML
- H1 heading repeats the same long text

---

## Option 2: Short Title (repo only) ⭐ SELECTED

**Title Pattern**: `owner/repo`

**Key Requirements**:
- NO H1 headings anywhere (H2 is highest)
- Tags ONLY in YAML frontmatter, NEVER in body text
- Rich, informative descriptions (extracted from README)

```yaml
---
created: 2024-12-30 00:13
description: Curated directory of websites and web apps that mimic desktop operating
  systems. Includes portfolios and experimental web desktops. Actively monitored for
  link validity and contributions welcome.
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
title: syxanash/awesome-web-desktops
type: gleaning
url: https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file
github_language: Ruby
github_stars: 1843
github_topics:
- awesome
- awesome-list
- classic-mac-os
- web-desktop
- windows98
github_archived: false
github_last_push: 2025-12-23 15:09:19+00:00
github_readme_excerpt: '[<img src="assets/logo.png" align="right" width="120">](https://simone.computer/#/webdesktops)'
---

Curated directory of websites and web apps that mimic desktop operating systems. Includes portfolios and experimental web desktops. Actively monitored for link validity and contributions welcome.

**1843 ★** · Ruby · Last updated 2025-12-23

## Link

[syxanash/awesome-web-desktops](https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file)

## Source

Gleaned from [[2024-12-30-Mo]] on 2024-12-30 00:13
```

**Pros**:
- Clean, concise title
- No YAML line wrapping issues
- Rich description from README (not just GitHub tagline)
- Easy to link to in Obsidian: `[[syxanash/awesome-web-desktops]]`
- Tags in proper location (YAML frontmatter)
- No H1 heading pollution

**Cons**:
- Requires better description extraction from READMEs
- Description quality is critical for searchability

---

## Option 3: Hybrid (repo + tagline)

**Title Pattern**: `owner/repo - {short tagline}`
**Description**: Enhanced from README excerpt

```yaml
---
created: 2024-12-30 00:13
description: Curated directory of websites and web apps that mimic desktop operating
  systems. Includes portfolios and experimental web desktops. Actively monitored for
  link validity and contributions are welcome.
domain: github.com
gleaning_id: f81bb4d2075f
source: Daily/2024/12-December/2024-12-30-Mo.md
status: active
title: syxanash/awesome-web-desktops - Web desktop OS lookalikes
type: gleaning
url: https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file
github_language: Ruby
github_stars: 1843
github_topics:
- awesome
- awesome-list
- classic-mac-os
- web-desktop
- windows98
github_archived: false
github_last_push: 2025-12-23 15:09:19+00:00
github_readme_excerpt: '[<img src="assets/logo.png" align="right" width="120">](https://simone.computer/#/webdesktops)'
---

# syxanash/awesome-web-desktops

**Web desktop OS lookalikes**

Curated directory of websites and web apps that mimic desktop operating systems. Includes portfolios and experimental web desktops. Actively monitored for link validity and contributions are welcome.

---

**Language**: Ruby | **Stars**: 1843 | **Last push**: 2025-12-23

**Topics**: awesome, awesome-list, classic-mac-os, web-desktop, windows98

## Link

[syxanash/awesome-web-desktops](https://github.com/syxanash/awesome-web-desktops?tab=readme-ov-file)

## Source

Gleaned from [[2024-12-30-Mo]] on 2024-12-30 00:13
```

**Pros**:
- Balanced title: repo name + context
- Enhanced description from README
- GitHub metadata is visible in body
- Clean presentation

**Cons**:
- Requires manual tagline creation
- More layout changes to body content

---

## Option 4: Minimal (repo only + README description)

**Title Pattern**: `owner/repo`
**Description**: First meaningful paragraph from README

```yaml
---
created: 2024-12-30 00:13
description: Curated directory of websites and web apps that mimic desktop operating
  systems, including portfolios and experimental web desktops
domain: github.com
gleaning_id: f81bb4d2075f
source: Daily/2024/12-December/2024-12-30-Mo.md
status: active
title: syxanash/awesome-web-desktops
type: gleaning
url: https://github.com/syxanash/awesome-web-desktops
github_language: Ruby
github_stars: 1843
github_topics:
- awesome
- awesome-list
- classic-mac-os
- web-desktop
- windows98
github_archived: false
github_last_push: 2025-12-23
github_readme_excerpt: '[<img src="assets/logo.png" align="right" width="120">](https://simone.computer/#/webdesktops)'
---

# syxanash/awesome-web-desktops

Curated directory of websites and web apps that mimic desktop operating systems, including portfolios and experimental web desktops.

**1843 ★** · Ruby · Last updated 2025-12-23

[View on GitHub](https://github.com/syxanash/awesome-web-desktops) · Gleaned from [[2024-12-30-Mo]]
```

**Pros**:
- Very clean and minimal
- Description from README (not GitHub API)
- Single-line metadata bar
- Modern, compact layout

**Cons**:
- Loses some detail
- Different structure than other gleanings

---

## Recommendation

**Option 2 (Short Title)** is recommended because:

1. **Clean and simple**: Just `owner/repo`
2. **No line wrapping**: Fits on one line in YAML
3. **Easy to link**: `[[syxanash/awesome-web-desktops]]` works perfectly
4. **Description stays useful**: Frontmatter description field contains the details
5. **Minimal changes**: Only need to update title field
6. **Consistent with principle**: Simple individual files, search finds connections

### Implementation

For Option 2, we would:

1. Update title to just `owner/repo`
2. Keep description as-is (or enhance from README)
3. Update H1 to just repo name
4. Add description as subtitle under H1
5. Keep all other fields the same

This maintains the "simple files" philosophy while making titles cleaner and more link-friendly.
