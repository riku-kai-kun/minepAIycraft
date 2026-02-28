import math
from functools import lru_cache

from OpenGL.GL import *

from . import state as s

NEIGHBOR_OFFSETS = (
    (1, 0, 0),
    (-1, 0, 0),
    (0, 0, 1),
    (0, 0, -1),
    (0, -1, 0),
    (0, 1, 0),
)


def init_world():
    s.PLACED_BLOCKS.clear()
    s.REMOVED_GROUND.clear()
    s.REMOVED_STONE.clear()
    s.PLACED_BLOCKS_BY_CHUNK.clear()
    s.REMOVED_GROUND_BY_CHUNK.clear()
    s.REMOVED_STONE_BY_CHUNK.clear()
    for chunk in s.ACTIVE_CHUNKS.values():
        if chunk.display_list:
            glDeleteLists(chunk.display_list, 1)
    s.ACTIVE_CHUNKS.clear()
    s.LAST_PLAYER_CHUNK = None
    s.LAST_PLAYER_Y = None
    s.CHUNKS_NEED_UPDATE = True


def is_in_world(x, y, z):
    if x < s.WORLD_MIN_X or x > s.WORLD_MAX_X:
        return False
    if z < s.WORLD_MIN_Z or z > s.WORLD_MAX_Z:
        return False
    if y < s.WORLD_MIN_Y or y > s.WORLD_MAX_Y:
        return False
    return True


def is_block_at(x, y, z):
    if not is_in_world(x, y, z):
        return False
    if (x, y, z) in s.PLACED_BLOCKS:
        return True
    if y == -1:
        return (x, y, z) not in s.REMOVED_GROUND
    if y <= -2:
        if is_cave_air(x, y, z):
            return False
        return (x, y, z) not in s.REMOVED_STONE
    return (x, y, z) in s.PLACED_BLOCKS


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
    if y < s.CAVE_MIN_Y or y > s.CAVE_MAX_Y:
        return False
    n1 = value_noise_3d(x, y, z, s.CAVE_SCALE, s.CAVE_SEED)
    n2 = value_noise_3d(x + 101, y - 37, z + 53, s.CAVE_SCALE * 1.9, s.CAVE_SEED + 17)
    density = (n1 * 0.7 + n2 * 0.3)
    return density > s.CAVE_THRESHOLD


def world_to_chunk(x, z):
    return (int(math.floor(x / s.CHUNK_SIZE)), int(math.floor(z / s.CHUNK_SIZE)))


def _add_to_chunk_index(index, chunk_key, pos):
    bucket = index.get(chunk_key)
    if bucket is None:
        bucket = set()
        index[chunk_key] = bucket
    bucket.add(pos)


def _discard_from_chunk_index(index, chunk_key, pos):
    bucket = index.get(chunk_key)
    if bucket is None:
        return
    bucket.discard(pos)
    if not bucket:
        del index[chunk_key]


def _chunk_key_from_pos(pos):
    return world_to_chunk(pos[0], pos[2])


