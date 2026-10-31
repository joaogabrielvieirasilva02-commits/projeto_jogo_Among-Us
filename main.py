# -*- coding: utf-8 -*-
"""
AMONG US PANDA3D 4.0 - ESTACAO ORBITAL
Versao basica single-player, 100% 3D, feita so com codigo (sem modelos externos).
"""
from panda3d.core import loadPrcFileData
loadPrcFileData("", """
window-title Among Us 3D - Estacao Orbital 4.0
win-size 1280 720
framebuffer-multisample 1
multisamples 4
sync-video 1
""")

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import (AmbientLight, DirectionalLight, Vec4, Vec3, Geom, GeomNode,
    GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, TextNode, Fog,
    ClockObject, TransparencyAttrib, CardMaker, AntialiasAttrib, ButtonRegistry)
import math, random

# ----------------------------------------------------------------- AJUSTES
USE_SHADOWS = True      # coloque False se o jogo ficar pesado no seu PC
NUM_IMPOSTORS = 3
NUM_BOTS = 14           # 14 bots + voce = 15 personagens
KILL_COOLDOWN = 70      # segundos entre as mortes de cada impostor
FIRST_KILL_DELAY = 28
TASK_GOAL = 40.0        # barra de tarefas da equipe
BOT_TASK_UNITS = 0.15   # quanto cada bot tripulante contribui por tarefa
WALK_SPEED = 7.0
SPRINT_SPEED = 10.5

# ----------------------------------------------------------------- MAPA
COLS = [-36, -12, 12, 36]
ROWS = [24, 0, -24]
ROOM_SIZE = 24
BOUND_X, BOUND_Y = 48, 36
DOOR_HALF = 2.5          # metade da largura da passagem
WALL_T = 0.3             # metade da espessura da parede

ROOMS = [  # nome, coluna, linha, cor do piso
    ("PONTE", 0, 0, (.10, .24, .34, 1)), ("REFEITÓRIO", 1, 0, (.30, .22, .16, 1)),
    ("LABORATÓRIO", 2, 0, (.12, .26, .30, 1)), ("COMUNICAÇÕES", 3, 0, (.17, .20, .34, 1)),
    ("ELÉTRICA", 0, 1, (.28, .26, .10, 1)), ("ADMINISTRAÇÃO", 1, 1, (.22, .21, .34, 1)),
    ("REATOR", 2, 1, (.30, .15, .18, 1)), ("NAVEGAÇÃO", 3, 1, (.10, .22, .28, 1)),
    ("ENFERMARIA", 0, 2, (.12, .29, .30, 1)), ("ARMAZÉM", 1, 2, (.24, .20, .15, 1)),
    ("MOTORES", 2, 2, (.26, .18, .12, 1)), ("OXIGÊNIO", 3, 2, (.10, .28, .20, 1)),
]
# passagens: (linha, coluna). H = entre (l,c) e (l,c+1). V = entre (l,c) e (l+1,c)
H_DOORS = {(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)}
V_DOORS = {(0, 0), (0, 1), (0, 3), (1, 1), (1, 2), (1, 3)}
# temas dos 4 cantos de cada sala
THEMES = {
    "PONTE": ["console", "console", "console", "console"],
    "REFEITÓRIO": ["table", "table", "table", "table"],
    "LABORATÓRIO": ["tank", "table", "tank", "console"],
    "COMUNICAÇÕES": ["console", "antenna", "console", "antenna"],
    "ELÉTRICA": ["console", "crate", "console", "crate"],
    "ADMINISTRAÇÃO": ["table", "console", "table", "console"],
    "REATOR": ["reactor", "console", "console", "reactor"],
    "NAVEGAÇÃO": ["console", "console", "tank", "console"],
    "ENFERMARIA": ["bed", "bed", "console", "bed"],
    "ARMAZÉM": ["crate", "crate", "crate", "crate"],
    "MOTORES": ["reactor", "crate", "crate", "reactor"],
    "OXIGÊNIO": ["tank", "tank", "console", "tank"],
}
# 16 tarefas: sala, canto (dx,dy), nome, segundos segurando E
TASKS = [
    (0, (-9.8, 5.5), "Alinhar navegação", 2.5), (0, (9.8, -5.5), "Traçar rota", 2.0),
    (1, (-9.8, 5.5), "Preparar refeição", 2.5),
    (2, (-9.8, 5.5), "Analisar amostras", 3.0), (2, (9.8, -5.5), "Calibrar microscópio", 2.0),
    (3, (-9.8, 5.5), "Reiniciar antena", 2.5),
    (4, (-9.8, 5.5), "Consertar fiação", 3.0), (4, (9.8, -5.5), "Desviar energia", 2.0),
    (5, (-9.8, 5.5), "Enviar relatório", 2.0),
    (6, (-9.8, 5.5), "Calibrar reator", 3.0), (6, (9.8, -5.5), "Resfriar núcleo", 2.5),
    (7, (-9.8, 5.5), "Atualizar mapa estelar", 2.5),
    (8, (-9.8, 5.5), "Escanear paciente", 3.0),
    (9, (-9.8, 5.5), "Organizar caixas", 2.0),
    (10, (-9.8, 5.5), "Abastecer motores", 3.0),
    (11, (-9.8, 5.5), "Verificar oxigênio", 2.5),
]

# ----------------------------------------------------------------- PERSONALIZACAO
PALETTE = [("Ciano", (.05, .82, .92)), ("Azul", (.20, .35, .95)), ("Verde", (.12, .68, .30)),
    ("Lima", (.60, .85, .20)), ("Amarelo", (.95, .82, .18)), ("Laranja", (.95, .50, .10)),
    ("Rosa", (.96, .45, .68)), ("Roxo", (.60, .30, .88)), ("Branco", (.90, .92, .95)),
    ("Preto", (.14, .15, .18)), ("Marrom", (.48, .32, .20)), ("Turquesa", (.10, .60, .55)),
    ("Vermelho", (.88, .10, .14)), ("Magenta", (.80, .20, .55)), ("Areia", (.75, .65, .45)),
    ("Coral", (.97, .42, .35)), ("Cinza", (.50, .55, .60)), ("Bordô", (.50, .10, .20))]
HATS = ["Nenhum", "Boné", "Coroa", "Antena", "Chef", "Viking"]
VISORS = [("Azul", (.22, .76, .94, .92)), ("Verde", (.30, .95, .50, .92)),
          ("Dourado", (.98, .80, .25, .92)), ("Rosa", (1.0, .45, .75, .92)),
          ("Preto", (.05, .06, .09, .95))]


