import json
import os

from . import state as s

SETTINGS_FILE_NAME = "settings.json"

DEFAULT_SETTINGS = {
    "main": {
        "auto_save_on_exit": True,
        "show_crosshair": True,
        "show_target_outline": True,
    },
    "graphics": {
        "chunk_radius": 4,
        "cave_render_range": 12,
        "max_chunk_builds_per_frame": 1,
        "water_update_interval": 0.2,
        "water_sim_margin_chunks": 2,
        "mountain_height_scale": 28,
        "tall_grass_spawn_threshold": 0.76,
    },
    "behavior": {
        "mouse_sensitivity": 0.1,
        "move_speed": 0.1,
        "crouch_speed": 0.05,
        "dash_speed_multiplier": 1.8,
        "dash_double_tap_window": 0.28,
    },
}

ALLOWED_OPTIONS = {
    "main": {
        "auto_save_on_exit": [True, False],
        "show_crosshair": [True, False],
        "show_target_outline": [True, False],
    },
    "graphics": {
        "chunk_radius": [3, 4, 5, 6, 7, 8],
        "cave_render_range": [8, 12, 16, 20, 24, 28],
        "max_chunk_builds_per_frame": [1, 2, 3, 4],
        "water_update_interval": [0.12, 0.16, 0.2, 0.25, 0.33],
        "water_sim_margin_chunks": [1, 2, 3, 4],
        "mountain_height_scale": [18, 24, 28, 34, 40],
        "tall_grass_spawn_threshold": [0.68, 0.72, 0.76, 0.8, 0.84],
    },
    "behavior": {
        "mouse_sensitivity": [0.05, 0.08, 0.1, 0.12, 0.16, 0.2],
        "move_speed": [0.08, 0.1, 0.12, 0.15],
        "crouch_speed": [0.04, 0.05, 0.06, 0.075],
        "dash_speed_multiplier": [1.4, 1.6, 1.8, 2.0, 2.2],
        "dash_double_tap_window": [0.2, 0.24, 0.28, 0.34, 0.4],
    },
}


def settings_path(base_dir):
    return os.path.join(base_dir, SETTINGS_FILE_NAME)


def _merge_with_defaults(data):
    merged = {}
    for section, defaults in DEFAULT_SETTINGS.items():
        merged[section] = {}
        user_section = data.get(section, {}) if isinstance(data, dict) else {}
        for key, default_value in defaults.items():
            value = user_section.get(key, default_value)
            allowed = ALLOWED_OPTIONS[section][key]
            if value not in allowed:
                value = default_value
            merged[section][key] = value
    return merged


def load_settings(base_dir):
    path = settings_path(base_dir)
    if not os.path.isfile(path):
        save_settings(base_dir, DEFAULT_SETTINGS)
        return _merge_with_defaults(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = DEFAULT_SETTINGS
    settings = _merge_with_defaults(data)
    save_settings(base_dir, settings)
    return settings


def save_settings(base_dir, settings):
    normalized = _merge_with_defaults(settings)
    with open(settings_path(base_dir), "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=True, indent=2)


def apply_settings_to_state(settings):
    normalized = _merge_with_defaults(settings)
    main = normalized["main"]
    graphics = normalized["graphics"]
    behavior = normalized["behavior"]

    s.AUTO_SAVE_ON_EXIT = main["auto_save_on_exit"]
    s.SHOW_CROSSHAIR = main["show_crosshair"]
    s.SHOW_TARGET_OUTLINE = main["show_target_outline"]

    s.CHUNK_RADIUS = graphics["chunk_radius"]
    s.CAVE_RENDER_RANGE = graphics["cave_render_range"]
    s.MAX_CHUNK_BUILDS_PER_FRAME = graphics["max_chunk_builds_per_frame"]
    s.WATER_UPDATE_INTERVAL = graphics["water_update_interval"]
    s.WATER_SIM_MARGIN_CHUNKS = graphics["water_sim_margin_chunks"]
    s.MOUNTAIN_HEIGHT_SCALE = graphics["mountain_height_scale"]
    s.TALL_GRASS_SPAWN_THRESHOLD = graphics["tall_grass_spawn_threshold"]

    s.MOUSE_SENSITIVITY = behavior["mouse_sensitivity"]
    s.MOVE_SPEED = behavior["move_speed"]
    s.CROUCH_SPEED = behavior["crouch_speed"]
    s.DASH_SPEED_MULTIPLIER = behavior["dash_speed_multiplier"]
    s.DASH_DOUBLE_TAP_WINDOW = behavior["dash_double_tap_window"]
