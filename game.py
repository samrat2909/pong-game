"""
PONG STRIKE - Game Engine
Core game loop with state machine, input handling, and rendering.
"""

import math
import random

import pygame
from constants import (
    COLOR_ACCENT,
    COLOR_ACCENT2,
    COLOR_BG_BOTTOM,
    COLOR_BG_TOP,
    COLOR_BUTTON,
    COLOR_BUTTON_HOVER,
    COLOR_GREEN,
    COLOR_ORANGE,
    COLOR_RED,
    COLOR_TEXT,
    COUNTDOWN_FONT_SIZE,
    COUNTDOWN_FRAMES,
    COUNTDOWN_NUMBERS,
    DIFFICULTIES,
    FLASH_DURATION,
    FONT_BODY,
    FONT_SCORE,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_TITLE,
    FPS,
    MENU_BALL_RADIUS,
    MENU_BALL_SPEED,
    PADDLE_HEIGHT,
    PADDLE_WIDTH,
    PADDLE_X,
    POWER_UP_BONUS,
    POWER_UP_INTERVAL_MAX,
    POWER_UP_INTERVAL_MIN,
    POWER_UP_SPEED_MULT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SOUND_VOLUME,
    STARTING_LIVES,
    STATE_GAME_OVER,
    STATE_HIGH_SCORES,
    STATE_MENU,
    STATE_PAUSED,
    STATE_PLAYING,
    WIN_SCORE,
)


from highscores import HighScoreManager
from particles import ParticleSystem, ScreenShake, Starfield
from sounds import SoundManager
from sprites import Ball, Paddle


class MenuBall:
    """Decorative bouncing ball for the menu screen."""
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vx = MENU_BALL_SPEED * random.choice([-1, 1])
        self.vy = MENU_BALL_SPEED * random.uniform(-0.8, 0.8)
        self.radius = MENU_BALL_RADIUS
        self.trail = []
        self.color = (0, 245, 255)

    def update(self):
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 25:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy
        if self.x - self.radius <= 0 or self.x + self.radius >= SCREEN_WIDTH:
            self.vx = -self.vx
            self.x = max(self.radius, min(self.x, SCREEN_WIDTH - self.radius))
        if self.y - self.radius <= 0 or self.y + self.radius >= SCREEN_HEIGHT:
            self.vy = -self.vy
            self.y = max(self.radius, min(self.y, SCREEN_HEIGHT - self.radius))

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            progress = i / len(self.trail)
            brightness = int(40 + 215 * progress)
            color = (0, brightness, brightness)
            pygame.draw.circle(surface, color, (tx, ty), max(1, int(self.radius * progress)))
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (100, 255, 255), (int(self.x), int(self.y)), self.radius - 2)