def add_placed_block(pos):
    if pos in s.PLACED_BLOCKS:
        return False
    s.PLACED_BLOCKS.add(pos)
    _add_to_chunk_index(s.PLACED_BLOCKS_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    return True


def discard_placed_block(pos):
    if pos not in s.PLACED_BLOCKS:
        return False
    s.PLACED_BLOCKS.discard(pos)
    _discard_from_chunk_index(s.PLACED_BLOCKS_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    return True


def add_removed_ground(pos):
    if pos in s.REMOVED_GROUND:
        return False
    s.REMOVED_GROUND.add(pos)
    _add_to_chunk_index(s.REMOVED_GROUND_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    return True


def add_removed_stone(pos):
    if pos in s.REMOVED_STONE:
        return False
    s.REMOVED_STONE.add(pos)
    _add_to_chunk_index(s.REMOVED_STONE_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    return True


def remove_block_at(pos):
    if pos in s.PLACED_BLOCKS:
        return discard_placed_block(pos)
    if pos[1] == -1:
        return add_removed_ground(pos)
    if pos[1] <= -2:
        return add_removed_stone(pos)
    return False


@lru_cache(maxsize=512)
def cave_air_candidates_for_window(min_x, max_x, min_z, max_z, min_y, max_y):
    if max_y < min_y:
        return ()
    candidates = []
    for x in range(min_x, max_x + 1):
        for z in range(min_z, max_z + 1):
            for y in range(min_y, max_y + 1):
                if is_cave_air(x, y, z):
                    candidates.append((x, y, z))
    return tuple(candidates)


def chunk_bounds(cx, cz):
    start_x = cx * s.CHUNK_SIZE
    start_z = cz * s.CHUNK_SIZE
    end_x = start_x + s.CHUNK_SIZE - 1
    end_z = start_z + s.CHUNK_SIZE - 1
    return start_x, end_x, start_z, end_z


def chunk_limits():
    min_cx = s.WORLD_MIN_X // s.CHUNK_SIZE
    max_cx = s.WORLD_MAX_X // s.CHUNK_SIZE
    min_cz = s.WORLD_MIN_Z // s.CHUNK_SIZE
    max_cz = s.WORLD_MAX_Z // s.CHUNK_SIZE
    return min_cx, max_cx, min_cz, max_cz


def is_chunk_in_world(cx, cz):
    min_cx, max_cx, min_cz, max_cz = chunk_limits()
    return min_cx <= cx <= max_cx and min_cz <= cz <= max_cz


def build_chunk_list(chunk):
    from . import rendering
    if chunk.display_list is None:
        chunk.display_list = glGenLists(1)
    glNewList(chunk.display_list, GL_COMPILE)
    cx, cz = chunk.key
    start_x, end_x, start_z, end_z = chunk_bounds(cx, cz)
    if (
        end_x < s.WORLD_MIN_X
        or start_x > s.WORLD_MAX_X
        or end_z < s.WORLD_MIN_Z
        or start_z > s.WORLD_MAX_Z
    ):
        glEndList()
        chunk.dirty = False
        return
    min_x = max(start_x, s.WORLD_MIN_X)
    max_x = min(end_x, s.WORLD_MAX_X)
    min_z = max(start_z, s.WORLD_MIN_Z)
    max_z = min(end_z, s.WORLD_MAX_Z)
    removed_stone = s.REMOVED_STONE
    placed_blocks = s.PLACED_BLOCKS
    removed_ground_by_chunk = s.REMOVED_GROUND_BY_CHUNK
    removed_stone_by_chunk = s.REMOVED_STONE_BY_CHUNK
    for x in range(min_x, max_x + 1):
        for z in range(min_z, max_z + 1):
            if (x, -1, z) not in s.REMOVED_GROUND and (x, -1, z) not in placed_blocks:
                glPushMatrix()
                glTranslatef(x, -1, z)
                rendering.draw_grass_block()
                glPopMatrix()

    for (x, y, z) in s.PLACED_BLOCKS_BY_CHUNK.get((cx, cz), ()):
        glPushMatrix()
        glTranslatef(x, y, z)
        rendering.draw_dirt_block()
        glPopMatrix()

    exposed_stone = set()
    candidates = set()
    ext_min_x = min_x - 1
    ext_max_x = max_x + 1
    ext_min_z = min_z - 1
    ext_max_z = max_z + 1
    for nx in range(cx - 1, cx + 2):
        for nz in range(cz - 1, cz + 2):
            for (ax, ay, az) in removed_ground_by_chunk.get((nx, nz), ()):
                if ext_min_x <= ax <= ext_max_x and ext_min_z <= az <= ext_max_z:
                    candidates.add((ax, ay, az))
            for (ax, ay, az) in removed_stone_by_chunk.get((nx, nz), ()):
                if ext_min_x <= ax <= ext_max_x and ext_min_z <= az <= ext_max_z:
                    candidates.add((ax, ay, az))

    center_y = int(round(s.player.position[1]))
    cave_min_y = max(s.CAVE_MIN_Y, center_y - s.CAVE_RENDER_RANGE, s.WORLD_MIN_Y)
    cave_max_y = min(s.CAVE_MAX_Y, center_y + s.CAVE_RENDER_RANGE, -2)
    for pos in cave_air_candidates_for_window(
        ext_min_x,
        ext_max_x,
        ext_min_z,
        ext_max_z,
        cave_min_y,
        cave_max_y,
    ):
        candidates.add(pos)

    for (ax, ay, az) in candidates:
        for dx, dy, dz in NEIGHBOR_OFFSETS:
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
        if y < s.WORLD_MIN_Y or y > -2:
            continue
        if not is_block_at(x, y, z):
            continue
        # Confirm at least one face is exposed to air
        for dx, dy, dz in NEIGHBOR_OFFSETS:
            nx, ny, nz = x + dx, y + dy, z + dz
            if not is_block_at(nx, ny, nz):
                glPushMatrix()
                glTranslatef(x, y, z)
                rendering.draw_stone_cube()
                glPopMatrix()
                break
    glEndList()
    chunk.dirty = False


def mark_chunk_dirty_at(x, z):
    cx, cz = world_to_chunk(x, z)
    keys = {(cx, cz)}
    if x % s.CHUNK_SIZE == 0:
        keys.add((cx - 1, cz))
    if x % s.CHUNK_SIZE == s.CHUNK_SIZE - 1:
        keys.add((cx + 1, cz))
    if z % s.CHUNK_SIZE == 0:
        keys.add((cx, cz - 1))
    if z % s.CHUNK_SIZE == s.CHUNK_SIZE - 1:
        keys.add((cx, cz + 1))
    for key in keys:
        if key in s.ACTIVE_CHUNKS:
            s.ACTIVE_CHUNKS[key].dirty = True
    s.CHUNKS_NEED_UPDATE = True


def update_visible_chunks(force=False):
    player_chunk = world_to_chunk(s.player.position[0], s.player.position[2])
    if force or player_chunk != s.LAST_PLAYER_CHUNK:
        s.LAST_PLAYER_CHUNK = player_chunk
        desired = set()
        for dx in range(-s.CHUNK_RADIUS, s.CHUNK_RADIUS + 1):
            for dz in range(-s.CHUNK_RADIUS, s.CHUNK_RADIUS + 1):
                cx = player_chunk[0] + dx
                cz = player_chunk[1] + dz
                if not is_chunk_in_world(cx, cz):
                    continue
                desired.add((cx, cz))
        for key in list(s.ACTIVE_CHUNKS.keys()):
            if key not in desired:
                chunk = s.ACTIVE_CHUNKS.pop(key)
                if chunk.display_list:
                    glDeleteLists(chunk.display_list, 1)
        for key in desired:
            if key not in s.ACTIVE_CHUNKS:
                s.ACTIVE_CHUNKS[key] = s.ChunkMesh(key)
        s.CHUNKS_NEED_UPDATE = True

    if s.LAST_PLAYER_Y is None:
        s.LAST_PLAYER_Y = s.player.position[1]
    if abs(s.player.position[1] - s.LAST_PLAYER_Y) >= s.CAVE_REFRESH_STEP:
        s.LAST_PLAYER_Y = s.player.position[1]
        for chunk in s.ACTIVE_CHUNKS.values():
            chunk.dirty = True
        s.CHUNKS_NEED_UPDATE = True

    if s.CHUNKS_NEED_UPDATE:
        builds = 0
        for chunk in s.ACTIVE_CHUNKS.values():
            if not chunk.dirty:
                continue
            build_chunk_list(chunk)
            builds += 1
            if builds >= s.MAX_CHUNK_BUILDS_PER_FRAME:
                break
        s.CHUNKS_NEED_UPDATE = any(chunk.dirty for chunk in s.ACTIVE_CHUNKS.values())


def get_player_height():
    return s.CROUCH_HEIGHT if s.player.crouching else s.PLAYER_HEIGHT


def get_eye_height():
    return s.CROUCH_EYE_HEIGHT if s.player.crouching else s.EYE_HEIGHT


def get_view_direction():
    yaw_rad = math.radians(s.camera.rotation[0])
    pitch_rad = math.radians(s.camera.rotation[1])
    dir_x = math.sin(yaw_rad) * math.cos(pitch_rad)
    dir_y = -math.sin(pitch_rad)
    dir_z = -math.cos(yaw_rad) * math.cos(pitch_rad)
    return (dir_x, dir_y, dir_z)


def intbound(scalar, d_scalar):
    if d_scalar > 0:
        return (math.floor(scalar + 1) - scalar) / d_scalar
    if d_scalar < 0:
        return (scalar - math.floor(scalar)) / (-d_scalar)
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

        if (
            vx < s.WORLD_MIN_X
            or vx > s.WORLD_MAX_X
            or vz < s.WORLD_MIN_Z
            or vz > s.WORLD_MAX_Z
            or vy < s.WORLD_MIN_Y
            or vy > s.WORLD_MAX_Y
        ):
            return (None, None)
    return (None, None)


def get_target_block():
    eye = (
        s.player.position[0],
        s.player.position[1] + get_eye_height(),
        s.player.position[2],
    )
    direction = get_view_direction()
    hit, _ = raycast_blocks(eye, direction, s.MAX_REACH)
    return hit


def get_player_aabb(pos):
    min_x = pos[0] - s.PLAYER_RADIUS
    max_x = pos[0] + s.PLAYER_RADIUS
    min_y = pos[1]
    max_y = pos[1] + get_player_height()
    min_z = pos[2] - s.PLAYER_RADIUS
    max_z = pos[2] + s.PLAYER_RADIUS
    return (min_x, max_x, min_y, max_y, min_z, max_z)


def block_aabb(x, y, z):
    return (x - 0.5, x + 0.5, y - 0.5, y + 0.5, z - 0.5, z + 0.5)


def aabb_overlap(a, b):
    return (
        a[0] < b[1]
        and a[1] > b[0]
        and a[2] < b[3]
        and a[3] > b[2]
        and a[4] < b[5]
        and a[5] > b[4]
    )


def iter_nearby_blocks(aabb):
    min_x = math.floor(aabb[0] - 0.5)
    max_x = math.floor(aabb[1] + 0.5)
    min_y = math.floor(aabb[2] - 0.5)
    max_y = math.floor(aabb[3] + 0.5)
    min_z = math.floor(aabb[4] - 0.5)
    max_z = math.floor(aabb[5] + 0.5)
    for x in range(min_x, max_x + 1):
        if x < s.WORLD_MIN_X or x > s.WORLD_MAX_X:
            continue
        for y in range(min_y, max_y + 1):
            if y < s.WORLD_MIN_Y or y > s.WORLD_MAX_Y:
                continue
            for z in range(min_z, max_z + 1):
                if z < s.WORLD_MIN_Z or z > s.WORLD_MAX_Z:
                    continue
                if is_block_at(x, y, z):
                    yield (x, y, z)


def resolve_collisions(dx, dy, dz):
    # X
    if dx != 0.0:
        s.player.position[0] += dx
        aabb = get_player_aabb(s.player.position)
        for bx, by, bz in iter_nearby_blocks(aabb):
            baabb = block_aabb(bx, by, bz)
            if aabb_overlap(aabb, baabb):
                if dx > 0:
                    s.player.position[0] = baabb[0] - s.PLAYER_RADIUS
                else:
                    s.player.position[0] = baabb[1] + s.PLAYER_RADIUS
                aabb = get_player_aabb(s.player.position)
    # Z
    if dz != 0.0:
        s.player.position[2] += dz
        aabb = get_player_aabb(s.player.position)
        for bx, by, bz in iter_nearby_blocks(aabb):
            baabb = block_aabb(bx, by, bz)
            if aabb_overlap(aabb, baabb):
                if dz > 0:
                    s.player.position[2] = baabb[4] - s.PLAYER_RADIUS
                else:
                    s.player.position[2] = baabb[5] + s.PLAYER_RADIUS
                aabb = get_player_aabb(s.player.position)
    # Y
    if dy != 0.0:
        s.player.position[1] += dy
        aabb = get_player_aabb(s.player.position)
        for bx, by, bz in iter_nearby_blocks(aabb):
            baabb = block_aabb(bx, by, bz)
            if aabb_overlap(aabb, baabb):
                if dy > 0:
                    s.player.position[1] = baabb[2] - get_player_height()
                    s.player.velocity_y = 0.0
                else:
                    s.player.position[1] = baabb[3]
                    s.player.velocity_y = 0.0
                    s.player.on_ground = True
                aabb = get_player_aabb(s.player.position)


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
    player_aabb = get_player_aabb(s.player.position)
    block_aabb_vals = block_aabb(x, y, z)
    if aabb_overlap(player_aabb, block_aabb_vals):
        return False
    return True
