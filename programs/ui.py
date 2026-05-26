import pygame
from pygame.locals import *
import os

from .settings_system import ALLOWED_OPTIONS


SETTINGS_LAYOUT = [
    ("main", "Main"),
    ("main", "language"),
    ("main", "auto_save_on_exit"),
    ("main", "show_crosshair"),
    ("main", "show_target_outline"),
    ("graphics", "Graphics"),
    ("graphics", "chunk_radius"),
    ("graphics", "cave_render_range"),
    ("graphics", "max_chunk_builds_per_frame"),
    ("graphics", "water_update_interval"),
    ("graphics", "water_sim_margin_chunks"),
    ("graphics", "mountain_height_scale"),
    ("graphics", "tall_grass_spawn_threshold"),
    ("behavior", "Behavior"),
    ("behavior", "mouse_sensitivity"),
    ("behavior", "move_speed"),
    ("behavior", "crouch_speed"),
    ("behavior", "dash_speed_multiplier"),
    ("behavior", "dash_double_tap_window"),
    ("controls", "Controls"),
    ("controls", "forward"),
    ("controls", "backward"),
    ("controls", "left"),
    ("controls", "right"),
    ("controls", "jump"),
    ("controls", "crouch"),
    ("controls", "sprint"),
    ("controls", "respawn"),
    ("controls", "save"),
    ("controls", "reload"),
    ("controls", "pause"),
]

DISPLAY_LABELS = {
    "language": "Language",
    "auto_save_on_exit": "Auto Save On Exit",
    "show_crosshair": "Show Crosshair",
    "show_target_outline": "Show Target Outline",
    "chunk_radius": "Chunk Radius",
    "cave_render_range": "Cave Render Range",
    "max_chunk_builds_per_frame": "Chunk Builds / Frame",
    "water_update_interval": "Water Update Interval",
    "water_sim_margin_chunks": "Water Sim Margin Chunks",
    "mountain_height_scale": "Mountain Height Scale",
    "tall_grass_spawn_threshold": "Tall Grass Density",
    "mouse_sensitivity": "Mouse Sensitivity",
    "move_speed": "Move Speed",
    "crouch_speed": "Crouch Speed",
    "dash_speed_multiplier": "Dash Speed Multiplier",
    "dash_double_tap_window": "Dash Double Tap Window",
    "forward": "Forward",
    "backward": "Backward",
    "left": "Left",
    "right": "Right",
    "jump": "Jump / Swim Up",
    "crouch": "Crouch",
    "sprint": "Sprint",
    "respawn": "Respawn",
    "save": "Save",
    "reload": "Reload",
    "pause": "Pause",
}

JA_LABELS = {
    "Language": "言語",
    "Auto Save On Exit": "終了時に自動保存",
    "Show Crosshair": "照準を表示",
    "Show Target Outline": "対象ブロック枠を表示",
    "Chunk Radius": "チャンク半径",
    "Cave Render Range": "洞窟描画範囲",
    "Chunk Builds / Frame": "フレーム毎チャンク構築",
    "Water Update Interval": "水更新間隔",
    "Water Sim Margin Chunks": "水シミュレーション余白",
    "Mountain Height Scale": "山の高さ",
    "Tall Grass Density": "草の密度",
    "Mouse Sensitivity": "マウス感度",
    "Move Speed": "移動速度",
    "Crouch Speed": "しゃがみ速度",
    "Dash Speed Multiplier": "ダッシュ倍率",
    "Dash Double Tap Window": "ダッシュ受付時間",
    "Forward": "前進",
    "Backward": "後退",
    "Left": "左移動",
    "Right": "右移動",
    "Jump / Swim Up": "ジャンプ / 浮上",
    "Crouch": "しゃがみ",
    "Sprint": "ダッシュ",
    "Respawn": "リスポーン",
    "Save": "保存",
    "Reload": "再読込",
    "Pause": "ポーズ",
    "Main": "基本",
    "Graphics": "描画",
    "Behavior": "操作感",
    "Controls": "キー設定",
}

