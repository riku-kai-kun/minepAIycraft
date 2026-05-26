import pygame
import sys
import time
import os
from datetime import datetime
from pygame.locals import *
from OpenGL.GL import *

from programs import state as s
from programs.controls import handle_input, event_matches_action
from programs.ui import run_start_menu, run_pause_menu
from programs.save_system import (
    ensure_saves_dir,
    list_save_slots,
    create_save_slot,
    save_to_slot,
    load_from_slot,
    build_snapshot,
    apply_snapshot,
)
from programs.multiplayer import MultiplayerSession
from programs.multiplayer import decode_invite_id, encode_invite_id
from programs.settings_system import (
    load_settings,
    save_settings,
    apply_settings_to_state,
)
from programs.rendering import (
    init_gl,
    update_environment_effects,
    draw_ground,
    draw_target_block_outline,
    draw_crosshair,
    draw_underwater_overlay,
    apply_camera_transform,
    draw_remote_players,
)
from programs.world import (
    init_world,
    update_water_flow,
    raycast_blocks,
    get_view_direction,
    get_eye_height,
    can_place_block,
    add_placed_block,
    remove_block_at,
    mark_chunk_dirty_at,
    resolve_collisions,
    is_supported,
    is_player_in_water,
    get_target_block,
)

# --- ゲームエンジン ver1.3 (操作) ---


