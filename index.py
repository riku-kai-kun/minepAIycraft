import pygame
import sys
import math
import time
from functools import lru_cache
from datetime import datetime
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# --- 定数 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SKY_COLOR = (0.5, 0.8, 1.0, 1)
CAPTION = "MinepAIycraft"
CHUNK_SIZE = 16
CHUNK_RADIUS = 6
VIEW_DISTANCE = CHUNK_SIZE * CHUNK_RADIUS
MAX_REACH = 6
STONE_DEPTH = 800
WORLD_SIZE = 10000
WORLD_MIN_X = -(WORLD_SIZE // 2)
WORLD_MAX_X = (WORLD_SIZE // 2) - 1
WORLD_MIN_Z = -(WORLD_SIZE // 2)
WORLD_MAX_Z = (WORLD_SIZE // 2) - 1
WORLD_MIN_Y = -1 - STONE_DEPTH
WORLD_MAX_Y = 8
LOG_PATH = "minepAIycraft.log"
CAVE_SEED = 1337
CAVE_SCALE = 0.07
CAVE_THRESHOLD = 0.72
CAVE_MIN_Y = -200
CAVE_MAX_Y = -20
CAVE_RENDER_RANGE = 20
CAVE_REFRESH_STEP = 8
MAX_CHUNK_BUILDS_PER_FRAME = 2

# --- ブロックの定義 ---
VERTICES = ((0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5))
SURFACES = ((0, 1, 2, 3), (3, 2, 7, 6), (6, 7, 5, 4), (4, 5, 1, 0), (1, 5, 7, 2), (4, 0, 3, 6))
EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 7), (7, 6), (6, 4),
    (0, 4), (1, 5), (2, 7), (3, 6),
)
COLORS = {"grass": (0.3, 0.8, 0.2), "dirt": (0.6, 0.4, 0.2), "stone": (0.5, 0.5, 0.5)}
TEXTURE_GRASS_TOP = "images/textures/grass_top.png"
TEXTURE_DIRT = "images/textures/dirt.png"
TEXTURE_STONE = "images/textures/stone.png"
CUBE_LIST_DIRT = None
TEX_COORDS = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
CUBE_LIST_GRASS_SIDES = None
CUBE_LIST_GRASS_TOP = None
CUBE_LIST_STONE = None
TEX_GRASS_TOP = None
TEX_DIRT = None
TEX_STONE = None
PLACED_BLOCKS = set()
REMOVED_GROUND = set()
REMOVED_STONE = set()
ACTIVE_CHUNKS = {}
LAST_PLAYER_CHUNK = None
LAST_PLAYER_Y = None
CHUNKS_NEED_UPDATE = True
BLOCKS_PLACED = 0
BLOCKS_REMOVED = 0
SESSION_START = time.time()

class ChunkMesh:
    def __init__(self, key):
        self.key = key
        self.display_list = None
        self.dirty = True

def draw_grass_block():
    glCallList(CUBE_LIST_GRASS_SIDES)
    glCallList(CUBE_LIST_GRASS_TOP)

def draw_dirt_block():
    glCallList(CUBE_LIST_DIRT)

def draw_stone_cube():
    glCallList(CUBE_LIST_STONE)

def draw_cube_edges():
    glDisable(GL_TEXTURE_2D)
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_LINES)
    for edge in EDGES:
        for vertex_index in edge:
            glVertex3fv(VERTICES[vertex_index])
    glEnd()
    glEnable(GL_TEXTURE_2D)

# --- プレイヤー/カメラ ---
PLAYER_HEIGHT = 1.8
PLAYER_RADIUS = 0.3
EYE_HEIGHT = 1.6
CROUCH_HEIGHT = 1.2
CROUCH_EYE_HEIGHT = 1.0
MOVE_SPEED = 0.1
CROUCH_SPEED = 0.05
MOUSE_SENSITIVITY = 0.1
GRAVITY = -0.01
JUMP_VELOCITY = 0.18

class Camera:
    def __init__(self):
        self.rotation = [0, 0] # [yaw, pitch]

class Player:
    def __init__(self):
        self.position = [0.0, 0.0, 0.0] # 足元座標
        self.velocity_y = 0.0
        self.on_ground = False
        self.crouching = False

camera = Camera()
player = Player()

# --- ゲームエンジン ver1.3 (操作) ---

def init_gl():
    """ OpenGLの初期化 """
    glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (SCREEN_WIDTH / SCREEN_HEIGHT), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glClearColor(*SKY_COLOR)
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
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    return tex_id

def load_textures():
    global TEX_GRASS_TOP, TEX_DIRT, TEX_STONE
    TEX_GRASS_TOP = load_texture(TEXTURE_GRASS_TOP)
    TEX_DIRT = load_texture(TEXTURE_DIRT)
    TEX_STONE = load_texture(TEXTURE_STONE)

def build_cube_list():
    global CUBE_LIST_DIRT, CUBE_LIST_GRASS_SIDES, CUBE_LIST_GRASS_TOP, CUBE_LIST_STONE
    CUBE_LIST_DIRT = glGenLists(1)
    glNewList(CUBE_LIST_DIRT, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, TEX_DIRT)
    glBegin(GL_QUADS)
    for surface in SURFACES:
        for i, vertex_index in enumerate(surface):
            u, v = TEX_COORDS[i]
            glTexCoord2f(u, v)
            glVertex3fv(VERTICES[vertex_index])
    glEnd()
    glEndList()

    CUBE_LIST_GRASS_SIDES = glGenLists(1)
    glNewList(CUBE_LIST_GRASS_SIDES, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, TEX_DIRT)
    glBegin(GL_QUADS)
    for i, surface in enumerate(SURFACES):
        if i == 4:
            continue
        for j, vertex_index in enumerate(surface):
            u, v = TEX_COORDS[j]
            glTexCoord2f(u, v)
            glVertex3fv(VERTICES[vertex_index])
    glEnd()
    glEndList()

    CUBE_LIST_GRASS_TOP = glGenLists(1)
    glNewList(CUBE_LIST_GRASS_TOP, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, TEX_GRASS_TOP)
    glBegin(GL_QUADS)
    surface = SURFACES[4]
    for i, vertex_index in enumerate(surface):
        u, v = TEX_COORDS[i]
        glTexCoord2f(u, v)
        glVertex3fv(VERTICES[vertex_index])
    glEnd()
    glEndList()

    CUBE_LIST_STONE = glGenLists(1)
    glNewList(CUBE_LIST_STONE, GL_COMPILE)
    glBindTexture(GL_TEXTURE_2D, TEX_STONE)
    glBegin(GL_QUADS)
    for surface in SURFACES:
        for i, vertex_index in enumerate(surface):
            u, v = TEX_COORDS[i]
            glTexCoord2f(u, v)
            glVertex3fv(VERTICES[vertex_index])
    glEnd()
    glEndList()

def init_world():
    global LAST_PLAYER_CHUNK, LAST_PLAYER_Y, CHUNKS_NEED_UPDATE
    PLACED_BLOCKS.clear()
    REMOVED_GROUND.clear()
    REMOVED_STONE.clear()
    for chunk in ACTIVE_CHUNKS.values():
        if chunk.display_list:
            glDeleteLists(chunk.display_list, 1)
    ACTIVE_CHUNKS.clear()
    LAST_PLAYER_CHUNK = None
    LAST_PLAYER_Y = None
    CHUNKS_NEED_UPDATE = True

def is_in_world(x, y, z):
    if x < WORLD_MIN_X or x > WORLD_MAX_X:
        return False
    if z < WORLD_MIN_Z or z > WORLD_MAX_Z:
        return False
    if y < WORLD_MIN_Y or y > WORLD_MAX_Y:
        return False
    return True

def is_block_at(x, y, z):
    if not is_in_world(x, y, z):
        return False
    if (x, y, z) in PLACED_BLOCKS:
        return True
    if y == -1:
        return (x, y, z) not in REMOVED_GROUND
    if y <= -2:
        if is_cave_air(x, y, z):
            return False
        return (x, y, z) not in REMOVED_STONE
    return (x, y, z) in PLACED_BLOCKS

@lru_cache(maxsize=500000)
def _hash3(x, y, z, seed):
    h = x * 374761393 + y * 668265263 + z * 2147483647 + seed * 374761393
    h = (h ^ (h >> 13)) & 0xFFFFFFFF
    return h

@lru_cache(maxsize=500000)
def _hash_float(x, y, z, seed):
    return _hash3(x, y, z, seed) / 0xFFFFFFFF

def _fade(t):
    return t * t * (3.0 - 2.0 * t)

def _lerp(a, b, t):
    return a + (b - a) * t

@lru_cache(maxsize=200000)
def value_noise_3d(x, y, z, scale, seed):
    sx = x * scale
    sy = y * scale
    sz = z * scale
    x0 = int(math.floor(sx))
    y0 = int(math.floor(sy))
    z0 = int(math.floor(sz))
    x1 = x0 + 1
    y1 = y0 + 1
    z1 = z0 + 1
    fx = _fade(sx - x0)
    fy = _fade(sy - y0)
    fz = _fade(sz - z0)

    v000 = _hash_float(x0, y0, z0, seed)
    v100 = _hash_float(x1, y0, z0, seed)
    v010 = _hash_float(x0, y1, z0, seed)
    v110 = _hash_float(x1, y1, z0, seed)
    v001 = _hash_float(x0, y0, z1, seed)
    v101 = _hash_float(x1, y0, z1, seed)
    v011 = _hash_float(x0, y1, z1, seed)
    v111 = _hash_float(x1, y1, z1, seed)

    x00 = _lerp(v000, v100, fx)
    x10 = _lerp(v010, v110, fx)
    x01 = _lerp(v001, v101, fx)
    x11 = _lerp(v011, v111, fx)
    y0v = _lerp(x00, x10, fy)
    y1v = _lerp(x01, x11, fy)
    return _lerp(y0v, y1v, fz)

@lru_cache(maxsize=200000)
def is_cave_air(x, y, z):
    if y < CAVE_MIN_Y or y > CAVE_MAX_Y:
        return False
    n1 = value_noise_3d(x, y, z, CAVE_SCALE, CAVE_SEED)
    n2 = value_noise_3d(x + 101, y - 37, z + 53, CAVE_SCALE * 1.9, CAVE_SEED + 17)
    density = (n1 * 0.7 + n2 * 0.3)
    return density > CAVE_THRESHOLD

def world_to_chunk(x, z):
    return (int(math.floor(x / CHUNK_SIZE)), int(math.floor(z / CHUNK_SIZE)))

def chunk_bounds(cx, cz):
    start_x = cx * CHUNK_SIZE
    start_z = cz * CHUNK_SIZE
    end_x = start_x + CHUNK_SIZE - 1
    end_z = start_z + CHUNK_SIZE - 1
    return start_x, end_x, start_z, end_z

def chunk_limits():
    min_cx = WORLD_MIN_X // CHUNK_SIZE
    max_cx = WORLD_MAX_X // CHUNK_SIZE
    min_cz = WORLD_MIN_Z // CHUNK_SIZE
    max_cz = WORLD_MAX_Z // CHUNK_SIZE
    return min_cx, max_cx, min_cz, max_cz

def is_chunk_in_world(cx, cz):
    min_cx, max_cx, min_cz, max_cz = chunk_limits()
    return min_cx <= cx <= max_cx and min_cz <= cz <= max_cz

def build_chunk_list(chunk):
    if chunk.display_list is None:
        chunk.display_list = glGenLists(1)
    glNewList(chunk.display_list, GL_COMPILE)
    cx, cz = chunk.key
    start_x, end_x, start_z, end_z = chunk_bounds(cx, cz)
    if end_x < WORLD_MIN_X or start_x > WORLD_MAX_X or end_z < WORLD_MIN_Z or start_z > WORLD_MAX_Z:
        glEndList()
        chunk.dirty = False
        return
    min_x = max(start_x, WORLD_MIN_X)
    max_x = min(end_x, WORLD_MAX_X)
    min_z = max(start_z, WORLD_MIN_Z)
    max_z = min(end_z, WORLD_MAX_Z)
    removed_ground = REMOVED_GROUND
    removed_stone = REMOVED_STONE
    placed_blocks = PLACED_BLOCKS
    for x in range(min_x, max_x + 1):
        for z in range(min_z, max_z + 1):
            if (x, -1, z) not in removed_ground and (x, -1, z) not in placed_blocks:
                glPushMatrix()
                glTranslatef(x, -1, z)
                draw_grass_block()
                glPopMatrix()

    for (x, y, z) in placed_blocks:
        if x < min_x or x > max_x or z < min_z or z > max_z:
            continue
        glPushMatrix()
        glTranslatef(x, y, z)
        draw_dirt_block()
        glPopMatrix()

    exposed_stone = set()
    candidates = set()
    for (ax, ay, az) in removed_ground:
        if ax < min_x - 1 or ax > max_x + 1 or az < min_z - 1 or az > max_z + 1:
            continue
        candidates.add((ax, ay, az))
    for (ax, ay, az) in removed_stone:
        if ax < min_x - 1 or ax > max_x + 1 or az < min_z - 1 or az > max_z + 1:
            continue
        candidates.add((ax, ay, az))

    center_y = int(round(player.position[1]))
    cave_min_y = max(CAVE_MIN_Y, center_y - CAVE_RENDER_RANGE, WORLD_MIN_Y)
    cave_max_y = min(CAVE_MAX_Y, center_y + CAVE_RENDER_RANGE, -2)
    if cave_max_y >= cave_min_y:
        for x in range(min_x - 1, max_x + 2):
            for z in range(min_z - 1, max_z + 2):
                for y in range(cave_min_y, cave_max_y + 1):
                    if is_cave_air(x, y, z):
                        candidates.add((x, y, z))

    for (ax, ay, az) in candidates:
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0), (0, 1, 0)):
            nx, ny, nz = ax + dx, ay + dy, az + dz
            if ny > -2:
                continue
            if nx < min_x or nx > max_x or nz < min_z or nz > max_z:
                continue
            if not is_in_world(nx, ny, nz):
                continue
            if not is_block_at(nx, ny, nz):
                continue
            if (nx, ny, nz) in removed_stone:
                continue
            if (nx, ny, nz) in placed_blocks:
                continue
            exposed_stone.add((nx, ny, nz))

    for (x, y, z) in exposed_stone:
        if y < WORLD_MIN_Y or y > -2:
            continue
        if not is_block_at(x, y, z):
            continue
        # Confirm at least one face is exposed to air
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -1, 0), (0, 1, 0)):
            nx, ny, nz = x + dx, y + dy, z + dz
            if not is_block_at(nx, ny, nz):
                glPushMatrix()
                glTranslatef(x, y, z)
                draw_stone_cube()
                glPopMatrix()
                break
    glEndList()
    chunk.dirty = False

