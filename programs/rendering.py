import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from . import state as s
from . import world


def draw_grass_block():
    glCallList(s.CUBE_LIST_GRASS_SIDES)
    glCallList(s.CUBE_LIST_GRASS_TOP)


def draw_dirt_block():
    glCallList(s.CUBE_LIST_DIRT)


def draw_stone_cube():
    glCallList(s.CUBE_LIST_STONE)


def draw_cube_edges():
    glDisable(GL_TEXTURE_2D)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_LINES)
    for edge in s.EDGES:
        for vertex_index in edge:
            glVertex3fv(s.VERTICES[vertex_index])
    glEnd()
    glEnable(GL_TEXTURE_2D)


def init_gl():
    """ OpenGLの初期化 """
    glViewport(0, 0, s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (s.SCREEN_WIDTH / s.SCREEN_HEIGHT), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(*s.SKY_COLOR)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
    glLineWidth(1.0)
    load_textures()
    build_cube_list()


def load_texture(path):
    surface = pygame.image.load(path).convert_alpha()
    surface = pygame.transform.flip(surface, False, True)
    width, height = surface.get_size()
    texture_data = pygame.image.tostring(surface, "RGBA", True)
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGBA,
        width,
        height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        texture_data,
    )
    return tex_id


def load_textures():
    s.TEX_GRASS_TOP = load_texture(s.TEXTURE_GRASS_TOP)
    s.TEX_DIRT = load_texture(s.TEXTURE_DIRT)
    s.TEX_STONE = load_texture(s.TEXTURE_STONE)


def build_cube_list():
    s.CUBE_LIST_DIRT = glGenLists(1)
    glNewList(s.CUBE_LIST_DIRT, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, s.TEX_DIRT)
    glBegin(GL_QUADS)
    for surface in s.SURFACES:
        for i, vertex_index in enumerate(surface):
            u, v = s.TEX_COORDS[i]
            glTexCoord2f(u, v)
            glVertex3fv(s.VERTICES[vertex_index])
    glEnd()
    glEndList()

    s.CUBE_LIST_GRASS_SIDES = glGenLists(1)
    glNewList(s.CUBE_LIST_GRASS_SIDES, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, s.TEX_DIRT)
    glBegin(GL_QUADS)
    for i, surface in enumerate(s.SURFACES):
        if i == 4:
            continue
        for j, vertex_index in enumerate(surface):
            u, v = s.TEX_COORDS[j]
            glTexCoord2f(u, v)
            glVertex3fv(s.VERTICES[vertex_index])
    glEnd()
    glEndList()

    s.CUBE_LIST_GRASS_TOP = glGenLists(1)
    glNewList(s.CUBE_LIST_GRASS_TOP, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, s.TEX_GRASS_TOP)
    glBegin(GL_QUADS)
    surface = s.SURFACES[4]
    for i, vertex_index in enumerate(surface):
        u, v = s.TEX_COORDS[i]
        glTexCoord2f(u, v)
        glVertex3fv(s.VERTICES[vertex_index])
    glEnd()
    glEndList()

    s.CUBE_LIST_STONE = glGenLists(1)
    glNewList(s.CUBE_LIST_STONE, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, s.TEX_STONE)
    glBegin(GL_QUADS)
    for surface in s.SURFACES:
        for i, vertex_index in enumerate(surface):
            u, v = s.TEX_COORDS[i]
            glTexCoord2f(u, v)
            glVertex3fv(s.VERTICES[vertex_index])
    glEnd()
    glEndList()


def draw_chunks():
    world.update_visible_chunks()
    for chunk in s.ACTIVE_CHUNKS.values():
        if chunk.display_list:
            glCallList(chunk.display_list)


def draw_ground():
    """ 互換用: チャンク描画に委譲 """
    draw_chunks()


def draw_target_block_outline(target):
    if target is None:
        return
    glPushMatrix()
    glTranslatef(target[0], target[1], target[2])
    glScalef(1.001, 1.001, 1.001)
    draw_cube_edges()
    glPopMatrix()


def draw_crosshair():
    glDisable(GL_TEXTURE_2D)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, s.SCREEN_WIDTH, s.SCREEN_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glLineWidth(2.0)
    glColor3f(0.0, 0.0, 0.0)
    cx = s.SCREEN_WIDTH * 0.5
    cy = s.SCREEN_HEIGHT * 0.5
    gap = 4
    length = 8
    glBegin(GL_LINES)
    glVertex2f(cx - length, cy)
    glVertex2f(cx - gap, cy)
    glVertex2f(cx + gap, cy)
    glVertex2f(cx + length, cy)
    glVertex2f(cx, cy - length)
    glVertex2f(cx, cy - gap)
    glVertex2f(cx, cy + gap)
    glVertex2f(cx, cy + length)
    glEnd()
    glLineWidth(1.0)
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_TEXTURE_2D)


def apply_camera_transform():
    """ カメラの変形を適用する """
    glLoadIdentity()
    glRotatef(s.camera.rotation[1], 1, 0, 0)  # Pitch
    glRotatef(s.camera.rotation[0], 0, 1, 0)  # Yaw
    glTranslatef(
        -s.player.position[0],
        -(s.player.position[1] + world.get_eye_height()),
        -s.player.position[2],
    )
