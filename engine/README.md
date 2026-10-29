# profile engine

Маленький движок на Python, который рисует анимированные SVG для README профиля.

```
pip install -r requirements.txt
python -m engine build                 # все карточки + обновить README
python -m engine build --only nvim     # только одна карточка, README обновится только для неё
python -m engine build --no-readme     # всё, но README не трогать
```

## Как устроено

* `config/profile.toml` — весь текст: имя, грейд, стек, фразы для `now`, клавиши.
  Обновить профиль = поправить этот файл.
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
`engine/` и коммитит результат. Можно запустить и вручную: Actions → profile engine → Run.
