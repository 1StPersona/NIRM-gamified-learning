# Адаптивная геймификация в обучении программированию (НИРМ)

[![CI](https://github.com/1StPersona/NIRM-gamified-learning/actions/workflows/ci.yml/badge.svg)](https://github.com/1StPersona/NIRM-gamified-learning/actions/workflows/ci.yml)

Научно-исследовательская работа магистранта Захарова Д. В. (Satbayev University). Тема: разработка платформы для обучения программированию с адаптивной геймификацией и оценка её влияния на вовлечённость и результаты студентов.

Репозиторий содержит прототип модели геймификации (глава 2 диссертации), сервис, который её исполняет, тесты, эксперименты и тексты практических заданий курса CSE7942 Research Project.

## Исследовательские вопросы

- **RQ1.** Повышает ли геймификация вовлечённость (индекс EI) по сравнению с курсом без игровых элементов?
- **RQ2.** Даёт ли адаптивная геймификация (АГ) больший прирост результатов, чем статическая (СГ)?
- **RQ3.** Точнее ли рейтинг Эло прогнозирует успех решения, чем статические метки сложности?

Дизайн: три условия (К / СГ / АГ), около 90 студентов, ANCOVA по претесту, поправка Холма. Подробно в [лекции 7](docs/lectures/lecture-7.md).

## Структура

```
gamification/            модель: EI (metrics), XP/уровни/значки (progression), Эло и выбор задачи (adaptive)
services/gamification_api FastAPI-сервис: POST /events/submission, GET /leaderboard, GET /health
tests/                   35 тестов pytest (один требует Redis)
simulation/              калибровка шага K на синтетических студентах
bench/                   микро- и нагрузочные бенчмарки, результаты и графики
docs/lectures/           задания к лекциям 1–9 (Markdown)
docs/word/               те же задания в Word (оформление КазНИТУ)
```

## Как воспроизвести

Нужен Python 3.13 (версии зависимостей зафиксированы в `requirements.txt`).

```bash
git clone https://github.com/1StPersona/NIRM-gamified-learning.git
cd NIRM-gamified-learning
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

make test        # 34 теста; +1 с Redis: REDIS_URL=redis://127.0.0.1:6379/0 make test
make simulate    # калибровка K (seed 42, 5 повторов) → bench/results/simulation.csv
make micro       # микробенчмарки → bench/results/micro.json
```

Нагрузочный тест (сервис и Redis в Docker):

```bash
docker compose up -d --build     # Redis 7.0 + сервис на :8000
make load STORE=redis            # 1/8/32/64 клиента × 3 повтора × 10 с → bench/results/load.csv
make report                      # bench/results/load_summary.md, bench/plots/load.png
```

Для хранилища в памяти запустите сервис без `REDIS_URL`: `uvicorn services.gamification_api.app:app --port 8000`, затем `make load STORE=memory`.

Окружение, на котором получены результаты, описано в `bench/results/environment.txt`. Абсолютные числа нагрузочного теста зависят от машины, сравнивать стоит соотношения.

## Основные результаты (лекция 8)

- Вся модель занимает меньше 10 мкс на событие; дольше всего выбор задачи из 50 (7,4 мкс).
- Сервис с Redis держит около 1 700 запр/с, p95 = 53 мс при 64 клиентах (цель ≤ 100 мс). С хранилищем в памяти около 6 600 запр/с.
- Выбран шаг Эло K = 0,2 для студентов и 0,1 для задач: наименьшая ошибка оценки способностей (RMSE 0,44).
- При адаптивном выборе AUC не различает модели, поэтому для RQ3 нужна доля случайных задач или сравнение по log-loss.

Подробно: [лекция 8](docs/lectures/lecture-8.md), [лекция 9](docs/lectures/lecture-9.md).

## Задания по курсу CSE7942

| Лекция | Тема | Файлы |
| --- | --- | --- |
| 1 | Исследовательский проект | [md](docs/lectures/lecture-1.md) · [docx](docs/word/Лекция_1_задание.docx) |
| 2 | Обзор литературы | [md](docs/lectures/lecture-2.md) · [docx](docs/word/Лекция_2_задание.docx) |
| 3 | Исследовательские вопросы и гипотезы | [md](docs/lectures/lecture-3.md) · [docx](docs/word/Лекция_3_задание.docx) |
| 4 | Структура IMRaD | [md](docs/lectures/lecture-4.md) · [docx](docs/word/Лекция_4_задание.docx) |
| 5 | Методы исследования | [md](docs/lectures/lecture-5.md) · [docx](docs/word/Лекция_5_задание.docx) |
| 6 | Управление данными и артефактами | [md](docs/lectures/lecture-6.md) · [docx](docs/word/Лекция_6_задание.docx) |
| 7 | Планирование эксперимента и метрики | [md](docs/lectures/lecture-7.md) · [docx](docs/word/Лекция_7_задание.docx) |
| 8 | Эксперименты в системных и серверных исследованиях | [md](docs/lectures/lecture-8.md) · [docx](docs/word/Лекция_8_задание.docx) |
| 9 | Репозиторий, CI и воспроизводимость | [md](docs/lectures/lecture-9.md) · [docx](docs/word/Лекция_9_задание.docx) |

## Лицензия

Apache 2.0, см. [LICENSE](LICENSE).
