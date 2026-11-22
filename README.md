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
analysis/                статистика и рисунки предварительных результатов
paper/                   статья в шаблоне IEEE (LaTeX, BibTeX, PDF)
presentation/            доклад и постер A1 (python -m presentation.build)
docs/lectures/           задания к лекциям 1–15 (Markdown)
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

## Предварительные результаты (лекции 10–13)

- Адаптивный выбор задач даёт посильную задачу (P(успех) 0,5–0,85) в 79 % попыток против 40 % при общем линейном порядке; сильнее всего выигрывают слабые студенты.
- Холодный старт: сильные студенты первые 15 попыток получают слишком лёгкие задачи; старт по пре-тесту поднимает их долю посильных задач с 0,64 до 0,81.
- На 10 % случайно выданных задач Эло прогнозирует успех точнее статических меток (AUC 0,81 против 0,78); при другой модели ответов выигрыш вдвое меньше.
- Воспроизвести: `make policies && make analyze` (seed 42), статья — `paper/`.

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
| 10 | Анализ результатов и визуализация | [md](docs/lectures/lecture-10.md) · [docx](docs/word/Лекция_10_задание.docx) |
| 11 | Научное письмо | [md](docs/lectures/lecture-11.md) · [docx](docs/word/Лекция_11_задание.docx) |
| 12 | Оформление: LaTeX и шаблон IEEE | [md](docs/lectures/lecture-12.md) · [docx](docs/word/Лекция_12_задание.docx) |
| 13 | Рецензирование и подача статьи | [md](docs/lectures/lecture-13.md) · [docx](docs/word/Лекция_13_задание.docx) |
| 14 | Доклад, постер и вопросы | [md](docs/lectures/lecture-14.md) · [docx](docs/word/Лекция_14_задание.docx) |
| 15 | Этика, воспроизводимость и влияние | [md](docs/lectures/lecture-15.md) · [docx](docs/word/Лекция_15_задание.docx) |

## Лицензия

Apache 2.0, см. [LICENSE](LICENSE).
