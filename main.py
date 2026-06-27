#!/usr/bin/env python3
"""
PONG STRIKE
═══════════════════════════════
A modern, polished take on the classic Pong game.
Built with Python and Pygame.

Features:
• Multiple difficulty levels (Easy, Medium, Hard)
• Particle effects and screen shaking
• High score tracking
• Smooth paddle physics with acceleration
• AI opponent with adjustable difficulty
• Combo system
• Beautiful visual effects

Controls:
• ↑/W - Move paddle up
• ↓/S - Move paddle down
• P/ESC - Pause
• H - High scores (from menu)

Run with: python main.py
"""

import sys
import os

# Add the script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

from constants import GAME_TITLE, SCREEN_HEIGHT, SCREEN_WIDTH
from game import Game


def main():
    """Initialize and run the game."""
    pygame.init()

    # Set up the display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)

    # Try to set icon (optional)
    try:
        icon = pygame.Surface((32, 32))
        icon.fill((0, 245, 255))
        pygame.draw.circle(icon, (255, 107, 53), (16, 16), 10)
        pygame.display.set_icon(icon)
    except Exception:
        pass

    # Create and run the game
    game = Game(screen)
    game.run()


if __name__ == "__main__":
    main()