UI_TEXT = {
    "en": {
        "new_save": "NEW SAVE",
        "load_selected": "LOAD SELECTED",
        "settings": "SETTINGS",
        "multiplayer": "MULTIPLAYER",
        "save_slots": "Save Slots",
        "no_saves": "No save files yet.",
        "home_info": "Choose NEW SAVE / LOAD / SETTINGS",
        "tip": "In game: Save/Reload keys are configurable",
        "paused": "Paused",
        "resume": "RESUME",
        "save_game": "SAVE GAME",
        "home": "HOME",
        "quit": "QUIT",
        "esc_resume": "ESC resumes the game",
        "apply": "APPLY",
        "back": "BACK",
        "press_key": "PRESS KEY",
        "settings_applied": "Settings applied",
        "multiplayer_title": "Multiplayer",
        "mp_desc": "Join with Room Code (ABC123) or Invite ID (MPC-...)",
        "mp_warn": "Warning: Network restrictions can prevent multiplayer connections.",
        "host_room": "HOST ROOM",
        "join_by_id": "JOIN BY ID",
        "required_version": "Required version",
    },
    "ja": {
        "new_save": "新規セーブ",
        "load_selected": "選択してロード",
        "settings": "設定",
        "multiplayer": "マルチプレイ",
        "save_slots": "セーブ一覧",
        "no_saves": "セーブデータはありません。",
        "home_info": "新規 / ロード / 設定を選択",
        "tip": "ゲーム内: 保存/再読込キーは設定で変更できます",
        "paused": "ポーズ",
        "resume": "再開",
        "save_game": "ゲーム保存",
        "home": "ホーム",
        "quit": "終了",
        "esc_resume": "ESCでゲームへ戻る",
        "apply": "適用",
        "back": "戻る",
        "press_key": "キーを押す",
        "settings_applied": "設定を適用しました",
        "multiplayer_title": "マルチプレイ",
        "mp_desc": "Room Code (ABC123) または Invite ID (MPC-...) で参加",
        "mp_warn": "注意: ネットワーク制限により接続できない場合があります。",
        "host_room": "部屋を作成",
        "join_by_id": "IDで参加",
        "required_version": "必要バージョン",
    },
}


def _lang(settings):
    return settings.get("main", {}).get("language", "ja")


def _text(settings, key):
    return UI_TEXT.get(_lang(settings), UI_TEXT["ja"]).get(key, UI_TEXT["en"].get(key, key))


def _label(settings, key):
    label = DISPLAY_LABELS.get(key, key)
    if _lang(settings) == "ja":
        return JA_LABELS.get(label, label)
    return label

_UI_ASSETS = None
_FONT_PATH = None


def _font_probe_text():
    texts = []
    for labels in (JA_LABELS,):
        texts.extend(str(value) for value in labels.values())
    for translations in UI_TEXT.values():
        texts.extend(str(value) for value in translations.values())
    texts.append("日本語 English 0123456789 /:-_.()")
    return "".join(texts)


def _candidate_font_paths():
    local_fonts_dir = "fonts"
    paths = [
        os.path.join(local_fonts_dir, "unifont-17.0.04.otf"),
        os.path.join(local_fonts_dir, "NotoSansCJKjp-Regular.otf"),
        os.path.join(local_fonts_dir, "NotoSansJP-Regular.otf"),
        os.path.join(local_fonts_dir, "ipaexg.ttf"),
        os.path.join(local_fonts_dir, "ipaexm.ttf"),
    ]
    if os.path.isdir(local_fonts_dir):
        for name in sorted(os.listdir(local_fonts_dir)):
            if name.lower().endswith((".ttf", ".ttc", ".otf")):
                paths.append(os.path.join(local_fonts_dir, name))

    # System fonts are only fallbacks when fonts/ has no usable font.
    paths.extend([
        "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc",
        "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc",
        os.path.expanduser("~/Library/Fonts/msgothic.ttc"),
        os.path.expanduser("~/Library/Fonts/msmincho.ttc"),
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        # Windows.
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
        "C:/Windows/Fonts/YuGothR.ttc",
        "C:/Windows/Fonts/msgothic.ttc",
        # Common Linux packages.
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    ])
    candidates = (
        "hiraginokakugothicpron",
        "hiraginokakugothicpro",
        "hiraginokakugothicstdn",
        "hiraginokakugothicstd",
        "msgothic",
        "msmincho",
        "meiryo",
        "yu gothic",
        "arial unicode",
        "hiragino sans",
        "hiraginosans",
        "noto sans cjk jp",
        "noto sans jp",
        "ipaexgothic",
        "apple sd gothic neo",
    )
    for name in candidates:
        path = pygame.font.match_font(name)
        if path:
            paths.append(path)

    seen = set()
    for path in paths:
        normalized = os.path.abspath(os.path.expanduser(path))
        if normalized in seen:
            continue
        seen.add(normalized)
        if os.path.isfile(normalized):
            yield normalized


def _font_missing_count(path, probe_text):
    try:
        font = pygame.font.Font(path, 24)
    except Exception:
        return None
    missing = 0
    for ch in set(probe_text):
        if ch.isspace():
            continue
        metrics = font.metrics(ch)
        if not metrics or metrics[0] is None:
            missing += 1
    return missing


