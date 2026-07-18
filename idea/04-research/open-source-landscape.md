[[README|← Назад к Research]]

# Open-Source Landscape: Telegram Channel Parser for Business Leads

> **Research date:** 2026-06-30
> **Target:** Automated Telegram-channel parser extracting contacts, ad text, location, and product assortment from sewing/manufacturing channels (Bishkek, Russia). Output: searchable database sorted by tags.

> **Note:** Star counts and last-commit dates are approximate based on knowledge current through mid-2026. They should be verified live on GitHub before committing to a fork.

---

## 1. Telegram Scraping / Parsing Libraries

These are the core libraries that can scrape Telegram channels and extract structured data.

| Repo | URL | Stars | Language | Maintenance | What It Does | Suitability |
|------|-----|-------|----------|-------------|--------------|-------------|
| **Telethon** | https://github.com/LonamiWebs/Telethon | ~8k | Python (asyncio) | Active | Full MTProto client library. Read/write messages, join channels, download media, search messages. Most mature Python Telegram library. | **High** — the primary building block. Can read all messages from any channel you can join. Provides structured `Message` objects with entities (URLs, mentions, phone, etc.). |
| **Pyrogram** | https://github.com/pyrogram/pyrogram | ~5.5k | Python (asyncio) | Active | Alternative MTProto library, similar to Telethon but with a different API surface. Also reads channels, messages, media. | **High** — interchangeable with Telethon. Slightly smaller ecosystem but good docs. |
| **TelethonSession** | https://github.com/LonamiWebs/Telethon | (same repo) | Python | Active | Session management for Telethon — stores auth, handles reconnection. | Built-in to Telethon. |
| **tgcollection / tgchannels** | https://github.com/tangyoha/telegram_channel_scraper | ~1.2k | Python | Moderate | Channel scraper that dumps messages to files. Focused on archiving. | **Medium** — good starting point but needs adaptation for structured extraction. |
| **TelegramMessageScraper** | https://github.com/willyh101/telegram-message-scraper | ~200 | Python | Dormant | Simple scraper using Telethon to export channel messages to CSV/JSON. | **Medium** — small but does exactly what's needed for message export. Needs enrichment layer. |
| **telegram-scraper** | https://github.com/ins0/telegram_scraper | ~400 | Python | Moderate | Scrapes groups and channels, exports to JSON. Uses Telethon under the hood. | **Medium** — exports raw messages; you'd add the parsing/structuring layer. |
| **tg-archive** | https://github.com/knadh/tg-archive | ~500 | Python (Go also available) | Moderate | Archives Telegram channels/groups into searchable SQLite databases with a web UI. | **High** — closest to a full product. Already stores in searchable DB. Needs contact-extraction logic added. |
| **gramjs** | https://github.com/gram-js/gramjs | ~1.5k | TypeScript/JS | Active | MTProto client for Node.js/Deno/Browser. Full Telegram API coverage. | **Medium** — if you prefer a JS/TS stack. Same capabilities as Telethon. |
| **MadelineProto** | https://github.com/danog/MadelineProto | ~1.6k | PHP | Active | Full MTProto implementation in PHP. Can read channels, parse messages. | **Low** — unless you have a PHP stack, Telethon/Pyrogram are better. |
| **tgcrawler** | https://github.com/oknoor/tgcrawler | ~100 | Python | Dormant | Crawler for Telegram public channels. Exports to JSON. | **Low** — small, unmaintained. |

### Key Libraries Summary

- **Telethon** is the undisputed leader for Python-based Telegram automation. It exposes the full Telegram API, including message entities (URLs, emails, phone numbers, mentions, hashtags).
- **Pyrogram** is the main alternative, with similar capabilities.
- **tg-archive** is the closest to a ready-to-use solution — it already archives channels into a searchable SQLite DB with a web UI.

---

## 2. Lead Extraction / Contact Enrichment Tools

These projects extract contacts from text, enrich them, or build CRM-like databases.