# ----------------------------------------------------------------- GEOMETRIA
def box(parent, name, pos, size, color):
    sx, sy, sz = [v / 2 for v in size]
    verts = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
             (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    faces = [([0, 3, 2, 1], (0, 0, -1)), ([4, 5, 6, 7], (0, 0, 1)), ([0, 1, 5, 4], (0, -1, 0)),
             ([3, 7, 6, 2], (0, 1, 0)), ([0, 4, 7, 3], (-1, 0, 0)), ([1, 2, 6, 5], (1, 0, 0))]
    vd = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vw, nw, cw = [GeomVertexWriter(vd, k) for k in ("vertex", "normal", "color")]
    prim = GeomTriangles(Geom.UHStatic)
    idx = 0
    for ids, n in faces:
        for i in ids:
            vw.addData3(*verts[i]); nw.addData3(*n); cw.addData4(*color)
        prim.addVertices(idx, idx + 1, idx + 2); prim.addVertices(idx, idx + 2, idx + 3)
        idx += 4
    g = Geom(vd); g.addPrimitive(prim)
    node = GeomNode(name); node.addGeom(g)
    np = parent.attachNewNode(node); np.setPos(*pos); np.setTwoSided(True)
    return np


def sphere(parent, name, pos, r, color, rings=10, seg=16):
    vd = GeomVertexData(name, GeomVertexFormat.getV3n3c4(), Geom.UHStatic)
    vw, nw, cw = [GeomVertexWriter(vd, k) for k in ("vertex", "normal", "color")]
    for a in range(rings + 1):
        ph = math.pi * a / rings
        for b in range(seg + 1):
            th = 2 * math.pi * b / seg
            n = (math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph))
            vw.addData3(n[0] * r, n[1] * r, n[2] * r); nw.addData3(*n); cw.addData4(*color)
    tr = GeomTriangles(Geom.UHStatic)
    row = seg + 1
    for a in range(rings):
        for b in range(seg):
            i = a * row + b
            tr.addVertices(i, i + row, i + 1); tr.addVertices(i + 1, i + row, i + row + 1)
    g = Geom(vd); g.addPrimitive(tr)
    gn = GeomNode(name); gn.addGeom(g)
    np = parent.attachNewNode(gn); np.setPos(*pos); np.setTwoSided(True)
    return np


# ----------------------------------------------------------------- FUNCOES DE MAPA
def room_center(i):
    _, c, r, _ = ROOMS[i]
    return COLS[c], ROWS[r]