def mark_chunk_dirty_at(x, z):
    global CHUNKS_NEED_UPDATE
    cx, cz = world_to_chunk(x, z)
    keys = {(cx, cz)}
    if x % CHUNK_SIZE == 0:
        keys.add((cx - 1, cz))
    if x % CHUNK_SIZE == CHUNK_SIZE - 1:
        keys.add((cx + 1, cz))
    if z % CHUNK_SIZE == 0:
        keys.add((cx, cz - 1))
    if z % CHUNK_SIZE == CHUNK_SIZE - 1:
        keys.add((cx, cz + 1))
    for key in keys:
        if key in ACTIVE_CHUNKS:
            ACTIVE_CHUNKS[key].dirty = True
    CHUNKS_NEED_UPDATE = True

def update_visible_chunks(force=False):
    global LAST_PLAYER_CHUNK, LAST_PLAYER_Y, CHUNKS_NEED_UPDATE
    player_chunk = world_to_chunk(player.position[0], player.position[2])
    if force or player_chunk != LAST_PLAYER_CHUNK:
        LAST_PLAYER_CHUNK = player_chunk
        desired = set()
        for dx in range(-CHUNK_RADIUS, CHUNK_RADIUS + 1):
            for dz in range(-CHUNK_RADIUS, CHUNK_RADIUS + 1):
                cx = player_chunk[0] + dx
                cz = player_chunk[1] + dz
                if not is_chunk_in_world(cx, cz):
                    continue
                desired.add((cx, cz))
        for key in list(ACTIVE_CHUNKS.keys()):
            if key not in desired:
                chunk = ACTIVE_CHUNKS.pop(key)
                if chunk.display_list:
                    glDeleteLists(chunk.display_list, 1)
        for key in desired:
            if key not in ACTIVE_CHUNKS:
                ACTIVE_CHUNKS[key] = ChunkMesh(key)
        CHUNKS_NEED_UPDATE = True

    if LAST_PLAYER_Y is None:
        LAST_PLAYER_Y = player.position[1]
    if abs(player.position[1] - LAST_PLAYER_Y) >= CAVE_REFRESH_STEP:
        LAST_PLAYER_Y = player.position[1]
        for chunk in ACTIVE_CHUNKS.values():
            chunk.dirty = True
        CHUNKS_NEED_UPDATE = True

    if CHUNKS_NEED_UPDATE:
        builds = 0
        for chunk in ACTIVE_CHUNKS.values():
            if not chunk.dirty:
                continue
            build_chunk_list(chunk)
            builds += 1
            if builds >= MAX_CHUNK_BUILDS_PER_FRAME:
                break
        CHUNKS_NEED_UPDATE = any(chunk.dirty for chunk in ACTIVE_CHUNKS.values())