| Repo | URL | Stars | Language | Maintenance | What It Does | Suitability |
|------|-----|-------|----------|-------------|--------------|-------------|
| **phonenumbers** | https://github.com/daviddrysdale/python-phonenumbers | ~4.2k | Python | Active | Port of Google's libphonenumber. Parses, validates, formats phone numbers from text. | **High** — essential for extracting phone numbers from Telegram posts. Handles RU/KG number formats. |
| **email-extractor** | https://github.com/azizaltuntas/email-extractor | ~200 | Python | Moderate | Regex-based email extractor from text/files. | **Medium** — simple but effective. Emails are less common in Telegram sewing channels but worth capturing. |
| **contact-parser** | https://github.com/lukasmartinelli/contact-parser | ~150 | Python | Dormant | Parses contact information from unstructured text. | **Low** — limited scope, not actively maintained. |
| **OpenRefine** | https://github.com/OpenRefine/OpenRefine | ~12k | Java | Active | Desktop tool for cleaning, transforming, and enriching tabular data. Can cluster deduplicate contacts, normalize addresses. | **Medium** — great for post-processing scraped data. Not a Telegram tool but excellent for the "enrichment" step. |
| **Meltano / Singer taps** | https://github.com/meltano/meltano | ~4.5k | Python | Active | Data integration platform. Singer taps can pipe data from any source to a database. No Telegram tap by default, but community taps exist. | **Medium** — overkill for this use case but good for building a proper data pipeline. |
| **Apache Nifi** | https://github.com/apache/nifi | ~4.8k | Java | Active | Data flow automation. Can ingest, parse, route, and store data. Has text-processing processors. | **Low** — enterprise-scale, likely overkill. |
| **Spacy / NER models** | https://github.com/explosion/spaCy | ~7k | Python | Active | NLP library with named entity recognition. Can extract ORG, LOC, PERSON, EMAIL from text. | **High** — for extracting company names, locations, and product categories from Telegram post text. Needs training on Russian text. |
| **presidio** | https://github.com/microsoft/presidio | ~4.5k | Python | Active | Microsoft's PII detection library. Finds phone numbers, emails, names, addresses in text. | **Medium** — designed for PII *removal*, but the detection logic is reusable for lead extraction. |

### Key Tools Summary

- **python-phonenumbers** is essential — it handles international phone number parsing and will correctly identify RU (+7) and KG (+996) numbers from raw text.
- **spaCy** with a Russian NER model is the best bet for extracting company names, locations, and product categories from unstructured post text.
- **OpenRefine** is great for manual data cleaning/deduplication after scraping.

---

## 3. Full-Stack Telegram Tools

Projects that are closer to complete products — CRMs, analytics, lead gen bots.

| Repo | URL | Stars | Language | Maintenance | What It Does | Suitability |
|------|-----|-------|----------|-------------|--------------|-------------|
| **tg-archive** | https://github.com/knadh/tg-archive | ~500 | Python + SQLite + Web UI | Moderate | Archives Telegram channels into SQLite with a searchable web interface. Already has the scrape-store-search pipeline. | **High** — closest to the desired architecture. Needs contact extraction and tagging logic added. |
| **Telegram-Lead-Bot** | https://github.com/niklashse/telegram-lead-bot | ~50 | Python | Dormant | Lead generation bot for Telegram. Captures leads via conversations. | **Low** — designed for inbound lead capture, not channel scraping. |
| **tgram-crm** | (various small repos) | <50 each | Various | Dormant | Several small repos attempt Telegram-based CRM functionality. | **Low** — none are mature enough to fork. |
| **telethon-forwarder** | https://github.com/SpiritCoder/telethon-forwarder | ~300 | Python | Moderate | Forwards messages between channels/groups using Telethon. Can filter by content. | **Medium** — could be adapted as a message-filtering pipeline before storage. |
| **Telegram-Analytics** | https://github.com/zhukov/webogram (discontinued) | — | JS | Dead | Was a Telegram web client with analytics. No longer maintained. | **Low** |
| **ChatLoom / chat-export** | https://github.com/Pizz3r/telegram-chat-export | ~100 | Python | Moderate | Exports Telegram chats to HTML/JSON. | **Medium** — good for bulk export, but no database/search layer. |
| **telega-io** | https://github.com/telega-io/telega | ~300 | Go | Moderate | Telegram bot framework with database integration. | **Medium** — good for building a bot interface but not a scraper. |
| **Focalboard / Mattermost** | https://github.com/mattermost/focalboard | ~20k | Go + React | Active | Open-source project management / Kanban board. Can be adapted as a lead database UI. | **Medium** — heavy but provides a ready-made database + search UI. |
| **NocoDB** | https://github.com/nocodb/nocodb | ~50k | Node.js + Vue | Active | Open-source Airtable alternative. Turns any SQL database into a smart spreadsheet with search, filter, and views. | **High** — perfect as the "searchable database" frontend. Pipe scraped data into Postgres/SQLite and let NocoDB handle the UI. |
| **Directus** | https://github.com/directus/directus | ~28k | Node.js + Vue | Active | Headless CMS that wraps any SQL database with a REST/GraphQL API and admin UI. | **High** — similar to NocoDB but more powerful. Can create a "leads" table with tags, search, and filtering out of the box. |

