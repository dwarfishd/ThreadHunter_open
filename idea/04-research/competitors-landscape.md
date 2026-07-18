[[README|← Назад к Research]]

# Competitors & Adjacent Landscape

*Research date: 2026-06-30*

---

## 1. Founders Building Similar Things (LinkedIn / Public)

### Telegram-Native CRM & Lead Generation

| Name / Profile | Company | What They're Building | Same Target User? |
|---|---|---|---|
| **Adithya Kumar** (Outerscope) | **CRMChat** (formerly Hints) | Telegram-native CRM & outreach app for Web3/GTM teams. Finds leads on Telegram, manages deals, multi-account outreach. Founded 2021, pivoted 2024. ~$440K ARR, ~4 employees. | Partially -- targets sales teams who source leads FROM Telegram (not parsers), but the end user is the same: a manager who needs structured leads from Telegram chaos. |
| **posokin** (LinkedIn) | **DISE CRM** (acquired by Minders, ~Aug 2025) | AI-native CRM for Telegram-based B2B ops. Manages 1000+ conversations, smart filters, pipelines, AI summaries. Initially crypto BD-focused, now broader B2B. | Partially -- manages leads already in Telegram chats rather than extracting them from channels, but same problem space: Telegram is unstructured and leads drown. |
| Unknown (Turkey-based, founded 2020) | **TGDesk / Wadesk** | "Best free Telegram CRM" -- manage multiple accounts, extract leads via group scraping, bulk senders, auto-adders. Unfunded (per Tracxn). Co-founders identified the need running a flower business. | **Yes** -- explicitly offers group scraping for lead extraction, closest direct overlap. |
| Unknown | **LeadGuru** | Omni-channel lead gen for community-driven sales. Monitors Slack, Discord, Telegram groups, qualifies leads by expressed intent, single-dashboard outreach. | **Yes** -- same core idea: find high-intent prospects in messaging communities and surface them for outreach. |
| Unknown | **ElixirLabs (Flow CRM)** | Telegram CRM + automation with AI-driven insights, lead nurture/conversion workflows, SaaS integrations. | Partially -- CRM on top of Telegram, not a parser/database builder. |
| Unknown | **iMBrace** | "Telegram Outbound Journey" platform for customer engagement and lead generation. | Partially -- outbound engagement, not channel parsing. |
| Unknown | **VVZ Studio** | Lightweight Telegram CRM -- instant alerts, status updates, task assignments, lead flow visibility. | No -- post-extraction CRM, not a parser. |

### Russian-Language Telegram Parsers (closest direct overlap)

| Name | What They're Building | Notes |
|---|---|---|
| **Tegranium** | Automated Telegram parser + AI lead finder + CRM. Searches groups by keywords, filters spam, auto-responder, 24/7 sales automation. | **Closest direct competitor** to the described idea -- AI-powered parsing + CRM in one tool. Russian-language market. |
| **TGCParser** | AI-driven Telegram parser that finds relevant chats/groups from plain-language audience descriptions, monitors 24/7, captures messages with author metadata, converts to leads. | Closest to the "describe your audience, we find and extract" model. Python-based. |
| **A-PARSER** (a-parser.com) | Professional scraper platform for SEO, e-commerce, AI automation. Includes Telegram data collection among many other sources. | General-purpose parser, not niche-specific. Established reputation since 2020s. |
| **TeleParser** (teleparser.com) | Free parser for Telegram, VKontakte, MAX. Auto post parsing, AI-rewrite, cross-posting. | Content-focused, not lead/contact extraction. |
| Various GitHub projects | `4eiz/telegram-parser`, `MaxVarna/telegram-parser`, `artih24/TeleParser`, `VLADIM88888/TELEGRAM-B2B-LEAD-SCRAPER`, `akula-marketing/telegram-parser` | Open-source scripts for parsing Telegram channels, collecting user data, extracting contacts. | Developer tools, not commercial products. Shows active demand. |

### Apify Ecosystem

**Apify** (apify.com) hosts multiple actors for Telegram scraping:
- **Telegram Lead Scraper** -- extracts leads from groups, channels, user profiles
- **Telegram Scraper** (tri_angle) -- extracts usernames, phone numbers, bios, full message history
- **Telegram Channels Scraper** (eunit) -- structured content, posts, media, metadata from public channels
- **Telegram Scraper** (dainty_screw) -- group member and lead extraction

These are infrastructure tools that anyone can build on top of. They show there is active, paid demand for Telegram lead extraction.

---

## 2. Who Is Raising Money Under This Problem?

### Funded / Venture-Backed

| Company | Round / Amount | Investors | What They Do | Proximity |
|---|---|---|---|---|
| **CRMChat (Outerscope)** | ~$2.5M total | Altair VC, Flashpoint, angels | Telegram-native CRM for Web3/GTM. Founded 2021, pivoted 2024 from "Hints." | **Close** -- same problem (Telegram is unstructured, leads drown), different angle (CRM overlay vs. parser/database). Est. $1.3M valuation, $440K ARR (2025). |
| **Pepper Cloud** (Singapore, founded 2017) | Bootstrapped / revenue-funded | None disclosed | AI-powered CRM with Telegram integration. Sales management, marketing automation, conversation tracking. Est. $4.7M ARR, $14.2M valuation (2025). | Medium -- general CRM with Telegram as a channel, not a parser. |
| **Minders** (venture builder) | Unknown | Unknown | Builds Telegram ecosystem infrastructure. Acquired DISE CRM (~Aug 2025). Targets crypto/Web3 B2B sales ops. | Medium -- infrastructure play, not a parser. Shows VC interest in Telegram B2B tooling. |

