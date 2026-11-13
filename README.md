# binateam.site

Сайт Bina Team: https://binateam.site

- `website/` — страницы, тексты и данные сайта (`website/data/*.json`: обновления, продукты, планы, статус).
- `scripts/build_site.py` — сборка в `_site/` и проверка ссылок: `python3 scripts/build_site.py --check`.
- `PRIVACY.md`, `TERMS.md` — политика конфиденциальности и условия sBoard (те же тексты, что в приложении).
- Публикация: при пуше в `main` GitHub Actions собирает сайт и выкладывает его в GitHub Pages.
- Релизы этого репозитория — файлы для установки sBoard (Release.apk, Release.aab).

Один раз в настройках репозитория: Settings → Pages → Source: GitHub Actions, Custom domain: `binateam.site`, Enforce HTTPS.