def _font_path():
    global _FONT_PATH
    if _FONT_PATH is not None:
        return _FONT_PATH

    probe_text = _font_probe_text()
    best_path = ""
    best_missing = None
    for path in _candidate_font_paths():
        missing = _font_missing_count(path, probe_text)
        if missing is None:
            continue
        if missing == 0:
            _FONT_PATH = path
            return _FONT_PATH
        if best_missing is None or missing < best_missing:
            best_path = path
            best_missing = missing
    if best_path:
        _FONT_PATH = best_path
        return _FONT_PATH

    _FONT_PATH = ""
    return _FONT_PATH


def _ui_font(size):
    path = _font_path()
    if path:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    return pygame.font.SysFont(None, size)


def _menu_fonts():
    return (
        _ui_font(64),
        _ui_font(28),
        _ui_font(34),
        _ui_font(30),
    )


def _load_ui_assets():
    global _UI_ASSETS
    if _UI_ASSETS is not None:
        return _UI_ASSETS

    base = os.path.join("images", "UI")
    paths = {
        "btn_green": os.path.join(base, "btn_green.png"),
        "btn_blue": os.path.join(base, "btn_blue.png"),
        "btn_gold": os.path.join(base, "btn_gold.png"),
        "btn_gray": os.path.join(base, "btn_gray.png"),
        "slot_normal": os.path.join(base, "slot_normal.png"),
        "slot_selected": os.path.join(base, "slot_selected.png"),
    }
    assets = {}
    for key, path in paths.items():
        if os.path.isfile(path):
            assets[key] = pygame.image.load(path).convert_alpha()
        else:
            assets[key] = None
    _UI_ASSETS = assets
    return _UI_ASSETS


def _draw_image_button(screen, rect, img, fallback_color):
    if img is not None:
        scaled = pygame.transform.smoothscale(img, (rect.width, rect.height))
        screen.blit(scaled, rect.topleft)
    else:
        pygame.draw.rect(screen, fallback_color, rect, border_radius=8)


def _draw_slot_bg(screen, rect, img, fallback_bg, fallback_border):
    if img is not None:
        scaled = pygame.transform.smoothscale(img, (rect.width, rect.height))
        screen.blit(scaled, rect.topleft)
    else:
        pygame.draw.rect(screen, fallback_bg, rect, border_radius=5)
        pygame.draw.rect(screen, fallback_border, rect, width=2, border_radius=5)


def _copy_settings(settings):
    return {
        "main": dict(settings["main"]),
        "graphics": dict(settings["graphics"]),
        "behavior": dict(settings["behavior"]),
        "controls": dict(settings["controls"]),
    }


def _format_value(value):
    if isinstance(value, bool):
        return "ON" if value else "OFF"
    if value == "ja":
        return "日本語"
    if value == "en":
        return "English"
    if isinstance(value, float):
        return f"{value:.3g}"
    return str(value)


def _cycle_option(section, key, current, direction):
    options = ALLOWED_OPTIONS[section][key]
    try:
        idx = options.index(current)
    except ValueError:
        idx = 0
    idx = (idx + direction) % len(options)
    return options[idx]


def _key_name_from_event(event):
    return pygame.key.name(event.key).lower()