def draw_chunks():
    update_visible_chunks()
    for chunk in ACTIVE_CHUNKS.values():
        if chunk.display_list:
            glCallList(chunk.display_list)

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def apply_camera_transform():
    """ カメラの変形を適用する """
    glLoadIdentity()
    glRotatef(camera.rotation[1], 1, 0, 0) # Pitch
    glRotatef(camera.rotation[0], 0, 1, 0) # Yaw
    glTranslatef(-player.position[0], -(player.position[1] + get_eye_height()), -player.position[2])

def get_player_height():
    return CROUCH_HEIGHT if player.crouching else PLAYER_HEIGHT

def get_eye_height():
    return CROUCH_EYE_HEIGHT if player.crouching else EYE_HEIGHT

def get_view_direction():
    yaw_rad = math.radians(camera.rotation[0])
    pitch_rad = math.radians(camera.rotation[1])
    dir_x = math.sin(yaw_rad) * math.cos(pitch_rad)
    dir_y = -math.sin(pitch_rad)
    dir_z = -math.cos(yaw_rad) * math.cos(pitch_rad)
    return (dir_x, dir_y, dir_z)

def intbound(s, ds):
    if ds > 0:
        return (math.floor(s + 1) - s) / ds
    if ds < 0:
        return (s - math.floor(s)) / (-ds)
    return float("inf")

