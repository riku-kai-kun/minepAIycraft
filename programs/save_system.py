import json
import os
from datetime import datetime

from . import state as s
from . import world

SAVE_FILE_NAME = "world.json"


def saves_root(base_dir):
    return os.path.join(base_dir, "saves")


def ensure_saves_dir(base_dir):
    os.makedirs(saves_root(base_dir), exist_ok=True)


def list_save_slots(base_dir):
    ensure_saves_dir(base_dir)
    root = saves_root(base_dir)
    slots = []
    for entry in os.scandir(root):
        if not entry.is_dir():
            continue
        if os.path.isfile(os.path.join(entry.path, SAVE_FILE_NAME)):
            slots.append((entry.name, entry.stat().st_mtime))
    slots.sort(key=lambda item: item[1], reverse=True)
    return [name for name, _ in slots]


def _new_slot_name():
    return datetime.now().strftime("save_%Y%m%d_%H%M%S")


def create_save_slot(base_dir, slot_name=None):
    ensure_saves_dir(base_dir)
    base_name = (slot_name or "").strip() or _new_slot_name()
    root = saves_root(base_dir)
    candidate = base_name
    suffix = 1
    while os.path.exists(os.path.join(root, candidate)):
        suffix += 1
        candidate = f"{base_name}_{suffix}"
    os.makedirs(os.path.join(root, candidate), exist_ok=False)
    return candidate


def _save_path(base_dir, slot_name):
    return os.path.join(saves_root(base_dir), slot_name, SAVE_FILE_NAME)


def _serialize():
    return {
        "version": 1,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "player": {
            "position": s.player.position,
            "velocity_y": s.player.velocity_y,
            "on_ground": s.player.on_ground,
            "crouching": s.player.crouching,
        },
        "camera": {"rotation": s.camera.rotation},
        "world": {
            "placed_blocks": [list(pos) for pos in sorted(s.PLACED_BLOCKS)],
            "removed_ground": [list(pos) for pos in sorted(s.REMOVED_GROUND)],
            "removed_stone": [list(pos) for pos in sorted(s.REMOVED_STONE)],
            "water_sources": [list(pos) for pos in sorted(s.WATER_SOURCES)],
        },
    }


def build_snapshot():
    return _serialize()


def apply_snapshot(snapshot_data):
    apply_loaded_data(snapshot_data)


def save_to_slot(base_dir, slot_name):
    ensure_saves_dir(base_dir)
    slot_dir = os.path.join(saves_root(base_dir), slot_name)
    os.makedirs(slot_dir, exist_ok=True)
    path = _save_path(base_dir, slot_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_serialize(), f, ensure_ascii=True, indent=2)
    return path


def load_from_slot(base_dir, slot_name):
    path = _save_path(base_dir, slot_name)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    apply_loaded_data(data)
    return path


def apply_loaded_data(data):
    world.init_world(generate_oceans=False)

    world_data = data.get("world", {})
    for pos in world_data.get("placed_blocks", []):
        world.add_placed_block((int(pos[0]), int(pos[1]), int(pos[2])))
    for pos in world_data.get("removed_ground", []):
        world.add_removed_ground((int(pos[0]), int(pos[1]), int(pos[2])))
    for pos in world_data.get("removed_stone", []):
        world.add_removed_stone((int(pos[0]), int(pos[1]), int(pos[2])))
    for pos in world_data.get("water_sources", []):
        world.add_water_source((int(pos[0]), int(pos[1]), int(pos[2])))

    player_data = data.get("player", {})
    position = player_data.get("position", [0.0, 0.0, 0.0])
    s.player.position = [float(position[0]), float(position[1]), float(position[2])]
    s.player.velocity_y = float(player_data.get("velocity_y", 0.0))
    s.player.on_ground = bool(player_data.get("on_ground", False))
    s.player.crouching = bool(player_data.get("crouching", False))

    camera_data = data.get("camera", {})
    rotation = camera_data.get("rotation", [0.0, 0.0])
    s.camera.rotation = [float(rotation[0]), float(rotation[1])]

    s.CHUNKS_NEED_UPDATE = True
    world.update_water_flow(force=True)
