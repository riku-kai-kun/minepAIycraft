import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

from . import state as s
from . import world


def draw_grass_block():
    glCallList(s.CUBE_LIST_GRASS_SIDES)
    glCallList(s.CUBE_LIST_GRASS_TOP)


def draw_grass_block_faces(face_indices):
    for face_index in face_indices:
        if face_index == 4:
            glCallList(s.FACE_LISTS_GRASS_TOP[face_index])
        else:
            glCallList(s.FACE_LISTS_DIRT[face_index])


def draw_dirt_block():
    glCallList(s.CUBE_LIST_DIRT)


def draw_dirt_block_faces(face_indices):
    for face_index in face_indices:
        glCallList(s.FACE_LISTS_DIRT[face_index])


def draw_stone_cube():
    glCallList(s.CUBE_LIST_STONE)


def draw_stone_block_faces(face_indices):
    for face_index in face_indices:
        glCallList(s.FACE_LISTS_STONE[face_index])


def draw_tall_grass():
    glCallList(s.CUBE_LIST_TALL_GRASS)


def build_tall_grass_list():
    s.CUBE_LIST_TALL_GRASS = glGenLists(1)
    glNewList(s.CUBE_LIST_TALL_GRASS, GL_COMPILE)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    glColor4f(0.36, 0.76, 0.28, 0.88)
    y0 = -0.50
    y1 = 0.18
    w = 0.30
    glBegin(GL_QUADS)
    # Crossed quads (minecraft-like grass card)
    glVertex3f(-w, y0, -w)
    glVertex3f(w, y0, w)
    glVertex3f(w, y1, w)
    glVertex3f(-w, y1, -w)

    glVertex3f(w, y0, -w)
    glVertex3f(-w, y0, w)
    glVertex3f(-w, y1, w)
    glVertex3f(w, y1, -w)
    glEnd()
    glDepthMask(GL_TRUE)
    glEnable(GL_TEXTURE_2D)
    glEndList()


def build_face_lists(texture_id):
    face_lists = []
    for surface in s.SURFACES:
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glBegin(GL_QUADS)
        for i, vertex_index in enumerate(surface):
            u, v = s.TEX_COORDS[i]
            glTexCoord2f(u, v)
            glVertex3fv(s.VERTICES[vertex_index])
        glEnd()
        glEndList()
        face_lists.append(display_list)
    return tuple(face_lists)


def draw_water_block(
    level=0,
    show_top=True,
    show_bottom=False,
    show_north=True,
    show_south=True,
    show_west=True,
    show_east=True,
):
    level = max(0, min(level, s.WATER_MAX_LEVEL))
    fill = max(0.22, 0.52 - level * 0.04)
    top_y = 0.48
    edge = 0.498
    bottom_y = -0.498
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, s.TEX_WATER)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)
    glBegin(GL_QUADS)
    # Top
    if show_top:
        glColor4f(0.32, 0.66, 0.98, min(0.72, fill + 0.15))
        glTexCoord2f(0.0, 0.0)
        glVertex3f(edge, top_y, -edge)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-edge, top_y, -edge)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-edge, top_y, edge)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(edge, top_y, edge)
    if show_bottom:
        glColor4f(0.12, 0.34, 0.68, fill)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-edge, bottom_y, -edge)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(edge, bottom_y, -edge)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(edge, bottom_y, edge)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-edge, bottom_y, edge)
    # Front (+Z)
    if show_south:
        glColor4f(0.16, 0.45, 0.90, fill)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(edge, bottom_y, edge)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-edge, bottom_y, edge)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-edge, top_y, edge)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(edge, top_y, edge)
    # Back (-Z)
    if show_north:
        glColor4f(0.16, 0.45, 0.90, fill)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-edge, bottom_y, -edge)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(edge, bottom_y, -edge)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(edge, top_y, -edge)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-edge, top_y, -edge)
    # Left (-X)
    if show_west:
        glColor4f(0.16, 0.45, 0.90, fill)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-edge, bottom_y, edge)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-edge, bottom_y, -edge)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-edge, top_y, -edge)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-edge, top_y, edge)
    # Right (+X)
    if show_east:
        glColor4f(0.16, 0.45, 0.90, fill)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(edge, bottom_y, -edge)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(edge, bottom_y, edge)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(edge, top_y, edge)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(edge, top_y, -edge)
    glEnd()
    glDepthMask(GL_TRUE)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)