def _draw_main_menu(screen, fonts, screen_width, screen_height, save_slots, selected_slot, scroll_index, settings):
    title_font, info_font, button_font, slot_font = fonts
    assets = _load_ui_assets()

    new_button = pygame.Rect((screen_width // 2) - 280, screen_height // 2 - 10, 250, 58)
    load_button = pygame.Rect((screen_width // 2) + 30, screen_height // 2 - 10, 250, 58)
    settings_button = pygame.Rect((screen_width // 2) - 125, screen_height // 2 + 58, 250, 52)
    multiplayer_button = pygame.Rect((screen_width // 2) - 125, screen_height // 2 + 118, 250, 52)
    list_top = screen_height // 2 + 188

    mouse_pos = pygame.mouse.get_pos()
    hover_new = new_button.collidepoint(mouse_pos)
    hover_load = load_button.collidepoint(mouse_pos) and selected_slot is not None
    hover_settings = settings_button.collidepoint(mouse_pos)
    hover_multiplayer = multiplayer_button.collidepoint(mouse_pos)

    max_rows = max(1, (screen_height - list_top - 44) // 38)
    max_scroll = max(0, len(save_slots) - max_rows)
    scroll_index = min(scroll_index, max_scroll)
    slot_rects = []
    y = list_top
    for slot_name in save_slots[scroll_index:scroll_index + max_rows]:
        rect = pygame.Rect((screen_width // 2) - 280, y, 560, 34)
        slot_rects.append((slot_name, rect))
        y += 38

    screen.fill((190, 230, 255))

    title_surface = title_font.render("MinepAIycraft", True, (20, 30, 40))
    title_rect = title_surface.get_rect(center=(screen_width // 2, screen_height // 4))
    screen.blit(title_surface, title_rect)

    info_surface = info_font.render(_text(settings, "home_info"), True, (40, 55, 70))
    info_rect = info_surface.get_rect(center=(screen_width // 2, screen_height // 4 + 50))
    screen.blit(info_surface, info_rect)

    _draw_image_button(
        screen,
        new_button,
        assets["btn_green"],
        (80, 170, 90) if hover_new else (60, 140, 70),
    )
    new_label = button_font.render(_text(settings, "new_save"), True, (245, 255, 245))
    screen.blit(new_label, new_label.get_rect(center=new_button.center))

    load_color = (70, 130, 190) if hover_load else (55, 105, 155)
    if selected_slot is None:
        load_color = (120, 130, 140)
    load_img = assets["btn_blue"] if selected_slot is not None else assets["btn_gray"]
    _draw_image_button(screen, load_button, load_img, load_color)
    load_label = button_font.render(_text(settings, "load_selected"), True, (245, 250, 255))
    screen.blit(load_label, load_label.get_rect(center=load_button.center))

    _draw_image_button(
        screen,
        settings_button,
        assets["btn_gold"],
        (220, 185, 95) if hover_settings else (200, 165, 80),
    )
    settings_label = button_font.render(_text(settings, "settings"), True, (35, 25, 10))
    screen.blit(settings_label, settings_label.get_rect(center=settings_button.center))

    _draw_image_button(
        screen,
        multiplayer_button,
        assets["btn_blue"],
        (95, 155, 215) if hover_multiplayer else (75, 125, 185),
    )
    mp_label = button_font.render(_text(settings, "multiplayer"), True, (240, 248, 255))
    screen.blit(mp_label, mp_label.get_rect(center=multiplayer_button.center))

    list_title = info_font.render(_text(settings, "save_slots"), True, (20, 30, 40))
    screen.blit(list_title, (screen_width // 2 - 280, list_top - 32))

    if not save_slots:
        empty_text = slot_font.render(_text(settings, "no_saves"), True, (70, 80, 90))
        screen.blit(empty_text, (screen_width // 2 - 280, list_top + 6))
    else:
        for slot_name, rect in slot_rects:
            is_selected = slot_name == selected_slot
            _draw_slot_bg(
                screen,
                rect,
                assets["slot_selected"] if is_selected else assets["slot_normal"],
                (230, 245, 255) if is_selected else (210, 228, 242),
                (45, 90, 135) if is_selected else (120, 145, 165),
            )
            slot_surface = slot_font.render(slot_name, True, (20, 30, 40))
            screen.blit(slot_surface, (rect.x + 10, rect.y + 6))

    tip = info_font.render(_text(settings, "tip"), True, (40, 55, 70))
    tip_rect = tip.get_rect(center=(screen_width // 2, screen_height - 20))
    screen.blit(tip, tip_rect)

    return {
        "new_button": new_button,
        "load_button": load_button,
        "settings_button": settings_button,
        "multiplayer_button": multiplayer_button,
        "slot_rects": slot_rects,
        "hover_new": hover_new,
        "hover_load": hover_load,
        "max_scroll": max_scroll,
        "scroll_index": scroll_index,
    }


def _draw_multiplayer_menu(
    screen,
    fonts,
    screen_width,
    screen_height,
    join_id_text,
    join_input_active,
    status_text,
    required_version,
    settings,
):
    title_font, info_font, button_font, slot_font = fonts
    assets = _load_ui_assets()

    host_button = pygame.Rect((screen_width // 2) - 280, 186, 250, 60)
    join_button = pygame.Rect((screen_width // 2) + 30, 186, 250, 60)
    back_button = pygame.Rect((screen_width // 2) - 120, screen_height - 70, 240, 48)
    input_rect = pygame.Rect((screen_width // 2) - 280, 280, 560, 50)

    mouse_pos = pygame.mouse.get_pos()
    hover_host = host_button.collidepoint(mouse_pos)
    hover_join = join_button.collidepoint(mouse_pos) and bool(join_id_text.strip())
    hover_back = back_button.collidepoint(mouse_pos)

    screen.fill((184, 216, 245))

    title_surface = title_font.render(_text(settings, "multiplayer_title"), True, (18, 32, 50))
    title_rect = title_surface.get_rect(center=(screen_width // 2, 72))
    screen.blit(title_surface, title_rect)

    desc = info_font.render(_text(settings, "mp_desc"), True, (35, 55, 80))
    screen.blit(desc, desc.get_rect(center=(screen_width // 2, 114)))
    warn = info_font.render(
        _text(settings, "mp_warn"),
        True,
        (160, 42, 42),
    )
    screen.blit(warn, warn.get_rect(center=(screen_width // 2, 140)))

    _draw_image_button(
        screen,
        host_button,
        assets["btn_green"],
        (76, 152, 90) if hover_host else (60, 130, 74),
    )
    host_label = button_font.render(_text(settings, "host_room"), True, (244, 255, 244))
    screen.blit(host_label, host_label.get_rect(center=host_button.center))

    join_img = assets["btn_blue"] if join_id_text.strip() else assets["btn_gray"]
    _draw_image_button(
        screen,
        join_button,
        join_img,
        (85, 135, 190) if hover_join else (65, 115, 168),
    )
    join_label = button_font.render(_text(settings, "join_by_id"), True, (240, 248, 255))
    screen.blit(join_label, join_label.get_rect(center=join_button.center))

    pygame.draw.rect(screen, (246, 252, 255), input_rect, border_radius=8)
    pygame.draw.rect(
        screen,
        (44, 92, 143) if join_input_active else (108, 136, 162),
        input_rect,
        width=3,
        border_radius=8,
    )
    shown = join_id_text if join_id_text else "ABC123 or MPC-XXXX..."
    shown_color = (16, 28, 44) if join_id_text else (130, 146, 162)
    text_surface = slot_font.render(shown, True, shown_color)
    screen.blit(text_surface, (input_rect.x + 12, input_rect.y + 12))

    _draw_image_button(
        screen,
        back_button,
        assets["btn_gold"],
        (168, 141, 91) if hover_back else (143, 117, 74),
    )
    back_label = button_font.render(_text(settings, "back"), True, (32, 24, 14))
    screen.blit(back_label, back_label.get_rect(center=back_button.center))

    if status_text:
        status_surface = info_font.render(status_text, True, (95, 35, 35))
        screen.blit(status_surface, status_surface.get_rect(center=(screen_width // 2, 352)))

    note = info_font.render(f"{_text(settings, 'required_version')}: {required_version}", True, (55, 70, 88))
    screen.blit(note, note.get_rect(center=(screen_width // 2, screen_height - 110)))

    return {
        "host_button": host_button,
        "join_button": join_button,
        "back_button": back_button,
        "input_rect": input_rect,
        "hover_host": hover_host,
        "hover_join": hover_join,
        "hover_back": hover_back,
    }


def _draw_settings_menu(screen, fonts, screen_width, screen_height, editable_settings, scroll_index, binding_key=None):
    title_font, info_font, button_font, slot_font = fonts
    assets = _load_ui_assets()

    back_button = pygame.Rect((screen_width // 2) - 260, screen_height - 70, 220, 46)
    apply_button = pygame.Rect((screen_width // 2) + 40, screen_height - 70, 220, 46)

    mouse_pos = pygame.mouse.get_pos()
    hover_back = back_button.collidepoint(mouse_pos)
    hover_apply = apply_button.collidepoint(mouse_pos)

    all_rows = []
    for section, key in SETTINGS_LAYOUT:
        if key in ("Main", "Graphics", "Behavior", "Controls"):
            all_rows.append({"type": "header", "text": _label(editable_settings, key)})
            continue
        all_rows.append(
            {
                "type": "setting",
                "section": section,
                "key": key,
            }
        )

    max_visible_rows = max(1, (screen_height - 190) // 42)
    max_scroll = max(0, len(all_rows) - max_visible_rows)
    scroll_index = min(scroll_index, max_scroll)
    visible_rows = all_rows[scroll_index:scroll_index + max_visible_rows]

    rows = []
    y = 98

    screen.fill((240, 228, 200))

    title_surface = title_font.render("Settings", True, (35, 28, 15))
    title_rect = title_surface.get_rect(center=(screen_width // 2, 52))
    screen.blit(title_surface, title_rect)

    for item in visible_rows:
        if item["type"] == "header":
            row = {"type": "header", "text": item["text"], "y": y}
            text = info_font.render(row["text"], True, (65, 45, 20))
            screen.blit(text, (90, row["y"]))
            rows.append(row)
            y += 30
            continue

        row_rect = pygame.Rect(80, y, screen_width - 160, 38)
        left_rect = pygame.Rect(row_rect.right - 160, y + 5, 28, 28)
        right_rect = pygame.Rect(row_rect.right - 36, y + 5, 28, 28)
        row = {
            "type": "setting",
            "section": item["section"],
            "key": item["key"],
            "row_rect": row_rect,
            "left_rect": left_rect,
            "right_rect": right_rect,
        }
        rows.append(row)
        section = row["section"]
        key = row["key"]
        value = editable_settings[section][key]

        pygame.draw.rect(screen, (255, 246, 230), row["row_rect"], border_radius=6)
        pygame.draw.rect(screen, (165, 140, 95), row["row_rect"], width=2, border_radius=6)

        label = _label(editable_settings, key)
        label_surface = slot_font.render(label, True, (45, 32, 17))
        screen.blit(label_surface, (row["row_rect"].x + 10, row["row_rect"].y + 8))

        if section == "controls" and key == binding_key:
            value_text = _text(editable_settings, "press_key")
            value_color = (150, 45, 35)
        else:
            value_text = _format_value(value)
            value_color = (30, 75, 120)
        value_surface = slot_font.render(value_text, True, value_color)
        value_rect = value_surface.get_rect(center=(row["row_rect"].right - 84, row["row_rect"].centery))
        screen.blit(value_surface, value_rect)

        if section != "controls":
            pygame.draw.rect(screen, (200, 185, 150), row["left_rect"], border_radius=4)
            pygame.draw.rect(screen, (120, 95, 60), row["left_rect"], width=2, border_radius=4)
            pygame.draw.rect(screen, (200, 185, 150), row["right_rect"], border_radius=4)
            pygame.draw.rect(screen, (120, 95, 60), row["right_rect"], width=2, border_radius=4)

            left_text = button_font.render("<", True, (55, 45, 28))
            right_text = button_font.render(">", True, (55, 45, 28))
            screen.blit(left_text, left_text.get_rect(center=row["left_rect"].center))
            screen.blit(right_text, right_text.get_rect(center=row["right_rect"].center))
        y += 42

    _draw_image_button(
        screen,
        back_button,
        assets["btn_gold"],
        (170, 145, 95) if hover_back else (145, 120, 80),
    )
    back_label = button_font.render(_text(editable_settings, "back"), True, (35, 25, 15))
    screen.blit(back_label, back_label.get_rect(center=back_button.center))

    _draw_image_button(
        screen,
        apply_button,
        assets["btn_green"],
        (95, 170, 105) if hover_apply else (80, 145, 90),
    )
    apply_label = button_font.render(_text(editable_settings, "apply"), True, (245, 255, 245))
    screen.blit(apply_label, apply_label.get_rect(center=apply_button.center))

    return {
        "rows": rows,
        "back_button": back_button,
        "apply_button": apply_button,
        "hover_back": hover_back,
        "hover_apply": hover_apply,
        "max_scroll": max_scroll,
        "scroll_index": scroll_index,
    }


def _draw_pause_menu(screen, fonts, screen_width, screen_height, can_save, status_text, settings):
    title_font, info_font, button_font, _ = fonts
    assets = _load_ui_assets()
    mouse_pos = pygame.mouse.get_pos()

    buttons = []
    labels = (
        ("resume", _text(settings, "resume"), "btn_green"),
        ("save", _text(settings, "save_game"), "btn_blue" if can_save else "btn_gray"),
        ("settings", _text(settings, "settings"), "btn_gold"),
        ("home", _text(settings, "home"), "btn_blue"),
        ("quit", _text(settings, "quit"), "btn_gray"),
    )
    start_y = 150
    for idx, (action, label, asset_key) in enumerate(labels):
        rect = pygame.Rect((screen_width // 2) - 150, start_y + idx * 62, 300, 48)
        buttons.append((action, label, asset_key, rect))

    screen.fill((38, 48, 58))
    title_surface = title_font.render(_text(settings, "paused"), True, (240, 248, 255))
    screen.blit(title_surface, title_surface.get_rect(center=(screen_width // 2, 82)))

    if status_text:
        status_surface = info_font.render(status_text, True, (220, 235, 245))
        screen.blit(status_surface, status_surface.get_rect(center=(screen_width // 2, 122)))

    result = {"buttons": {}}
    for action, label, asset_key, rect in buttons:
        enabled = action != "save" or can_save
        hover = rect.collidepoint(mouse_pos) and enabled
        fallback = (80, 150, 95)
        if asset_key == "btn_blue":
            fallback = (75, 125, 185)
        elif asset_key == "btn_gold":
            fallback = (190, 155, 80)
        elif asset_key == "btn_gray":
            fallback = (105, 115, 125)
        if hover:
            fallback = tuple(min(255, channel + 25) for channel in fallback)
        _draw_image_button(screen, rect, assets[asset_key], fallback)
        text_color = (245, 250, 255) if enabled else (180, 188, 195)
        label_surface = button_font.render(label, True, text_color)
        screen.blit(label_surface, label_surface.get_rect(center=rect.center))
        result["buttons"][action] = {"rect": rect, "enabled": enabled}

    tip = info_font.render(_text(settings, "esc_resume"), True, (190, 205, 218))
    screen.blit(tip, tip.get_rect(center=(screen_width // 2, screen_height - 34)))
    return result


def run_pause_menu(screen_width, screen_height, caption, settings, can_save, status_text=""):
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(f"{caption} | Paused")
    clock = pygame.time.Clock()
    fonts = _menu_fonts()
    mode = "pause"
    current_settings = _copy_settings(settings)
    editable_settings = _copy_settings(current_settings)
    settings_scroll_index = 0
    settings_binding_key = None

    while True:
        if mode == "settings":
            ui_state = _draw_settings_menu(
                screen,
                fonts,
                screen_width,
                screen_height,
                editable_settings,
                settings_scroll_index,
                settings_binding_key,
            )
            settings_scroll_index = ui_state["scroll_index"]
        else:
            ui_state = _draw_pause_menu(
                screen,
                fonts,
                screen_width,
                screen_height,
                can_save,
                status_text,
                current_settings,
            )

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return {"action": "quit", "settings": current_settings}
            if mode == "settings" and settings_binding_key and event.type == KEYDOWN:
                editable_settings["controls"][settings_binding_key] = _key_name_from_event(event)
                settings_binding_key = None
                continue
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                if mode == "settings":
                    editable_settings = _copy_settings(current_settings)
                    settings_binding_key = None
                    mode = "pause"
                    continue
                return {"action": "resume", "settings": current_settings}

            if mode == "settings":
                if event.type == KEYDOWN and event.key == K_UP:
                    settings_scroll_index = max(0, settings_scroll_index - 1)
                if event.type == KEYDOWN and event.key == K_DOWN:
                    settings_scroll_index = min(ui_state["max_scroll"], settings_scroll_index + 1)
                if event.type == MOUSEWHEEL:
                    if event.y > 0:
                        settings_scroll_index = max(0, settings_scroll_index - 1)
                    elif event.y < 0:
                        settings_scroll_index = min(ui_state["max_scroll"], settings_scroll_index + 1)
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if ui_state["hover_back"]:
                        editable_settings = _copy_settings(current_settings)
                        settings_binding_key = None
                        mode = "pause"
                        continue
                    if ui_state["hover_apply"]:
                        current_settings = _copy_settings(editable_settings)
                        settings_binding_key = None
                        status_text = _text(current_settings, "settings_applied")
                        mode = "pause"
                        continue
                    for row in ui_state["rows"]:
                        if row["type"] != "setting":
                            continue
                        section = row["section"]
                        key = row["key"]
                        if section == "controls":
                            if row["row_rect"].collidepoint(event.pos):
                                settings_binding_key = key
                                break
                            continue
                        current = editable_settings[section][key]
                        if row["left_rect"].collidepoint(event.pos):
                            editable_settings[section][key] = _cycle_option(section, key, current, -1)
                            break
                        if row["right_rect"].collidepoint(event.pos):
                            editable_settings[section][key] = _cycle_option(section, key, current, 1)
                            break
            else:
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    for action, data in ui_state["buttons"].items():
                        if data["enabled"] and data["rect"].collidepoint(event.pos):
                            if action == "settings":
                                editable_settings = _copy_settings(current_settings)
                                settings_scroll_index = 0
                                settings_binding_key = None
                                mode = "settings"
                                break
                            return {"action": action, "settings": current_settings}


def run_start_menu(screen_width, screen_height, caption, save_slots, settings, app_version):
    """ホーム画面で新規/ロード/設定を扱うUI。"""
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(f"{caption} | Home")
    clock = pygame.time.Clock()
    fonts = _menu_fonts()

    selected_slot = save_slots[0] if save_slots else None
    mode = "main"
    scroll_index = 0
    join_input_active = False
    join_id_text = ""
    mp_status_text = ""
    current_settings = _copy_settings(settings)
    editable_settings = _copy_settings(current_settings)
    settings_scroll_index = 0
    settings_binding_key = None

    while True:
        if mode == "main":
            ui_state = _draw_main_menu(
                screen,
                fonts,
                screen_width,
                screen_height,
                save_slots,
                selected_slot,
                scroll_index,
                current_settings,
            )
            scroll_index = ui_state["scroll_index"]
        else:
            if mode == "settings":
                ui_state = _draw_settings_menu(
                    screen,
                    fonts,
                    screen_width,
                    screen_height,
                    editable_settings,
                    settings_scroll_index,
                    settings_binding_key,
                )
                settings_scroll_index = ui_state["scroll_index"]
            else:
                ui_state = _draw_multiplayer_menu(
                    screen,
                    fonts,
                    screen_width,
                    screen_height,
                    join_id_text,
                    join_input_active,
                    mp_status_text,
                    app_version,
                    current_settings,
                )

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if mode == "settings" and settings_binding_key and event.type == KEYDOWN:
                editable_settings["controls"][settings_binding_key] = _key_name_from_event(event)
                settings_binding_key = None
                continue
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                if mode == "settings":
                    settings_binding_key = None
                    mode = "main"
                    continue
                if mode == "multiplayer":
                    mode = "main"
                    continue
                return None

            if mode == "main":
                if event.type == KEYDOWN and event.key == K_UP:
                    scroll_index = max(0, scroll_index - 1)
                if event.type == KEYDOWN and event.key == K_DOWN:
                    scroll_index = min(ui_state["max_scroll"], scroll_index + 1)
                if event.type == MOUSEWHEEL:
                    if event.y > 0:
                        scroll_index = max(0, scroll_index - 1)
                    elif event.y < 0:
                        scroll_index = min(ui_state["max_scroll"], scroll_index + 1)
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if ui_state["hover_new"]:
                        return {"action": "new", "settings": current_settings}
                    if ui_state["hover_load"]:
                        return {"action": "load", "slot": selected_slot, "settings": current_settings}
                    if ui_state["settings_button"].collidepoint(event.pos):
                        editable_settings = _copy_settings(current_settings)
                        settings_scroll_index = 0
                        settings_binding_key = None
                        mode = "settings"
                        continue
                    if ui_state["multiplayer_button"].collidepoint(event.pos):
                        mode = "multiplayer"
                        join_input_active = False
                        mp_status_text = ""
                        continue
                    for slot_name, rect in ui_state["slot_rects"]:
                        if rect.collidepoint(event.pos):
                            selected_slot = slot_name
                            break
            elif mode == "settings":
                if event.type == KEYDOWN and event.key == K_UP:
                    settings_scroll_index = max(0, settings_scroll_index - 1)
                if event.type == KEYDOWN and event.key == K_DOWN:
                    settings_scroll_index = min(ui_state["max_scroll"], settings_scroll_index + 1)
                if event.type == MOUSEWHEEL:
                    if event.y > 0:
                        settings_scroll_index = max(0, settings_scroll_index - 1)
                    elif event.y < 0:
                        settings_scroll_index = min(ui_state["max_scroll"], settings_scroll_index + 1)
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if ui_state["hover_back"]:
                        editable_settings = _copy_settings(current_settings)
                        settings_binding_key = None
                        mode = "main"
                        continue
                    if ui_state["hover_apply"]:
                        current_settings = _copy_settings(editable_settings)
                        settings_binding_key = None
                        mode = "main"
                        continue
                    for row in ui_state["rows"]:
                        if row["type"] != "setting":
                            continue
                        section = row["section"]
                        key = row["key"]
                        if section == "controls":
                            if row["row_rect"].collidepoint(event.pos):
                                settings_binding_key = key
                                break
                            continue
                        current = editable_settings[section][key]
                        if row["left_rect"].collidepoint(event.pos):
                            editable_settings[section][key] = _cycle_option(section, key, current, -1)
                            break
                        if row["right_rect"].collidepoint(event.pos):
                            editable_settings[section][key] = _cycle_option(section, key, current, 1)
                            break
            else:
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    join_input_active = ui_state["input_rect"].collidepoint(event.pos)
                    if ui_state["hover_back"]:
                        mode = "main"
                        mp_status_text = ""
                        continue
                    if ui_state["hover_host"]:
                        return {"action": "mp_host", "slot": selected_slot, "settings": current_settings}
                    if ui_state["hover_join"]:
                        return {
                            "action": "mp_join",
                            "join_id": join_id_text.strip(),
                            "settings": current_settings,
                        }
                if event.type == KEYDOWN and join_input_active:
                    if event.key == K_BACKSPACE:
                        join_id_text = join_id_text[:-1]
                    elif event.key == K_RETURN:
                        if join_id_text.strip():
                            return {
                                "action": "mp_join",
                                "join_id": join_id_text.strip(),
                                "settings": current_settings,
                            }
                    elif event.unicode and event.unicode.isprintable():
                        if len(join_id_text) < 64:
                            join_id_text += event.unicode
