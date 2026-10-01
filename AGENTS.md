# Project notes (ANJUMANEFAIZANERABBANI website)

- Django 5.2 project `config`; apps: core, videos, events, gallery, contact. Vanilla JS/CSS only (no build step).
- Windows dev shell is PowerShell; venv at `.venv` → use `.\.venv\Scripts\python`.
- Setup: `.\.venv\Scripts\python manage.py migrate` then `seed_demo` (reads photos from `asserts/`).
- Verify: `.\.venv\Scripts\python manage.py test` (25 tests) and `manage.py check --deploy` with `DEBUG=False`.
- Run: `.\.venv\Scripts\python manage.py runserver` → site at `/`, admin at `/manage/` (`/admin/` is intentionally 404).
- Home page data is cached (`core.utils.HOME_CACHE_KEY`) and cleared by signals in `core/signals.py` on content saves.
- Keep `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"` — YouTube embeds fail (Error 153) without a referrer.