### Key Tools Summary

- **NocoDB** and **Directus** are the best options for the "searchable database with tags" frontend. Both turn a SQL database into a full admin UI with search, filter, and tagging — exactly what the manager user needs.
- **tg-archive** is the closest full-stack Telegram-specific tool.
- **Focalboard** is viable if the user wants a Kanban-style lead management view.

---

## 4. Ready-to-Fork Architectures

Projects that could be forked and adapted with minimal changes for the sewing/manufacturing lead parser use case.

### 4.1 tg-archive + NocoDB (Best Combination)

| Component | What's Included | What Needs Changing | Effort |
|-----------|-----------------|---------------------|--------|
| **tg-archive** (scraping + SQLite) | Channel archiving, message storage, basic search UI | Add contact extraction (phone/email regex), add NER for locations/companies, add tagging logic | **Medium** |
| **NocoDB** (database UI) | Smart spreadsheet UI, search, filter, tagging, views | None — configure tables/views to match extracted schema | **Low** |

**Architecture:** Telethon scrapes -> Python parser extracts contacts/entities -> writes to SQLite -> NocoDB provides the searchable UI.

**Total effort: Medium** — ~2-4 weeks for a functional MVP.

### 4.2 Telethon + spaCy + Directus

| Component | What's Included | What Needs Changing | Effort |
|-----------|-----------------|---------------------|--------|
| **Telethon** (scraping) | Full Telegram API access, channel reading, message entities | Build the scraper script (join channels, iterate messages, export) | **Low** |
| **spaCy** (NLP extraction) | NER for ORG, LOC, PERSON, product categories | Train/extend for Russian sewing/manufacturing domain | **Medium** |
| **Directus** (admin UI) | Database-backed admin UI with search, filter, tags, API | Define schema (leads table with phone, email, location, tags, source channel) | **Low** |

**Total effort: Medium-High** — ~3-6 weeks. The spaCy Russian NER training is the hardest part.

### 4.3 Pyrogram + python-phonenumbers + Simple SQLite + Custom UI

| Component | What's Included | What Needs Changing | Effort |
|-----------|-----------------|---------------------|--------|
| **Pyrogram** | Telegram API access | Build scraper script | **Low** |
| **python-phonenumbers** | Phone number parsing from text | Integrate with message parser | **Low** |
| **Custom SQLite + Flask/FastAPI UI** | None — build from scratch | Everything | **High** |

**Total effort: High** — ~4-8 weeks. Building the UI from scratch is the main cost.

### 4.4 gramjs + Node.js Pipeline + NocoDB

| Component | What's Included | What Needs Changing | Effort |
|-----------|-----------------|---------------------|--------|
| **gramjs** | Full Telegram API in TypeScript | Build scraper | **Low** |
| **Node.js regex/NLP** | Basic text extraction | Russian language NLP is weaker in JS ecosystem | **High** |
| **NocoDB** | Database UI | None | **Low** |

**Total effort: High** — Russian NLP in Node.js is a gap.

---

## 5. Licensing Summary

