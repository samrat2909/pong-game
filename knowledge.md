# Project knowledge

This file gives Codebuff context about your project: goals, commands, conventions, and gotchas.

## Quickstart
- **Setup:** `pip install pygame`
- **Dev:** `python main.py`
- **Test:** (none configured)
- **Lint:** (none configured)

## Architecture
PONG STRIKE — a polished Pong clone built with Python 3.7+ and Pygame 2.0+.

**Key files:**
- `main.py` — Entry point. Initializes Pygame, creates screen, runs `Game.run()`.
- `game.py` — Core game loop, state machine (menu / playing / paused / game_over / high_scores), input handling, rendering, AI logic.
- `sprites.py` — `Ball` and `Paddle` classes with physics, collision, trail/glow rendering.
- `particles.py` — `ParticleSystem`, `Starfield`, `ScreenShake`, and `Particle`/`Star` helper classes.
- `highscores.py` — `HighScoreManager` reads/writes `highscores.json`.
- `constants.py` — All config: screen size, colors, fonts, difficulty presets, physics constants, game states.
- `highscores.json` — Persistent high scores (auto-created).

**Data flow:**
`main.py` → `Game` → owns `Paddle`(×2), `Ball`, `ParticleSystem`, `Starfield`, `ScreenShake`, `HighScoreManager`.
Each frame: `handle_events()` → `update()` → `draw()`.

## Conventions
- **Style:** 4-space indent, type-hints not used, docstrings on classes and key methods.
- **Naming:** snake_case for functions/variables, UPPER_CASE for constants.
- **Imports:** standard lib first, then pygame, then local modules (alphabetical within groups).
- **Colors:** defined as RGB tuples in `constants.py`, referenced by name everywhere.
- **State machine:** string constants (`STATE_MENU`, etc.) drive `Game.state`.
- **Frame-rate independence:** `dt` (delta time) multiplier used in `Paddle` and `Star` updates; clamped to 0.5–2.0.

## Gotchas / Constraints
- **No package.json / requirements.txt** — only dependency is `pygame`. Install with `pip install pygame`.
- **No test suite or linter configured.**
- Fonts depend on system availability of `segoeui`; falls back to Pygame default font if missing.
- `constants.py` calls `pygame.font.init()` at import time — importing constants before `pygame.init()` in `main.py` works because `main.py` calls `pygame.init()` after imports, but font objects are created at import.
- High scores file (`highscores.json`) is written to the current working directory.
- AI difficulty is controlled by `difficulty_index` (0/1/2) selecting from `DIFFICULTIES` list.
- Gameplay extras configured in `constants.py`: `STARTING_LIVES` and a power-up system (`POWER_UP_SPEED_MULT`, `POWER_UP_INTERVAL_MIN/MAX`, `POWER_UP_BONUS`).
- Win condition: first to `WIN_SCORE` (11).