def room_of(x, y):
    c = min(3, max(0, int((x + BOUND_X) // ROOM_SIZE)))
    r = min(2, max(0, int((BOUND_Y - y) // ROOM_SIZE)))
    return r * 4 + c


def scale_color(col, k, a=1):
    return (col[0] * k, col[1] * k, col[2] * k, a)


class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(.01, .015, .045, 1)
        self.rng = random.Random()
        self.elapsed = 0.0
        self.state = "menu"
        self.opt = {"color": 0, "hat": 0, "visor": 0}
        self.menu_row = 0
        self.walls = []
        self.people = []
        self.tasks = []
        self.door_pos = {}
        self.door_panels = []
        self.adj = {i: [] for i in range(12)}
        self.zoom = 1.0
        self.cam_focus = Vec3(0, -90, 1)
        self.cam_pos = Vec3(0, -97, 2.4)
        self.pvel = Vec3(0, 0, 0)
        self.stamina = 100.0
        self.exhausted = False
        self.task_units = 0.0
        self.msg_end = 0
        self.player = None
        self.vote_cands = []
        self.vote_sel = 0
        self.btn = {n: ButtonRegistry.ptr().findButton(n) for n in
                    ("w", "a", "s", "d", "e", "arrow_up", "arrow_down", "arrow_left",
                     "arrow_right", "shift")}

        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.setup_lights()
        self.people_root = self.render.attachNewNode("people")
        self.build_graph()
        self.build_station()
        self.build_doors()
        self.build_space()
        self.build_showroom()
        self.build_ui()

        self.accept("arrow_up", self.nav_key, [0, -1]); self.accept("arrow_down", self.nav_key, [0, 1])
        self.accept("arrow_left", self.nav_key, [-1, 0]); self.accept("arrow_right", self.nav_key, [1, 0])
        self.accept("w", self.nav_key, [0, -1]); self.accept("s", self.nav_key, [0, 1])
        self.accept("a", self.nav_key, [-1, 0]); self.accept("d", self.nav_key, [1, 0])
        self.accept("enter", self.on_enter); self.accept("escape", self.on_escape)
        self.accept("r", self.on_report); self.accept("m", self.on_map)
        self.accept("wheel_up", self.on_zoom, [-.1]); self.accept("wheel_down", self.on_zoom, [.1])
        self.go_menu()
        self.taskMgr.add(self.update, "update")

    # ------------------------------------------------------------ cenario
    def setup_lights(self):
        a = AmbientLight("ambient"); a.setColor(Vec4(.46, .52, .66, 1))
        self.render.setLight(self.render.attachNewNode(a))
        d = DirectionalLight("sun"); d.setColor(Vec4(.95, .92, .84, 1))
        self.shadows_on = False
        if USE_SHADOWS:
            try:
                d.setShadowCaster(True, 2048, 2048)
                d.getLens().setFilmSize(80, 80)
                d.getLens().setNearFar(5, 160)
                self.shadows_on = True
            except Exception:
                self.shadows_on = False
        self.sun = self.render.attachNewNode(d)
        self.sun.setPos(22, -22, 48); self.sun.lookAt(0, 0, 0)
        self.render.setLight(self.sun)
        if self.shadows_on:
            self.render.setShaderAuto()
        f = Fog("nebula"); f.setColor(.01, .015, .045); f.setExpDensity(.0028)
        self.render.setFog(f)

    def build_graph(self):
        """Grafo de salas usado pela navegacao dos bots."""
        for (r, c) in H_DOORS:
            a, b = r * 4 + c, r * 4 + c + 1
            self.adj[a].append(b); self.adj[b].append(a)
        for (r, c) in V_DOORS:
            a, b = r * 4 + c, (r + 1) * 4 + c
            self.adj[a].append(b); self.adj[b].append(a)
        self.next_room = {}
        for dst in range(12):           # BFS a partir de cada destino
            prev = {dst: None}; queue = [dst]
            while queue:
                cur = queue.pop(0)
                for n in self.adj[cur]:
                    if n not in prev:
                        prev[n] = cur; queue.append(n)
            for src in range(12):
                if src != dst and src in prev:
                    self.next_room[(src, dst)] = prev[src]

    def add_wall(self, x1, x2, y1, y2):
        h = 2.8
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        box(self.env, "wall", (cx, cy, h / 2), (x2 - x1, y2 - y1, h), (.16, .23, .35, 1))
        box(self.env, "trim", (cx, cy, h + .05), (x2 - x1 + .05, y2 - y1 + .05, .12), (.10, .70, .95, 1))
        box(self.env, "base", (cx, cy, .12), (x2 - x1 + .08, y2 - y1 + .08, .24), (.08, .12, .2, 1))
        self.walls.append((x1, x2, y1, y2))

    def door_frame(self, x, y, axis, a, b):
        key = (a, b)
        self.door_pos[key] = (x, y, axis); self.door_pos[(b, a)] = (x, y, axis)
        gl = (.10, .75, 1.0, 1)
        fr = (.30, .42, .56, 1)
        if axis == "v":     # parede vertical, atravessa-se no eixo X
            for s in (-1, 1):
                box(self.env, "post", (x, y + s * DOOR_HALF, 1.5), (.9, .5, 3.0), fr)
            box(self.env, "lintel", (x, y, 2.95), (.7, DOOR_HALF * 2 + .5, .3), gl)
            box(self.env, "floor-glow", (x, y, .1), (1.6, DOOR_HALF * 2, .05), (.05, .35, .5, 1))
        else:
            for s in (-1, 1):
                box(self.env, "post", (x + s * DOOR_HALF, y, 1.5), (.5, .9, 3.0), fr)
            box(self.env, "lintel", (x, y, 2.95), (DOOR_HALF * 2 + .5, .7, .3), gl)
            box(self.env, "floor-glow", (x, y, .1), (DOOR_HALF * 2, 1.6, .05), (.05, .35, .5, 1))

    def build_station(self):
        self.env = self.render.attachNewNode("env")
        env = self.env
        box(env, "deck", (0, 0, -.45), (104, 80, .8), (.05, .08, .13, 1))
        for i, (name, c, r, col) in enumerate(ROOMS):
            cx, cy = COLS[c], ROWS[r]
            box(env, "floor", (cx, cy, .02), (23.6, 23.6, .1), col)
            box(env, "floor-in", (cx, cy, .08), (15, 15, .04), scale_color(col, .78))
            for s in (-1, 1):
                box(env, "neon", (cx + s * 7.6, cy, .11), (.12, 15.2, .03), (.1, .7, .95, 1))
                box(env, "neon", (cx, cy + s * 7.6, .11), (15.2, .12, .03), (.1, .7, .95, 1))
            tn = TextNode("label"); tn.setText(name); tn.setTextColor(.6, .9, 1, 1)
            tn.setAlign(TextNode.ACenter)
            tnp = self.render.attachNewNode(tn)
            tnp.setPos(cx, cy - 10.4, .14); tnp.setP(-90); tnp.setScale(1.5); tnp.setLightOff()
            themes = THEMES[name]
            for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
                self.place(themes[k], cx + sx * 7, cy + sy * 7, sx, col)
        # paredes externas
        o = BOUND_X; p = BOUND_Y; T = WALL_T
        self.add_wall(-o - T, o + T, p - T, p + T); self.add_wall(-o - T, o + T, -p - T, -p + T)
        self.add_wall(-o - T, -o + T, -p, p); self.add_wall(o - T, o + T, -p, p)
        # paredes internas verticais (entre colunas)
        for r in range(3):
            for c in range(3):
                x = COLS[c] + 12; ya = ROWS[r] - 12; yb = ROWS[r] + 12; mid = ROWS[r]
                if (r, c) in H_DOORS:
                    self.add_wall(x - T, x + T, ya, mid - DOOR_HALF)
                    self.add_wall(x - T, x + T, mid + DOOR_HALF, yb)
                    self.door_frame(x, mid, "v", r * 4 + c, r * 4 + c + 1)
                else:
                    self.add_wall(x - T, x + T, ya, yb)
        # paredes internas horizontais (entre linhas)
        for r in range(2):
            for c in range(4):
                y = ROWS[r] - 12; xa = COLS[c] - 12; xb = COLS[c] + 12; mid = COLS[c]
                if (r, c) in V_DOORS:
                    self.add_wall(xa, mid - DOOR_HALF, y - T, y + T)
                    self.add_wall(mid + DOOR_HALF, xb, y - T, y + T)
                    self.door_frame(mid, y, "h", r * 4 + c, (r + 1) * 4 + c)
                else:
                    self.add_wall(xa, xb, y - T, y + T)
        # terminais de tarefas
        self.task_marker_root = self.render.attachNewNode("markers")
        for (ri, (dx, dy), name, hold) in TASKS:
            cx, cy = room_center(ri)
            x, y = cx + dx, cy + dy
            box(env, "pedestal", (x, y, .55), (1.1, .9, 1.1), (.11, .19, .27, 1))
            box(env, "task-screen", (x, y - .47, .98), (.78, .05, .45), (.08, .85, .62, 1))
            box(env, "task-top", (x, y, 1.14), (1.2, 1.0, .08), (.2, .6, .5, 1))
            mk = box(self.task_marker_root, "marker", (x, y, 3.6), (.3, .3, 5.5), (1, .9, .2, .35))
            mk.setTransparency(TransparencyAttrib.MAlpha); mk.setLightOff()
            self.tasks.append({"name": name, "pos": Vec3(x, y, 0), "done": False,
                               "hold": hold, "prog": 0.0, "marker": mk, "room": ri})
        env.flattenStrong()

    def place(self, kind, x, y, side, col):
        """Mobilia dos cantos (com colisao)."""
        env = self.env
        dark = (.10, .17, .25, 1); metal = (.30, .38, .48, 1)
        glow = (.05, .75, .92, 1)
        if kind == "console":
            box(env, "console", (x, y, .7), (2.2, 1.3, 1.4), dark)
            box(env, "screen", (x, y - .68, 1.0), (1.6, .06, .7), glow)
            box(env, "keys", (x, y - .45, 1.42), (1.8, .5, .08), metal)
            sz = (2.2, 1.3)
        elif kind == "table":
            box(env, "table-top", (x, y, .95), (3.0, 1.8, .14), (.55, .45, .32, 1))
            for dx in (-1.2, 1.2):
                for dy in (-.7, .7):
                    box(env, "leg", (x + dx, y + dy, .45), (.14, .14, .9), metal)
            sz = (3.0, 1.8)
        elif kind == "tank":
            box(env, "tank", (x, y, 1.3), (1.7, 1.7, 2.6), (.1, .45, .65, 1))
            box(env, "tank-top", (x, y, 2.65), (1.9, 1.9, .2), metal)
            box(env, "tank-base", (x, y, .1), (1.9, 1.9, .2), metal)
            sz = (1.9, 1.9)
        elif kind == "crate":
            box(env, "crate", (x, y, .8), (2.0, 2.0, 1.6), (.42, .32, .20, 1))
            box(env, "crate-band", (x, y, .8), (2.05, 2.05, .2), (.9, .7, .1, 1))
            sz = (2.0, 2.0)
        elif kind == "bed":
            box(env, "bed", (x, y, .35), (1.6, 3.0, .7), (.85, .9, .95, 1))
            box(env, "pillow", (x, y + 1.0, .8), (1.2, .7, .2), (.4, .7, .9, 1))
            sz = (1.6, 3.0)
        elif kind == "antenna":
            box(env, "ant-base", (x, y, .5), (1.8, 1.8, 1.0), dark)
            box(env, "ant-mast", (x, y, 2.2), (.25, .25, 2.4), metal)
            box(env, "ant-dish", (x, y, 3.0), (1.6, .2, 1.0), (.8, .85, .9, 1))
            sz = (1.8, 1.8)
        else:  # reactor / motor
            box(env, "core-base", (x, y, .3), (2.4, 2.4, .6), metal)
            box(env, "core", (x, y, 1.6), (1.5, 1.5, 2.6), (.95, .35, .2, 1))
            box(env, "core-ring", (x, y, 1.6), (2.0, 2.0, .25), (1, .8, .3, 1))
            sz = (2.4, 2.4)
        self.walls.append((x - sz[0] / 2, x + sz[0] / 2, y - sz[1] / 2, y + sz[1] / 2))

    def build_doors(self):
        """Portas deslizantes que abrem quando alguem chega perto."""
        seen = set()
        for (a, b), (x, y, axis) in self.door_pos.items():
            if (min(a, b), max(a, b)) in seen:
                continue
            seen.add((min(a, b), max(a, b)))
            panels = []
            for s in (-1, 1):
                if axis == "v":
                    np = box(self.render, "door", (x, y + s * 1.25, 1.2), (.22, 2.5, 2.4), (.18, .42, .58, 1))
                    closed = Vec3(x, y + s * 1.25, 1.2); opened = Vec3(x, y + s * 3.9, 1.2)
                else:
                    np = box(self.render, "door", (x + s * 1.25, y, 1.2), (2.5, .22, 2.4), (.18, .42, .58, 1))
                    closed = Vec3(x + s * 1.25, y, 1.2); opened = Vec3(x + s * 3.9, y, 1.2)
                panels.append((np, closed, opened))
            self.door_panels.append({"center": Vec3(x, y, 0), "panels": panels, "amt": 0.0})

    def build_space(self):
        rng = random.Random(7)
        stars = self.render.attachNewNode("stars")
        for _ in range(260):
            x = rng.uniform(-170, 170); y = rng.uniform(-170, 170); z = rng.uniform(-70, -22)
            s = rng.uniform(.25, .7); c = rng.choice([(1, 1, 1, 1), (.7, .85, 1, 1), (1, .9, .7, 1)])
            box(stars, "star", (x, y, z), (s, s, s), c)
        stars.flattenStrong(); stars.setLightOff(); stars.setFogOff()
        planet = sphere(self.render, "planet", (-110, 70, -60), 34, (.15, .35, .75, 1), 14, 24)
        planet.setFogOff()
        moon = sphere(self.render, "moon", (95, -80, -45), 14, (.65, .62, .58, 1), 10, 18)
        moon.setFogOff()

    def build_showroom(self):
        self.show_pos = Vec3(0, -90, 0)
        sr = self.render.attachNewNode("showroom")
        box(sr, "platform", (0, -90, -.1), (9, 9, .4), (.12, .18, .28, 1))
        box(sr, "ring", (0, -90, .12), (7.4, 7.4, .06), (.1, .7, .95, 1))
        box(sr, "ring2", (0, -90, .16), (6.6, 6.6, .06), (.06, .1, .18, 1))
        box(sr, "backdrop", (0, -84.5, 3), (14, .4, 7), (.06, .10, .17, 1))
        for x in (-5, 5):
            box(sr, "pillar", (x, -86, 2), (.5, .5, 4), (.2, .35, .5, 1))
        self.preview = None
        self.rebuild_preview()

    def rebuild_preview(self):
        if self.preview:
            self.preview["root"].removeNode()
        col = PALETTE[self.opt["color"]][1]
        self.preview = self.build_crew(self.render, col, self.opt["hat"], VISORS[self.opt["visor"]][1], "preview")
        self.preview["root"].setPos(0, -90, .2); self.preview["root"].setScale(1.8)
        if self.state != "menu":
            self.preview["root"].hide()

    # ------------------------------------------------------------ personagens
    def build_crew(self, parent, color, hat=0, visor=(.22, .76, .94, .92), name="crew"):
        c = (color[0], color[1], color[2], 1)
        dk = scale_color(c, .68)
        root = parent.attachNewNode(name)
        anim = root.attachNewNode("anim")
        box(anim, "body", (0, 0, .95), (.92, .88, 1.45), c)
        sphere(anim, "helmet", (0, 0, 1.55), .47, c)
        box(anim, "pack", (0, .58, .95), (.70, .30, .90), dk)
        v = box(anim, "visor", (.14, -.42, 1.50), (.62, .10, .40), visor)
        v.setTransparency(TransparencyAttrib.MAlpha)
        sh = box(anim, "shine", (.30, -.48, 1.60), (.18, .03, .09), (1, 1, 1, .9))
        sh.setTransparency(TransparencyAttrib.MAlpha)
        if hat == 1:      # bone
            box(anim, "cap", (0, -.02, 2.0), (.92, .92, .22), (.85, .15, .15, 1))
            box(anim, "brim", (0, -.52, 1.95), (.8, .45, .06), (.65, .1, .1, 1))
        elif hat == 2:    # coroa
            gold = (.98, .80, .15, 1)
            box(anim, "crown", (0, 0, 2.06), (.84, .84, .2), gold)
            for sx in (-.3, .3):
                for sy in (-.3, .3):
                    box(anim, "spike", (sx, sy, 2.28), (.14, .14, .24), gold)
        elif hat == 3:    # antena
            box(anim, "stick", (0, 0, 2.28), (.06, .06, .52), (.7, .7, .75, 1))
            sphere(anim, "ball", (0, 0, 2.58), .13, (.95, .2, .2, 1), 6, 8)
        elif hat == 4:    # chef
            box(anim, "chef-band", (0, 0, 2.08), (.84, .84, .2), (.95, .95, .95, 1))
            sphere(anim, "chef-top", (0, 0, 2.42), .5, (.97, .97, .97, 1), 8, 12)
        elif hat == 5:    # viking
            box(anim, "helm", (0, 0, 2.06), (.94, .94, .2), (.55, .58, .62, 1))
            for s in (-1, 1):
                box(anim, "horn", (s * .52, 0, 2.2), (.14, .14, .36), (.95, .92, .8, 1))
                box(anim, "horn-tip", (s * .60, 0, 2.46), (.12, .12, .22), (.95, .92, .8, 1))
        anim.flattenStrong()
        lf = box(root, "foot-l", (-.25, 0, .17), (.34, .50, .34), dk)
        rf = box(root, "foot-r", (.25, 0, .17), (.34, .50, .34), dk)
        if not self.shadows_on:
            blob = box(root, "blob", (0, 0, .03), (1.3, 1.3, .02), (0, 0, 0, .4))
            blob.setTransparency(TransparencyAttrib.MAlpha); blob.setLightOff()
        return {"root": root, "anim": anim, "lf": lf, "rf": rf}

    def make_char(self, name, color, pos, hat, visor, impostor=False, player=False):
        parts = self.build_crew(self.people_root, color, hat, visor, name)
        root = parts["root"]; root.setPos(pos[0], pos[1], 0)
        tn = TextNode("tag"); tn.setText("VOCÊ" if player else name)
        tn.setTextColor(.3, 1, 1, 1) if player else tn.setTextColor(1, 1, 1, .9)
        tn.setAlign(TextNode.ACenter)
        tag = root.attachNewNode(tn)
        tag.setZ(3.0); tag.setScale(.5); tag.setBillboardPointEye(); tag.setLightOff()
        d = {"name": name, "node": root, "parts": parts, "tag": tag, "impostor": impostor,
             "player": player, "alive": True, "body": False, "dest": None, "wait": self.rng.uniform(.5, 3),
             "cool": FIRST_KILL_DELAY + self.rng.uniform(0, 12), "phase": self.rng.uniform(0, 6),
             "moving": False, "h": 0.0, "ht": 0.0, "room": ""}
        self.people.append(d)
        return d

    def ring_positions(self, n):
        cx, cy = room_center(1)
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            pts.append((cx + 5.2 * math.cos(a), cy + 5.2 * math.sin(a)))
        self.rng.shuffle(pts)
        return pts

    def face(self, c, tx, ty):
        p = c["node"].getPos()
        h = math.degrees(math.atan2(tx - p.x, -(ty - p.y)))
        c["h"] = c["ht"] = h; c["node"].setH(h)

    def clear_people(self):
        for c in self.people:
            c["node"].removeNode()
        self.people = []

    def new_game(self):
        self.clear_people()
        for t in self.tasks:
            t["done"] = False; t["prog"] = 0.0; t["marker"].show()
        self.task_units = 0.0; self.stamina = 100.0; self.exhausted = False
        self.pvel = Vec3(0, 0, 0)
        ring = self.ring_positions(NUM_BOTS + 1)
        pal = [p for i, p in enumerate(PALETTE) if i != self.opt["color"]]
        self.rng.shuffle(pal)
        self.player = self.make_char("Você", PALETTE[self.opt["color"]][1], ring[0], self.opt["hat"],
                                     VISORS[self.opt["visor"]][1], player=True)
        imps = set(self.rng.sample(range(NUM_BOTS), NUM_IMPOSTORS))
        for i in range(NUM_BOTS):
            name, col = pal[i]
            hat = self.rng.choice([0, 0, 1, 2, 3, 4, 5])
            vis = VISORS[self.rng.randrange(len(VISORS))][1]
            self.make_char(name, col, ring[i + 1], hat, vis, impostor=(i in imps))
        cx, cy = room_center(1)
        for c in self.people:
            self.face(c, cx, cy)
        self.state = "play"
        self.people_root.show()
        self.preview["root"].hide()
        self.show_play_ui(True)
        self.over_root.hide(); self.vote_root.hide()
        self.say("Há %d impostores a bordo! Faça tarefas e descubra quem são." % NUM_IMPOSTORS, 6)

    # ------------------------------------------------------------ interface
    def card(self, parent, x, z, w, h, color):
        cm = CardMaker("card"); cm.setFrame(-.5, .5, -.5, .5)
        np = parent.attachNewNode(cm.generate())
        np.setPos(x, 0, z); np.setScale(w, 1, h); np.setColor(*color)
        np.setTransparency(TransparencyAttrib.MAlpha)
        return np

    def bar(self, parent, x, z, w, h, color):
        self.card(parent, x + w / 2, z, w + .012, h + .012, (0, 0, 0, .6))
        cm = CardMaker("bar"); cm.setFrame(0, 1, -.5, .5)
        fg = parent.attachNewNode(cm.generate())
        fg.setPos(x, 0, z); fg.setScale(w, 1, h); fg.setColor(*color)
        return {"fg": fg, "w": w, "h": h}

    def set_bar(self, b, frac):
        b["fg"].setScale(max(.0001, b["w"] * max(0, min(1, frac))), 1, b["h"])

    def text(self, parent, txt, pos, scale, fg, align=TextNode.ACenter):
        return OnscreenText(parent=parent, text=txt, pos=pos, scale=scale, fg=fg, align=align,
                            mayChange=True, shadow=(0, 0, 0, .8))

    def build_ui(self):
        a2d = self.aspect2d
        self.hud_tl = self.a2dTopLeft.attachNewNode("hud_tl")
        self.hud_tr = self.a2dTopRight.attachNewNode("hud_tr")
        self.hud_bl = self.a2dBottomLeft.attachNewNode("hud_bl")
        self.hud_c = a2d.attachNewNode("hud_c")
        # tarefas (equipe)
        self.text(self.hud_tl, "TAREFAS DA EQUIPE", (.05, -.08), .045, (.7, .95, 1, 1), TextNode.ALeft)
        self.task_bar = self.bar(self.hud_tl, .05, -.13, .65, .03, (.2, .9, .4, 1))
        self.my_tasks = self.text(self.hud_tl, "", (.05, -.22), .04, (1, 1, 1, 1), TextNode.ALeft)
        self.place_txt = self.text(self.hud_tl, "", (.05, -.29), .04, (.8, .9, 1, 1), TextNode.ALeft)
        self.alive_txt = self.text(self.hud_tl, "", (.05, -.36), .04, (1, .85, .5, 1), TextNode.ALeft)
        # energia
        self.text(self.hud_bl, "ENERGIA (SHIFT)", (.05, .12), .035, (1, 1, 1, 1), TextNode.ALeft)
        self.stam_bar = self.bar(self.hud_bl, .05, .08, .4, .025, (1, .8, .2, 1))
        # barra de segurar tarefa
        self.hold_bg = self.hud_c.attachNewNode("hold")
        self.hold_bar = self.bar(self.hold_bg, -.25, -.68, .5, .035, (.3, 1, .6, 1))
        self.hold_bg.hide()
        self.prompt = self.text(self.hud_c, "", (0, -.80), .055, (.5, 1, .8, 1))
        self.msg = self.text(self.hud_c, "", (0, .78), .05, (1, .87, .35, 1))
        self.foot = self.text(self.hud_c, "WASD/Setas mover • SHIFT correr • E tarefa • R reportar • M mapa • Roda zoom • ESC menu",
                              (0, -.95), .035, (.8, .88, 1, .9))
        self.build_minimap()
        # menu
        self.menu_root = a2d.attachNewNode("menu")
        self.text(self.menu_root, "ESTAÇÃO ORBITAL", (0, .82), .13, (.45, .9, 1, 1))
        self.text(self.menu_root, "versão 4.0  •  3D  •  15 personagens  •  3 impostores", (0, .72), .05, (.8, .9, 1, 1))
        self.menu_rows = [self.text(self.menu_root, "", (-1.15, .30 - i * .16), .07, (1, 1, 1, 1), TextNode.ALeft)
                          for i in range(3)]
        self.menu_help = self.text(self.menu_root,
            "CIMA/BAIXO escolher   ESQ/DIR mudar   ENTER jogar   ESC sair",
            (0, -.82), .05, (.6, 1, .8, 1))
        self.text(self.menu_root,
            "Personalize seu tripulante!\nFaça tarefas, fuja dos impostores,\nreporte corpos (R) e vote em quem\nvocê acha suspeito.",
            (1.15, .30), .05, (.85, .9, 1, 1), TextNode.ARight)
        # votacao
        self.vote_root = a2d.attachNewNode("vote")
        self.card(self.vote_root, 0, 0, 3.2, 2.0, (0, 0, .05, .82))
        self.vote_title = self.text(self.vote_root, "", (0, .86), .065, (1, .5, .4, 1))
        self.vote_list = self.text(self.vote_root, "", (-1.05, .68), .05, (1, 1, 1, 1), TextNode.ALeft)
        self.text(self.vote_root, "CIMA/BAIXO escolher  •  ENTER votar", (0, -.9), .045, (.6, 1, .8, 1))
        self.vote_root.hide()
        # fim de jogo
        self.over_root = a2d.attachNewNode("over")
        self.card(self.over_root, 0, 0, 3.2, .7, (0, 0, 0, .75))
        self.over_title = self.text(self.over_root, "", (0, .06), .13, (1, 1, 1, 1))
        self.over_sub = self.text(self.over_root, "", (0, -.10), .05, (.9, .9, .9, 1))
        self.over_root.hide()

    def build_minimap(self):
        self.map_root = self.hud_tr.attachNewNode("minimap")
        W, H = .62, .465
        self.map_w, self.map_h = W, H
        self.map_root.setPos(-.38, 0, -.30)
        self.card(self.map_root, 0, 0, W + .03, H + .03, (0, 0, 0, .55))
        for i, (name, c, r, col) in enumerate(ROOMS):
            x, y = COLS[c], ROWS[r]
            self.card(self.map_root, *self.mm(x, y), W / 4 * .94, H / 3 * .90, scale_color(col, 1.8, .9))
        seen = set()
        for (a, b), (x, y, axis) in self.door_pos.items():
            if (min(a, b), max(a, b)) in seen: continue
            seen.add((min(a, b), max(a, b)))
            self.card(self.map_root, *self.mm(x, y), .018, .018, (.2, .9, 1, 1))
        self.task_dots = [self.card(self.map_root, *self.mm(t["pos"].x, t["pos"].y), .016, .016, (1, .9, .2, 1))
                          for t in self.tasks]
        self.body_dots = [self.card(self.map_root, 0, 0, .02, .02, (1, .15, .15, 1)) for _ in range(NUM_BOTS + 1)]
        for b in self.body_dots: b.hide()
        self.me_dot = self.card(self.map_root, 0, 0, .026, .026, (.2, 1, 1, 1))

    def mm(self, x, y):
        return (x / (BOUND_X * 2) * self.map_w, y / (BOUND_Y * 2) * self.map_h)

    def show_play_ui(self, on):
        for n in (self.hud_tl, self.hud_tr, self.hud_bl, self.hud_c):
            n.show() if on else n.hide()
        if on:
            self.hold_bg.hide()

    def say(self, t, d=3.0):
        self.msg.setText(t); self.msg_end = self.elapsed + d

    # ------------------------------------------------------------ entrada
    def down(self, name):
        w = self.mouseWatcherNode
        if not w:
            return False
        return w.is_button_down(self.btn[name])

    def nav_key(self, dx, dy):
        if self.state == "menu":
            if dx == 0:
                self.menu_row = (self.menu_row + dy) % 3
            else:
                k = ("color", "hat", "visor")[self.menu_row]
                n = (len(PALETTE), len(HATS), len(VISORS))[self.menu_row]
                self.opt[k] = (self.opt[k] + dx) % n
                self.rebuild_preview()
        elif self.state == "vote" and dx == 0:
            n = len(self.vote_cands) + 1
            self.vote_sel = (self.vote_sel + dy) % n

    def on_enter(self):
        if self.state == "menu" or self.state == "over":
            self.new_game()
        elif self.state == "vote":
            self.resolve_vote()

    def on_escape(self):
        if self.state == "menu":
            self.userExit()
        else:
            self.go_menu()

    def on_map(self):
        if self.state == "play":
            self.map_root.show() if self.map_root.isHidden() else self.map_root.hide()

    def on_zoom(self, d):
        self.zoom = max(.55, min(1.6, self.zoom + d))

    def go_menu(self):
        self.state = "menu"
        self.people_root.hide()
        self.show_play_ui(False)
        self.over_root.hide(); self.vote_root.hide()
        self.menu_root.show()
        self.preview["root"].show()
        self.cam_focus = Vec3(0, -90, 1.5); self.cam_pos = Vec3(0, -98.5, 2.6)

    # ------------------------------------------------------------ fisica / navegacao
    def blocked(self, x, y, r=.45):
        if x < -BOUND_X + r or x > BOUND_X - r or y < -BOUND_Y + r or y > BOUND_Y - r:
            return True
        for x1, x2, y1, y2 in self.walls:
            if x + r > x1 and x - r < x2 and y + r > y1 and y - r < y2:
                return True
        return False

    @staticmethod
    def dist2(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def move_toward(self, c, tp, speed, dt):
        p = c["node"].getPos()
        dx, dy = tp.x - p.x, tp.y - p.y
        dist = math.hypot(dx, dy)
        if dist < .05:
            c["moving"] = False
            return dist
        dx /= dist; dy /= dist
        step = min(speed * dt, dist)
        nx, ny = p.x + dx * step, p.y + dy * step
        moved = False
        if not self.blocked(nx, p.y):
            c["node"].setX(nx); moved = True
        if not self.blocked(c["node"].getX(), ny):
            c["node"].setY(ny); moved = True
        c["moving"] = moved
        if moved:
            c["ht"] = math.degrees(math.atan2(dx, -dy))
        return dist

    def nav_point(self, pos, dest):
        """Proximo ponto de passagem para ir de pos ate dest passando pelas portas."""
        ra, rb = room_of(pos.x, pos.y), room_of(dest.x, dest.y)
        if ra == rb:
            return dest
        nxt = self.next_room.get((ra, rb))
        if nxt is None:
            return dest
        x, y, axis = self.door_pos[(ra, nxt)]
        door = Vec3(x, y, 0)
        if math.hypot(x - pos.x, y - pos.y) < 1.7:
            ncx, ncy = room_center(nxt)
            ux, uy = ncx - x, ncy - y
            l = math.hypot(ux, uy) or 1
            return Vec3(x + ux / l * 3.0, y + uy / l * 3.0, 0)
        return door

    def random_dest(self, room=None):
        i = self.rng.randrange(12) if room is None else room
        cx, cy = room_center(i)
        if self.rng.random() < .5:
            return Vec3(cx + self.rng.uniform(-9, 9), cy + self.rng.uniform(-2.2, 2.2), 0)
        return Vec3(cx + self.rng.uniform(-2.2, 2.2), cy + self.rng.uniform(-9, 9), 0)

    # ------------------------------------------------------------ IA
    def ai_crew(self, c, dt):
        pos = c["node"].getPos()
        if c["wait"] > 0:
            c["wait"] -= dt; c["moving"] = False
            if c["wait"] <= 0:
                c["dest"] = None
            return
        if c["dest"] is None:
            cur = room_of(pos.x, pos.y)
            nr = self.rng.randrange(12)
            c["dest"] = self.random_dest(nr if nr != cur or self.rng.random() < .2 else (nr + 1) % 12)
        self.move_toward(c, self.nav_point(pos, c["dest"]), 3.1, dt)
        if self.dist2(pos, c["dest"]) < .7:
            c["wait"] = self.rng.uniform(2.0, 4.5)
            self.task_units = min(TASK_GOAL, self.task_units + BOT_TASK_UNITS)

    def ai_impostor(self, c, dt):
        c["cool"] = max(0.0, c["cool"] - dt)
        pos = c["node"].getPos()
        victim = None; bestd = 999
        if c["cool"] <= 0:
            for v in self.people:
                if v is c or not v["alive"] or v["impostor"]:
                    continue
                d = self.dist2(pos, v["node"].getPos())
                lim = 11 if v["player"] else 8
                if d < lim and d < bestd:
                    victim, bestd = v, d
        if victim:
            tp = self.nav_point(pos, victim["node"].getPos())
            self.move_toward(c, tp, 4.3 if victim["player"] else 3.6, dt)
            if bestd < 1.5:
                self.kill(c, victim)
            return
        if c["wait"] > 0:
            c["wait"] -= dt; c["moving"] = False
            if c["wait"] <= 0:
                c["dest"] = None
            return
        if c["dest"] is None:
            prey = [v for v in self.people if v["alive"] and not v["impostor"]]
            if prey and self.rng.random() < .6:
                t = self.rng.choice(prey)["node"].getPos()
                c["dest"] = Vec3(t.x, t.y, 0)
            else:
                c["dest"] = self.random_dest()
        self.move_toward(c, self.nav_point(pos, c["dest"]), 3.2, dt)
        if self.dist2(pos, c["dest"]) < .8:
            c["wait"] = self.rng.uniform(.5, 1.8)

    def kill(self, killer, v):
        v["alive"] = False; v["body"] = True; v["moving"] = False
        v["node"].setR(90); v["node"].setZ(.48)
        v["node"].setColorScale(.62, .55, .55, 1)
        v["tag"].hide()
        killer["cool"] = KILL_COOLDOWN
        killer["dest"] = None; killer["wait"] = self.rng.uniform(1, 2)
        if v["player"]:
            self.finish(False, "Você foi eliminado por um impostor!")
            return
        if self.player and self.player["alive"] and \
                self.dist2(self.player["node"].getPos(), v["node"].getPos()) < 16:
            self.say("Você ouviu um grito por perto... corra!", 3)
        self.check_end()

    def check_end(self):
        if self.state not in ("play", "vote"):
            return
        imps = [c for c in self.people if c["impostor"] and c["alive"]]
        crew = [c for c in self.people if not c["impostor"] and c["alive"]]
        if self.task_units >= TASK_GOAL:
            self.finish(True, "Todas as tarefas foram concluídas!")
        elif not imps:
            self.finish(True, "Todos os impostores foram eliminados!")
        elif len(crew) <= len(imps):
            self.finish(False, "Os impostores dominaram a estação!")

    def finish(self, win, why):
        self.state = "over"
        self.vote_root.hide(); self.hold_bg.hide()
        self.over_title.setText("VITÓRIA!" if win else "DERROTA!")
        self.over_title.setFg((.4, 1, .6, 1) if win else (1, .35, .35, 1))
        self.over_sub.setText(why + "\nENTER jogar de novo   •   ESC menu")
        self.over_root.show()
        self.msg.setText("")
        for c in self.people:
            c["moving"] = False

    # ------------------------------------------------------------ reuniao
    def on_report(self):
        if self.state != "play":
            return
        pp = self.player["node"].getPos()
        body = None
        for c in self.people:
            if c["body"] and self.dist2(pp, c["node"].getPos()) < 4.5:
                body = c; break
        if not body:
            self.say("Nenhum corpo por perto para reportar.", 2)
            return
        self.start_vote(body)

    def start_vote(self, body):
        self.state = "vote"
        bp = body["node"].getPos()
        self.vote_cands = [c for c in self.people if c["alive"] and not c["player"]]
        for c in self.vote_cands:
            p = c["node"].getPos()
            c["room"] = ROOMS[room_of(p.x, p.y)][0]
            c["near"] = self.dist2(p, bp) < 14
            c["moving"] = False
        self.vote_sel = 0
        self.vote_room_name = ROOMS[room_of(bp.x, bp.y)][0]
        self.vote_title.setText("REUNIÃO! Corpo de %s em %s" % (body["name"], self.vote_room_name))
        self.hold_bg.hide(); self.prompt.setText("")
        self.vote_root.show()
        self.refresh_vote()

    def refresh_vote(self):
        lines = []
        for i, c in enumerate(self.vote_cands):
            mark = ">" if i == self.vote_sel else " "
            near = "  [perto do corpo]" if c["near"] else ""
            lines.append("%s %-10s visto em %s%s" % (mark, c["name"], c["room"], near))
        lines.append("%s Pular votação" % (">" if self.vote_sel == len(self.vote_cands) else " "))
        self.vote_list.setText("\n".join(lines))

    def resolve_vote(self):
        sel = self.vote_sel
        if sel < len(self.vote_cands):
            c = self.vote_cands[sel]
            c["alive"] = False; c["node"].hide()
            msg = "%s foi ejetado. %s" % (c["name"], "Era um IMPOSTOR!" if c["impostor"] else "Não era impostor...")
        else:
            msg = "Ninguém foi ejetado."
        for c in self.people:
            if c["body"]:
                c["node"].hide(); c["body"] = False
        left = len([c for c in self.people if c["impostor"] and c["alive"]])
        msg += "  Restam %d impostor(es)." % left
        alive = [c for c in self.people if c["alive"]]
        pts = self.ring_positions(len(alive))
        cx, cy = room_center(1)
        for c, p in zip(alive, pts):
            c["node"].setPos(p[0], p[1], 0); self.face(c, cx, cy)
            c["dest"] = None; c["wait"] = self.rng.uniform(1, 3)
            if c["impostor"]:
                c["cool"] = max(c["cool"], 20)
        self.pvel = Vec3(0, 0, 0)
        self.vote_root.hide()
        self.state = "play"
        self.say(msg, 7)
        self.check_end()

    # ------------------------------------------------------------ loop
    def nearest_task(self):
        p = self.player["node"].getPos(); best = None; bd = 999
        for t in self.tasks:
            if t["done"]:
                continue
            d = self.dist2(p, t["pos"])
            if d < bd:
                best, bd = t, d
        return best, bd

    def update_player(self, dt):
        pl = self.player
        mx = my = 0
        if self.down("w") or self.down("arrow_up"): my += 1
        if self.down("s") or self.down("arrow_down"): my -= 1
        if self.down("a") or self.down("arrow_left"): mx -= 1
        if self.down("d") or self.down("arrow_right"): mx += 1
        l = math.hypot(mx, my)
        if l > 0:
            mx /= l; my /= l
        want = l > 0
        sprint = want and self.down("shift") and self.stamina > 0 and not self.exhausted
        speed = SPRINT_SPEED if sprint else WALK_SPEED
        if sprint:
            self.stamina -= 30 * dt
            if self.stamina <= 0:
                self.stamina = 0; self.exhausted = True
        else:
            self.stamina = min(100.0, self.stamina + (14 if want else 24) * dt)
            if self.exhausted and self.stamina >= 25:
                self.exhausted = False
        k = min(1.0, 11 * dt)
        self.pvel = Vec3(self.pvel.x + (mx * speed - self.pvel.x) * k,
                         self.pvel.y + (my * speed - self.pvel.y) * k, 0)
        p = pl["node"].getPos()
        nx, ny = p.x + self.pvel.x * dt, p.y + self.pvel.y * dt
        if not self.blocked(nx, p.y): pl["node"].setX(nx)
        if not self.blocked(pl["node"].getX(), ny): pl["node"].setY(ny)
        sp = math.hypot(self.pvel.x, self.pvel.y)
        pl["moving"] = sp > .8
        if sp > .8:
            pl["ht"] = math.degrees(math.atan2(self.pvel.x, -self.pvel.y))
        pl["speed_ratio"] = sp / WALK_SPEED

        # tarefas
        t, d = self.nearest_task()
        prompt = ""
        holding = False
        if t and d < 2.7:
            prompt = "[E] segure: " + t["name"]
            if self.down("e") and sp < 3.5:
                holding = True
                t["prog"] += dt / t["hold"]
                if t["prog"] >= 1:
                    t["done"] = True; t["marker"].hide(); t["prog"] = 0
                    self.task_units = min(TASK_GOAL, self.task_units + 1)
                    self.say("Tarefa concluída: " + t["name"], 2.5)
                    self.check_end()
            self.hold_bar_val = t["prog"]
        for o in self.tasks:
            if o is not t and o["prog"] > 0:
                o["prog"] = max(0.0, o["prog"] - dt * 1.5)
        if t and t["prog"] > 0 and not holding:
            t["prog"] = max(0.0, t["prog"] - dt * 1.5)
        if t and t["prog"] > 0:
            self.hold_bg.show(); self.set_bar(self.hold_bar, t["prog"])
        else:
            self.hold_bg.hide()
        if not prompt:
            for c in self.people:
                if c["body"] and self.dist2(p, c["node"].getPos()) < 4.5:
                    prompt = "[R] Reportar corpo"; break
        self.prompt.setText(prompt)

    def update_play(self, dt):
        self.update_player(dt)
        for c in self.people:
            if c["player"] or not c["alive"]:
                continue
            if c["impostor"]:
                self.ai_impostor(c, dt)
            else:
                self.ai_crew(c, dt)
            if self.state != "play":
                return

    def animate(self, dt):
        for c in self.people:
            n = c["node"]
            if not c["alive"]:
                continue
            diff = (c["ht"] - c["h"] + 180) % 360 - 180
            c["h"] += diff * min(1.0, 12 * dt)
            n.setH(c["h"])
            pr = c["parts"]
            if c["moving"]:
                c["phase"] += dt * 11
                sw = math.sin(c["phase"]) * .2
                pr["lf"].setY(sw); pr["rf"].setY(-sw)
                pr["anim"].setZ(abs(math.sin(c["phase"])) * .07)
            else:
                pr["lf"].setY(pr["lf"].getY() * .8); pr["rf"].setY(pr["rf"].getY() * .8)
                pr["anim"].setZ(pr["anim"].getZ() * .8)
        for dr in self.door_panels:
            near = any(c["alive"] and self.dist2(c["node"].getPos(), dr["center"]) < 4.6 for c in self.people)
            tgt = 1.0 if near else 0.0
            dr["amt"] += (tgt - dr["amt"]) * min(1.0, 9 * dt)
            for np, closed, opened in dr["panels"]:
                np.setPos(closed + (opened - closed) * dr["amt"])
        for t in self.tasks:
            if not t["done"]:
                t["marker"].setZ(3.6 + math.sin(self.elapsed * 3 + t["pos"].x) * .2)

    def update_camera(self, dt):
        if self.state == "menu":
            tp = self.show_pos
            self.preview["root"].setH(math.sin(self.elapsed * .9) * 38)
            self.preview["anim"].setZ(math.sin(self.elapsed * 2.2) * .03)
            cam = Vec3(0, -98.5, 2.6); foc = Vec3(0, -90, 1.7)
        else:
            p = self.player["node"].getPos()
            tp = p
            cam = Vec3(p.x, p.y - 20 * self.zoom, 27 * self.zoom)
            foc = Vec3(p.x, p.y, .8)
        k = min(1.0, 7 * dt)
        self.cam_pos = self.cam_pos + (cam - self.cam_pos) * k
        self.cam_focus = self.cam_focus + (foc - self.cam_focus) * k
        self.camera.setPos(self.cam_pos); self.camera.lookAt(self.cam_focus)
        gx, gy = round(tp.x / 3) * 3, round(tp.y / 3) * 3
        self.sun.setPos(gx + 22, gy - 22, 48); self.sun.lookAt(gx, gy, 0)

    def update_hud(self):
        self.set_bar(self.task_bar, self.task_units / TASK_GOAL)
        done = sum(1 for t in self.tasks if t["done"])
        self.my_tasks.setText("Suas tarefas: %d / %d" % (done, len(self.tasks)))
        p = self.player["node"].getPos()
        self.place_txt.setText("Local: " + ROOMS[room_of(p.x, p.y)][0])
        alive = sum(1 for c in self.people if c["alive"])
        self.alive_txt.setText("Vivos a bordo: %d" % alive)
        self.set_bar(self.stam_bar, self.stamina / 100)
        self.stam_bar["fg"].setColor(*((.9, .3, .2, 1) if self.exhausted else (1, .8, .2, 1)))
        mpx, mpz = self.mm(p.x, p.y)
        self.me_dot.setPos(mpx, 0, mpz)
        for t, dot in zip(self.tasks, self.task_dots):
            dot.show() if not t["done"] else dot.hide()
        bodies = [c for c in self.people if c["body"]]
        for i, dot in enumerate(self.body_dots):
            if i < len(bodies):
                bp = bodies[i]["node"].getPos(); m = self.mm(bp.x, bp.y)
                dot.setPos(m[0], 0, m[1]); dot.show()
            else:
                dot.hide()

    def update(self, task):
        dt = min(ClockObject.getGlobalClock().getDt(), .05)
        self.elapsed += dt
        if self.state == "play":
            self.update_play(dt)
        if self.state != "menu":
            if self.state == "vote":
                self.refresh_vote()
            self.animate(dt)
            self.update_hud()
            if self.elapsed > self.msg_end and self.state != "over":
                self.msg.setText("")
        self.update_camera(dt)
        if self.state == "menu":
            names = [("COR", PALETTE[self.opt["color"]][0]), ("CHAPÉU", HATS[self.opt["hat"]]),
                     ("VISOR", VISORS[self.opt["visor"]][0])]
            for i, (lab, val) in enumerate(names):
                sel = i == self.menu_row
                self.menu_rows[i].setText(("> " if sel else "  ") + "%s:  <  %s  >" % (lab, val))
                self.menu_rows[i].setFg((.4, 1, .8, 1) if sel else (.85, .9, 1, 1))
        return Task.cont


if __name__ == "__main__":
    Game().run()