def update_environment_effects():
    underwater = world.is_camera_underwater()
    if underwater:
        glClearColor(0.10, 0.28, 0.42, 1.0)
        glEnable(GL_FOG)
        fog_color = (GLfloat * 4)(0.12, 0.32, 0.48, 1.0)
        glFogfv(GL_FOG_COLOR, fog_color)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, 1.5)
        glFogf(GL_FOG_END, 18.0)
    else:
        glClearColor(*s.SKY_COLOR)
        glDisable(GL_FOG)


def draw_underwater_overlay():
    if not world.is_camera_underwater():
        return
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, s.SCREEN_WIDTH, s.SCREEN_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glColor4f(0.10, 0.35, 0.52, 0.25)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(s.SCREEN_WIDTH, 0)
    glVertex2f(s.SCREEN_WIDTH, s.SCREEN_HEIGHT)
    glVertex2f(0, s.SCREEN_HEIGHT)
    glEnd()
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_TEXTURE_2D)


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
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
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
    s.TEX_WATER = load_texture(s.TEXTURE_WATER)


def build_cube_list():
    s.FACE_LISTS_DIRT = build_face_lists(s.TEX_DIRT)
    s.FACE_LISTS_GRASS_TOP = build_face_lists(s.TEX_GRASS_TOP)
    s.FACE_LISTS_STONE = build_face_lists(s.TEX_STONE)

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

    build_tall_grass_list()


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


def draw_remote_players(players):
    if not players:
        return

    def draw_colored_box(width, height, depth, color):
        hw = width * 0.5
        hh = height * 0.5
        hd = depth * 0.5
        glColor3f(*color)
        glBegin(GL_QUADS)
        # Front
        glVertex3f(-hw, -hh, hd)
        glVertex3f(hw, -hh, hd)
        glVertex3f(hw, hh, hd)
        glVertex3f(-hw, hh, hd)
        # Back
        glVertex3f(hw, -hh, -hd)
        glVertex3f(-hw, -hh, -hd)
        glVertex3f(-hw, hh, -hd)
        glVertex3f(hw, hh, -hd)
        # Left
        glVertex3f(-hw, -hh, -hd)
        glVertex3f(-hw, -hh, hd)
        glVertex3f(-hw, hh, hd)
        glVertex3f(-hw, hh, -hd)
        # Right
        glVertex3f(hw, -hh, hd)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(hw, hh, -hd)
        glVertex3f(hw, hh, hd)
        # Top
        glVertex3f(-hw, hh, hd)
        glVertex3f(hw, hh, hd)
        glVertex3f(hw, hh, -hd)
        glVertex3f(-hw, hh, -hd)
        # Bottom
        glVertex3f(-hw, -hh, -hd)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(hw, -hh, hd)
        glVertex3f(-hw, -hh, hd)
        glEnd()

    glDisable(GL_TEXTURE_2D)
    for player in players.values():
        pos = player.get("position", [0.0, 0.0, 0.0])
        glPushMatrix()
        glTranslatef(float(pos[0]), float(pos[1]), float(pos[2]))

        # Fixed skin (head, torso, legs)
        glPushMatrix()
        glTranslatef(0.0, 1.55, 0.0)
        draw_colored_box(0.42, 0.42, 0.42, (0.95, 0.82, 0.68))
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.0, 0.95, 0.0)
        draw_colored_box(0.58, 0.68, 0.30, (0.15, 0.45, 0.85))
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-0.16, 0.35, 0.0)
        draw_colored_box(0.24, 0.65, 0.24, (0.20, 0.22, 0.30))
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.16, 0.35, 0.0)
        draw_colored_box(0.24, 0.65, 0.24, (0.20, 0.22, 0.30))
        glPopMatrix()

        glPopMatrix()
    glEnable(GL_TEXTURE_2D)