### Notable: No Direct VC Funding for "Telegram Channel Parser for Lead Gen"

**No venture-backed startup was found that is explicitly building a Telegram channel parser into a structured lead database for a specific vertical (e.g., manufacturing/sewing).** This is a gap. The funded players in this space are either:
- General CRMs that add Telegram as an input channel (Pepper Cloud, CRMChat)
- Community intent monitors (LeadGuru)
- Infrastructure tools (Apify actors)
- Analytics platforms (TGStat, Telemetr -- see below)

### Adjacent Funded Players (Intent Data / Signal-Based Selling)

| Company | Funding | Relevance |
|---|---|---|
| **Apollo.io** | $100M+ (Series D, 2023) | B2B contact database + intent signals (funding, hiring, expansion). Does NOT use messaging app data. Same end user (managers seeking leads), different data source. |
| **ZoomInfo** | Public (NASDAQ: ZI) | Largest B2B database. No messaging app data. Same end user. |
| **Lusha** | $30M+ | Contact enrichment. No messaging app data. |

These validate the "structured lead database" market but do not compete on the data source (messaging apps).

---

## 3. Telegram Business Tools Ecosystem (Established Players)

### Analytics & Channel Discovery

| Platform | Founded | What They Do | Lead Extraction? | Funding |
|---|---|---|---|---|
| **TGStat** (tgstat.com) | Pre-2017 | Largest Telegram analytics platform. 2M+ channels/groups tracked. Search, benchmarking, real-time metrics, competitor analysis. | No individual lead extraction, but surfaces channels by topic/keyword -- could pivot. | Unclear -- listings on investor databases suggest Series-A / ICO stage, but details are behind paywalls. Russian-founded. |
| **Telemetr** (telemetr.io) | ~2017 | "First" Telegram analytics service. 11M+ channels in database. Deep audience quality analysis, ad campaign tracking, bot/fake follower detection. | No individual lead extraction. Focused on advertiser intelligence. | Unknown. Russian-founded. |

Both TGStat and Telemetr have the **data infrastructure** to pivot into lead extraction. They already index channels, categorize by topic, and track post content. Adding contact extraction and structured output would be a natural extension.

### CRM / Sales Tools

| Platform | Founded | What They Do | Funding |
|---|---|---|---|
| **CRMChat** | 2021 (pivot 2024) | Telegram-native CRM, lead management, multi-account outreach, automation. | $2.5M (Altair VC, Flashpoint) |
| **DISE CRM** | 2024 | AI-native CRM for Telegram B2B. Pipeline management, AI summaries, smart filters. Acquired by Minders. | Acquired (terms undisclosed) |
| **TGDesk / Wadesk** | 2020 | Free Telegram CRM, group scraping, bulk tools. | Unfunded |
| **Pepper Cloud** | 2017 | General CRM with Telegram integration. | Revenue-funded |

### Parsing & Automation Tools (Russian Market)

| Tool | What They Do | Business Model |
|---|---|---|
| **Tegranium** | AI-powered group parsing, lead search by keyword, spam filtering, auto-responder, CRM | Commercial SaaS |
| **TGCParser** | AI audience discovery, 24/7 monitoring, message + author metadata extraction | Open-source / Python-based |
| **A-PARSER** | Universal scraper platform (SEO, e-commerce, Telegram) | Commercial SaaS |
| **TeleParser** | Free Telegram/VK/MAX parser, content parsing, cross-posting | Free |

### Potential Pivot Threats

| Company | Why They Could Pivot |
|---|---|
| **TGStat / Telemetr** | Already have channel indexes and content databases. Adding contact extraction and structured lead output is a natural next step. |
| **Apify** | Already hosts Telegram scraping actors. Could productize a vertical-specific lead database on top of their infrastructure. |
| **CRMChat** | Already builds Telegram-native sales tools. Adding automated channel parsing to their CRM would complete the funnel. |
| **Minders** | Venture builder actively acquiring/building Telegram B2B infrastructure. DISE CRM acquisition signals this thesis. |
| **LeadGuru** | Already monitors communities for intent signals. Extending from Slack/Discord to Telegram channel parsing is adjacent. |

---

## Summary: Competitive Positioning

| Dimension | Landscape Assessment |
|---|---|
| **Direct competitors** | **None found** that do vertical-specific (sewing/manufacturing) Telegram channel parsing into a structured lead database. Closest are Tegranium and TGCParser (general-purpose, not vertical-specific). |
| **Funded competitors** | **None** raising money specifically for this. CRMChat ($2.5M) is the closest funded player but they build a CRM overlay, not a parser/database. |
| **Infrastructure overlap** | Apify actors handle the raw scraping. The gap is the **vertical-specific structuring, tagging, and search layer** on top. |
| **Pivot risk** | Medium. TGStat/Telemetr have the data, CRMChat has the user base, Minders has the thesis. None currently focus on manufacturing/sewing vertical. |
| **Differentiation opportunity** | The vertical focus (Bishkek + Russia sewing/manufacturing) is defensible. No player owns this niche. The value is in the **tagging schema** (location, assortment, contacts) and the **searchable database** -- not the raw parsing. |
| **Geographic moat** | Strong. The Russian-language, CIS-focused nature of the target channels creates a moat against Western players. Russian-language parsers exist but none target this vertical specifically. |

## Связанные разделы
- [[delta|Delta: чем идея уникальна]] — уникальные элементы
- [[what-to-avoid|What to Avoid]] — почему конкуренты провалились
- [[../07-decisions/product-decisions|Product Decisions]] — как дифференцироваться