class Game:
    """Main game class that manages states, updates, and rendering."""

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MENU
        self.dt = 1.0  # Delta time multiplier

        # Game objects
        self.paddle = Paddle()
        self.paddle2 = Paddle(x=SCREEN_WIDTH - PADDLE_X - PADDLE_WIDTH)  # AI opponent
        self.ball = Ball()

        # Effects
        self.particles = ParticleSystem()
        self.starfield = Starfield()
        self.shake = ScreenShake()
        self.sound = SoundManager()
        self.sound.set_volume(SOUND_VOLUME)

        # Menu decoration
        self.menu_ball = MenuBall()

        # AI smoothing target
        self._ai_target_y = SCREEN_HEIGHT // 2

        # Cached countdown font (avoids re-creating SysFont every frame)
        try:
            self._countdown_font = pygame.font.SysFont("segoeui", COUNTDOWN_FONT_SIZE, bold=True)
        except Exception:
            self._countdown_font = pygame.font.Font(None, COUNTDOWN_FONT_SIZE)

        # Screen flash
        self.flash_color = None
        self.flash_alpha = 0

        # Game state
        self.score = 0
        self.ai_score = 0
        self.lives = STARTING_LIVES
        self.max_score = WIN_SCORE
        self.difficulty_index = 1  # Medium by default
        self.difficulty = DIFFICULTIES[self.difficulty_index]

        # UI state
        self.flash_message = ""
        self.flash_timer = 0
        self.score_popup = 0
        self.ai_score_popup = 0

        # Combo system
        self.combo = 0
        self.combo_timer = 0

        # High scores
        self.high_score_mgr = HighScoreManager()
        self.new_high_score = False

        # Input
        self.keys = {}

        # Countdown before serve
        self.countdown_active = False
        self.countdown_frame = 0
        self.countdown_index = 0

        # Ball launch delay (legacy)
        self.launch_timer = 0

        # Power-up system
        self.power_up_timer = random.randint(POWER_UP_INTERVAL_MIN, POWER_UP_INTERVAL_MAX)

        # Match statistics
        self.stats = {
            "rallies": 0,
            "longest_rally": 0,
            "current_rally": 0,
            "aces": 0,           # Ball past player before paddle touch
            "player_hits": 0,
            "ai_hits": 0,
            "power_hits": 0,
        }

        self._apply_difficulty()
        self.ball.launch(angle=random.uniform(math.pi * 2 / 3, math.pi * 4 / 3))

    def _apply_difficulty(self):
        """Apply the current difficulty settings."""
        diff = DIFFICULTIES[self.difficulty_index]
        self.difficulty = diff
        self.ball.speed = diff["ball_speed"]
        self.ball.max_speed = diff["max_speed"]
        self.paddle.set_speed(diff["paddle_speed"])
        self.paddle.set_height(diff["paddle_height"])

    def handle_events(self):
        """Process all input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if self.state == STATE_MENU:
                    self._handle_menu_key(event.key)
                elif self.state == STATE_PLAYING:
                    self._handle_playing_key(event.key)
                elif self.state == STATE_PAUSED:
                    self._handle_paused_key(event.key)
                elif self.state == STATE_GAME_OVER:
                    self._handle_game_over_key(event.key)
                elif self.state == STATE_HIGH_SCORES:
                    self._handle_high_scores_key(event.key)

            elif event.type == pygame.MOUSEMOTION:
                if self.state == STATE_MENU:
                    self._handle_menu_mouse(event.pos)
                elif self.state == STATE_GAME_OVER:
                    pass  # Could add buttons here

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == STATE_MENU:
                    self._handle_menu_click(event.pos)
                elif self.state == STATE_GAME_OVER:
                    self._handle_game_over_click(event.pos)
                elif self.state == STATE_HIGH_SCORES:
                    self.state = STATE_MENU

    def _handle_menu_key(self, key):
        if key == pygame.K_RETURN or key == pygame.K_SPACE:
            self.sound.play("menu_select")
            self.start_game()
        elif key == pygame.K_LEFT:
            self.difficulty_index = (self.difficulty_index - 1) % len(DIFFICULTIES)
            self.sound.play("menu_select")
        elif key == pygame.K_RIGHT:
            self.difficulty_index = (self.difficulty_index + 1) % len(DIFFICULTIES)
            self.sound.play("menu_select")
        elif key == pygame.K_h:
            self.sound.play("menu_select")
            self.state = STATE_HIGH_SCORES
        elif key == pygame.K_ESCAPE:
            self.sound.play("menu_select")
            self.running = False

    def _handle_playing_key(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_p:
            self.state = STATE_PAUSED

    def _handle_paused_key(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_p:
            self.state = STATE_PLAYING
        elif key == pygame.K_q:
            self.state = STATE_MENU
            self.reset_game()

    def _handle_game_over_key(self, key):
        if key == pygame.K_RETURN or key == pygame.K_SPACE:
            self.state = STATE_MENU
            self.reset_game()
        elif key == pygame.K_r:
            self.start_game()
        elif key == pygame.K_ESCAPE:
            self.state = STATE_MENU
            self.reset_game()

    def _handle_high_scores_key(self, key):
        if key == pygame.K_ESCAPE or key == pygame.K_RETURN or key == pygame.K_SPACE:
            self.state = STATE_MENU

    def _handle_menu_mouse(self, pos):
        # Handled in draw_menu with hover effects
        pass

    def _handle_menu_click(self, pos):
        # Check if click is on Start button
        btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 280, 200, 50)
        if btn_rect.collidepoint(pos):
            self.sound.play("menu_select")
            self.start_game()
            return

        # Difficulty buttons
        for i in range(len(DIFFICULTIES)):
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120 + i * 120, 400, 100, 30)
            if btn_rect.collidepoint(pos):
                self.difficulty_index = i
                self.sound.play("menu_select")
                return

        # High scores button
        hs_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 470, 200, 50)
        if hs_rect.collidepoint(pos):
            self.sound.play("menu_select")
            self.state = STATE_HIGH_SCORES
            return

        # Quit button
        quit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 535, 200, 50)
        if quit_rect.collidepoint(pos):
            self.sound.play("menu_select")
            self.running = False

    def _handle_game_over_click(self, pos):
        stats_y = 360 if self.new_high_score else 340
        button_y = stats_y + 3 * 28 + 30
        restart_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, button_y, 200, 50)
        if restart_rect.collidepoint(pos):
            self.start_game()

        menu_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, button_y + 75, 200, 50)
        if menu_rect.collidepoint(pos):
            self.state = STATE_MENU
            self.reset_game()

    def start_game(self):
        """Start a new game with current settings."""
        self.state = STATE_PLAYING
        self._apply_difficulty()
        self.reset_game(keep_difficulty=True)
        self._start_countdown()

    def reset_game(self, keep_difficulty=False):
        """Reset all game state."""
        self.score = 0
        self.ai_score = 0
        self.lives = STARTING_LIVES
        self.combo = 0
        self.combo_timer = 0
        self.flash_message = ""
        self.flash_timer = 0
        self.flash_color = None
        self.flash_alpha = 0
        self.score_popup = 0
        self.ai_score_popup = 0
        self.new_high_score = False
        self.launch_timer = 0
        self.countdown_active = False
        self.countdown_frame = 0
        self.countdown_index = 0
        self.power_up_timer = random.randint(POWER_UP_INTERVAL_MIN, POWER_UP_INTERVAL_MAX)

        # Reset match stats
        self.stats = {
            "rallies": 0,
            "longest_rally": 0,
            "current_rally": 0,
            "aces": 0,
            "player_hits": 0,
            "ai_hits": 0,
            "power_hits": 0,
        }

        self.paddle.reset()
        self.paddle2.reset(x=SCREEN_WIDTH - PADDLE_X - PADDLE_WIDTH)
        self.ball.reset()
        self.particles.clear()
        self.shake = ScreenShake()

        if not keep_difficulty:
            self.difficulty_index = 1

    def update(self):
        """Main update loop - called every frame."""
        self.dt = self.clock.tick(FPS) / 16.67  # Normalize to ~60fps
        self.dt = max(0.5, min(self.dt, 2.0))  # Clamp dt

        # Always update starfield
        self.starfield.update(self.dt)

        if self.state == STATE_MENU:
            self.menu_ball.update()
        elif self.state == STATE_PLAYING:
            self._update_playing()
        elif self.state == STATE_GAME_OVER:
            self._update_game_over()

        # Always update particles
        self.particles.update()
        self.shake.update()

        # Score popup timers
        if self.score_popup > 0:
            self.score_popup -= 1
        if self.ai_score_popup > 0:
            self.ai_score_popup -= 1

    def _update_playing(self):
        """Update game logic while playing."""
        # Handle paddle input
        self.keys = pygame.key.get_pressed()

        # Player paddle (left) - pass dt for frame-rate independent movement
        if self.keys[pygame.K_UP] or self.keys[pygame.K_w]:
            self.paddle.move_up(self.dt)
        elif self.keys[pygame.K_DOWN] or self.keys[pygame.K_s]:
            self.paddle.move_down(self.dt)
        else:
            self.paddle.stop()

        self.paddle.update(self.dt)

        # AI paddle (right) - follows the ball
        self._update_ai()

        # Handle countdown
        if self.countdown_active:
            self._update_countdown()
            return

        # Ball launch delay (legacy, kept for safety)
        if self.launch_timer > 0:
            self.launch_timer -= 1
            return

        # Update ball
        self.ball.update()

        # Power-up timer
        if not self.ball.powered_up:
            self.power_up_timer -= 1
            if self.power_up_timer <= 0 and self.ball.vx != 0 and self.ball.vy != 0:
                self._activate_power_up()

        # Check wall collisions
        wall_event = self.ball.check_wall_collision()
        if wall_event == "wall_top" or wall_event == "wall_bottom":
            self.sound.play("wall_bounce")
            self.particles.emit_wall_hit(self.ball.x, self.ball.y)
        elif wall_event == "wall_right":
            # Player scores!
            self._on_player_score()
        elif wall_event == "wall_right_blocked":
            # Power-up blocked the goal — bounce back for a second chance
            self.sound.play("wall_bounce")
            self.particles.emit_wall_hit(self.ball.x, self.ball.y)
            self.particles.emit(self.ball.x, self.ball.y, (0, 255, 255), count=15, speed_multiplier=1.5)
            self.flash_message = "BLOCKED!"
            self.flash_timer = 30
            self.shake.trigger(intensity=3, duration=3)

        # Check player paddle collision (left side)
        if self.ball.check_paddle_collision(self.paddle):
            self.sound.play("paddle_hit")
            self.paddle.on_hit()
            self.shake.trigger(intensity=4, duration=4)
            self.particles.emit_paddle_hit(self.ball.x, self.ball.y)
            self.combo += 1
            self.combo_timer = 30  # Reset combo timer
            self.stats["player_hits"] += 1
            self.stats["current_rally"] += 1

            if self.combo > 1:
                self.sound.play("combo")
                self.particles.emit_combo(self.ball.x, self.ball.y, self.combo)

            if self.ball.powered_up:
                self.stats["power_hits"] += 1
                self.score += POWER_UP_BONUS
                self.flash_message = f"⚡ POWER HIT! +{POWER_UP_BONUS}"
                self.flash_timer = 50
                self._deactivate_power_up()
                self.particles.emit_score(self.ball.x, self.ball.y)

        # Check AI paddle collision (right side)
        if self.ball.check_paddle2_collision(self.paddle2):
            self.sound.play("paddle_hit")
            self.paddle2.on_hit()
            self.particles.emit_paddle_hit(self.ball.x, self.ball.y)
            self.stats["ai_hits"] += 1
            self.stats["current_rally"] += 1

            if self.ball.powered_up:
                self.stats["power_hits"] += 1
                self.ai_score += POWER_UP_BONUS
                self.flash_message = f"⚡ AI POWER HIT! +{POWER_UP_BONUS}"
                self.flash_timer = 50
                self._deactivate_power_up()
                self.particles.emit_score(self.ball.x, self.ball.y)

                if self.ai_score >= self.max_score:
                    self._on_game_over(victory=False)
                    return

        # Check if ball passed left wall (player missed — AI also scores)
        if self.ball.x - self.ball.radius <= 0:
            if self.ball.powered_up:
                # Power-up blocked the goal — bounce back for a second chance
                self.ball.x = self.ball.radius
                self.ball.vx = abs(self.ball.vx)
                self.ball.vy += random.uniform(-0.5, 0.5)  # Prevent horizontal dead zone
                self.sound.play("wall_bounce")
                self.particles.emit_wall_hit(self.ball.x, self.ball.y)
                self.particles.emit(self.ball.x, self.ball.y, (0, 255, 255), count=15, speed_multiplier=1.5)
                self.flash_message = "BLOCKED!"
                self.flash_timer = 30
                self.shake.trigger(intensity=3, duration=3)
            else:
                self._on_ai_score()

        # Combo timer decay
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0

    def _update_ai(self):
        """Update AI paddle movement with predictive tracking and smooth lag."""
        paddle_center = self.paddle2.y + self.paddle2.height / 2
        ball = self.ball

        # Predict where the ball will be when it reaches the paddle's X position
        if ball.vx > 0 and abs(ball.vx) > 0.1:
            # Time for ball to reach AI paddle
            dx = self.paddle2.x - ball.x
            time_to_reach = dx / ball.vx
            raw_prediction = ball.y + ball.vy * time_to_reach

            # Account for wall bounces
            if raw_prediction < 0 or raw_prediction > SCREEN_HEIGHT:
                bounces = int(abs(raw_prediction) / SCREEN_HEIGHT)
                remainder = abs(raw_prediction) % SCREEN_HEIGHT
                if bounces % 2 == 0:
                    target_y = remainder
                else:
                    target_y = SCREEN_HEIGHT - remainder
            else:
                target_y = raw_prediction

            target_y = max(0, min(SCREEN_HEIGHT, target_y))
        else:
            target_y = ball.y

        # Smoothly lag the AI's target (natural reaction delay)
        # Lag factor: Hard=0.95 (fast tracking), Easy=0.6 (slow/lazy)
        lag_factor = 0.5 + self.difficulty_index * 0.2
        self._ai_target_y += (target_y - self._ai_target_y) * lag_factor

        # Move toward the lagged target position
        diff = self._ai_target_y - paddle_center

        # Precision and speed based on difficulty
        reaction_speed = self.difficulty["paddle_speed"] * (0.55 + self.difficulty_index * 0.2)
        dead_zone = max(4, 20 - self.difficulty_index * 5)  # Smaller = more precise

        if abs(diff) > dead_zone:
            self.paddle2.velocity = reaction_speed if diff > 0 else -reaction_speed
        else:
            # Fine-tuning near target
            self.paddle2.velocity = diff * 0.15

        self.paddle2.update(self.dt)

    def _start_countdown(self):
        """Start the serve countdown."""
        self.countdown_active = True
        self.countdown_frame = 0
        self.countdown_index = 0
        self.ball.reset()

    def _update_countdown(self):
        """Update countdown state."""
        self.countdown_frame += 1
        frames_per_number = COUNTDOWN_FRAMES // len(COUNTDOWN_NUMBERS)
        new_index = min(self.countdown_frame // frames_per_number, len(COUNTDOWN_NUMBERS) - 1)

        if new_index != self.countdown_index:
            self.countdown_index = new_index
            if COUNTDOWN_NUMBERS[self.countdown_index] == "GO!":
                self.sound.play("go")
            else:
                self.sound.play("countdown")

        if self.countdown_frame >= COUNTDOWN_FRAMES:
            self.countdown_active = False
            # Launch the ball
            direction = 1 if random.random() < 0.5 else -1
            if direction == 1:
                self.ball.launch(angle=random.uniform(-math.pi / 3, math.pi / 3))
            else:
                self.ball.launch(angle=random.uniform(math.pi * 2 / 3, math.pi * 4 / 3))

    def _activate_power_up(self):
        """Activate the power-up — ball glows and speeds up."""
        self.ball.powered_up = True
        self.sound.play("power_up")
        # Immediate speed boost
        self.ball.vx *= POWER_UP_SPEED_MULT
        self.ball.vy *= POWER_UP_SPEED_MULT
        self.flash_message = "⚡ POWER BALL ⚡"
        self.flash_timer = 50
        self.shake.trigger(intensity=3, duration=6)
        # Celebration particles
        self.particles.emit(
            self.ball.x, self.ball.y,
            (0, 255, 255),
            count=25,
            speed_multiplier=2.0,
        )

    def _deactivate_power_up(self):
        """Deactivate the power-up and reset the timer."""
        if self.ball.powered_up:
            self.ball.powered_up = False
            self.ball.vx /= POWER_UP_SPEED_MULT
            self.ball.vy /= POWER_UP_SPEED_MULT
        self.power_up_timer = random.randint(POWER_UP_INTERVAL_MIN, POWER_UP_INTERVAL_MAX)

    def _on_player_score(self):
        """Handle player scoring."""
        self.score += 1
        self.score_popup = 20
        self.sound.play("score")
        self._trigger_flash(COLOR_ACCENT)
        self.particles.emit_score(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2)

        # Track rally stats
        self.stats["rallies"] += 1
        if self.stats["current_rally"] > self.stats["longest_rally"]:
            self.stats["longest_rally"] = self.stats["current_rally"]
        self.stats["current_rally"] = 0

        # Check win
        if self.score >= self.max_score:
            self._on_game_over(victory=True)
            return

        # Deactivate power-up and reset timer
        self._deactivate_power_up()

        # Start countdown for next serve
        self._start_countdown()

        # Flash message
        self.flash_message = f"Point! ({self.score})"
        self.flash_timer = 60

    def _on_ai_score(self):
        """Handle AI scoring."""
        self.lives -= 1
        self.ai_score += 1
        self.ai_score_popup = 20
        self.sound.play("life_lost")
        self._trigger_flash(COLOR_RED)
        self.particles.emit_lost_ball(0, self.ball.y)
        self.shake.trigger(intensity=8, duration=6)

        # Track rally stats
        self.stats["rallies"] += 1
        if self.stats["current_rally"] > self.stats["longest_rally"]:
            self.stats["longest_rally"] = self.stats["current_rally"]
        self.stats["current_rally"] = 0

        if self.lives <= 0:
            self._on_game_over(victory=False)
            return

        # Deactivate power-up and reset timer
        self._deactivate_power_up()

        # Start countdown for next serve
        self._start_countdown()

        self.flash_message = f"Life lost! ({self.lives} remaining)"
        self.flash_timer = 60

    def _trigger_flash(self, color):
        """Trigger a screen flash effect."""
        self.flash_color = color
        self.flash_alpha = 120

    def _on_game_over(self, victory=False):
        """Handle game over state."""
        self.state = STATE_GAME_OVER
        if victory:
            self.sound.play("victory")
            self.flash_message = "VICTORY!"
            self._trigger_flash(COLOR_GREEN)
            self.flash_timer = 90
            self.shake.trigger(intensity=10, duration=20)
            # Big celebration particles
            for _ in range(8):
                self.particles.emit_score(
                    random.randint(200, SCREEN_WIDTH - 200),
                    random.randint(100, SCREEN_HEIGHT - 100),
                )
                self.particles.emit_confetti(
                    random.randint(100, SCREEN_WIDTH - 100),
                    random.randint(50, SCREEN_HEIGHT - 50),
                )
        else:
            self.sound.play("game_over")
            self.flash_message = "GAME OVER"
            self._trigger_flash(COLOR_RED)
            self.shake.trigger(intensity=12, duration=12)
            self.particles.emit_lost_ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            # Extra dramatic particles
            for _ in range(3):
                self.particles.emit_lost_ball(
                    random.randint(100, SCREEN_WIDTH - 100),
                    random.randint(100, SCREEN_HEIGHT - 100),
                )

        # Check high score
        diff_name = DIFFICULTIES[self.difficulty_index]["name"]
        self.new_high_score = self.high_score_mgr.add_score(self.score, diff_name)

    def _update_game_over(self):
        """Update effects during game over."""
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def _draw_gradient_bg(self, surface):
        """Draw a gradient background."""
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(COLOR_BG_TOP[0] * (1 - ratio) + COLOR_BG_BOTTOM[0] * ratio)
            g = int(COLOR_BG_TOP[1] * (1 - ratio) + COLOR_BG_BOTTOM[1] * ratio)
            b = int(COLOR_BG_TOP[2] * (1 - ratio) + COLOR_BG_BOTTOM[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_center_line(self, surface):
        """Draw the dashed center line."""
        dash_len = 15
        gap_len = 10
        center_x = SCREEN_WIDTH // 2
        line_color = (60, 60, 80)  # Dim color (alpha not supported on display surface)
        for y in range(0, SCREEN_HEIGHT, dash_len + gap_len):
            pygame.draw.line(
                surface,
                line_color,
                (center_x, y),
                (center_x, y + dash_len),
                2,
            )

    def draw(self):
        """Main render call."""
        # Apply screen shake offset
        shake_offset = self.shake.offset

        # Draw background
        self._draw_gradient_bg(self.screen)
        self.starfield.draw(self.screen)
        self._draw_center_line(self.screen)

        if self.state == STATE_MENU:
            self.menu_ball.draw(self.screen)
            self._draw_menu()
        elif self.state == STATE_PLAYING:
            self._draw_game(shake_offset)
            self._draw_hud()
            if self.countdown_active:
                self._draw_countdown()
        elif self.state == STATE_PAUSED:
            self._draw_game(shake_offset)
            self._draw_hud()
            self._draw_pause_overlay()
        elif self.state == STATE_GAME_OVER:
            self._draw_game(shake_offset)
            self._draw_hud()
            self._draw_game_over()
        elif self.state == STATE_HIGH_SCORES:
            self._draw_high_scores()

        # Draw screen flash overlay
        self._draw_flash()

        # Draw particles on top of everything
        self.particles.draw(self.screen, shake_offset)

        pygame.display.flip()

    def _draw_flash(self):
        """Draw screen flash overlay."""
        if self.flash_color and self.flash_alpha > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*self.flash_color[:3], int(self.flash_alpha)))
            self.screen.blit(flash_surf, (0, 0))
            self.flash_alpha = max(0, self.flash_alpha - (120 // FLASH_DURATION))
            if self.flash_alpha <= 0:
                self.flash_color = None

    def _draw_countdown(self):
        """Draw the serve countdown animation."""
        total_frames = COUNTDOWN_FRAMES
        frames_per_number = total_frames // len(COUNTDOWN_NUMBERS)
        idx = min(self.countdown_frame // frames_per_number, len(COUNTDOWN_NUMBERS) - 1)
        number_text = COUNTDOWN_NUMBERS[idx]

        # Calculate pulse scale
        progress_in_step = (self.countdown_frame % frames_per_number) / frames_per_number
        # Scale: start big, shrink to normal
        if number_text == "GO!":
            scale = 0.8 + 0.3 * (1 - progress_in_step)
            color = COLOR_GREEN
        else:
            scale = 1.0 + 1.5 * (1 - progress_in_step) * 0.5
            color = COLOR_ACCENT2

        # Fade out near the end of each step
        fade = 1.0 if progress_in_step < 0.7 else (1.0 - (progress_in_step - 0.7) / 0.3)

        # Render number using cached font, scale for animation
        base_text = self._countdown_font.render(number_text, True, color)
        base_shadow = self._countdown_font.render(number_text, True, (0, 0, 0))

        scaled_w = int(base_text.get_width() * scale)
        scaled_h = int(base_text.get_height() * scale)
        if scaled_w > 0 and scaled_h > 0:
            text = pygame.transform.scale(base_text, (scaled_w, scaled_h))
            shadow = pygame.transform.scale(base_shadow, (scaled_w, scaled_h))
        else:
            text = base_text
            shadow = base_shadow

        text.set_alpha(int(255 * fade))
        shadow.set_alpha(int(100 * fade))

        self.screen.blit(
            shadow,
            (SCREEN_WIDTH // 2 - text.get_width() // 2 + 4,
             SCREEN_HEIGHT // 2 - text.get_height() // 2 + 4),
        )

        self.screen.blit(
            text,
            (SCREEN_WIDTH // 2 - text.get_width() // 2,
             SCREEN_HEIGHT // 2 - text.get_height() // 2),
        )

    def _draw_game(self, shake_offset=(0, 0)):
        """Draw game objects."""
        # Draw paddles with offset
        self.paddle.draw(self.screen)
        self.paddle2.draw(self.screen)

        # Draw ball (only if not in menu)
        if self.state != STATE_MENU:
            self.ball.draw(self.screen)

    def _draw_hud(self):
        """Draw heads-up display."""
        # Score
        player_score_text = FONT_SCORE.render(str(self.score), True, COLOR_ACCENT)
        ai_score_text = FONT_SCORE.render(str(self.ai_score), True, COLOR_TEXT)

        # Draw with shadow
        shadow_offset = 2

        # Player score (left — same side as player paddle)
        player_x = SCREEN_WIDTH // 4
        self.screen.blit(player_score_text, (player_x - player_score_text.get_width() // 2 + shadow_offset, 30 + shadow_offset))
        self.screen.blit(player_score_text, (player_x - player_score_text.get_width() // 2, 30))

        # Player label
        player_label = FONT_SMALL.render("YOU", True, COLOR_ACCENT)
        player_label.set_alpha(160)
        self.screen.blit(player_label, (player_x - player_label.get_width() // 2, 80))

        # AI score (right)
        ai_x = SCREEN_WIDTH * 3 // 4
        self.screen.blit(ai_score_text, (ai_x - ai_score_text.get_width() // 2 + shadow_offset, 30 + shadow_offset))
        self.screen.blit(ai_score_text, (ai_x - ai_score_text.get_width() // 2, 30))

        # AI label
        ai_label = FONT_SMALL.render("AI", True, COLOR_TEXT)
        ai_label.set_alpha(160)
        self.screen.blit(ai_label, (ai_x - ai_label.get_width() // 2, 80))

        # Power-up indicator
        if self.ball.powered_up:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.008))
            power_label = FONT_SUBTITLE.render("⚡ POWER BALL ⚡", True, (0, 255, 255))
            power_label.set_alpha(int(150 + 105 * pulse))
            self.screen.blit(
                power_label,
                (SCREEN_WIDTH // 2 - power_label.get_width() // 2, 140),
            )

        # Lives with pulsing heart
        if self.lives <= 1 and self.state == STATE_PLAYING:
            # Pulse when on last life
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.006))
            heart_color = (255, int(50 + 100 * pulse), int(50 + 100 * pulse))
            lives_text = "♥" * self.lives
            lives_render = FONT_BODY.render(lives_text, True, heart_color)
            lives_render.set_alpha(int(180 + 75 * pulse))
        else:
            lives_text = "♥" * self.lives
            lives_render = FONT_BODY.render(lives_text, True, COLOR_RED)
        self.screen.blit(lives_render, (20, SCREEN_HEIGHT - 40))

        # Score popups (floating +1 animation)
        if self.score_popup > 0:
            popup_alpha = int(255 * (self.score_popup / 20))
            popup_y_offset = int(30 * (1 - self.score_popup / 20))
            popup_text = FONT_SUBTITLE.render("+1", True, COLOR_GREEN)
            popup_text.set_alpha(popup_alpha)
            self.screen.blit(
                popup_text,
                (player_x + 40, 25 - popup_y_offset),
            )
        if self.ai_score_popup > 0:
            popup_alpha = int(255 * (self.ai_score_popup / 20))
            popup_y_offset = int(30 * (1 - self.ai_score_popup / 20))
            popup_text = FONT_SUBTITLE.render("+1", True, COLOR_RED)
            popup_text.set_alpha(popup_alpha)
            self.screen.blit(
                popup_text,
                (ai_x + 40, 25 - popup_y_offset),
            )

        # Rally counter
        if self.state == STATE_PLAYING and self.stats["current_rally"] > 1:
            rally_render = FONT_SMALL.render(f"Rally: {self.stats['current_rally']}", True, COLOR_TEXT)
            rally_render.set_alpha(120)
            self.screen.blit(
                rally_render,
                (SCREEN_WIDTH // 2 - rally_render.get_width() // 2, 180),
            )

        # Combo display
        if self.combo > 1 and self.combo_timer > 0:
            combo_text = FONT_SUBTITLE.render(f"Combo x{self.combo}", True, COLOR_ORANGE)
            self.screen.blit(combo_text, (SCREEN_WIDTH // 2 - combo_text.get_width() // 2, 100))

        # Flash message
        if self.flash_timer > 0:
            alpha = min(255, int(255 * (self.flash_timer / 60)))
            color = COLOR_GREEN if "VICTORY" in self.flash_message or "Point" in self.flash_message else COLOR_ORANGE
            flash_render = FONT_SUBTITLE.render(self.flash_message, True, color)
            flash_render.set_alpha(alpha)
            self.screen.blit(
                flash_render,
                (SCREEN_WIDTH // 2 - flash_render.get_width() // 2, SCREEN_HEIGHT // 2 - 80),
            )

    def _draw_pause_overlay(self):
        """Draw pause overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        pause_text = FONT_TITLE.render("PAUSED", True, COLOR_ACCENT2)
        self.screen.blit(
            pause_text,
            (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60),
        )

        hint_text = FONT_BODY.render("Press ESC or P to resume  |  Q to quit", True, COLOR_TEXT)
        self.screen.blit(
            hint_text,
            (SCREEN_WIDTH // 2 - hint_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20),
        )

    def _draw_menu(self):
        """Draw the main menu."""
        # Title with glow effect
        title = FONT_TITLE.render("PONG STRIKE", True, COLOR_ACCENT2)
        title_shadow = FONT_TITLE.render("PONG STRIKE", True, (0, 0, 0))

        # Pulsing title
        pulse = math.sin(pygame.time.get_ticks() * 0.003) * 0.1 + 0.9
        scaled_title = pygame.transform.scale(
            title,
            (int(title.get_width() * pulse), int(title.get_height() * pulse)),
        )

        title_x = SCREEN_WIDTH // 2 - scaled_title.get_width() // 2
        title_y = 120 - (scaled_title.get_height() - title.get_height()) // 2

        # Draw shadow first
        self.screen.blit(title_shadow, (title_x + 3, title_y + 3))
        self.screen.blit(scaled_title, (title_x, title_y))

        # Subtitle
        subtitle = FONT_SUBTITLE.render("A modern classic reimagined", True, COLOR_TEXT)
        self.screen.blit(
            subtitle,
            (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 200),
        )

        # Draw buttons
        self._draw_menu_button("START GAME", SCREEN_WIDTH // 2 - 100, 280, 200, 50, COLOR_ACCENT2)
        self._draw_difficulty_selector()
        self._draw_menu_button("HIGH SCORES", SCREEN_WIDTH // 2 - 100, 470, 200, 50, COLOR_TEXT)
        self._draw_menu_button("QUIT", SCREEN_WIDTH // 2 - 100, 535, 200, 50, COLOR_RED)

        # Controls hint
        controls = [
            "↑/W - Move Up   ↓/S - Move Down",
            "P/ESC - Pause   H - High Scores",
        ]
        for i, text in enumerate(controls):
            rendered = FONT_SMALL.render(text, True, COLOR_TEXT)
            rendered.set_alpha(140)
            self.screen.blit(
                rendered,
                (SCREEN_WIDTH // 2 - rendered.get_width() // 2, 620 + i * 25),
            )

    def _draw_menu_button(self, text, x, y, w, h, accent_color):
        """Draw a menu button with hover effect."""
        mouse_pos = pygame.mouse.get_pos()
        btn_rect = pygame.Rect(x, y, w, h)
        hovered = btn_rect.collidepoint(mouse_pos)

        # Button background
        color = COLOR_BUTTON_HOVER if hovered else COLOR_BUTTON
        pygame.draw.rect(self.screen, color, btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, accent_color, btn_rect, width=2, border_radius=8)

        # Glow on hover
        if hovered:
            glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
            for i in range(10, 0, -2):
                alpha = int(20 * (i / 10))
                glow_rect = pygame.Rect(10 - i, 10 - i, w + i * 2, h + i * 2)
                pygame.draw.rect(
                    glow,
                    (*accent_color[:3], alpha),
                    glow_rect,
                    border_radius=12,
                )
            self.screen.blit(glow, (x - 10, y - 10))

        # Button text
        text_render = FONT_BODY.render(text, True, COLOR_TEXT if not hovered else accent_color)
        self.screen.blit(text_render, (x + w // 2 - text_render.get_width() // 2, y + h // 2 - text_render.get_height() // 2))

    def _draw_difficulty_selector(self):
        """Draw the difficulty selection row."""
        label = FONT_SMALL.render("Difficulty:", True, COLOR_TEXT)
        self.screen.blit(label, (SCREEN_WIDTH // 2 - 120, 376))

        for i, diff in enumerate(DIFFICULTIES):
            x = SCREEN_WIDTH // 2 - 120 + i * 120
            y = 400
            w = 100
            h = 30

            rect = pygame.Rect(x, y, w, h)
            selected = i == self.difficulty_index
            color = COLOR_ACCENT if selected else COLOR_BUTTON
            border_color = COLOR_ACCENT2 if selected else (60, 60, 60)

            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            pygame.draw.rect(self.screen, border_color, rect, width=2 if selected else 1, border_radius=6)

            text_render = FONT_SMALL.render(diff["name"], True, COLOR_TEXT)
            self.screen.blit(text_render, (x + w // 2 - text_render.get_width() // 2, y + 5))

    def _draw_game_over(self):
        """Draw game over screen overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        is_victory = self.score >= self.max_score
        title_color = COLOR_GREEN if is_victory else COLOR_RED
        title_text = "VICTORY!" if is_victory else "GAME OVER"

        # Title with pulsing glow
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.004))
        title_render = FONT_TITLE.render(title_text, True, title_color)

        # Glow effect for title
        for glow_i in range(3, 0, -1):
            glow_alpha = int(40 * pulse / glow_i)
            glow_surf = FONT_TITLE.render(title_text, True, title_color)
            glow_surf.set_alpha(glow_alpha)
            self.screen.blit(
                glow_surf,
                (SCREEN_WIDTH // 2 - glow_surf.get_width() // 2 + glow_i * 2,
                 150 - glow_i * 2),
            )

        self.screen.blit(
            title_render,
            (SCREEN_WIDTH // 2 - title_render.get_width() // 2, 150),
        )

        # Score summary
        score_text = FONT_SCORE.render(f"{self.score} - {self.ai_score}", True, COLOR_ACCENT)
        self.screen.blit(
            score_text,
            (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 240),
        )

        diff_text = FONT_SUBTITLE.render(f"Difficulty: {self.difficulty['name']}", True, COLOR_TEXT)
        self.screen.blit(
            diff_text,
            (SCREEN_WIDTH // 2 - diff_text.get_width() // 2, 300),
        )

        # High score notification
        if self.new_high_score:
            hs_pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            hs_text = FONT_BODY.render("★ NEW HIGH SCORE! ★", True, COLOR_ACCENT)
            hs_text.set_alpha(int(150 + 105 * hs_pulse))

            # Star sparkles around the text
            sparkle_x = SCREEN_WIDTH // 2 - hs_text.get_width() // 2 + hs_pulse * hs_text.get_width()
            sparkle_y = 350 + 5 * math.sin(pygame.time.get_ticks() * 0.01)
            self.particles.emit(int(sparkle_x), int(sparkle_y), COLOR_ACCENT, count=1, speed_multiplier=0.5)

            self.screen.blit(
                hs_text,
                (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 350),
            )

        # Match statistics
        stats_y = 360
        if not self.new_high_score:
            stats_y = 340

        stats_lines = [
            f"Rallies: {self.stats['rallies']}",
            f"Longest Rally: {self.stats['longest_rally']} hits",
            f"Player Hits: {self.stats['player_hits']}",
        ]
        for i, line in enumerate(stats_lines):
            stat_render = FONT_SMALL.render(line, True, COLOR_TEXT)
            stat_render.set_alpha(160)
            self.screen.blit(
                stat_render,
                (SCREEN_WIDTH // 2 - stat_render.get_width() // 2, stats_y + i * 28),
            )

        # Buttons with keyboard hints
        button_y = stats_y + len(stats_lines) * 28 + 30
        self._draw_menu_button("PLAY AGAIN", SCREEN_WIDTH // 2 - 100, button_y, 200, 50, COLOR_GREEN)
        hint1 = FONT_SMALL.render("[ Enter / Space ]", True, COLOR_TEXT)
        hint1.set_alpha(100)
        self.screen.blit(hint1, (SCREEN_WIDTH // 2 - hint1.get_width() // 2, button_y + 55))

        self._draw_menu_button("MAIN MENU", SCREEN_WIDTH // 2 - 100, button_y + 75, 200, 50, COLOR_ACCENT2)
        hint2 = FONT_SMALL.render("[ Escape ]", True, COLOR_TEXT)
        hint2.set_alpha(100)
        self.screen.blit(hint2, (SCREEN_WIDTH // 2 - hint2.get_width() // 2, button_y + 130))

    def _draw_high_scores(self):
        """Draw the high scores screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        title = FONT_TITLE.render("HIGH SCORES", True, COLOR_ACCENT)
        self.screen.blit(
            title,
            (SCREEN_WIDTH // 2 - title.get_width() // 2, 80),
        )

        scores = self.high_score_mgr.get_scores()
        if not scores:
            empty_text = FONT_BODY.render("No scores yet. Play a game!", True, COLOR_TEXT)
            self.screen.blit(
                empty_text,
                (SCREEN_WIDTH // 2 - empty_text.get_width() // 2, 300),
            )
        else:
            # Header
            header = FONT_SMALL.render(f"{'#':<4} {'Score':<8} {'Difficulty':<12} {'Date':<20}", True, COLOR_ACCENT2)
            self.screen.blit(header, (SCREEN_WIDTH // 2 - 180, 160))

            for i, entry in enumerate(scores[:10]):
                color = COLOR_ACCENT if i == 0 else COLOR_TEXT
                row = f"{i + 1:<4} {entry['score']:<8} {entry.get('difficulty', 'Medium'):<12} {entry.get('date', 'N/A'):<20}"
                row_render = FONT_BODY.render(row, True, color)
                self.screen.blit(row_render, (SCREEN_WIDTH // 2 - 180, 200 + i * 35))

        # Back hint
        hint = FONT_BODY.render("Press any key to return", True, COLOR_TEXT)
        hint.set_alpha(120)
        self.screen.blit(
            hint,
            (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 80),
        )

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
