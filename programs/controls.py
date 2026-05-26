import math
import pygame
from pygame.locals import *

from . import state as s
from . import world


def key_code_for_action(action):
    name = s.KEY_BINDINGS.get(action, "")
    try:
        return pygame.key.key_code(name)
    except Exception:
        default = {
            "forward": K_w,
            "backward": K_s,
            "left": K_a,
            "right": K_d,
            "jump": K_SPACE,
            "crouch": K_LSHIFT,
            "sprint": K_LCTRL,
            "respawn": K_r,
            "save": K_F5,
            "reload": K_F9,
            "pause": K_ESCAPE,
        }.get(action)
        return default


def is_action_pressed(keys, action):
    key_code = key_code_for_action(action)
    return key_code is not None and keys[key_code]


def event_matches_action(event, action):
    return event.type == KEYDOWN and event.key == key_code_for_action(action)


def handle_input():
    """ ユーザー入力を処理する """
    keys = pygame.key.get_pressed()
    s.player.crouching = is_action_pressed(keys, "crouch")
    now = pygame.time.get_ticks() * 0.001
    forward_pressed = is_action_pressed(keys, "forward")
    sprint_pressed = is_action_pressed(keys, "sprint")

    # 前進キーのダブルタップまたはダッシュキーで開始。前進キーを離したら即停止。
    if forward_pressed and not s.player.prev_w_pressed:
        if (now - s.player.last_w_tap_time) <= s.DASH_DOUBLE_TAP_WINDOW:
            s.player.sprinting = True
        s.player.last_w_tap_time = now
    if sprint_pressed and forward_pressed:
        s.player.sprinting = True
    if not forward_pressed or s.player.crouching:
        s.player.sprinting = False
    s.player.prev_w_pressed = forward_pressed

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
    if forward_pressed:  # 前進
        move_dx += fwd_x_comp * speed
        move_dz += fwd_z_comp * speed
    if is_action_pressed(keys, "backward"):  # 後退
        move_dx -= fwd_x_comp * speed
        move_dz -= fwd_z_comp * speed
    if is_action_pressed(keys, "left"):  # 左へ平行移動
        move_dx -= right_x_comp * speed
        move_dz -= right_z_comp * speed
    if is_action_pressed(keys, "right"):  # 右へ平行移動
        move_dx += right_x_comp * speed
        move_dz += right_z_comp * speed

    if is_action_pressed(keys, "jump"):
        if world.is_player_in_water():
            s.player.velocity_y = min(
                s.WATER_SWIM_UP_VELOCITY,
                s.player.velocity_y + 0.01,
            )
        elif s.player.on_ground:
            s.player.velocity_y = s.JUMP_VELOCITY
            s.player.on_ground = False

    return move_dx, move_dz
