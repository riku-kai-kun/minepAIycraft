import time

# --- 定数 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SKY_COLOR = (0.5, 0.8, 1.0, 1)
CAPTION = "MinepAIycraft"
APP_VERSION = "minepAIycraft_ver0.4"
MULTIPLAYER_PORT = 38573
MULTIPLAYER_ROOM_ID_LEN = 6
MULTIPLAYER_RELAY_HOST = "127.0.0.1"
MULTIPLAYER_RELAY_PORT = 39000
CHUNK_SIZE = 16
CHUNK_RADIUS = 4
VIEW_DISTANCE = CHUNK_SIZE * CHUNK_RADIUS
MAX_REACH = 6
STONE_DEPTH = 320
WORLD_SIZE = 10000
WORLD_MIN_X = -(WORLD_SIZE // 2)
WORLD_MAX_X = (WORLD_SIZE // 2) - 1
WORLD_MIN_Z = -(WORLD_SIZE // 2)
WORLD_MAX_Z = (WORLD_SIZE // 2) - 1
WORLD_MIN_Y = -1 - STONE_DEPTH
WORLD_MAX_Y = 63
LOG_PATH = "minepAIycraft.log"
CAVE_SEED = 1337
CAVE_SCALE = 0.07
CAVE_THRESHOLD = 0.72
CAVE_MIN_Y = -200
CAVE_MAX_Y = -20
CAVE_RENDER_RANGE = 12
CAVE_REFRESH_STEP = 8
MAX_CHUNK_BUILDS_PER_FRAME = 1
MOUNTAIN_HEIGHT_SCALE = 28
SEA_LEVEL = 0
WATER_MAX_LEVEL = 7
WATER_UPDATE_INTERVAL = 0.2
WATER_SIM_MARGIN_CHUNKS = 2
TALL_GRASS_SPAWN_THRESHOLD = 0.76

# --- ブロックの定義 ---
VERTICES = (
    (0.5, -0.5, -0.5),
    (0.5, 0.5, -0.5),
    (-0.5, 0.5, -0.5),
    (-0.5, -0.5, -0.5),
    (0.5, -0.5, 0.5),
    (0.5, 0.5, 0.5),
    (-0.5, -0.5, 0.5),
    (-0.5, 0.5, 0.5),
)
SURFACES = (
    (0, 1, 2, 3),
    (3, 2, 7, 6),
    (6, 7, 5, 4),
    (4, 5, 1, 0),
    (1, 5, 7, 2),
    (4, 0, 3, 6),
)
EDGES = (
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 7), (7, 6), (6, 4),
    (0, 4), (1, 5), (2, 7), (3, 6),
)
COLORS = {
    "grass": (0.3, 0.8, 0.2),
    "dirt": (0.6, 0.4, 0.2),
    "stone": (0.5, 0.5, 0.5),
}
TEXTURE_GRASS_TOP = "images/textures/grass_top.png"
TEXTURE_DIRT = "images/textures/dirt.png"
TEXTURE_STONE = "images/textures/stone.png"
TEXTURE_WATER = "images/textures/water.png"
TEX_COORDS = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

CUBE_LIST_DIRT = None
CUBE_LIST_GRASS_SIDES = None
CUBE_LIST_GRASS_TOP = None
CUBE_LIST_STONE = None
TEX_GRASS_TOP = None
TEX_DIRT = None
TEX_STONE = None
TEX_WATER = None

PLACED_BLOCKS = set()
REMOVED_GROUND = set()
REMOVED_STONE = set()
PLACED_BLOCKS_BY_CHUNK = {}
REMOVED_GROUND_BY_CHUNK = {}
REMOVED_STONE_BY_CHUNK = {}
WATER_SOURCES = set()
WATER_BLOCKS = {}
WATER_BLOCKS_BY_CHUNK = {}
ACTIVE_CHUNKS = {}
LAST_PLAYER_CHUNK = None
LAST_PLAYER_Y = None
CHUNKS_NEED_UPDATE = True
WATER_NEEDS_UPDATE = True
LAST_WATER_UPDATE = 0.0
BLOCKS_PLACED = 0
BLOCKS_REMOVED = 0
SESSION_START = time.time()

class ChunkMesh:
    def __init__(self, key):
        self.key = key
        self.display_list = None
        self.dirty = True

# --- プレイヤー/カメラ ---
PLAYER_HEIGHT = 1.8
PLAYER_RADIUS = 0.3
EYE_HEIGHT = 1.6
CROUCH_HEIGHT = 1.2
CROUCH_EYE_HEIGHT = 1.0
MOVE_SPEED = 0.1
CROUCH_SPEED = 0.05
MOUSE_SENSITIVITY = 0.1
DASH_SPEED_MULTIPLIER = 1.8
DASH_DOUBLE_TAP_WINDOW = 0.28
GRAVITY = -0.01
WATER_GRAVITY = -0.003
JUMP_VELOCITY = 0.18
WATER_SWIM_UP_VELOCITY = 0.09
WATER_MOVE_MULTIPLIER = 0.55
SHOW_CROSSHAIR = True
SHOW_TARGET_OUTLINE = True
AUTO_SAVE_ON_EXIT = True

class Camera:
    def __init__(self):
        self.rotation = [0, 0]  # [yaw, pitch]

class Player:
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]  # 足元座標
        self.velocity_y = 0.0
        self.on_ground = False
        self.crouching = False
        self.sprinting = False
        self.last_w_tap_time = -999.0
        self.prev_w_pressed = False

camera = Camera()
player = Player()
