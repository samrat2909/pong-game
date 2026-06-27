"""
PONG STRIKE - Sound Manager
Procedural sound generation using pygame's mixer.
All sounds are generated programmatically — no external audio files needed.
"""

import math
import array
import random

import pygame


# ─── Helper: generate raw PCM samples ───────────────────────────────────────

def _create_sound(wave_func, duration, volume=0.3):
    """
    Generate a pygame Sound from a waveform function.
    wave_func(frequency, t) -> sample value in [-1.0, 1.0]
    """
    try:
        if not pygame.mixer.get_init():
            return None
        sample_rate = pygame.mixer.get_init()[0]
        n_samples = int(sample_rate * duration)
        samples = array.array('h', [0]) * n_samples
        for i in range(n_samples):
            t = i / sample_rate
            sample = wave_func(t)
            # Clamp
            sample = max(-1.0, min(1.0, sample))
            samples[i] = int(volume * 32767 * sample)
        return pygame.mixer.Sound(buffer=bytes(samples))
    except Exception:
        return None


def _sine(freq, t):
    return math.sin(2 * math.pi * freq * t)


def _square(freq, t):
    return 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0


def _noise(freq, t):
    return random.uniform(-1, 1)


def _sweep(start_freq, end_freq, t, duration):
    freq = start_freq + (end_freq - start_freq) * (t / max(duration, 0.001))
    return math.sin(2 * math.pi * freq * t)


# ─── Sound generators ───────────────────────────────────────────────────────

def _gen_paddle_hit():
    """Short sharp hit sound."""
    def wave(t):
        freq = 300 + t * 2000  # Quick sweep up
        env = max(0, 1 - t / 0.1)  # Fast decay
        return math.sin(2 * math.pi * freq * t) * env
    return _create_sound(wave, 0.1, volume=0.25)


def _gen_wall_bounce():
    """Softer bounce sound."""
    def wave(t):
        freq = 200 + t * 1000
        env = max(0, 1 - t / 0.08)
        return math.sin(2 * math.pi * freq * t) * env
    return _create_sound(wave, 0.08, volume=0.15)


def _gen_score():
    """Rising two-tone score sound."""
    def wave(t):
        if t < 0.08:
            freq = 400
        elif t < 0.2:
            freq = 600
        else:
            freq = 800
        env = max(0, 1 - t / 0.35)
        return math.sin(2 * math.pi * freq * t) * env
    return _create_sound(wave, 0.35, volume=0.3)


def _gen_victory():
    """Celebratory ascending arpeggio."""
    def wave(t):
        notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
        note_dur = 0.15
        note_idx = min(int(t / note_dur), len(notes) - 1)
        freq = notes[note_idx]
        env = max(0, 1 - (t % note_dur) / note_dur)
        return math.sin(2 * math.pi * freq * t) * env
    return _create_sound(wave, 0.6, volume=0.3)


def _gen_game_over():
    """Descending sad tone."""
    def wave(t):
        freq = 400 - t * 300
        env = max(0, 1 - t / 0.5)
        return math.sin(2 * math.pi * freq * t) * env
    return _create_sound(wave, 0.5, volume=0.25)


def _gen_power_up():
    """Wobbling sci-fi power-up sound."""
    def wave(t):
        freq = 200 + t * 800
        wobble = 1 + 0.3 * math.sin(2 * math.pi * 30 * t)
        env = max(0, 1 - t / 0.4)
        return math.sin(2 * math.pi * freq * wobble * t) * env
    return _create_sound(wave, 0.4, volume=0.25)


def _gen_countdown_beep():
    """Short beep for countdown."""
    def wave(t):
        env = max(0, 1 - t / 0.12)
        return math.sin(2 * math.pi * 800 * t) * env
    return _create_sound(wave, 0.12, volume=0.2)


def _gen_go():
    """Higher, longer 'GO!' sound."""
    def wave(t):
        env = max(0, 1 - t / 0.25)
        return math.sin(2 * math.pi * 1000 * t) * env
    return _create_sound(wave, 0.25, volume=0.25)


def _gen_menu_select():
    """Soft click for menu selection."""
    def wave(t):
        env = max(0, 1 - t / 0.05)
        return math.sin(2 * math.pi * 500 * t) * env
    return _create_sound(wave, 0.05, volume=0.12)


def _gen_life_lost():
    """Low descending tone for losing a life."""
    def wave(t):
        freq = 300 - t * 400
        env = max(0, 1 - t / 0.4)
        return math.sin(2 * math.pi * freq * t) * env
    return _create_sound(wave, 0.4, volume=0.3)


def _gen_combo():
    """Rising chirp for combo hits."""
    def wave(t):
        freq = 500 + t * 1500
        env = max(0, 1 - t / 0.15)
        return math.sin(2 * math.pi * freq * t) * env
    return _create_sound(wave, 0.15, volume=0.2)


# ─── Sound Manager ──────────────────────────────────────────────────────────

class SoundManager:
    """Manages all game sounds. Generates them on init, plays on demand."""

    def __init__(self):
        self.enabled = True
        self._sounds = {}
        self._init_sounds()

    def _init_sounds(self):
        """Generate all sound effects."""
        try:
            # Try to initialize the mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        except Exception:
            self.enabled = False
            return

        self._sounds = {
            "paddle_hit": _gen_paddle_hit(),
            "wall_bounce": _gen_wall_bounce(),
            "score": _gen_score(),
            "victory": _gen_victory(),
            "game_over": _gen_game_over(),
            "power_up": _gen_power_up(),
            "countdown": _gen_countdown_beep(),
            "go": _gen_go(),
            "menu_select": _gen_menu_select(),
            "life_lost": _gen_life_lost(),
            "combo": _gen_combo(),
        }

        # If any sound failed, disable audio
        if any(s is None for s in self._sounds.values()):
            self.enabled = False

    def play(self, name):
        """Play a sound by name."""
        if not self.enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass

    def set_volume(self, vol):
        """Set volume for all sounds (0.0 to 1.0)."""
        for sound in self._sounds.values():
            if sound:
                try:
                    sound.set_volume(vol)
                except Exception:
                    pass
