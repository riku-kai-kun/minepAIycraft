import math
import time
from collections import deque
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


def init_world(generate_oceans=True):
    s.PLACED_BLOCKS.clear()
    s.REMOVED_GROUND.clear()
    s.REMOVED_STONE.clear()
    s.PLACED_BLOCKS_BY_CHUNK.clear()
    s.REMOVED_GROUND_BY_CHUNK.clear()
    s.REMOVED_STONE_BY_CHUNK.clear()
    s.TALL_GRASS_BLOCKS_BY_CHUNK.clear()
    s.WATER_SOURCES.clear()
    s.WATER_BLOCKS.clear()
    s.WATER_BLOCKS_BY_CHUNK.clear()
    for chunk in s.ACTIVE_CHUNKS.values():
        if chunk.display_list:
            glDeleteLists(chunk.display_list, 1)
    s.ACTIVE_CHUNKS.clear()
    s.LAST_PLAYER_CHUNK = None
    s.LAST_PLAYER_Y = None
    s.CHUNKS_NEED_UPDATE = True
    s.WATER_NEEDS_UPDATE = True
    s.LAST_WATER_UPDATE = 0.0
    if generate_oceans:
        generate_ocean_basins()
    rebuild_water(force=True)


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
    if y >= -1:
        return is_natural_terrain_at(x, y, z)
    if y <= -2:
        if is_cave_air(x, y, z):
            return False
        return (x, y, z) not in s.REMOVED_STONE
    return (x, y, z) in s.PLACED_BLOCKS


@lru_cache(maxsize=400000)
def get_surface_height(x, z):
    # Flat world(-1)ベースに、疎な山塊を重ねる
    macro = value_noise_3d(x, 0, z, 0.010, s.CAVE_SEED + 401)
    detail = value_noise_3d(x + 913, 0, z - 417, 0.034, s.CAVE_SEED + 457)
    mask = max(0.0, (macro - 0.57) / 0.43)
    height = int(round((mask ** 1.65) * s.MOUNTAIN_HEIGHT_SCALE + (detail - 0.5) * 4))
    if height < 0:
        height = 0
    return min(s.WORLD_MAX_Y, -1 + height)


def is_natural_terrain_at(x, y, z):
    if y < -1:
        return False
    top = get_surface_height(x, z)
    if y > top:
        return False
    return (x, y, z) not in s.REMOVED_GROUND


@lru_cache(maxsize=200000)
def tall_grass_density_passes(x, z, threshold):
    # 低周波+高周波ノイズを混ぜて、列状パターンを避ける
    n1 = value_noise_3d(x + 137, 0, z - 241, 0.18, s.CAVE_SEED + 911)
    n2 = value_noise_3d(x - 59, 0, z + 83, 0.43, s.CAVE_SEED + 977)
    jitter = _hash_float(x, 0, z, s.CAVE_SEED + 1031) * 0.12
    density = n1 * 0.72 + n2 * 0.28 + jitter
    return density > threshold


def should_spawn_tall_grass_block(x, ground_y, z):
    grass_pos = (x, ground_y + 1, z)
    if grass_pos in s.PLACED_BLOCKS:
        return False
    if is_water_at(grass_pos[0], grass_pos[1], grass_pos[2]):
        return False
    return tall_grass_density_passes(x, z, s.TALL_GRASS_SPAWN_THRESHOLD)


