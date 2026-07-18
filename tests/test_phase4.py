"""Phase 4 tests: contact extraction, tag classification, pipeline."""

import pytest

from threadhunter.db import init_db
from threadhunter.extract.contacts import (
    ExtractedContact,
    _normalize_phone,
    extract_contacts,
)
from threadhunter.extract.tags import ExtractedTag, classify_tags
from threadhunter.pipeline import process_channel, process_post

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RULES_YAML = """\
location:
  - Бишкек
  - Ош
  - Москва
  - Санкт-Петербург
  - Новосибирск
  - Екатеринбург
  - Алматы
assortment:
  - футболки
  - куртки
  - спецодежда
  - джинсы
  - платья
offer_type:
  - pattern: "ищем"
  - pattern: "предлагаем"
  - pattern: "требуется"
  - pattern: "на заказ"
  - pattern: "есть в наличии"
  - pattern: "шьём"
  - pattern: "шьем"
"""


@pytest.fixture
def db(monkeypatch, tmp_path):
    """Set up a temporary database."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("TH_DB", str(db_path))
    init_db(db_path)
    return db_path


@pytest.fixture(autouse=True)
def _clear_rules_cache():
    """Clear the tag-rules cache between tests."""
    import threadhunter.extract.tags as tags_mod

    tags_mod._rules_cache = None


@pytest.fixture
def rules_dir(tmp_path, monkeypatch):
    """Create data/tags-rules.yaml in tmp_path and chdir there."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "tags-rules.yaml").write_text(RULES_YAML, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def sample_post(db):
    """Insert a sample post and return its id."""
    from threadhunter.db import get_connection

    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO channels (telegram_id) VALUES (?)",
            ("test_channel",),
        )
        conn.execute(
            "INSERT INTO posts (channel_id, telegram_post_id, raw_text) "
            "VALUES (1, '100', 'Test post')"
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM posts WHERE telegram_post_id = '100'"
        ).fetchone()
        return row["id"]
    finally:
        conn.close()


# ===================================================================
# Contact extraction (15+ examples)
# ===================================================================


class TestExtractContacts:
    """Contact extraction from raw post text."""

    def test_phone_kg_with_spaces(self):
        contacts = extract_contacts("Звоните: +996 555 123 456")
        phones = [c for c in contacts if c.type == "phone"]
        assert phones == [ExtractedContact(type="phone", value="+996555123456")]

    def test_phone_ru_with_parens_dashes(self):
        contacts = extract_contacts("Тел: +7(999)123-45-67")
        phones = [c for c in contacts if c.type == "phone"]
        assert phones == [ExtractedContact(type="phone", value="+79991234567")]

    def test_phone_ru_domestic_8(self):
        contacts = extract_contacts("Звоните 8 800 555 35 35")
        phones = [c for c in contacts if c.type == "phone"]
        assert phones == [ExtractedContact(type="phone", value="+78005553535")]

    def test_phone_kg_compact(self):
        contacts = extract_contacts("+996555123456")
        phones = [c for c in contacts if c.type == "phone"]
        assert phones == [ExtractedContact(type="phone", value="+996555123456")]

    def test_phone_ru_intl(self):
        contacts = extract_contacts("Наш номер: +7 999 123 45 67")
        phones = [c for c in contacts if c.type == "phone"]
        assert phones == [ExtractedContact(type="phone", value="+79991234567")]

    def test_telegram_username(self):
        contacts = extract_contacts("Пишите @factory_bishkek")
        tg = [c for c in contacts if c.type == "telegram"]
        assert tg == [ExtractedContact(type="telegram", value="factory_bishkek")]

    def test_email(self):
        contacts = extract_contacts("Почта: info@factory.kg")
        emails = [c for c in contacts if c.type == "email"]
        assert emails == [ExtractedContact(type="email", value="info@factory.kg")]

    def test_telegram_rejects_cyrillic(self):
        contacts = extract_contacts("Пишите @иванов")
        tg = [c for c in contacts if c.type == "telegram"]
        assert tg == []

    def test_multiple_contacts(self):
        text = (
            "Швейная фабрика в Бишкеке. "
            "Тел: +996 555 123 456, @factory, info@factory.kg"
        )
        contacts = extract_contacts(text)
        assert len(contacts) == 3
        types = {c.type for c in contacts}
        assert types == {"phone", "telegram", "email"}

    def test_no_contacts(self):
        contacts = extract_contacts("Просто обычный текст без контактов")
        assert contacts == []

    def test_empty_text(self):
        assert extract_contacts("") == []
        assert extract_contacts(None) == []  # type: ignore[arg-type]

    def test_dedup_same_contact_in_text(self):
        contacts = extract_contacts(
            "+996 555 123 456 и ещё раз +996555123456"
        )
        phones = [c for c in contacts if c.type == "phone"]
        assert len(phones) == 1

    def test_phone_with_dots(self):
        contacts = extract_contacts("Тел: +996.555.123.456")
        phones = [c for c in contacts if c.type == "phone"]
        assert len(phones) == 1
        assert phones[0].value == "+996555123456"

    def test_multiple_phones(self):
        text = "Первый: +996 555 111 222, второй: +7 999 333 44 55"
        contacts = extract_contacts(text)
        phones = [c for c in contacts if c.type == "phone"]
        assert len(phones) == 2
        values = {p.value for p in phones}
        assert "+996555111222" in values
        assert "+79993334455" in values

    def test_real_ad_post(self):
        text = (
            "Ищем швею на производство курток в Бишкеке. "
            "ЗП от 30000 сом. Тел: +996 700 123 456, @hr_factory"
        )
        contacts = extract_contacts(text)
        assert len(contacts) == 2
        phones = [c for c in contacts if c.type == "phone"]
        assert phones[0].value == "+996700123456"
        tg = [c for c in contacts if c.type == "telegram"]
        assert tg[0].value == "hr_factory"

    def test_contact_types_sorted(self):
        contacts = extract_contacts(
            "@user info@test.com +996 555 123 456"
        )
        assert contacts[0].type == "email"
        assert contacts[1].type == "phone"
        assert contacts[2].type == "telegram"


