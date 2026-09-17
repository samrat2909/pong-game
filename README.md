# PONG STRIKE ⚡

A modern, polished take on the classic Pong game, built with Python and Pygame. Features smooth physics, particle effects, AI opponents, and a sleek neon aesthetic.

## Features

- **🎮 Smooth Controls** - Paddle physics with acceleration/friction for responsive gameplay
- **🤖 Smart AI Opponent** - Adjustable difficulty (Easy / Medium / Hard)
- **✨ Particle Effects** - Explosions on paddle hits, wall bounces, and scoring
- **🎯 Combo System** - Chain hits for style points
- **🏆 High Scores** - Persistent score tracking across sessions
- **💫 Visual Polish** - Glow effects, screen shake, starfield background, ball trails
- **⏸️ Pause Support** - Pause/Resume anytime with ESC or P

## Requirements

- Python 3.7+
- Pygame 2.0+

## Installation

```bash
# Install pygame
pip install pygame

# Run the game
python main.py
```

## Controls

| Key          | Action                 |
|-------------|------------------------|
| ↑ / W       | Move paddle up         |
| ↓ / S       | Move paddle down       |
| ESC / P     | Pause / Resume         |
| ← / →       | Change difficulty (menu)|
| Enter/Space | Start game             |
| H           | View high scores (menu)|

## Project Structure

```
pong-strike/
├── main.py          # Entry point
├── game.py          # Game engine and state machine
├── sprites.py       # Ball and Paddle classes
├── particles.py     # Particle system, starfield, screen shake
├── highscores.py    # High score manager
├── constants.py     # Game configuration and settings
└── README.md        # This file
```

## Difficulty Levels

| Difficulty | Ball Speed | Paddle Size | AI Skill |
|-----------|-----------|-------------|----------|
| Easy      | Slow      | Large       | Low      |
| Medium    | Moderate  | Standard    | Moderate |
| Hard      | Fast      | Small       | High     |

## License

Brought to you by Samrat


PS. This game is majorly made by AI and not me i only made a few modifications where AI had done some mistakes.