def get_ground_visible_faces(x, y, z, top, surface_heights, placed_blocks):
    faces = []

    def side_solid(nx, ny, nz):
        if nx < s.WORLD_MIN_X or nx > s.WORLD_MAX_X or nz < s.WORLD_MIN_Z or nz > s.WORLD_MAX_Z:
            return False
        if (nx, ny, nz) in placed_blocks:
            return True
        neighbor_top = surface_heights.get((nx, nz))
        if neighbor_top is None:
            neighbor_top = get_surface_height(nx, nz)
        return ny <= neighbor_top and (nx, ny, nz) not in s.REMOVED_GROUND

    for face_index, nx, nz in (
        (0, x, z - 1),
        (1, x - 1, z),
        (2, x, z + 1),
        (3, x + 1, z),
    ):
        if not side_solid(nx, y, nz):
            faces.append(face_index)

    above = (x, y + 1, z)
    if above not in placed_blocks:
        if y == top or (y + 1 <= top and above in s.REMOVED_GROUND):
            faces.append(4)

    below = (x, y - 1, z)
    if below not in placed_blocks:
        if y - 1 >= -1:
            if below in s.REMOVED_GROUND:
                faces.append(5)
        elif (x, y - 1, z) in s.REMOVED_STONE:
            faces.append(5)

    return tuple(faces)


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
    remove_water_source(pos)
    s.PLACED_BLOCKS.add(pos)
    _add_to_chunk_index(s.PLACED_BLOCKS_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    s.WATER_NEEDS_UPDATE = True
    return True


def discard_placed_block(pos):
    if pos not in s.PLACED_BLOCKS:
        return False
    s.PLACED_BLOCKS.discard(pos)
    _discard_from_chunk_index(s.PLACED_BLOCKS_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    s.WATER_NEEDS_UPDATE = True
    return True


def add_removed_ground(pos):
    if pos in s.REMOVED_GROUND:
        return False
    s.REMOVED_GROUND.add(pos)
    _add_to_chunk_index(s.REMOVED_GROUND_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    s.WATER_NEEDS_UPDATE = True
    return True


def add_removed_stone(pos):
    if pos in s.REMOVED_STONE:
        return False
    s.REMOVED_STONE.add(pos)
    _add_to_chunk_index(s.REMOVED_STONE_BY_CHUNK, _chunk_key_from_pos(pos), pos)
    s.WATER_NEEDS_UPDATE = True
    return True


def is_water_at(x, y, z):
    return (x, y, z) in s.WATER_BLOCKS


def add_water_source(pos):
    x, y, z = int(pos[0]), int(pos[1]), int(pos[2])
    tpos = (x, y, z)
    if not is_in_world(x, y, z):
        return False
    if is_block_at(x, y, z):
        return False
    if tpos in s.WATER_SOURCES:
        return False
    s.WATER_SOURCES.add(tpos)
    s.WATER_NEEDS_UPDATE = True
    return True


def remove_water_source(pos):
    x, y, z = int(pos[0]), int(pos[1]), int(pos[2])
    tpos = (x, y, z)
    if tpos not in s.WATER_SOURCES:
        return False
    s.WATER_SOURCES.discard(tpos)
    s.WATER_NEEDS_UPDATE = True
    return True


def remove_block_at(pos):
    if pos in s.PLACED_BLOCKS:
        return discard_placed_block(pos)
    x, y, z = pos
    if y >= -1 and is_natural_terrain_at(x, y, z):
        return add_removed_ground(pos)
    if y <= -2:
        return add_removed_stone(pos)
    return False


def generate_ocean_basins():
    # Spawn付近に固定の海盆地を作る。水は水源から流して埋める。
    basins = (
        ((28, 12), 16, 9),
        ((-34, -18), 22, 13),
        ((64, -42), 18, 10),
    )
    for (cx, cz), radius, max_depth in basins:
        r2 = radius * radius
        for x in range(cx - radius, cx + radius + 1):
            for z in range(cz - radius, cz + radius + 1):
                dx = x - cx
                dz = z - cz
                dist2 = dx * dx + dz * dz
                if dist2 > r2:
                    continue
                ring = math.sqrt(dist2) / float(radius)
                depth = max(3, int(round((1.0 - ring) * max_depth)))
                if depth <= 0:
                    continue
                top = get_surface_height(x, z)
                for y in range(-1, top + 1):
                    add_removed_ground((x, y, z))
                for y in range(-2, -depth - 2, -1):
                    add_removed_stone((x, y, z))
                # Surface heightを地表穴(-1)に合わせて、外部(通常は空中)へ溢れないようにする
                if not is_block_at(x, -1, z):
                    add_water_source((x, -1, z))


def _commit_water_map(new_levels):
    old_levels = s.WATER_BLOCKS
    old_positions = set(old_levels.keys())
    new_positions = set(new_levels.keys())
    removed = old_positions - new_positions
    added = new_positions - old_positions
    changed_level = {
        pos for pos in (old_positions & new_positions)
        if old_levels.get(pos) != new_levels.get(pos)
    }

    for pos in removed:
        key = world_to_chunk(pos[0], pos[2])
        bucket = s.WATER_BLOCKS_BY_CHUNK.get(key)
        if bucket is not None:
            bucket.pop(pos, None)
            if not bucket:
                del s.WATER_BLOCKS_BY_CHUNK[key]

    for pos in (added | changed_level):
        key = world_to_chunk(pos[0], pos[2])
        bucket = s.WATER_BLOCKS_BY_CHUNK.get(key)
        if bucket is None:
            bucket = {}
            s.WATER_BLOCKS_BY_CHUNK[key] = bucket
        bucket[pos] = new_levels[pos]

    s.WATER_BLOCKS = new_levels
    for x, _, z in (removed | added | changed_level):
        mark_chunk_dirty_at(x, z)


def _iter_chunk_keys_for_bounds(min_x, max_x, min_z, max_z):
    min_cx = int(math.floor(min_x / s.CHUNK_SIZE))
    max_cx = int(math.floor(max_x / s.CHUNK_SIZE))
    min_cz = int(math.floor(min_z / s.CHUNK_SIZE))
    max_cz = int(math.floor(max_z / s.CHUNK_SIZE))
    for cx in range(min_cx, max_cx + 1):
        for cz in range(min_cz, max_cz + 1):
            yield (cx, cz)


def _in_bounds(pos, bounds):
    x, _, z = pos
    min_x, max_x, min_z, max_z = bounds
    return min_x <= x <= max_x and min_z <= z <= max_z


def _water_sim_bounds():
    px, pz = s.player.position[0], s.player.position[2]
    pcx, pcz = world_to_chunk(px, pz)
    radius = s.CHUNK_RADIUS + s.WATER_SIM_MARGIN_CHUNKS
    min_cx = pcx - radius
    max_cx = pcx + radius
    min_cz = pcz - radius
    max_cz = pcz + radius
    min_x = max(s.WORLD_MIN_X, min_cx * s.CHUNK_SIZE)
    max_x = min(s.WORLD_MAX_X, (max_cx + 1) * s.CHUNK_SIZE - 1)
    min_z = max(s.WORLD_MIN_Z, min_cz * s.CHUNK_SIZE)
    max_z = min(s.WORLD_MAX_Z, (max_cz + 1) * s.CHUNK_SIZE - 1)
    return (min_x, max_x, min_z, max_z)


def _commit_water_partial(local_next, bounds):
    min_x, max_x, min_z, max_z = bounds
    current_positions = set()
    for key in _iter_chunk_keys_for_bounds(min_x, max_x, min_z, max_z):
        bucket = s.WATER_BLOCKS_BY_CHUNK.get(key, {})
        for pos in bucket.keys():
            if _in_bounds(pos, bounds):
                current_positions.add(pos)

    new_positions = set(local_next.keys())
    removed = current_positions - new_positions
    added = new_positions - current_positions
    changed_level = {
        pos for pos in (current_positions & new_positions)
        if s.WATER_BLOCKS.get(pos) != local_next.get(pos)
    }

    for pos in removed:
        s.WATER_BLOCKS.pop(pos, None)
        key = world_to_chunk(pos[0], pos[2])
        bucket = s.WATER_BLOCKS_BY_CHUNK.get(key)
        if bucket is not None:
            bucket.pop(pos, None)
            if not bucket:
                del s.WATER_BLOCKS_BY_CHUNK[key]

    for pos in (added | changed_level):
        s.WATER_BLOCKS[pos] = local_next[pos]
        key = world_to_chunk(pos[0], pos[2])
        bucket = s.WATER_BLOCKS_BY_CHUNK.get(key)
        if bucket is None:
            bucket = {}
            s.WATER_BLOCKS_BY_CHUNK[key] = bucket
        bucket[pos] = local_next[pos]

    for x, _, z in (removed | added | changed_level):
        mark_chunk_dirty_at(x, z)


def rebuild_water(force=False):
    if not force and not s.WATER_NEEDS_UPDATE:
        return
    new_levels = {}
    queue = deque()

    for source in tuple(s.WATER_SOURCES):
        if is_in_world(source[0], source[1], source[2]) and not is_block_at(source[0], source[1], source[2]):
            queue.append((source, 0))

    while queue:
        (x, y, z), level = queue.popleft()
        if not is_in_world(x, y, z):
            continue
        if is_block_at(x, y, z):
            continue
        prev = new_levels.get((x, y, z))
        if prev is not None and prev <= level:
            continue
        new_levels[(x, y, z)] = level

        below = (x, y - 1, z)
        if is_in_world(below[0], below[1], below[2]) and not is_block_at(below[0], below[1], below[2]):
            queue.append((below, level))

        if level >= s.WATER_MAX_LEVEL:
            continue
        next_level = level + 1
        for nx, ny, nz in ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1)):
            if is_in_world(nx, ny, nz) and not is_block_at(nx, ny, nz):
                queue.append(((nx, ny, nz), next_level))

    _commit_water_map(new_levels)
    s.WATER_NEEDS_UPDATE = False


def _step_water_flow(bounds):
    prev = s.WATER_BLOCKS
    min_x, max_x, min_z, max_z = bounds
    influence_bounds = (min_x - 1, max_x + 1, min_z - 1, max_z + 1)

    candidates = set()
    for src in s.WATER_SOURCES:
        if _in_bounds(src, influence_bounds):
            candidates.add(src)

    for key in _iter_chunk_keys_for_bounds(*influence_bounds):
        bucket = s.WATER_BLOCKS_BY_CHUNK.get(key, {})
        for x, y, z in bucket.keys():
            if not _in_bounds((x, y, z), influence_bounds):
                continue
            candidates.add((x, y, z))
            candidates.add((x + 1, y, z))
            candidates.add((x - 1, y, z))
            candidates.add((x, y + 1, z))
            candidates.add((x, y - 1, z))
            candidates.add((x, y, z + 1))
            candidates.add((x, y, z - 1))

    local_next = {}
    for x, y, z in candidates:
        if x < min_x or x > max_x or z < min_z or z > max_z:
            continue
        if not is_in_world(x, y, z):
            continue
        if is_block_at(x, y, z):
            continue
        pos = (x, y, z)
        if pos in s.WATER_SOURCES:
            local_next[pos] = 0
            continue

        best = None
        up = (x, y + 1, z)
        below = (x, y - 1, z)
        old = prev.get(pos)

        up_level = prev.get(up)
        if up_level is not None:
            best = up_level if best is None else min(best, up_level)

        can_fall = is_in_world(below[0], below[1], below[2]) and not is_block_at(below[0], below[1], below[2])
        if can_fall:
            if old is not None or up_level is not None:
                best = 0 if best is None else min(best, 0)
            else:
                for npos in ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1)):
                    if prev.get(npos) is not None:
                        best = 0 if best is None else min(best, 0)
                        break

        supported = is_block_at(below[0], below[1], below[2]) or (below in prev) or (below in s.WATER_SOURCES)
        if supported:
            for npos in ((x + 1, y, z), (x - 1, y, z), (x, y, z + 1), (x, y, z - 1)):
                nlevel = prev.get(npos)
                if nlevel is None:
                    continue
                if nlevel >= s.WATER_MAX_LEVEL:
                    continue
                cand = nlevel + 1
                best = cand if best is None else min(best, cand)

        if best is None and old is not None and old < s.WATER_MAX_LEVEL:
            best = old + 1

        if best is not None and best <= s.WATER_MAX_LEVEL:
            local_next[pos] = best

    _commit_water_partial(local_next, bounds)
    s.WATER_NEEDS_UPDATE = False