class TestNormalizePhone:
    """Phone number normalisation edge cases."""

    def test_kg_format(self):
        assert _normalize_phone("+996 555 123 456") == "+996555123456"

    def test_ru_intl(self):
        assert _normalize_phone("+7 999 123 45 67") == "+79991234567"

    def test_ru_domestic(self):
        assert _normalize_phone("8 800 555 35 35") == "+78005553535"

    def test_too_short(self):
        assert _normalize_phone("+12345") is None

    def test_compact_kg(self):
        assert _normalize_phone("+996555123456") == "+996555123456"

    def test_compact_ru(self):
        assert _normalize_phone("+79991234567") == "+79991234567"


# ===================================================================
# Tag classification
# ===================================================================


class TestClassifyTags:
    """Rules-based tag classification."""

    def test_location_bishkek(self, rules_dir):
        tags = classify_tags("Швейная мастерская в Бишкеке")
        locations = [t for t in tags if t.type == "location"]
        assert locations == [ExtractedTag(type="location", value="Бишкек")]

    def test_assortment_kurtki(self, rules_dir):
        tags = classify_tags("Шьём куртки оптом")
        assortment = [t for t in tags if t.type == "assortment"]
        assert len(assortment) == 1
        assert assortment[0].value == "куртки"

    def test_offer_type_ishchem(self, rules_dir):
        tags = classify_tags("Ищем швею с опытом")
        offer = [t for t in tags if t.type == "offer_type"]
        assert len(offer) == 1
        assert offer[0].value == "ищем"

    def test_multiple_tags(self, rules_dir):
        tags = classify_tags("Ищем швею, Бишкек")
        assert len(tags) == 2
        types = {t.type for t in tags}
        assert types == {"location", "offer_type"}

    def test_no_tags(self, rules_dir):
        tags = classify_tags("Просто обычный текст")
        assert tags == []

    def test_empty_text(self, rules_dir):
        assert classify_tags("") == []
        assert classify_tags(None) is not None  # should not crash

    def test_assortment_dzhinsy(self, rules_dir):
        tags = classify_tags("Шьем джинсы на заказ. Бишкек")
        assortment = [t for t in tags if t.type == "assortment"]
        assert len(assortment) == 1
        assert assortment[0].value == "джинсы"

    def test_location_moscow(self, rules_dir):
        tags = classify_tags("Производство спецодежды, Москва")
        locations = [t for t in tags if t.type == "location"]
        assert any(t.value == "Москва" for t in locations)

    def test_offer_type_nazakaz(self, rules_dir):
        tags = classify_tags("Пошив платьев на заказ")
        offer = [t for t in tags if t.type == "offer_type"]
        assert any(t.value == "на заказ" for t in offer)

    def test_full_ad(self, rules_dir):
        text = "Предлагаем пошив футболки оптом, Ош, +996 555 123 456"
        tags = classify_tags(text)
        types = {t.type for t in tags}
        assert "location" in types
        assert "assortment" in types
        assert "offer_type" in types

    def test_tags_sorted_by_type(self, rules_dir):
        tags = classify_tags("Ищем швею, Бишкек, куртки")
        type_order = [t.type for t in tags]
        assert type_order == sorted(type_order)