def raycast_blocks(origin, direction, max_dist):
    ox, oy, oz = origin
    dx, dy, dz = direction
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length <= 0.0:
        return (None, None)
    dx /= length
    dy /= length
    dz /= length

    px = ox + 0.5
    py = oy + 0.5
    pz = oz + 0.5
    vx = math.floor(px)
    vy = math.floor(py)
    vz = math.floor(pz)

    step_x = 1 if dx > 0 else -1 if dx < 0 else 0
    step_y = 1 if dy > 0 else -1 if dy < 0 else 0
    step_z = 1 if dz > 0 else -1 if dz < 0 else 0

    t_max_x = intbound(px, dx)
    t_max_y = intbound(py, dy)
    t_max_z = intbound(pz, dz)
    t_delta_x = abs(1 / dx) if dx != 0 else float("inf")
    t_delta_y = abs(1 / dy) if dy != 0 else float("inf")
    t_delta_z = abs(1 / dz) if dz != 0 else float("inf")

    prev = None
    t = 0.0
    while t <= max_dist:
        if is_block_at(vx, vy, vz):
            return ((vx, vy, vz), prev)
        if t_max_x < t_max_y:
            if t_max_x < t_max_z:
                prev = (vx, vy, vz)
                vx += step_x
                t = t_max_x
                t_max_x += t_delta_x
            else:
                prev = (vx, vy, vz)
                vz += step_z
                t = t_max_z
                t_max_z += t_delta_z
        else:
            if t_max_y < t_max_z:
                prev = (vx, vy, vz)
                vy += step_y
                t = t_max_y
                t_max_y += t_delta_y
            else:
                prev = (vx, vy, vz)
                vz += step_z
                t = t_max_z
                t_max_z += t_delta_z

        if (vx < WORLD_MIN_X or vx > WORLD_MAX_X or
            vz < WORLD_MIN_Z or vz > WORLD_MAX_Z or
            vy < WORLD_MIN_Y or vy > WORLD_MAX_Y):
            return (None, None)
    return (None, None)

