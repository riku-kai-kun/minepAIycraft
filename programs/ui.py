import pygame
from pygame.locals import *
import os

from .settings_system import ALLOWED_OPTIONS


SETTINGS_LAYOUT = [
    ("main", "Main"),
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
]

DISPLAY_LABELS = {
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
}

_UI_ASSETS = None


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
    }


def _format_value(value):
    if isinstance(value, bool):
        return "ON" if value else "OFF"
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


def _draw_main_menu(screen, fonts, screen_width, screen_height, save_slots, selected_slot, scroll_index):
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

    info_surface = info_font.render("Choose NEW SAVE / LOAD / SETTINGS", True, (40, 55, 70))
    info_rect = info_surface.get_rect(center=(screen_width // 2, screen_height // 4 + 50))
    screen.blit(info_surface, info_rect)

    _draw_image_button(
        screen,
        new_button,
        assets["btn_green"],
        (80, 170, 90) if hover_new else (60, 140, 70),
    )
    new_label = button_font.render("NEW SAVE", True, (245, 255, 245))
    screen.blit(new_label, new_label.get_rect(center=new_button.center))

    load_color = (70, 130, 190) if hover_load else (55, 105, 155)
    if selected_slot is None:
        load_color = (120, 130, 140)
    load_img = assets["btn_blue"] if selected_slot is not None else assets["btn_gray"]
    _draw_image_button(screen, load_button, load_img, load_color)
    load_label = button_font.render("LOAD SELECTED", True, (245, 250, 255))
    screen.blit(load_label, load_label.get_rect(center=load_button.center))

    _draw_image_button(
        screen,
        settings_button,
        assets["btn_gold"],
        (220, 185, 95) if hover_settings else (200, 165, 80),
    )
    settings_label = button_font.render("SETTINGS", True, (35, 25, 10))
    screen.blit(settings_label, settings_label.get_rect(center=settings_button.center))

    _draw_image_button(
        screen,
        multiplayer_button,
        assets["btn_blue"],
        (95, 155, 215) if hover_multiplayer else (75, 125, 185),
    )
    mp_label = button_font.render("MULTIPLAYER", True, (240, 248, 255))
    screen.blit(mp_label, mp_label.get_rect(center=multiplayer_button.center))

    list_title = info_font.render("Save Slots", True, (20, 30, 40))
    screen.blit(list_title, (screen_width // 2 - 280, list_top - 32))

    if not save_slots:
        empty_text = slot_font.render("No save files yet.", True, (70, 80, 90))
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

    tip = info_font.render("In game: F5=Save, F9=Reload current slot", True, (40, 55, 70))
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

    title_surface = title_font.render("Multiplayer", True, (18, 32, 50))
    title_rect = title_surface.get_rect(center=(screen_width // 2, 72))
    screen.blit(title_surface, title_rect)

    desc = info_font.render("Join with Room Code (ABC123) or Invite ID (MPC-...)", True, (35, 55, 80))
    screen.blit(desc, desc.get_rect(center=(screen_width // 2, 114)))
    warn = info_font.render(
        "Warning: Network restrictions can prevent multiplayer connections.",
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
    host_label = button_font.render("HOST ROOM", True, (244, 255, 244))
    screen.blit(host_label, host_label.get_rect(center=host_button.center))

    join_img = assets["btn_blue"] if join_id_text.strip() else assets["btn_gray"]
    _draw_image_button(
        screen,
        join_button,
        join_img,
        (85, 135, 190) if hover_join else (65, 115, 168),
    )
    join_label = button_font.render("JOIN BY ID", True, (240, 248, 255))
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
    back_label = button_font.render("BACK", True, (32, 24, 14))
    screen.blit(back_label, back_label.get_rect(center=back_button.center))

    if status_text:
        status_surface = info_font.render(status_text, True, (95, 35, 35))
        screen.blit(status_surface, status_surface.get_rect(center=(screen_width // 2, 352)))

    note = info_font.render(f"Required version: {required_version}", True, (55, 70, 88))
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


def _draw_settings_menu(screen, fonts, screen_width, screen_height, editable_settings, scroll_index):
    title_font, info_font, button_font, slot_font = fonts
    assets = _load_ui_assets()

    back_button = pygame.Rect((screen_width // 2) - 260, screen_height - 70, 220, 46)
    apply_button = pygame.Rect((screen_width // 2) + 40, screen_height - 70, 220, 46)

    mouse_pos = pygame.mouse.get_pos()
    hover_back = back_button.collidepoint(mouse_pos)
    hover_apply = apply_button.collidepoint(mouse_pos)

    all_rows = []
    for section, key in SETTINGS_LAYOUT:
        if key in ("Main", "Graphics", "Behavior"):
            all_rows.append({"type": "header", "text": key})
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

        label = DISPLAY_LABELS.get(key, key)
        label_surface = slot_font.render(label, True, (45, 32, 17))
        screen.blit(label_surface, (row["row_rect"].x + 10, row["row_rect"].y + 8))

        value_surface = slot_font.render(_format_value(value), True, (30, 75, 120))
        value_rect = value_surface.get_rect(center=(row["row_rect"].right - 84, row["row_rect"].centery))
        screen.blit(value_surface, value_rect)

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
    back_label = button_font.render("BACK", True, (35, 25, 15))
    screen.blit(back_label, back_label.get_rect(center=back_button.center))

    _draw_image_button(
        screen,
        apply_button,
        assets["btn_green"],
        (95, 170, 105) if hover_apply else (80, 145, 90),
    )
    apply_label = button_font.render("APPLY", True, (245, 255, 245))
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


def run_start_menu(screen_width, screen_height, caption, save_slots, settings, app_version):
    """ホーム画面で新規/ロード/設定を扱うUI。"""
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption(f"{caption} | Home")
    clock = pygame.time.Clock()
    fonts = (
        pygame.font.SysFont(None, 64),
        pygame.font.SysFont(None, 28),
        pygame.font.SysFont(None, 34),
        pygame.font.SysFont(None, 30),
    )

    selected_slot = save_slots[0] if save_slots else None
    mode = "main"
    scroll_index = 0
    join_input_active = False
    join_id_text = ""
    mp_status_text = ""
    current_settings = _copy_settings(settings)
    editable_settings = _copy_settings(current_settings)
    settings_scroll_index = 0

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
                )

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                if mode == "settings":
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
                        mode = "main"
                        continue
                    if ui_state["hover_apply"]:
                        current_settings = _copy_settings(editable_settings)
                        mode = "main"
                        continue
                    for row in ui_state["rows"]:
                        if row["type"] != "setting":
                            continue
                        section = row["section"]
                        key = row["key"]
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