# ===================================================================
# Pipeline integration
# ===================================================================


class TestPipeline:
    """Pipeline orchestrator tests."""

    def test_process_post_saves_contacts(self, db, rules_dir, sample_post):
        process_post(sample_post, "Звоните: +996 555 123 456, @factory")
        from threadhunter.db import get_connection

        conn = get_connection()
        try:
            contacts = conn.execute(
                "SELECT type, value FROM contacts WHERE post_id = ? "
                "ORDER BY type",
                (sample_post,),
            ).fetchall()
            assert len(contacts) == 2
            assert contacts[0]["type"] == "phone"
            assert contacts[0]["value"] == "+996555123456"
            assert contacts[1]["type"] == "telegram"
            assert contacts[1]["value"] == "factory"
        finally:
            conn.close()

    def test_process_post_saves_tags(self, db, rules_dir, sample_post):
        process_post(sample_post, "Ищем швею, Бишкек, куртки")
        from threadhunter.db import get_connection

        conn = get_connection()
        try:
            tags = conn.execute(
                "SELECT type, value FROM tags WHERE post_id = ? ORDER BY type",
                (sample_post,),
            ).fetchall()
            assert len(tags) >= 2
            types = {t["type"] for t in tags}
            assert "location" in types
            assert "offer_type" in types
        finally:
            conn.close()

    def test_process_post_none_text(self, db, sample_post):
        process_post(sample_post, None)
        from threadhunter.db import get_connection

        conn = get_connection()
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM contacts WHERE post_id = ?",
                (sample_post,),
            ).fetchone()[0]
            assert count == 0
        finally:
            conn.close()

    def test_process_post_empty_text(self, db, sample_post):
        process_post(sample_post, "")
        from threadhunter.db import get_connection

        conn = get_connection()
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM contacts WHERE post_id = ?",
                (sample_post,),
            ).fetchone()[0]
            assert count == 0
        finally:
            conn.close()

    def test_dedup_same_post(self, db, rules_dir, sample_post):
        text = "+996 555 123 456"
        process_post(sample_post, text)
        process_post(sample_post, text)
        from threadhunter.db import get_connection

        conn = get_connection()
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM contacts WHERE post_id = ?",
                (sample_post,),
            ).fetchone()[0]
            assert count == 1
        finally:
            conn.close()

    def test_same_contact_different_posts(self, db, rules_dir):
        from threadhunter.db import get_connection

        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO channels (telegram_id) VALUES (?)",
                ("ch1",),
            )
            conn.execute(
                "INSERT INTO posts (channel_id, telegram_post_id, raw_text) "
                "VALUES (1, '200', '+996 555 123 456')"
            )
            conn.execute(
                "INSERT INTO posts (channel_id, telegram_post_id, raw_text) "
                "VALUES (1, '201', '+996 555 123 456')"
            )
            conn.commit()
        finally:
            conn.close()

        process_post(1, "+996 555 123 456")
        process_post(2, "+996 555 123 456")

        conn = get_connection()
        try:
            count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
            assert count == 2  # same value, different posts → 2 rows
        finally:
            conn.close()

    def test_process_channel_returns_count(self, db, rules_dir):
        from threadhunter.db import get_connection

        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO channels (telegram_id) VALUES (?)",
                ("ch_test",),
            )
            conn.execute(
                "INSERT INTO posts (channel_id, telegram_post_id, raw_text) "
                "VALUES (1, '300', 'Текст +996 555 111 222')"
            )
            conn.execute(
                "INSERT INTO posts (channel_id, telegram_post_id, raw_text) "
                "VALUES (1, '301', 'Другой текст')"
            )
            conn.commit()
        finally:
            conn.close()

        count = process_channel(1)
        assert count == 2
