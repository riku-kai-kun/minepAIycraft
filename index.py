import pygame
import sys
import time
from datetime import datetime
from pygame.locals import *
from OpenGL.GL import *

from programs import state as s
from programs.controls import handle_input
from programs.rendering import (
    init_gl,
    draw_ground,
    draw_target_block_outline,
    draw_crosshair,
    apply_camera_transform,
)
from programs.world import (
    init_world,
    raycast_blocks,
    get_view_direction,
    get_eye_height,
    can_place_block,
    mark_chunk_dirty_at,
    resolve_collisions,
    is_supported,
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
    s.BLOCKS_PLACED = 0
    s.BLOCKS_REMOVED = 0
    s.SESSION_START = time.time()
    pygame.init()
    pygame.display.set_mode((s.SCREEN_WIDTH, s.SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(s.CAPTION)

    # マウスを非表示 & ウィンドウ内に固定
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    init_gl()
    init_world()
    log_event("Session start")
    clock = pygame.time.Clock()

    def shutdown_and_exit():
        duration = time.time() - s.SESSION_START
        log_event(
            "Session end"
            f" | duration={duration:.1f}s"
            f" | placed={s.BLOCKS_PLACED}"
            f" | removed={s.BLOCKS_REMOVED}"
            f" | pos=({s.player.position[0]:.2f},{s.player.position[1]:.2f},{s.player.position[2]:.2f})"
        )
        pygame.quit()
        sys.exit()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                shutdown_and_exit()
            if event.type == KEYDOWN and event.key == K_r:
                s.player.position = [0.0, 0.0, 0.0]
                s.player.velocity_y = 0.0
                s.player.on_ground = False
                log_event("Respawn")
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
                        if hit in s.PLACED_BLOCKS:
                            s.PLACED_BLOCKS.discard(hit)
                        elif hit[1] == -1:
                            s.REMOVED_GROUND.add(hit)
                        elif hit[1] <= -2:
                            s.REMOVED_STONE.add(hit)
                        s.BLOCKS_REMOVED += 1
                        mark_chunk_dirty_at(hit[0], hit[2])
                if event.button == 1:
                    if can_place_block(prev):
                        s.PLACED_BLOCKS.add(prev)
                        s.BLOCKS_PLACED += 1
                        mark_chunk_dirty_at(prev[0], prev[2])

        move_dx, move_dz = handle_input()
        if s.player.crouching and s.player.on_ground and (move_dx != 0.0 or move_dz != 0.0):
            next_pos = [s.player.position[0] + move_dx, s.player.position[1], s.player.position[2] + move_dz]
            if not is_supported(next_pos):
                move_dx = 0.0
                move_dz = 0.0

        s.player.on_ground = False
        s.player.velocity_y += s.GRAVITY
        resolve_collisions(move_dx, s.player.velocity_y, move_dz)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        apply_camera_transform()
        draw_ground()
        target = get_target_block()
        draw_target_block_outline(target)
        draw_crosshair()

        pygame.display.flip()
        clock.tick(60)  # 60 FPSに制限


if __name__ == '__main__':
    main()