def get_target_block():
    eye = (player.position[0], player.position[1] + get_eye_height(), player.position[2])
    direction = get_view_direction()
    hit, _ = raycast_blocks(eye, direction, MAX_REACH)
    return hit

def get_player_aabb(pos):
    min_x = pos[0] - PLAYER_RADIUS
    max_x = pos[0] + PLAYER_RADIUS
    min_y = pos[1]
    max_y = pos[1] + get_player_height()
    min_z = pos[2] - PLAYER_RADIUS
    max_z = pos[2] + PLAYER_RADIUS
    return (min_x, max_x, min_y, max_y, min_z, max_z)

def block_aabb(x, y, z):
    return (x - 0.5, x + 0.5, y - 0.5, y + 0.5, z - 0.5, z + 0.5)

def aabb_overlap(a, b):
    return (a[0] < b[1] and a[1] > b[0] and
            a[2] < b[3] and a[3] > b[2] and
            a[4] < b[5] and a[5] > b[4])

def iter_nearby_blocks(aabb):
    min_x = math.floor(aabb[0] - 0.5)
    max_x = math.floor(aabb[1] + 0.5)
    min_y = math.floor(aabb[2] - 0.5)
    max_y = math.floor(aabb[3] + 0.5)
    min_z = math.floor(aabb[4] - 0.5)
    max_z = math.floor(aabb[5] + 0.5)
    for x in range(min_x, max_x + 1):
        if x < WORLD_MIN_X or x > WORLD_MAX_X:
            continue
        for y in range(min_y, max_y + 1):
            if y < WORLD_MIN_Y or y > WORLD_MAX_Y:
                continue
            for z in range(min_z, max_z + 1):
                if z < WORLD_MIN_Z or z > WORLD_MAX_Z:
                    continue
                if is_block_at(x, y, z):
                    yield (x, y, z)

