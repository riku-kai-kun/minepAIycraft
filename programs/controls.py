import math
import pygame
from pygame.locals import *

from . import state as s


def handle_input():
    """ ユーザー入力を処理する """
    keys = pygame.key.get_pressed()
    s.player.crouching = keys[K_LSHIFT] or keys[K_RSHIFT]

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

    if keys[K_SPACE] and s.player.on_ground:
        s.player.velocity_y = s.JUMP_VELOCITY
        s.player.on_ground = False

    return move_dx, move_dz