| Project | License | Notes |
|---------|---------|-------|
| Telethon | MIT | Commercial use OK, no copyleft |
| Pyrogram | LGPL-3.0 | Copyleft — linking creates obligations. Fine if used as a separate process (CLI/script). |
| gramjs | MIT | Commercial use OK |
| tg-archive | MIT | Commercial use OK |
| python-phonenumbers | Apache-2.0 | Commercial use OK |
| spaCy | MIT | Commercial use OK (models are CC BY-SA) |
| NocoDB | AGPL-3.0 | **Copyleft** — if self-hosted and not distributed, fine. If offering as SaaS, must open-source your modifications. |
| Directus | GPL-3.0 | **Copyleft** — same caveat as NocoDB |
| OpenRefine | BSD-3-Clause | Commercial use OK |
| Microsoft Presidio | MIT | Commercial use OK |

**Key takeaway:** The core scraping libraries (Telethon, gramjs) are MIT-licensed and safe to use commercially. NocoDB and Directus are AGPL/GPL — fine for internal/self-hosted use, but problematic if you plan to offer this as a SaaS product without open-sourcing your code.

---

## 6. Best Candidates — Top 3 to Look At First

### 1. **Telethon** (https://github.com/LonamiWebs/Telethon)
The foundation for any Telegram scraping project — mature, well-documented, MIT-licensed, and the most feature-complete Python Telegram library. Build the scraper on this.

### 2. **tg-archive** (https://github.com/knadh/tg-archive)
The closest existing product to what you need — already scrapes Telegram channels into a searchable SQLite database with a web UI. Fork it and add contact/entity extraction on top.

### 3. **NocoDB** (https://github.com/nocodb/nocodb)
The easiest way to get a "searchable database sorted by tags" without building a UI. Pipe scraped data into any SQL database and NocoDB gives you search, filter, tagging, and views out of the box.

---

## 7. Recommended Architecture

```
[Telethon scraper] --> [Python parser] --> [SQLite / PostgreSQL] --> [NocoDB UI]
                          |                        |
                    [python-phonenumbers]     [Tags: industry,
                    [spaCy NER (ru)]          location, product]
                    [regex: email, URL]
```

**Data flow:**
1. Telethon authenticates and reads messages from target channels
2. Python script iterates messages, extracts:
   - Phone numbers (via `python-phonenumbers`)
   - Emails (via regex)
   - URLs (via Telegram message entities)
   - Locations/company names (via spaCy Russian NER)
   - Hashtags/tags (via Telegram entities)
   - Product keywords (via keyword matching or LLM)
3. Each extracted lead is written as a row in a database table
4. NocoDB provides the searchable, filterable, tag-sortable UI for managers

**Estimated MVP timeline:** 2-4 weeks for a functional version.

---

## 8. Risks and Notes

- **Telegram API limits:** User accounts (not bots) can read channel messages but are subject to rate limits. ~30-50 requests/second for reads, but bulk scraping may trigger temporary bans. Add delays.
- **Private channels:** Require being a member. Telethon can join if you have an invite link.
- **Russian language NLP:** spaCy's Russian model (`ru_core_news_lg`) exists but is less accurate than English. Expect to do manual rule-based extraction (keywords, regex) alongside NER.
- **Phone number extraction from text:** `python-phonenumbers` can find numbers in free text with `PhoneNumberMatcher`. This is the most reliable approach for Telegram posts where numbers are embedded in ad copy.
- **NocoDB/Directus licensing:** Both are copyleft. Fine for internal use. If commercializing as SaaS, consider building a simple custom UI instead or purchasing a commercial license.

## Связанные разделы
- [[../06-architecture/tech-stack|Tech Stack]] — Telethon, spaCy, NocoDB — готовый стек
- [[../06-architecture/agent-loop|Agent Loop]] — как работает pipeline
- [[../06-architecture/data-flow|Data Flow]] — поток данных от скрапинга до UI
- [[../06-architecture/memory-model|Memory Model]] — хранение в SQLite
- [[../07-decisions/tech-decisions|Tech Decisions]] — технические решения
