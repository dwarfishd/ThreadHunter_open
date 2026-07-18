[[README|← Назад к Research]]

# What to Avoid

## Где у конкурентов болит и почему стартапы провалились

### 1. Platform Dependency Risk (API Telegram)

**Источник:** accelerators-landscape.md, social-trends.md

Чатовые стартапы волны 2016-2018 (Facebook Messenger, Telegram, Slack) массово погибали из-за изменений API платформ. Telegram исторически пермиссивен, но это может измениться.

**Конкретные риски:**
- Изменение rate limits для пользовательских аккаунтов (сейчас ~30-50 запросов/сек для чтения)
- Блокировка аккаунтов за bulk-скрапинг (временные баны при массовой выгрузке)
- Изменение ToS в отношении scraping (Telegram — серая зона, но не защищён)
- Закрытие доступа к приватным каналам (требуют инвайт-линк и членство)

**Как митигировать:** добавлять задержки между запросами, ротировать сессии, не превышать rate limits. Коммерческие инструменты (Xreacher, Apify) уже решают это через прокси и прогрев аккаунтов.

### 2. ToS / Legal Risk

**Источник:** social-trends.md, accelerators-landscape.md

Скрапинг данных operates в compliance gray zone. B2B-скраперы сталкивались с GDPR, LinkedIn v. hiQ litigation, блокировками.

**Конкретные риски:**
- Россия/СНГ: законы о защите данных, отношение регуляторов к сбору бизнес-контактов
- Telegram может ужесточить политику в отношении коммерческого использования API
- «Permission-aware workflows» — selling point коммерческих инструментов. Инструмент, ориентированный на публично размещённую бизнес-информацию (фабрики, которые сами рекламируются), имеет более сильную compliance-позицию, чем массовый DM-спам

**Как митигировать:** парсить только публичные каналы, где бизнес сам публикует контакты. Не DM-спам инструмент, а база для легитимного бизнес-поиска.

### 3. Отсутствие острого Buyer Pain

**Источник:** accelerators-landscape.md, saas-landscape.md

B2B-продукты проваливаются, когда решают проблему, которую покупатель не ощущает остро (Failory: «Building a Nutrition B2B SaaS That No One Demanded»).

**Конкретный риск:** если швейные менеджеры могут найти фабрики через Google, сарафанное радио или существующие директории — парсер решает nice-to-have, а не must-have.

**Как митигировать:** валидировать, что текущий процесс поиска фабрик действительно болезненный. Продавать не «парсер», а «база активных контактов фабрик, которые прямо сейчас рекламируют свои услуги».

### 4. Data Cleaning Hell

**Источник:** social-trends.md, saas-landscape.md

Сырые данные Telegram требуют значительной очистки перед использованием. Это #1 cited challenge.

**Конкретные проблемы:**
- Только публичная метадата (юзернеймы, имена, last-seen buckets, био). Глубокая персональная информация редко доступна
- Тексты постов неструктурированы, на русском/кыргызском, с сленгом и сокращениями
- Дедупликация контактов (один бизнес в нескольких каналах, разные номера)
- spaCy Russian NER (`ru_core_news_lg`) менее точен, чем английский. Ожидать ручную rule-based экстракцию alongside NER

**Как митигировать:** investing в domain-specific tagging schema — это и есть моат. Без структурирования сырые данные бесполезны.

### 5. Monetization Friction

**Источник:** accelerators-landscape.md, saas-landscape.md

B2B-lead-data инструменты struggle с ценообразованием:
- Per-lead модель создаёт misaligned incentives (покупатель не хочет платить за каждый лид)
- Subscription модель требует continuous value
- Marketplace модель требует two-sided liquidity

**Как митигировать:** модель подписки ($10-50/мес) за доступ к обновляемой базе — чистый SaaS, не per-lead, не marketplace.

### 6. Рыночный размер (TAM)

**Источник:** accelerators-landscape.md

Нишевый инструмент для Бишкека/России/швейной индустрии имеет естественно ограниченный TAM. YC ожидает $1B+ narratives.

**Конкретный риск:** это скорее bootstrapped или regional-VC play, а не YC-scale компания.

**Как митигировать:** начать с одной вертикали (швейная), доказать PMF, затем расширять на смежные (обувная, мебельная, промышленное шитьё).

### 7. Постмортемы: конкретные грабли

| Постмортем | Источник | Урок для проекта |
|---|---|---|
| «Spending $95K to Build a Product With No Demand» | Failory | Не строить до валидации спроса. Проверить, что менеджеры хотят структурированные лиды до полного pipeline |
| «Building a Nutrition B2B SaaS That No One Demanded» | Failory | B2B-продукт должен решать острую проблему. Валидировать pain point поиска фабрик |
| «Lost in the Idea Maze After Joining YC & Raising $462K» | Failory | Не овер-инженерить. Scope tightly to one niche (швейная в Бишкеке), resist expansion до PMF |
| «How Crypto Hype Misled A Startup» | Failory | Не гнаться за трендами (AI-агент, LLM) ради новизны. Driver — реальные pain points менеджеров |

## Связанные разделы
- [[../11-risks/technical|Technical Risks]] — platform dependency risk ↔ local-first как антидот
- [[../11-risks/product|Product Risks]] — отсутствие buyer pain ↔ action-oriented принцип
- [[../11-risks/strategic|Strategic Risks]] — TAM ограничения ↔ one-person-company подход
- [[../11-risks/operational|Operational Risks]] — data cleaning hell ↔ proactive автоматизация
