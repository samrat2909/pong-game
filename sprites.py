"""
PONG STRIKE - Game Sprites
Ball and Paddle game objects with physics and rendering.
"""

import math
import random

import pygame

from constants import (
    BALL_BASE_SPEED,
    BALL_MAX_SPEED,
    BALL_RADIUS,
    BALL_SPEED_INCREMENT,
    BALL_START_X,
    BALL_START_Y,
    COLOR_BALL,
    COLOR_BALL_TRAIL,
    COLOR_PADDLE,
    COLOR_PADDLE_HIT,
    PADDLE_ACCELERATION,
    PADDLE_FRICTION,
    PADDLE_HEIGHT,
    PADDLE_MAX_SPEED,
    PADDLE_ROUNDED,
    PADDLE_SPEED_BASE,
    PADDLE_WIDTH,
    PADDLE_X,
    POWER_UP_SPEED_MULT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TRAIL_LENGTH,
    TRAIL_MIN_RADIUS,
)


class Paddle:
    """Player-controlled paddle with smooth acceleration physics."""

    def __init__(self, x=PADDLE_X, y=SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.x = x
        self.y = y
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.speed = PADDLE_SPEED_BASE
        self.velocity = 0
        self.max_speed = PADDLE_MAX_SPEED
        self.acceleration = PADDLE_ACCELERATION
        self.friction = PADDLE_FRICTION
        self.hit_glow = 0
        self.glow_surf = self._create_glow_surface()

    def _create_glow_surface(self):
        """Create a glow surface for the paddle."""
        glow_size = 20
        surf = pygame.Surface((self.width + glow_size * 2, self.height + glow_size * 2), pygame.SRCALPHA)
        # Use a dimmed version of the paddle color for glow
        glow_color = (0, 180, 255)
        for i in range(glow_size, 0, -2):
            alpha = int(40 * (i / glow_size))
            r, g, b = glow_color
            pygame.draw.rect(
                surf,
                (r, g, b, alpha),
                (glow_size - i, glow_size - i, self.width + i * 2, self.height + i * 2),
                border_radius=PADDLE_ROUNDED + i // 2,
            )
        return surf

    def move_up(self, dt=1.0):
        self.velocity -= self.acceleration * dt

    def move_down(self, dt=1.0):
        self.velocity += self.acceleration * dt

    def stop(self):
        # Friction is handled in update() - do nothing here
        pass

    def update(self, dt=1.0):
        # Apply friction (frame-rate independent)
        if dt > 0:
            self.velocity *= pow(self.friction, dt)

        # Clamp velocity
        self.velocity = max(-self.max_speed, min(self.velocity, self.max_speed))

        # Move (frame-rate independent)
        self.y += self.velocity * dt

        # Clamp to screen
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))

        # Update rect
        self.rect.y = self.y

        # Decay hit glow
        if self.hit_glow > 0:
            self.hit_glow -= 1

    def set_speed(self, speed):
        self.speed = speed

    def set_height(self, height):
        old_center = self.y + self.height // 2
        self.height = height
        self.y = old_center - height // 2
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.glow_surf = self._create_glow_surface()

    def on_hit(self):
        self.hit_glow = 10

    def draw(self, surface):
        # Draw glow
        glow_x = self.x - 20
        glow_y = self.y - 20
        if self.hit_glow > 0:
            # Bigger, brighter glow on hit
            extra = self.hit_glow * 2
            hit_glow_surf = pygame.Surface(
                (self.width + 20 * 2 + extra, self.height + 20 * 2 + extra),
                pygame.SRCALPHA,
            )
            hit_color = (255, 255, 255)
            for i in range(20 + extra, 0, -2):
                alpha = int(60 * (i / (20 + extra)))
                pygame.draw.rect(
                    hit_glow_surf,
                    (hit_color[0], hit_color[1], hit_color[2], alpha),
                    (20 + extra - i, 20 + extra - i,
                     self.width + i * 2, self.height + i * 2),
                    border_radius=PADDLE_ROUNDED + i // 2,
                )
            surface.blit(hit_glow_surf, (glow_x - extra // 2, glow_y - extra // 2))
        else:
            surface.blit(self.glow_surf, (glow_x, glow_y))

        # Draw paddle body
        color = COLOR_PADDLE_HIT if self.hit_glow > 5 else COLOR_PADDLE
        pygame.draw.rect(surface, color, self.rect, border_radius=PADDLE_ROUNDED)

        # Draw a subtle edge highlight on the paddle face
        if self.hit_glow <= 0:
            highlight_rect = pygame.Rect(
                self.x + 2, self.y + 4,
                3, self.height - 8
            )
            pygame.draw.rect(
                surface,
                (100, 255, 255, 40),
                highlight_rect,
                border_radius=2,
            )

    def reset(self, x=PADDLE_X, y=SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2):
        self.x = x
        self.y = y
        self.velocity = 0
        self.rect.x = x
        self.rect.y = y


class Ball:
    """The ball with trail effect and physics."""

    def __init__(self):
        self.x = BALL_START_X
        self.y = BALL_START_Y
        self.radius = BALL_RADIUS
        self.speed = BALL_BASE_SPEED
        self.max_speed = BALL_MAX_SPEED
        self.vx = 0
        self.vy = 0
        self.trail = []
        self.glow_surf = self._create_glow_surface()
        self.powered_up = False
        self._pulse = 0.0

    def _create_glow_surface(self):
        """Create a glow surface for the ball."""
        glow_size = 30
        surf = pygame.Surface((self.radius * 2 + glow_size * 2, self.radius * 2 + glow_size * 2), pygame.SRCALPHA)
        glow_color = (255, 150, 50)
        for i in range(glow_size, 0, -2):
            alpha = int(30 * (i / glow_size))
            r, g, b = glow_color
            pygame.draw.circle(
                surf,
                (r, g, b, alpha),
                (self.radius + glow_size, self.radius + glow_size),
                self.radius + i,
            )
        return surf

    def launch(self, angle=None):
        """Launch the ball at a random or specified angle."""
        if angle is None:
            angle = random.uniform(-math.pi / 4, math.pi / 4)
            direction = random.choice([-1, 1])
            angle = math.pi / 2 + direction * (math.pi / 2 + angle)

        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed

    def set_speed(self, speed):
        """Update speed while maintaining direction."""
        current_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if current_speed > 0:
            ratio = speed / current_speed
            self.vx *= ratio
            self.vy *= ratio
        self.speed = speed

    def update(self):
        """Update ball position and trail."""
        # Add trail point
        self.trail.append((self.x, self.y))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

        # Move ball
        self.x += self.vx
        self.y += self.vy

        # Speed increment every frame (gradual difficulty)
        current_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        max_speed = self.max_speed * (POWER_UP_SPEED_MULT if self.powered_up else 1.0)
        if current_speed < max_speed:
            increment = BALL_SPEED_INCREMENT * (1.005 if self.powered_up else 1.0)
            ratio = min(increment, max_speed / current_speed)
            self.vx *= ratio
            self.vy *= ratio

        # Pulse animation for powered-up state
        self._pulse += 0.08

    def bounce_top_bottom(self):
        """Bounce off top or bottom wall."""
        self.vy = -self.vy

    def bounce_paddle(self, paddle):
        """Bounce off the left (player) paddle — ball goes right."""
        # Calculate hit position as a ratio from 0 to 1
        hit_pos = (self.y - paddle.rect.y) / paddle.rect.height
        hit_pos = max(0, min(1, hit_pos))

        # Map to angle: -60° to +60°
        angle = (hit_pos - 0.5) * (math.pi / 3)

        # Bounce right (away from left paddle)
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        self.vx = abs(math.cos(angle) * speed)
        self.vy = -math.sin(angle) * speed

        # Ensure minimum horizontal speed
        min_horizontal = speed * 0.4
        if abs(self.vx) < min_horizontal:
            self.vx = min_horizontal
            self.vy = math.sqrt(max(0, speed ** 2 - self.vx ** 2)) * (1 if self.vy >= 0 else -1)

    def bounce_paddle2(self, paddle):
        """Bounce off the right (AI) paddle — ball goes left."""
        # Calculate hit position as a ratio from 0 to 1
        hit_pos = (self.y - paddle.rect.y) / paddle.rect.height
        hit_pos = max(0, min(1, hit_pos))

        # Map to angle: -60° to +60° (inverted for right-side paddle)
        angle = (hit_pos - 0.5) * (math.pi / 3)

        # Bounce left (away from right paddle)
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        self.vx = -abs(math.cos(angle) * speed)
        self.vy = -math.sin(angle) * speed

        # Ensure minimum horizontal speed
        min_horizontal = speed * 0.4
        if abs(self.vx) < min_horizontal:
            self.vx = -min_horizontal
            self.vy = math.sqrt(max(0, speed ** 2 - self.vx ** 2)) * (1 if self.vy >= 0 else -1)

    def check_wall_collision(self):
        """Check and handle wall collisions. Returns event type or None."""
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.bounce_top_bottom()
            return "wall_top"
        if self.y + self.radius >= SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.bounce_top_bottom()
            return "wall_bottom"
        if self.x + self.radius >= SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            if self.powered_up:
                # Power-up blocks the goal — bounce back toward player
                self.vx = -abs(self.vx)
                self.vy += random.uniform(-0.5, 0.5)  # Prevent horizontal dead zone
                return "wall_right_blocked"
            return "wall_right"
        return None

    def check_paddle_collision(self, paddle):
        """Check collision with left (player) paddle. Ball bounces right."""
        ball_rect = pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )
        if ball_rect.colliderect(paddle.rect):
            self.bounce_paddle(paddle)
            return True
        return False

    def check_paddle2_collision(self, paddle):
        """Check collision with right (AI) paddle. Ball bounces left."""
        ball_rect = pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2,
        )
        if ball_rect.colliderect(paddle.rect):
            self.bounce_paddle2(paddle)
            return True
        return False

    def draw_trail(self, surface):
        """Draw the ball trail with improved glow effect."""
        trail_len = len(self.trail)
        if trail_len == 0:
            return

        for i, (tx, ty) in enumerate(self.trail):
            progress = i / trail_len
            alpha = int(60 + 40 * progress)
            radius = max(
                TRAIL_MIN_RADIUS,
                int(self.radius * (0.2 + 0.8 * progress)),
            )

            trail_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

            if self.powered_up:
                # Cyan trail for powered-up ball
                color = (0, 255, 255)
                # Extra glow layers
                for g in range(3, 0, -1):
                    g_radius = radius + g * 2
                    g_alpha = int(alpha * 0.2 / g)
                    g_surf = pygame.Surface((g_radius * 2, g_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(
                        g_surf,
                        (color[0], color[1], color[2], g_alpha),
                        (g_radius, g_radius),
                        g_radius,
                    )
                    surface.blit(g_surf, (int(tx - g_radius), int(ty - g_radius)))
            else:
                color = COLOR_BALL_TRAIL

            pygame.draw.circle(
                trail_surf,
                (color[0], color[1], color[2], alpha),
                (radius, radius),
                radius,
            )
            surface.blit(trail_surf, (int(tx - radius), int(ty - radius)))

    def draw(self, surface):
        """Draw the ball with glow effect."""
        # Draw trail
        self.draw_trail(surface)

        if self.powered_up:
            # Pulsing power-up glow
            pulse = abs(math.sin(self._pulse))
            scale = 0.8 + 0.4 * pulse

            # Bigger, brighter glow for power-up
            glow_size = int(45 * scale)
            glow_surf = pygame.Surface(
                (self.radius * 2 + glow_size * 2, self.radius * 2 + glow_size * 2),
                pygame.SRCALPHA,
            )
            glow_color = (0, 255, 255)
            alpha = int(40 + 40 * pulse)
            for i in range(glow_size, 0, -2):
                a = int(alpha * (i / glow_size))
                pygame.draw.circle(
                    glow_surf,
                    (glow_color[0], glow_color[1], glow_color[2], a),
                    (self.radius + glow_size, self.radius + glow_size),
                    self.radius + i,
                )

            cx, cy = int(self.x - self.radius - glow_size), int(self.y - self.radius - glow_size)
            surface.blit(glow_surf, (cx, cy))

            # Draw ball in bright cyan with white-hot center
            ball_color = (
                int(0 + 200 * pulse),
                255,
                int(200 + 55 * pulse),
            )
            pygame.draw.circle(surface, ball_color, (int(self.x), int(self.y)), self.radius)

            # White hot center
            pygame.draw.circle(
                surface,
                (255, 255, 255),
                (int(self.x), int(self.y)),
                self.radius // 3,
            )

            # Extra spark highlight
            spark_offset = self.radius // 3
            spark_alpha = int(120 + 135 * pulse)
            spark_surf = pygame.Surface((self.radius, self.radius), pygame.SRCALPHA)
            pygame.draw.circle(
                spark_surf,
                (255, 255, 255, spark_alpha),
                (self.radius // 2, self.radius // 2),
                self.radius // 2,
            )
            surface.blit(
                spark_surf,
                (int(self.x - self.radius // 2 - spark_offset), int(self.y - self.radius // 2 - spark_offset)),
            )

            # Draw energy rings around the ball
            for ring_i in range(2):
                ring_radius = self.radius + 8 + ring_i * 6 + int(4 * pulse)
                ring_alpha = int(60 + 60 * pulse - ring_i * 20)
                ring_surf = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    ring_surf,
                    (0, 255, 255, ring_alpha),
                    (ring_radius, ring_radius),
                    ring_radius,
                    width=2,
                )
                surface.blit(
                    ring_surf,
                    (int(self.x - ring_radius), int(self.y - ring_radius)),
                )
        else:
            # Normal draw
            glow_x = self.x - self.radius - 30
            glow_y = self.y - self.radius - 30
            surface.blit(self.glow_surf, (glow_x, glow_y))

            # Draw ball
            pygame.draw.circle(surface, COLOR_BALL, (int(self.x), int(self.y)), self.radius)

            # Draw highlight (for 3D effect)
            highlight_offset = self.radius // 3
            highlight_surf = pygame.Surface((self.radius, self.radius), pygame.SRCALPHA)
            pygame.draw.circle(
                highlight_surf,
                (255, 255, 255, 60),
                (self.radius // 2, self.radius // 2),
                self.radius // 2,
            )
            surface.blit(
                highlight_surf,
                (int(self.x - self.radius // 2 - highlight_offset),
                 int(self.y - self.radius // 2 - highlight_offset)),
            )

    def reset(self):
        """Reset ball to center."""
        self.x = BALL_START_X
        self.y = BALL_START_Y
        self.trail.clear()
        self.vx = 0
        self.vy = 0
        self.powered_up = False
        self._pulse = 0.0