def resolve_collisions(dx, dy, dz):
    # X
    if dx != 0.0:
        player.position[0] += dx
        aabb = get_player_aabb(player.position)
        for bx, by, bz in iter_nearby_blocks(aabb):
            baabb = block_aabb(bx, by, bz)
            if aabb_overlap(aabb, baabb):
                if dx > 0:
                    player.position[0] = baabb[0] - PLAYER_RADIUS
                else:
                    player.position[0] = baabb[1] + PLAYER_RADIUS
                aabb = get_player_aabb(player.position)
    # Z
    if dz != 0.0:
        player.position[2] += dz
        aabb = get_player_aabb(player.position)
        for bx, by, bz in iter_nearby_blocks(aabb):
            baabb = block_aabb(bx, by, bz)
            if aabb_overlap(aabb, baabb):
                if dz > 0:
                    player.position[2] = baabb[4] - PLAYER_RADIUS
                else:
                    player.position[2] = baabb[5] + PLAYER_RADIUS
                aabb = get_player_aabb(player.position)
    # Y
    if dy != 0.0:
        player.position[1] += dy
        aabb = get_player_aabb(player.position)
        for bx, by, bz in iter_nearby_blocks(aabb):
            baabb = block_aabb(bx, by, bz)
            if aabb_overlap(aabb, baabb):
                if dy > 0:
                    player.position[1] = baabb[2] - get_player_height()
                    player.velocity_y = 0.0
                else:
                    player.position[1] = baabb[3]
                    player.velocity_y = 0.0
                    player.on_ground = True
                aabb = get_player_aabb(player.position)

