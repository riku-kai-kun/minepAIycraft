import math
import pygame
from pygame.locals import *

from . import state as s
from . import world


def handle_input():
    """ ユーザー入力を処理する """
    keys = pygame.key.get_pressed()
    s.player.crouching = keys[K_LSHIFT] or keys[K_RSHIFT]
    now = pygame.time.get_ticks() * 0.001
    w_pressed = keys[K_w]
    ctrl_pressed = keys[K_LCTRL] or keys[K_RCTRL]

    # WダブルタップまたはCtrlでダッシュ開始。Wを離したら即停止。
    if w_pressed and not s.player.prev_w_pressed:
        if (now - s.player.last_w_tap_time) <= s.DASH_DOUBLE_TAP_WINDOW:
            s.player.sprinting = True
        s.player.last_w_tap_time = now
    if ctrl_pressed and w_pressed:
        s.player.sprinting = True
    if not w_pressed:
        s.player.sprinting = False
    s.player.prev_w_pressed = w_pressed

    # マウスの動き
    dx, dy = pygame.mouse.get_rel()
    s.camera.rotation[0] += dx * s.MOUSE_SENSITIVITY
    s.camera.rotation[1] += dy * s.MOUSE_SENSITIVITY
    s.camera.rotation[1] = max(-89, min(89, s.camera.rotation[1]))

    # Yawをラジアンに変換
    yaw_rad = math.radians(s.camera.rotation[0])

    # 正しい前方・右方ベクトルを計算
    # OpenGLの-Z方向が前方であることを考慮する
    fwd_x_comp = math.sin(yaw_rad)
    fwd_z_comp = -math.cos(yaw_rad)

    right_x_comp = math.cos(yaw_rad)
    right_z_comp = math.sin(yaw_rad)

    # WASDキーでの移動
    move_dx = 0.0
    move_dz = 0.0
    speed = s.CROUCH_SPEED if s.player.crouching else s.MOVE_SPEED
    if s.player.sprinting and not s.player.crouching:
        speed *= s.DASH_SPEED_MULTIPLIER
    if world.is_player_in_water():
        speed *= s.WATER_MOVE_MULTIPLIER
    if keys[K_w]:  # 前進
        move_dx += fwd_x_comp * speed
        move_dz += fwd_z_comp * speed
    if keys[K_s]:  # 後退
        move_dx -= fwd_x_comp * speed
        move_dz -= fwd_z_comp * speed
    if keys[K_a]:  # 左へ平行移動
        move_dx -= right_x_comp * speed
        move_dz -= right_z_comp * speed
    if keys[K_d]:  # 右へ平行移動
        move_dx += right_x_comp * speed
        move_dz += right_z_comp * speed

    if keys[K_SPACE]:
        if world.is_player_in_water():
            s.player.velocity_y = min(
                s.WATER_SWIM_UP_VELOCITY,
                s.player.velocity_y + 0.01,
            )
        elif s.player.on_ground:
            s.player.velocity_y = s.JUMP_VELOCITY
            s.player.on_ground = False

    return move_dx, move_dz
