"""
PONG STRIKE - Particle System
Handles particle effects, starfield background, and screen shake.
"""

import math
import random

import pygame

from constants import (
    COLOR_BALL,
    COLOR_PADDLE,
    COMBO_PARTICLE_BURST,
    PARTICLE_COUNT,
    PARTICLE_LIFETIME,
    PARTICLE_MAX_SPEED,
    PARTICLE_MAX_SIZE,
    PARTICLE_MIN_SIZE,
    SHAKE_DECAY,
    SHAKE_DURATION,
    SHAKE_INTENSITY,
    STAR_COUNT,
    STAR_MAX_SPEED,
    STAR_MAX_SIZE,
    STAR_MIN_SPEED,
    STAR_MIN_SIZE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class Particle:
    """A single particle with position, velocity, color, and lifetime."""

    def __init__(self, x, y, color, speed_multiplier=1.0):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, PARTICLE_MAX_SPEED) * speed_multiplier
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = random.uniform(PARTICLE_MIN_SIZE, PARTICLE_MAX_SIZE)
        self.lifetime = random.randint(PARTICLE_LIFETIME // 2, PARTICLE_LIFETIME)
        self.max_lifetime = self.lifetime
        self.color = color
        self.decay = random.uniform(0.95, 0.99)

    @property
    def alive(self):
        return self.lifetime > 0

    @property
    def alpha(self):
        return int(255 * (self.lifetime / self.max_lifetime))

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= self.decay
        self.vy *= self.decay
        self.lifetime -= 1

    def draw(self, surface, offset=(0, 0)):
        alpha = self.alpha
        if alpha <= 0:
            return
        pos = (int(self.x + offset[0]), int(self.y + offset[1]))
        color = (*self.color[:3], alpha)
        surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (int(self.size), int(self.size)), int(self.size))
        surface.blit(surf, pos)


class ParticleSystem:
    """Manages all active particles."""

    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=PARTICLE_COUNT, speed_multiplier=1.0):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed_multiplier))

    def emit_paddle_hit(self, x, y):
        self.emit(x, y, COLOR_PADDLE, count=15, speed_multiplier=1.5)
        self.emit(x, y, (255, 255, 255), count=8, speed_multiplier=2.0)

    def emit_wall_hit(self, x, y):
        self.emit(x, y, COLOR_BALL, count=10, speed_multiplier=1.2)
        self.emit(x, y, (255, 255, 200), count=5, speed_multiplier=1.0)

    def emit_score(self, x, y):
        self.emit(x, y, (255, 215, 0), count=25, speed_multiplier=2.5)
        self.emit(x, y, (255, 255, 255), count=15, speed_multiplier=3.0)

    def emit_lost_ball(self, x, y):
        self.emit(x, y, (255, 50, 50), count=30, speed_multiplier=3.0)
        self.emit(x, y, (255, 100, 100), count=15, speed_multiplier=2.0)

    def emit_confetti(self, x, y):
        """Emit confetti burst for celebrations."""
        colors = [
            (255, 215, 0),   # Gold
            (255, 50, 50),    # Red
            (0, 255, 120),    # Green
            (0, 245, 255),    # Cyan
            (255, 107, 53),   # Orange
            (255, 0, 255),    # Magenta
            (100, 100, 255),  # Blue
        ]
        for _ in range(40):
            color = random.choice(colors)
            p = Particle(x, y, color, speed_multiplier=2.5)
            p.size = random.uniform(3, 6)
            self.particles.append(p)

    def emit_combo(self, x, y, combo_count):
        """Emit celebratory burst for combo hits."""
        intensity = min(combo_count, 5)
        count = COMBO_PARTICLE_BURST * intensity
        self.emit(x, y, (255, 165, 0), count=count, speed_multiplier=1.5 + intensity * 0.3)
        self.emit(x, y, (255, 255, 255), count=count // 2, speed_multiplier=2.0)

    def update(self):
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

    def draw(self, surface, offset=(0, 0)):
        for p in self.particles:
            p.draw(surface, offset)

    def clear(self):
        self.particles.clear()


class Star:
    """A background star with slow parallax movement."""

    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(STAR_MIN_SPEED, STAR_MAX_SPEED)
        self.size = random.uniform(STAR_MIN_SIZE, STAR_MAX_SIZE)
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.01, 0.05)
        self.twinkle_offset = random.uniform(0, 2 * math.pi)

    def update(self, dt):
        self.y += self.speed * dt * 60

        # Twinkle effect
        self.current_brightness = int(
            self.brightness * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * self.twinkle_speed + self.twinkle_offset))
        )

        # Wrap around
        if self.y > SCREEN_HEIGHT:
            self.y = -self.size
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        b = min(255, self.current_brightness + 10)
        color = (self.current_brightness, self.current_brightness, b)
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(surface, color, pos, int(self.size))


class Starfield:
    """Manages the background starfield."""

    def __init__(self):
        self.stars = [Star() for _ in range(STAR_COUNT)]

    def update(self, dt):
        for star in self.stars:
            star.update(dt)

    def draw(self, surface):
        for star in self.stars:
            star.draw(surface)


class ScreenShake:
    """Manages screen shake effect."""

    def __init__(self):
        self.intensity = 0
        self.duration = 0

    def trigger(self, intensity=SHAKE_INTENSITY, duration=SHAKE_DURATION):
        self.intensity = intensity
        self.duration = duration

    def update(self):
        if self.duration > 0:
            self.duration -= 1
            self.intensity *= SHAKE_DECAY
            if self.duration <= 0:
                self.intensity = 0
                self.duration = 0

    @property
    def offset(self):
        if self.duration <= 0:
            return (0, 0)
        return (
            random.randint(-int(self.intensity), int(self.intensity)),
            random.randint(-int(self.intensity), int(self.intensity)),
        )

    @property
    def active(self):
        return self.duration > 0
