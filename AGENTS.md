# PONG STRIKE — AGENTS.md

## Setup & run
- Only dependency: `pygame` — install with `pip install pygame`
- Run: `python main.py`
- No test suite, linter, or formatter configured

## Architecture
- Entrypoint: `main.py` → `Game` (owns paddle×2, ball, particle system, starfield, screen shake, high score manager)
- Per-frame: `handle_events()` → `update()` → `draw()`
- State machine via string constants from `constants.py`: `STATE_MENU`, `STATE_PLAYING`, `STATE_PAUSED`, `STATE_GAME_OVER`, `STATE_HIGH_SCORES`
- Difficulty: `difficulty_index` (0/1/2) selects from `DIFFICULTIES` list in `constants.py`
- Win condition: first to `WIN_SCORE` (11)
- High scores: `highscores.json` in CWD, managed by `HighScoreManager` in `highscores.py`

## Quirks & gotchas
- `constants.py` calls `pygame.font.init()` at import time — safe because font objects are created during import, while `pygame.init()` happens in `main()` after imports
- Fonts depend on `segoeui` (Windows); falls back to Pygame default if unavailable
- `dt` (delta time) multiplier used for frame-rate independence, clamped to 0.5–2.0
- No `.gitignore`, no `requirements.txt`, no CI
- All config in `constants.py`: screen size, colors, physics, difficulty presets, game states, font definitions
