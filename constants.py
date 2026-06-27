"""
PONG STRIKE - Game Constants
A modern, polished take on the classic Pong game.
"""

import pygame

# ─── Display ────────────────────────────────────────────────────────────────
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60
GAME_TITLE = "PONG STRIKE"
WIN_SCORE = 11

# ─── Colors ─────────────────────────────────────────────────────────────────
# Dark theme with neon accents
COLOR_BG = (10, 10, 26)
COLOR_BG_TOP = (10, 10, 40)
COLOR_BG_BOTTOM = (5, 5, 15)

COLOR_PADDLE = (0, 245, 255)        # Cyan
COLOR_PADDLE_GLOW = (0, 180, 255, 80)
COLOR_PADDLE_HIT = (255, 255, 255)

COLOR_BALL = (255, 107, 53)         # Orange
COLOR_BALL_GLOW = (255, 150, 50, 60)
COLOR_BALL_TRAIL = (255, 107, 53, 40)

COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_SHADOW = (0, 0, 0, 60)
COLOR_ACCENT = (255, 215, 0)        # Gold
COLOR_ACCENT2 = (0, 245, 255)       # Cyan

COLOR_GREEN = (0, 255, 120)
COLOR_RED = (255, 50, 50)
COLOR_ORANGE = (255, 165, 0)

COLOR_MENU_BG = (15, 15, 35)
COLOR_MENU_ACCENT = (0, 245, 255)
COLOR_MENU_HOVER = (0, 200, 220)
COLOR_BUTTON = (30, 30, 60)
COLOR_BUTTON_HOVER = (50, 50, 90)
COLOR_BUTTON_BORDER = (0, 245, 255)

# ─── Paddle ─────────────────────────────────────────────────────────────────
PADDLE_WIDTH = 12
PADDLE_HEIGHT = 100
PADDLE_X = 30
PADDLE_SPEED_BASE = 5.0
PADDLE_ACCELERATION = 0.65
PADDLE_FRICTION = 0.85
PADDLE_MAX_SPEED = 11.0
PADDLE_ROUNDED = 4

# ─── Ball ────────────────────────────────────────────────────────────────────
BALL_RADIUS = 10
BALL_BASE_SPEED = 5
BALL_MAX_SPEED = 12
BALL_SPEED_INCREMENT = 1.02
BALL_START_X = SCREEN_WIDTH // 2
BALL_START_Y = SCREEN_HEIGHT // 2

# ─── Trail ──────────────────────────────────────────────────────────────────
TRAIL_LENGTH = 12
TRAIL_MIN_RADIUS = 3
TRAIL_FADE_SPEED = 4

# ─── Particles ──────────────────────────────────────────────────────────────
PARTICLE_COUNT = 20
PARTICLE_MAX_SPEED = 4
PARTICLE_LIFETIME = 30
PARTICLE_MIN_SIZE = 2
PARTICLE_MAX_SIZE = 6

# ─── Screen Shake ───────────────────────────────────────────────────────────
SHAKE_INTENSITY = 6
SHAKE_DECAY = 0.85
SHAKE_DURATION = 8

# ─── Starfield ──────────────────────────────────────────────────────────────
STAR_COUNT = 120
STAR_MIN_SPEED = 0.3
STAR_MAX_SPEED = 1.5
STAR_MIN_SIZE = 1
STAR_MAX_SIZE = 3

STARTING_LIVES = 4

# ─── Power-up ────────────────────────────────────────────────────────────────
POWER_UP_SPEED_MULT = 1.5          # Speed multiplier when powered up
POWER_UP_INTERVAL_MIN = 240        # Min frames between power-ups (4s at 60fps)
POWER_UP_INTERVAL_MAX = 600        # Max frames between power-ups (10s at 60fps)
POWER_UP_BONUS = 2                 # Extra points for hitting powered-up ball

# ─── Difficulty presets ─────────────────────────────────────────────────────
DIFFICULTY_EASY = {
    "name": "Easy",
    "ball_speed": 4.0,
    "paddle_speed": 5.5,
    "speed_increment": 1.01,
    "max_speed": 9,
    "paddle_height": 120,
}
DIFFICULTY_MEDIUM = {
    "name": "Medium",
    "ball_speed": 5.5,
    "paddle_speed": 5.0,
    "speed_increment": 1.02,
    "max_speed": 11,
    "paddle_height": 100,
}
DIFFICULTY_HARD = {
    "name": "Hard",
    "ball_speed": 7.0,
    "paddle_speed": 4.5,
    "speed_increment": 1.03,
    "max_speed": 14,
    "paddle_height": 80,
}

DIFFICULTIES = [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]

# ─── High Scores ────────────────────────────────────────────────────────────
HIGH_SCORES_FILE = "highscores.json"
MAX_HIGH_SCORES = 10

# ─── Game States ────────────────────────────────────────────────────────────
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"
STATE_HIGH_SCORES = "high_scores"

# ─── Fonts ──────────────────────────────────────────────────────────────────
try:
    pygame.font.init()
    FONT_TITLE = pygame.font.SysFont("segoeui", 72, bold=True)
    FONT_SUBTITLE = pygame.font.SysFont("segoeui", 28)
    FONT_BODY = pygame.font.SysFont("segoeui", 24)
    FONT_SMALL = pygame.font.SysFont("segoeui", 18)
    FONT_SCORE = pygame.font.SysFont("segoeui", 48, bold=True)
    FONT_MENU = pygame.font.SysFont("segoeui", 32, bold=True)
except Exception:
    # Font init already attempted above — use default pygame font as fallback
    FONT_TITLE = pygame.font.Font(None, 72)
    FONT_SUBTITLE = pygame.font.Font(None, 28)
    FONT_BODY = pygame.font.Font(None, 24)
    FONT_SMALL = pygame.font.Font(None, 18)
    FONT_SCORE = pygame.font.Font(None, 48)
    FONT_MENU = pygame.font.Font(None, 32)
