# profile engine

Маленький движок на Python, который рисует анимированные SVG для README профиля.

```
uv sync                                       # Python 3.12 + зависимости из uv.lock
uv run python -m engine build                 # все карточки + обновить README
uv run python -m engine build --only nvim     # только одна карточка, README обновится только для неё
uv run python -m engine build --no-readme     # всё, но README не трогать
uv run python -m engine build --offline       # без GitHub API: цифры проектов из assets/stats.json
```

Зависимости — в `pyproject.toml`, точные версии — в `uv.lock` (коммитится).
Новая зависимость: `uv add <pkg>`. Playwright для проверки кадров — в dev-группе:
`uv run playwright install chromium`.

## Как устроено

* `config/profile.toml` — весь текст: имя, грейд, стек, фразы для `now`, клавиши,
  репозитории проектов. Обновить профиль = поправить этот файл.
* `engine/stats.py` — живые данные проектов из GitHub API (звёзды, число решённых
  задач по сложности и источникам, код решений из `showcase`). Последний удачный снимок
  кладётся в `assets/stats.json`; если API недоступен — сборка берёт его.
* `engine/cards/divider.py` — разделитель секций `01 · PROFILE` / `02 · PROJECTS`:
  линейка с тиками и бегущий блик.
* `engine/cards/algorithms.py` — карточка `Algorithms` в стиле LeetCode: кольцо
  easy/medium/hard, чипы источников, редактор по очереди «сабмитит» задачи из `showcase`
  (Pending → Judging → Accepted + сложность из комментария `# O(...)` в решении).
* `engine/cards/aura.py` — карточка темы Aura Dark: окно Logseq в самой теме,
  TODO↔DONE, последний блок печатается и стирается (фразы `aura.typing`).
* `engine/cards/nvim.py` — шапка: Neovim, который бесконечно редактирует `profile.py`
  (переход к строке через `j` / `/now` / `17G`, `ci"`, ввод, `:w`, `:!python %`)
  и neofetch-вывод в терминальном сплите справа.
* `engine/cards/badges.py` — ряд клавиш, которые по очереди «нажимаются».
* `engine/kit.py` — палитра Tokyo Night, встраивание шрифта, помощники для анимации.

Анимация — это SMIL (`<animate calcMode="discrete">`) с одним общим периодом,
поэтому все элементы идут синхронно и цикл бесшовный. Начальное значение каждого
элемента записано и как обычный атрибут: без анимации видно полный красивый кадр.
JavaScript не используется (GitHub его вырезает).

Шрифт JetBrains Mono (OFL, см. `fonts/OFL.txt`) встраивается в каждый SVG,
урезанный только до использованных символов, — поэтому выглядит одинаково везде.

## Новая карточка

1. Создай `engine/cards/<name>.py` с функцией `render(cfg) -> str`.
2. Добавь её в `CARDS` в `engine/__main__.py`.
3. Поставь в `README.md` метки `<!-- ENGINE:<NAME>:START -->` и `<!-- ENGINE:<NAME>:END -->`.

## Автосборка

`.github/workflows/profile.yml` пересобирает карточки при каждом пуше в `config/` или
`engine/` и раз в день (живая статистика), коммитит результат. Сборка детерминирована
(шрифт без метки времени), так что коммит появляется только при реальных изменениях.
Можно запустить и вручную: Actions → profile engine → Run.
