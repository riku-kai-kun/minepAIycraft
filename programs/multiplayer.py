import json
import queue
import socket
import string
import threading
import random
import base64
import os
import time

from . import state as s


def _normalize_room_code(code):
    cleaned = "".join(ch for ch in (code or "").upper() if ch in string.ascii_uppercase + string.digits)
    return cleaned


def parse_room_code(room_code):
    code = _normalize_room_code(room_code)
    if len(code) != s.MULTIPLAYER_ROOM_ID_LEN:
        raise ValueError(f"Room code must be {s.MULTIPLAYER_ROOM_ID_LEN} chars")
    return code


def encode_invite_id(host, port, room_code):
    raw = f"{host}:{int(port)}:{parse_room_code(room_code)}"
    token = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii").rstrip("=")
    return f"MPC-{token}"


def decode_invite_id(invite_id):
    text = (invite_id or "").strip()
    if not text.startswith("MPC-"):
        raise ValueError("Invalid invite ID prefix")
    token = text[4:]
    padded = token + "=" * ((4 - len(token) % 4) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    parts = decoded.split(":")
    if len(parts) != 3:
        raise ValueError("Invalid invite payload")
    host = parts[0].strip()
    if not host:
        raise ValueError("Invite host is empty")
    try:
        port = int(parts[1])
    except ValueError as exc:
        raise ValueError("Invite port is invalid") from exc
    room_code = parse_room_code(parts[2])
    return host, port, room_code


def _send_json_line(sock, payload):
    data = (json.dumps(payload, ensure_ascii=True) + "\n").encode("utf-8")
    sock.sendall(data)


def _recv_json_line(sock_file):
    line = sock_file.readline()
    if not line:
        raise ConnectionError("Connection closed")
    return json.loads(line)


class MultiplayerSession:
    def __init__(self):
        self.mode = "single"
        self.room_id = None
        self.local_player_id = None

        self._sock = None
        self._sock_file = None
        self._running = False

        self._players_lock = threading.Lock()
        self._players = {}
        self._events = queue.Queue()

    def is_multiplayer(self):
        return self.mode in ("host", "client")

    def get_remote_players(self):
        with self._players_lock:
            players = {}
            for player_id, state in self._players.items():
                if player_id == self.local_player_id:
                    continue
                players[player_id] = {
                    "position": list(state.get("position", [0.0, 0.0, 0.0])),
                    "rotation": list(state.get("rotation", [0.0, 0.0])),
                }
            return players

    def poll_events(self):
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except queue.Empty:
                break
        return events

    def _connect_relay(self, relay_host, relay_port):
        sock = socket.create_connection((relay_host, relay_port), timeout=8)
        sock_file = sock.makefile("r", encoding="utf-8", newline="\n")
        self._sock = sock
        self._sock_file = sock_file

    def start_host(self, snapshot, relay_host=None, relay_port=None):
        if self.is_multiplayer():
            raise RuntimeError("Session already started")

        relay_host = relay_host or s.MULTIPLAYER_RELAY_HOST
        relay_port = relay_port or s.MULTIPLAYER_RELAY_PORT
        self._connect_relay(relay_host, relay_port)

        _send_json_line(
            self._sock,
            {
                "type": "hello",
                "mode": "host",
                "version": s.APP_VERSION,
                "snapshot": snapshot,
            },
        )
        response = _recv_json_line(self._sock_file)
        if response.get("type") == "reject":
            self._sock.close()
            raise ValueError(response.get("reason", "Host start rejected"))
        if response.get("type") != "host_ready":
            self._sock.close()
            raise ValueError("Invalid relay response")

        self.mode = "host"
        self.room_id = response.get("room_code")
        self.local_player_id = response.get("player_id", "host")
        self._running = True
        with self._players_lock:
            self._players = {self.local_player_id: {"position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0]}}

        threading.Thread(target=self._recv_loop, daemon=True).start()
        return self.room_id

    def join_room(self, room_code, relay_host=None, relay_port=None):
        if self.is_multiplayer():
            raise RuntimeError("Session already started")

        relay_host = relay_host or s.MULTIPLAYER_RELAY_HOST
        relay_port = relay_port or s.MULTIPLAYER_RELAY_PORT
        code = parse_room_code(room_code)

        self._connect_relay(relay_host, relay_port)
        _send_json_line(
            self._sock,
            {
                "type": "hello",
                "mode": "join",
                "version": s.APP_VERSION,
                "room_code": code,
            },
        )
        response = _recv_json_line(self._sock_file)
        if response.get("type") == "reject":
            self._sock.close()
            raise ValueError(response.get("reason", "Join rejected"))
        if response.get("type") != "join_ready":
            self._sock.close()
            raise ValueError("Invalid relay response")

        self.mode = "client"
        self.room_id = code
        self.local_player_id = response.get("player_id")
        self._running = True
        with self._players_lock:
            self._players = {}

        threading.Thread(target=self._recv_loop, daemon=True).start()
        return response.get("snapshot")

    def send_local_state(self, position, rotation):
        if not self.is_multiplayer() or not self._sock:
            return
        payload = {
            "type": "state",
            "position": [float(position[0]), float(position[1]), float(position[2])],
            "rotation": [float(rotation[0]), float(rotation[1])],
        }
        try:
            _send_json_line(self._sock, payload)
        except Exception as exc:
            self._events.put({"type": "error", "message": f"Network send failed: {exc}"})

    def send_block_action(self, action, pos):
        if not self.is_multiplayer() or not self._sock:
            return
        payload = {
            "type": "block",
            "action": action,
            "pos": [int(pos[0]), int(pos[1]), int(pos[2])],
        }
        try:
            _send_json_line(self._sock, payload)
        except Exception as exc:
            self._events.put({"type": "error", "message": f"Block sync failed: {exc}"})

    def shutdown(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self._sock_file = None
        self.mode = "single"
        self.room_id = None
        self.local_player_id = None

    def _recv_loop(self):
        try:
            while self._running and self._sock_file:
                message = _recv_json_line(self._sock_file)
                msg_type = message.get("type")
                if msg_type == "state":
                    player_id = message.get("player_id")
                    if not player_id:
                        continue
                    with self._players_lock:
                        self._players[player_id] = {
                            "position": message.get("position", [0.0, 0.0, 0.0]),
                            "rotation": message.get("rotation", [0.0, 0.0]),
                        }
                elif msg_type == "block":
                    self._events.put(message)
                elif msg_type == "server_notice":
                    self._events.put({"type": "info", "message": message.get("message", "Server notice")})
        except Exception:
            self._events.put({"type": "error", "message": "Disconnected from relay server"})


class RelayServer:
    def __init__(
        self,
        host="0.0.0.0",
        port=39000,
        persistent_room_code=None,
        snapshot_file=None,
    ):
        self.host = host
        self.port = port
        self.snapshot_file = snapshot_file
        self._server_sock = None
        self._rooms_lock = threading.Lock()
        self._rooms = {}
        self._last_snapshot_save = 0.0

        if persistent_room_code:
            code = parse_room_code(persistent_room_code)
            snapshot = self._load_snapshot()
            self._rooms[code] = {
                "code": code,
                "version": s.APP_VERSION,
                "snapshot": snapshot,
                "host_id": "server",
                "next_no": 0,
                "clients": {},
                "persistent": True,
            }

    def serve_forever(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(64)
        self._server_sock = server
        print(f"Relay server listening on {self.host}:{self.port}")
        while True:
            conn, _ = server.accept()
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _make_room_code(self):
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choice(alphabet) for _ in range(s.MULTIPLAYER_ROOM_ID_LEN))
            with self._rooms_lock:
                if code not in self._rooms:
                    return code

    def _handle_client(self, conn):
        conn_file = conn.makefile("r", encoding="utf-8", newline="\n")
        room_code = None
        player_id = None
        is_host = False
        try:
            hello = _recv_json_line(conn_file)
            if hello.get("type") != "hello":
                _send_json_line(conn, {"type": "reject", "reason": "Invalid hello"})
                conn.close()
                return

            if hello.get("version") != s.APP_VERSION:
                _send_json_line(
                    conn,
                    {
                        "type": "reject",
                        "reason": f"Version mismatch. Required: {s.APP_VERSION}",
                    },
                )
                conn.close()
                return

            mode = hello.get("mode")
            if mode == "host":
                room_code = self._make_room_code()
                player_id = "host"
                is_host = True
                room = {
                    "code": room_code,
                    "version": s.APP_VERSION,
                    "snapshot": hello.get("snapshot") or {},
                    "host_id": player_id,
                    "next_no": 1,
                    "clients": {player_id: conn},
                }
                with self._rooms_lock:
                    self._rooms[room_code] = room
                _send_json_line(conn, {"type": "host_ready", "room_code": room_code, "player_id": player_id})
            elif mode == "join":
                room_code = parse_room_code(hello.get("room_code"))
                with self._rooms_lock:
                    room = self._rooms.get(room_code)
                    if not room:
                        _send_json_line(conn, {"type": "reject", "reason": "Room not found"})
                        conn.close()
                        return
                    if room["version"] != s.APP_VERSION:
                        _send_json_line(conn, {"type": "reject", "reason": "Version mismatch"})
                        conn.close()
                        return
                    room["next_no"] += 1
                    player_id = f"p{room['next_no']}"
                    room["clients"][player_id] = conn
                _send_json_line(
                    conn,
                    {
                        "type": "join_ready",
                        "room_code": room_code,
                        "player_id": player_id,
                        "snapshot": room.get("snapshot") or {},
                    },
                )
                self._broadcast(room_code, {"type": "server_notice", "message": f"Player joined: {player_id}"}, exclude={player_id})
            else:
                _send_json_line(conn, {"type": "reject", "reason": "Unknown mode"})
                conn.close()
                return

            while True:
                message = _recv_json_line(conn_file)
                msg_type = message.get("type")
                if msg_type == "state":
                    payload = {
                        "type": "state",
                        "player_id": player_id,
                        "position": message.get("position", [0.0, 0.0, 0.0]),
                        "rotation": message.get("rotation", [0.0, 0.0]),
                    }
                    self._broadcast(room_code, payload, exclude={player_id})
                elif msg_type == "block":
                    action = message.get("action")
                    pos = message.get("pos")
                    if action in ("place", "remove") and isinstance(pos, list) and len(pos) == 3:
                        payload = {
                            "type": "block",
                            "player_id": player_id,
                            "action": action,
                            "pos": [int(pos[0]), int(pos[1]), int(pos[2])],
                        }
                        self._apply_block_to_snapshot(room_code, action, payload["pos"])
                        self._broadcast(room_code, payload, exclude=set())
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
            if not room_code or not player_id:
                return
            with self._rooms_lock:
                room = self._rooms.get(room_code)
                if not room:
                    return
                room["clients"].pop(player_id, None)
                if is_host:
                    # Host left: close room.
                    clients = list(room["clients"].values())
                    self._rooms.pop(room_code, None)
                    for client in clients:
                        try:
                            _send_json_line(client, {"type": "server_notice", "message": "Host left. Room closed."})
                            client.close()
                        except Exception:
                            pass
                    return
                if not room["clients"] and not room.get("persistent"):
                    self._rooms.pop(room_code, None)
            self._broadcast(room_code, {"type": "server_notice", "message": f"Player left: {player_id}"}, exclude={player_id})

    def _broadcast(self, room_code, payload, exclude=None):
        exclude = exclude or set()
        dead = []
        with self._rooms_lock:
            room = self._rooms.get(room_code)
            if not room:
                return
            items = list(room["clients"].items())
        for pid, conn in items:
            if pid in exclude:
                continue
            try:
                _send_json_line(conn, payload)
            except Exception:
                dead.append(pid)
        if dead:
            with self._rooms_lock:
                room = self._rooms.get(room_code)
                if not room:
                    return
                for pid in dead:
                    room["clients"].pop(pid, None)

    def _apply_block_to_snapshot(self, room_code, action, pos):
        with self._rooms_lock:
            room = self._rooms.get(room_code)
            if not room:
                return
            snapshot = room.get("snapshot")
            if not isinstance(snapshot, dict):
                return
            world = snapshot.setdefault("world", {})
            placed = world.setdefault("placed_blocks", [])
            removed_ground = world.setdefault("removed_ground", [])
            removed_stone = world.setdefault("removed_stone", [])
            water_sources = world.setdefault("water_sources", [])

            tpos = [int(pos[0]), int(pos[1]), int(pos[2])]

            def remove_from(lst):
                try:
                    lst.remove(tpos)
                except ValueError:
                    pass

            if action == "place":
                remove_from(removed_ground)
                remove_from(removed_stone)
                remove_from(water_sources)
                if tpos not in placed:
                    placed.append(tpos)
            elif action == "remove":
                remove_from(placed)
                if tpos[1] >= -1:
                    if tpos not in removed_ground:
                        removed_ground.append(tpos)
                elif tpos[1] <= -2:
                    if tpos not in removed_stone:
                        removed_stone.append(tpos)
        self._save_snapshot_if_needed()

    def _load_snapshot(self):
        if not self.snapshot_file or not os.path.isfile(self.snapshot_file):
            return {}
        try:
            with open(self.snapshot_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_snapshot_if_needed(self, force=False):
        if not self.snapshot_file:
            return
        now = time.time()
        if not force and (now - self._last_snapshot_save) < 1.0:
            return
        self._last_snapshot_save = now
        with self._rooms_lock:
            if not self._rooms:
                return
            room = next(iter(self._rooms.values()))
            snapshot = room.get("snapshot") or {}
        try:
            directory = os.path.dirname(self.snapshot_file)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(self.snapshot_file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=True, indent=2)
        except Exception:
            pass


def run_relay_server(host="0.0.0.0", port=39000):
    RelayServer(host=host, port=port).serve_forever()


def run_dedicated_world_server(
    host="0.0.0.0",
    port=39000,
    room_code=None,
    snapshot_file=None,
):
    server = RelayServer(
        host=host,
        port=port,
        persistent_room_code=room_code or "".join(
            random.choice(string.ascii_uppercase + string.digits)
            for _ in range(s.MULTIPLAYER_ROOM_ID_LEN)
        ),
        snapshot_file=snapshot_file,
    )
    code = next(iter(server._rooms.keys()))
    print(f"[Dedicated] room_code={code}")
    server.serve_forever()
