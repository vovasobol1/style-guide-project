# Руководство по стилю документации КампусБук

Руководство по стилю для документации сервиса бронирования аудиторий КампусБук. Проект ведется по подходу Docs as Code: правила хранятся в Git, сайт собирает MkDocs, изменения проходят Pull Request, линтинг и автоматическую публикацию.

Сайт руководства: <https://vovasobol1.github.io/style-guide-project/>

## Структура репозитория

| Путь | Что лежит |
| --- | --- |
| `docs/` | Страницы руководства в Markdown |
| `docs/rules/` | Разделы с правилами |
| `docs/doc-templates/` | Шаблоны документов |
| `docs/examples/` | Документы, на которых проверено руководство |
| `scripts/stylecheck.py` | Проверка правил стиля, которые можно проверить автоматически |
| `scripts/stop_words.txt` | Список нежелательных слов для `stylecheck` |
| `mkdocs.yml` | Настройки сайта и навигация |
| `.markdownlint-cli2.jsonc` | Настройки `markdownlint` |
| `.github/workflows/docs.yml` | Проверка, сборка и публикация сайта |

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm ci

npm run lint
mkdocs serve
```

Сайт откроется по адресу `http://127.0.0.1:8000`.

## Как внести изменения

Порядок работы с ветками, требования к коммитам и процесс ревью описаны в файле [CONTRIBUTING.md](CONTRIBUTING.md).