def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(s.LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


def main():
    """ ゲームのメイン処理 """
    base_dir = os.getcwd()
    s.BLOCKS_PLACED = 0
    s.BLOCKS_REMOVED = 0
    s.SESSION_START = time.time()
    pygame.init()

    ensure_saves_dir(base_dir)
    settings = load_settings(base_dir)
    apply_settings_to_state(settings)
    menu_result = run_start_menu(
        s.SCREEN_WIDTH,
        s.SCREEN_HEIGHT,
        s.CAPTION,
        list_save_slots(base_dir),
        settings,
        s.APP_VERSION,
    )
    if menu_result is None:
        pygame.quit()
        sys.exit()
    action = menu_result.get("action")
    selected_slot = menu_result.get("slot")
    join_id_text = menu_result.get("join_id")
    settings = menu_result.get("settings", settings)
    save_settings(base_dir, settings)
    apply_settings_to_state(settings)

    pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(s.CAPTION)

    # マウスを非表示 & ウィンドウ内に固定
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.event.clear()
    pygame.mouse.get_rel()

    init_gl()
    current_save_slot = selected_slot
    mp_session = MultiplayerSession()

    def enter_game_display():
        pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption(s.CAPTION)
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.event.clear()
        pygame.mouse.get_rel()
        init_gl()
        for chunk in s.ACTIVE_CHUNKS.values():
            chunk.display_list = None
            chunk.dirty = True
        s.LAST_PLAYER_CHUNK = None
        s.CHUNKS_NEED_UPDATE = True

    def enter_menu_display():
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        pygame.event.clear()

    def reset_local_player():
        s.player.position = [0.0, 0.0, 0.0]
        s.player.velocity_y = 0.0
        s.player.on_ground = False
        s.player.crouching = False
        s.player.sprinting = False
        s.player.last_w_tap_time = -999.0
        s.player.prev_w_pressed = False
        s.camera.rotation = [0.0, 0.0]

    if action in ("new", "load", "mp_host"):
        if action == "new" or (action == "mp_host" and not current_save_slot) or not current_save_slot:
            current_save_slot = create_save_slot(base_dir)
            init_world()
            reset_local_player()
            save_to_slot(base_dir, current_save_slot)
        else:
            try:
                load_from_slot(base_dir, current_save_slot)
            except Exception:
                current_save_slot = create_save_slot(base_dir)
                init_world()
                reset_local_player()
                save_to_slot(base_dir, current_save_slot)

        if action == "mp_host":
            snapshot = build_snapshot()
            room_code = mp_session.start_host(
                snapshot,
                relay_host=s.MULTIPLAYER_RELAY_HOST,
                relay_port=s.MULTIPLAYER_RELAY_PORT,
            )
            invite_id = encode_invite_id(
                s.MULTIPLAYER_RELAY_HOST,
                s.MULTIPLAYER_RELAY_PORT,
                room_code,
            )
            log_event(f"Multiplayer host started | version={s.APP_VERSION}")
            log_event(f"Share this Room Code: {room_code}")
            log_event(f"Share this Invite ID: {invite_id}")
            log_event(
                "Warning: Depending on network restrictions, multiplayer may be unavailable."
            )
    elif action == "mp_join":
        try:
            relay_host = s.MULTIPLAYER_RELAY_HOST
            relay_port = s.MULTIPLAYER_RELAY_PORT
            room_code = join_id_text
            if (join_id_text or "").strip().startswith("MPC-"):
                relay_host, relay_port, room_code = decode_invite_id(join_id_text)
            snapshot = mp_session.join_room(room_code, relay_host=relay_host, relay_port=relay_port)
            apply_snapshot(snapshot)
            log_event(
                f"Joined multiplayer room | version={s.APP_VERSION} | code={room_code}"
            )
            current_save_slot = None
        except Exception as exc:
            log_event(f"Failed to join multiplayer: {exc}")
            log_event(
                "Warning: This can be caused by network restrictions/firewall settings."
            )
            pygame.quit()
            sys.exit()
    else:
        current_save_slot = create_save_slot(base_dir)
        init_world()
        reset_local_player()
        save_to_slot(base_dir, current_save_slot)

    log_event("Session start")
    if current_save_slot:
        log_event(f"Save slot selected: {current_save_slot}")
    clock = pygame.time.Clock()

    def finish_session():
        if s.AUTO_SAVE_ON_EXIT and current_save_slot and mp_session.mode != "client":
            try:
                save_to_slot(base_dir, current_save_slot)
                log_event(f"Auto-saved: {current_save_slot}")
            except Exception as exc:
                log_event(f"Auto-save failed: {exc}")
        duration = time.time() - s.SESSION_START
        log_event(
            "Session end"
            f" | duration={duration:.1f}s"
            f" | placed={s.BLOCKS_PLACED}"
            f" | removed={s.BLOCKS_REMOVED}"
            f" | pos=({s.player.position[0]:.2f},{s.player.position[1]:.2f},{s.player.position[2]:.2f})"
        )
        mp_session.shutdown()

    def shutdown_and_exit():
        finish_session()
        pygame.quit()
        sys.exit()

    def restart_to_home():
        finish_session()
        pygame.quit()
        try:
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as exc:
            print(f"Failed to return home: {exc}")
            sys.exit(1)

    def save_current_game():
        if current_save_slot and mp_session.mode != "client":
            save_to_slot(base_dir, current_save_slot)
            log_event(f"Saved: {current_save_slot}")
            return f"Saved: {current_save_slot}"
        log_event("Save disabled in joined multiplayer")
        return "Save disabled in joined multiplayer"

    def open_pause_menu():
        nonlocal settings
        enter_menu_display()
        status_text = ""
        while True:
            result = run_pause_menu(
                s.SCREEN_WIDTH,
                s.SCREEN_HEIGHT,
                s.CAPTION,
                settings,
                bool(current_save_slot and mp_session.mode != "client"),
                status_text,
            )
            if result is None:
                result = {"action": "resume", "settings": settings}
            settings = result.get("settings", settings)
            save_settings(base_dir, settings)
            apply_settings_to_state(settings)
            action_name = result.get("action")
            if action_name == "save":
                try:
                    status_text = save_current_game()
                except Exception as exc:
                    status_text = f"Save failed: {exc}"
                    log_event(status_text)
                continue
            if action_name == "home":
                restart_to_home()
            if action_name == "quit":
                shutdown_and_exit()
            enter_game_display()
            return

    while True:
        for net_event in mp_session.poll_events():
            if net_event.get("type") == "error":
                log_event(net_event.get("message", "Network error"))
            if net_event.get("type") == "info":
                log_event(net_event.get("message", "Network info"))
            if net_event.get("type") == "block":
                if net_event.get("player_id") == mp_session.local_player_id:
                    continue
                pos = tuple(net_event.get("pos", [0, 0, 0]))
                action_name = net_event.get("action")
                if action_name == "place":
                    if add_placed_block(pos):
                        mark_chunk_dirty_at(pos[0], pos[2])
                elif action_name == "remove":
                    if remove_block_at(pos):
                        mark_chunk_dirty_at(pos[0], pos[2])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                shutdown_and_exit()
            if event_matches_action(event, "pause"):
                open_pause_menu()
                continue
            if event_matches_action(event, "respawn"):
                s.player.position = [0.0, 0.0, 0.0]
                s.player.velocity_y = 0.0
                s.player.on_ground = False
                log_event("Respawn")
            if event_matches_action(event, "save"):
                try:
                    save_current_game()
                except Exception as exc:
                    log_event(f"Save failed: {exc}")
            if event_matches_action(event, "reload"):
                if current_save_slot and not mp_session.is_multiplayer():
                    try:
                        load_from_slot(base_dir, current_save_slot)
                        log_event(f"Loaded: {current_save_slot}")
                    except Exception as exc:
                        log_event(f"Load failed: {exc}")
                else:
                    log_event("Reload disabled while multiplayer is active")
            if event.type == MOUSEBUTTONDOWN:
                eye = (
                    s.player.position[0],
                    s.player.position[1] + get_eye_height(),
                    s.player.position[2],
                )
                direction = get_view_direction()
                hit, prev = raycast_blocks(eye, direction, s.MAX_REACH)
                if event.button == 3:
                    if hit is not None:
                        if remove_block_at(hit):
                            s.BLOCKS_REMOVED += 1
                            mark_chunk_dirty_at(hit[0], hit[2])
                            mp_session.send_block_action("remove", hit)
                if event.button == 1:
                    if can_place_block(prev):
                        if add_placed_block(prev):
                            s.BLOCKS_PLACED += 1
                            mark_chunk_dirty_at(prev[0], prev[2])
                            mp_session.send_block_action("place", prev)

        move_dx, move_dz = handle_input()
        if s.player.crouching and s.player.on_ground and (move_dx != 0.0 or move_dz != 0.0):
            next_pos = [s.player.position[0] + move_dx, s.player.position[1], s.player.position[2] + move_dz]
            if not is_supported(next_pos):
                move_dx = 0.0
                move_dz = 0.0

        s.player.on_ground = False
        if is_player_in_water():
            s.player.velocity_y += s.WATER_GRAVITY
            if s.player.velocity_y < -0.06:
                s.player.velocity_y = -0.06
        else:
            s.player.velocity_y += s.GRAVITY
        resolve_collisions(move_dx, s.player.velocity_y, move_dz)
        mp_session.send_local_state(s.player.position, s.camera.rotation)
        update_water_flow()

        update_environment_effects()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        apply_camera_transform()
        draw_ground()
        draw_remote_players(mp_session.get_remote_players())
        draw_underwater_overlay()
        target = get_target_block()
        if s.SHOW_TARGET_OUTLINE:
            draw_target_block_outline(target)
        if s.SHOW_CROSSHAIR:
            draw_crosshair()

        pygame.display.flip()
        clock.tick(60)  # 60 FPSに制限


if __name__ == '__main__':
    main()