def handle_input():
    """ ユーザー入力を処理する """
    keys = pygame.key.get_pressed()
    player.crouching = keys[K_LSHIFT] or keys[K_RSHIFT]
    
    # マウスの動き
    dx, dy = pygame.mouse.get_rel()
    camera.rotation[0] += dx * MOUSE_SENSITIVITY
    camera.rotation[1] += dy * MOUSE_SENSITIVITY
    camera.rotation[1] = max(-89, min(89, camera.rotation[1]))
    
    # Yawをラジアンに変換
    yaw_rad = math.radians(camera.rotation[0])
    
    # 正しい前方・右方ベクトルを計算
    # OpenGLの-Z方向が前方であることを考慮する
    fwd_x_comp = math.sin(yaw_rad)
    fwd_z_comp = -math.cos(yaw_rad)
    
    right_x_comp = math.cos(yaw_rad)
    right_z_comp = math.sin(yaw_rad)

    # WASDキーでの移動
    move_dx = 0.0
    move_dz = 0.0
    speed = CROUCH_SPEED if player.crouching else MOVE_SPEED
    if keys[K_w]: # 前進
        move_dx += fwd_x_comp * speed
        move_dz += fwd_z_comp * speed
    if keys[K_s]: # 後退
        move_dx -= fwd_x_comp * speed
        move_dz -= fwd_z_comp * speed
    if keys[K_a]: # 左へ平行移動
        move_dx -= right_x_comp * speed
        move_dz -= right_z_comp * speed
    if keys[K_d]: # 右へ平行移動
        move_dx += right_x_comp * speed
        move_dz += right_z_comp * speed

    if keys[K_SPACE] and player.on_ground:
        player.velocity_y = JUMP_VELOCITY
        player.on_ground = False

    return move_dx, move_dz

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
    glOrtho(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    glLineWidth(2.0)
    glColor3f(0.0, 0.0, 0.0)
    cx = SCREEN_WIDTH * 0.5
    cy = SCREEN_HEIGHT * 0.5
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

def is_supported(pos):
    aabb = get_player_aabb(pos)
    foot_y = aabb[2]
    support_slice = (aabb[0], aabb[1], foot_y - 0.05, foot_y - 0.001, aabb[4], aabb[5])
    for bx, by, bz in iter_nearby_blocks(support_slice):
        baabb = block_aabb(bx, by, bz)
        if aabb_overlap(support_slice, baabb):
            return True
    return False

def can_place_block(pos):
    if pos is None:
        return False
    x, y, z = pos
    if not is_in_world(x, y, z):
        return False
    if is_block_at(x, y, z):
        return False
    player_aabb = get_player_aabb(player.position)
    block_aabb_vals = block_aabb(x, y, z)
    if aabb_overlap(player_aabb, block_aabb_vals):
        return False
    return True

def main():
    """ ゲームのメイン処理 """
    global BLOCKS_PLACED, BLOCKS_REMOVED, SESSION_START
    BLOCKS_PLACED = 0
    BLOCKS_REMOVED = 0
    SESSION_START = time.time()
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption(CAPTION)
    
    # マウスを非表示 & ウィンドウ内に固定
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    init_gl()
    init_world()
    log_event("Session start")
    clock = pygame.time.Clock()

    def shutdown_and_exit():
        duration = time.time() - SESSION_START
        log_event(
            "Session end"
            f" | duration={duration:.1f}s"
            f" | placed={BLOCKS_PLACED}"
            f" | removed={BLOCKS_REMOVED}"
            f" | pos=({player.position[0]:.2f},{player.position[1]:.2f},{player.position[2]:.2f})"
        )
        pygame.quit()
        sys.exit()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                shutdown_and_exit()
            if event.type == KEYDOWN and event.key == K_r:
                player.position = [0.0, 0.0, 0.0]
                player.velocity_y = 0.0
                player.on_ground = False
                log_event("Respawn")
            if event.type == MOUSEBUTTONDOWN:
                eye = (player.position[0], player.position[1] + get_eye_height(), player.position[2])
                direction = get_view_direction()
                hit, prev = raycast_blocks(eye, direction, MAX_REACH)
                if event.button == 3:
                    if hit is not None and is_block_at(*hit):
                        if hit in PLACED_BLOCKS:
                            PLACED_BLOCKS.discard(hit)
                        elif hit[1] == -1:
                            REMOVED_GROUND.add(hit)
                        elif hit[1] <= -2:
                            REMOVED_STONE.add(hit)
                        BLOCKS_REMOVED += 1
                        mark_chunk_dirty_at(hit[0], hit[2])
                if event.button == 1:
                    if can_place_block(prev):
                        PLACED_BLOCKS.add(prev)
                        BLOCKS_PLACED += 1
                        mark_chunk_dirty_at(prev[0], prev[2])

        move_dx, move_dz = handle_input()
        if player.crouching and player.on_ground and (move_dx != 0.0 or move_dz != 0.0):
            next_pos = [player.position[0] + move_dx, player.position[1], player.position[2] + move_dz]
            if not is_supported(next_pos):
                move_dx = 0.0
                move_dz = 0.0

        player.on_ground = False
        player.velocity_y += GRAVITY
        resolve_collisions(move_dx, player.velocity_y, move_dz)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        apply_camera_transform()
        draw_ground()
        target = get_target_block()
        draw_target_block_outline(target)
        draw_crosshair()
        
        pygame.display.flip()
        clock.tick(60) # 60 FPSに制限


if __name__ == '__main__':
    main()