def update_water_flow(force=False):
    now = time.time()
    if force:
        s.LAST_WATER_UPDATE = now
        rebuild_water(force=True)
        return
    if (now - s.LAST_WATER_UPDATE) >= s.WATER_UPDATE_INTERVAL:
        s.LAST_WATER_UPDATE = now
        _step_water_flow(_water_sim_bounds())


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
    surface_heights = {
        (x, z): get_surface_height(x, z)
        for x in range(max(s.WORLD_MIN_X, min_x - 1), min(s.WORLD_MAX_X, max_x + 1) + 1)
        for z in range(max(s.WORLD_MIN_Z, min_z - 1), min(s.WORLD_MAX_Z, max_z + 1) + 1)
    }
    tall_grass_blocks = []
    for x in range(min_x, max_x + 1):
        for z in range(min_z, max_z + 1):
            top = surface_heights[(x, z)]
            if (x, top, z) not in s.REMOVED_GROUND and should_spawn_tall_grass_block(x, top, z):
                tall_grass_blocks.append((x, top + 1, z))
            for y in range(-1, top + 1):
                if (x, y, z) in s.REMOVED_GROUND:
                    continue
                if (x, y, z) in placed_blocks:
                    continue
                visible_faces = get_ground_visible_faces(x, y, z, top, surface_heights, placed_blocks)
                if not visible_faces:
                    continue
                glPushMatrix()
                glTranslatef(x, y, z)
                if y == top:
                    rendering.draw_grass_block_faces(visible_faces)
                elif y >= top - 3:
                    rendering.draw_dirt_block_faces(visible_faces)
                else:
                    rendering.draw_stone_block_faces(visible_faces)
                glPopMatrix()
    s.TALL_GRASS_BLOCKS_BY_CHUNK[(cx, cz)] = tuple(tall_grass_blocks)

    for (x, y, z) in s.TALL_GRASS_BLOCKS_BY_CHUNK.get((cx, cz), ()):
        glPushMatrix()
        glTranslatef(x, y, z)
        rendering.draw_tall_grass()
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

    # 半透明水は最後に描画して見た目を安定させる
    for (x, y, z), level in s.WATER_BLOCKS_BY_CHUNK.get((cx, cz), {}).items():
        if is_block_at(x, y, z):
            continue
        show_top = not is_water_at(x, y + 1, z)
        show_bottom = (not is_water_at(x, y - 1, z)) and (not is_block_at(x, y - 1, z))
        show_north = not is_water_at(x, y, z - 1)
        show_south = not is_water_at(x, y, z + 1)
        show_west = not is_water_at(x - 1, y, z)
        show_east = not is_water_at(x + 1, y, z)
        if not (show_top or show_bottom or show_north or show_south or show_west or show_east):
            continue
        glPushMatrix()
        glTranslatef(x, y, z)
        rendering.draw_water_block(
            level,
            show_top=show_top,
            show_bottom=show_bottom,
            show_north=show_north,
            show_south=show_south,
            show_west=show_west,
            show_east=show_east,
        )
        glPopMatrix()
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
                s.TALL_GRASS_BLOCKS_BY_CHUNK.pop(key, None)
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


def point_to_block(x, y, z):
    return (
        int(math.floor(x + 0.5)),
        int(math.floor(y + 0.5)),
        int(math.floor(z + 0.5)),
    )


def is_player_in_water():
    # 頭と胴体の2点判定。どちらかが水なら水中扱い。
    px, py, pz = s.player.position
    top_y = py + max(0.2, get_player_height() * 0.75)
    bx1, by1, bz1 = point_to_block(px, py + 0.2, pz)
    bx2, by2, bz2 = point_to_block(px, top_y, pz)
    return is_water_at(bx1, by1, bz1) or is_water_at(bx2, by2, bz2)


def is_camera_underwater():
    px, py, pz = s.player.position
    eye_y = py + get_eye_height()
    bx, by, bz = point_to_block(px, eye_y, pz)
    if not is_water_at(bx, by, bz):
        return False
    water_surface_y = by + 0.48
    return eye_y < water_surface_y - 0.03
