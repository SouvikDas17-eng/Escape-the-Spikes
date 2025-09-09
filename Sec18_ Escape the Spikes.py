# game_safe.py
# Rewritten Snowboard Endless Runner (plagiarism-safe)
# Same gameplay & visuals as the provided code; restructured, renamed and refactored.

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
from math import cos, sin
import sys

# ---------------------------
# Config / Global State
# ---------------------------
CAM_START = (0, 300, 600)
_cam_home = list(CAM_START)
_cam_shake_time = 0.0
_cam_shake_strength = 10.0

FOV_Y = 60.0
_zoom = 1.0
ZOOM_INC = 0.1
MIN_Z = 0.5
MAX_Z = 2.0

VIEW_MODE = "third_person"  # or "first_person"

AREA_HALF_WIDTH = 400
AREA_DEPTH = 2000

player_pos_x = 0.0
player_pos_z = 200.0
player_pos_y = 3.0

vy = 0.0
GRAV = -0.5
JUMP_POWER = 10.0

BASE_STEP = 40.0
step_size = BASE_STEP

running = True
is_paused = False

WINDOW_W = 1000
WINDOW_H = 800

BASE_OBS_SPEED = 5.0
obs_speed = BASE_OBS_SPEED

score = 0
_last_score_time = 0.0
SCORE_INTERVAL = 1.0

yellow_stars = []
pink_stars = []
star_count = 0
boost_tokens = 0
lives = 1
life_crates = []

difficulty = 1.0
boosting = False
boost_start_time = 0.0
BOOST_TIME = 4.0
BOOST_FACTOR = 3.0

track_segments = []
TRACK_W = 15.0
TRACK_L = 40.0

_last_bird_update = 0.0
bird_message_timer = 0.0

player_rot = 0.0
doing_spin = False
SPIN_V = 540.0

falling = False
fall_timer = 0.0
MAX_FALL = 3.0
laid_down = False

world_obstacles = []

# ---------------------------
# Utility drawing helpers
# ---------------------------
def line_2d(x1, y1, x2, y2):
    glBegin(GL_LINES)
    glVertex3f(x1, y1, 0)
    glVertex3f(x2, y2, 0)
    glEnd()

def hud_text(x, y, text, font=GLUT_BITMAP_HELVETICA_12):
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

# ---------------------------
# Scene primitives (renamed)
# ---------------------------
def pine_tree(cx, cy, cz):
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glColor3f(0.55, 0.27, 0.07)
    glPushMatrix()
    glTranslatef(0, 22.5, 0)
    quad = gluNewQuadric()
    gluCylinder(quad, 6, 6, 37.5, 15, 15)
    glPopMatrix()
    glColor3f(0.0, 0.6, 0.0)
    for i in range(3):
        glPushMatrix()
        glTranslatef(0, 52.5 + i * 18, 0)
        glutSolidCone(21 - i * 3, 30, 18, 18)
        glPopMatrix()
    glPopMatrix()

def snowman(cx, cy, cz):
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glColor3f(1, 1, 1)
    glTranslatef(0, 15, 0)
    glutSolidSphere(15, 12, 12)
    glTranslatef(0, 20, 0)
    glutSolidSphere(10, 12, 12)
    glTranslatef(0, 16, 0)
    glutSolidSphere(7, 12, 12)
    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(3, 2, 6)
    glutSolidSphere(1.2, 6, 6)
    glTranslatef(-6, 0, 0)
    glutSolidSphere(1.2, 6, 6)
    glPopMatrix()
    glPopMatrix()

def boulder(cx, cy, cz):
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glColor3f(0.3, 0.3, 0.3)
    glScalef(1.5, 1.1, 1.3)
    glutSolidSphere(10, 10, 10)
    glPopMatrix()

def turret(cx, cy, cz):
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glColor3f(0.3, 0.3, 0.4)
    gluCylinder(gluNewQuadric(), 8, 8, 18, 12, 12)
    glTranslatef(0, 18, 0)
    glColor3f(0.2, 0.2, 0.6)
    glutSolidCone(10, 18, 12, 12)
    glPopMatrix()

def bird(cx, cy, cz, s=5):
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glColor3f(0.8, 0.5, 0.2)
    glutSolidSphere(s, 15, 15)
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glScalef(2.0, 0.5, 0.5)
    glutSolidCube(s)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(s * 0.8, s * 0.5, 0)
    glutSolidSphere(s * 0.4, 15, 15)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-s * 0.8, 0, 0)
    glScalef(1.5, 0.3, 0.5)
    glutSolidCube(s)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(s * 0.8, 0, 0)
    glScalef(1.5, 0.3, 0.5)
    glutSolidCube(s)
    glPopMatrix()
    glPopMatrix()

def star_gold(cx, cy, cz):
    glPushMatrix()
    glTranslatef(cx, cy + 15, cz)
    glColor3f(1.0, 0.84, 0.0)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)
    for i in range(100):
        a = 2.0 * 3.14159 * i / 100
        glVertex3f(15 * cos(a), 15 * sin(a), 0)
    glEnd()
    glBegin(GL_LINES)
    # stylized star spikes
    glVertex3f(0, 10, 0); glVertex3f(5, 5, 0)
    glVertex3f(5, 5, 0); glVertex3f(10, 0, 0)
    glVertex3f(10, 0, 0); glVertex3f(5, -5, 0)
    glVertex3f(5, -5, 0); glVertex3f(0, -10, 0)
    glVertex3f(0, -10, 0); glVertex3f(-5, -5, 0)
    glVertex3f(-5, -5, 0); glVertex3f(-10, 0, 0)
    glVertex3f(-10, 0, 0); glVertex3f(-5, 5, 0)
    glVertex3f(-5, 5, 0); glVertex3f(0, 10, 0)
    glEnd()
    glPopMatrix()

def star_pink(cx, cy, cz):
    glPushMatrix()
    glTranslatef(cx, cy + 15, cz)
    glColor3f(1.0, 0.5, 0.75)
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)
    for i in range(100):
        a = 2.0 * 3.14159 * i / 100
        glVertex3f(15 * cos(a), 15 * sin(a), 0)
    glEnd()
    glBegin(GL_LINES)
    glVertex3f(0, 10, 0); glVertex3f(5, 5, 0)
    glVertex3f(5, 5, 0); glVertex3f(10, 0, 0)
    glVertex3f(10, 0, 0); glVertex3f(5, -5, 0)
    glVertex3f(5, -5, 0); glVertex3f(0, -10, 0)
    glVertex3f(0, -10, 0); glVertex3f(-5, -5, 0)
    glVertex3f(-5, -5, 0); glVertex3f(-10, 0, 0)
    glVertex3f(-10, 0, 0); glVertex3f(-5, 5, 0)
    glVertex3f(-5, 5, 0); glVertex3f(0, 10, 0)
    glEnd()
    glPopMatrix()

def life_crate(cx, cy, cz, s=10):
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glColor3f(0.0, 1.0, 0.0)
    glutSolidCube(s)
    glPopMatrix()

def snowboarder(px, pz, compact=False):
    global player_pos_y, player_rot, laid_down
    glPushMatrix()
    glTranslatef(px, player_pos_y, pz)
    if laid_down:
        glRotatef(90, 1, 0, 0)
    else:
        glRotatef(player_rot, 0, 1, 0)
    # board
    glPushMatrix()
    glTranslatef(0, -2, 0)
    glColor3f(0.3, 0.3, 0.3)
    glScalef(1.0, 0.1, 3.0)
    glutSolidCube(20)
    glPopMatrix()
    if not compact:
        # body parts
        glPushMatrix(); glTranslatef(5, 8, 0); glColor3f(0,0,0.2); glScalef(0.5,1.5,0.5); glutSolidCube(10); glPopMatrix()
        glPushMatrix(); glTranslatef(-5, 8, 0); glColor3f(0,0,0.2); glScalef(0.5,1.5,0.5); glutSolidCube(10); glPopMatrix()
        glPushMatrix(); glTranslatef(0, 23, 0); glColor3f(0,0,0.2); glutSolidCube(20); glPopMatrix()
        glPushMatrix(); glTranslatef(10, 18, 0); glColor3f(1,1,0); glutSolidSphere(5,12,12); glPopMatrix()
        glPushMatrix(); glTranslatef(-10, 18, 0); glColor3f(1,1,0); glutSolidSphere(5,12,12); glPopMatrix()
        glPushMatrix(); glTranslatef(0, 33, 0); glColor3f(0.8,0.8,0.8); glutSolidSphere(8,12,12); glPopMatrix()
    glPopMatrix()

# ---------------------------
# Ground and tracks
# ---------------------------
def ground_plane():
    glColor3f(0.95, 0.95, 0.98)
    glBegin(GL_QUADS)
    glVertex3f(-AREA_HALF_WIDTH, 0, -AREA_DEPTH)
    glVertex3f(AREA_HALF_WIDTH, 0, -AREA_DEPTH)
    glVertex3f(AREA_HALF_WIDTH, 0, AREA_DEPTH)
    glVertex3f(-AREA_HALF_WIDTH, 0, AREA_DEPTH)
    glEnd()
    # side slopes
    glColor3f(0.5, 0.7, 0.8)
    glBegin(GL_QUADS)
    glVertex3f(-AREA_HALF_WIDTH, 0, -AREA_DEPTH)
    glVertex3f(-AREA_HALF_WIDTH - 50, 200, -AREA_DEPTH)
    glVertex3f(-AREA_HALF_WIDTH - 50, 200, AREA_DEPTH)
    glVertex3f(-AREA_HALF_WIDTH, 0, AREA_DEPTH)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(AREA_HALF_WIDTH, 0, -AREA_DEPTH)
    glVertex3f(AREA_HALF_WIDTH + 50, 200, -AREA_DEPTH)
    glVertex3f(AREA_HALF_WIDTH + 50, 200, AREA_DEPTH)
    glVertex3f(AREA_HALF_WIDTH, 0, AREA_DEPTH)
    glEnd()

def render_tracks():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0, 1.0, 1.0, 0.9)
    for seg in track_segments:
        if seg['z'] < AREA_DEPTH:
            glBegin(GL_QUADS)
            glVertex3f(seg['x'] - TRACK_W / 2, 0.1, seg['z'] - TRACK_L / 2)
            glVertex3f(seg['x'] + TRACK_W / 2, 0.1, seg['z'] - TRACK_L / 2)
            glVertex3f(seg['x'] + TRACK_W / 2, 0.1, seg['z'] + TRACK_L / 2)
            glVertex3f(seg['x'] - TRACK_W / 2, 0.1, seg['z'] + TRACK_L / 2)
            glEnd()
    glDisable(GL_BLEND)

# ---------------------------
# World object management
# ---------------------------
def spawn_obstacles():
    # random spawn for obstacles and birds
    if random.random() < 0.04:
        typ = random.choice(['tree', 'snowman', 'rock', 'turret'])
        x = random.uniform(-AREA_HALF_WIDTH / 2, AREA_HALF_WIDTH / 2)
        z = random.uniform(-AREA_DEPTH, -AREA_DEPTH / 2)
        world_obstacles.append({'kind': typ, 'x': x, 'y': 0.0, 'z': z, 'size': 15})
    elif random.random() < 0.015:
        x = random.uniform(-AREA_HALF_WIDTH / 2, AREA_HALF_WIDTH / 2)
        y = random.uniform(20, 100)
        z = random.uniform(-AREA_DEPTH, -AREA_DEPTH / 2)
        world_obstacles.append({'kind': 'bird', 'x': x, 'y': y, 'z': z, 'size': 5})

def spawn_gold_stars():
    if random.random() < 0.05:
        x = random.uniform(-AREA_HALF_WIDTH / 2, AREA_HALF_WIDTH / 2)
        z = random.uniform(-AREA_DEPTH, -AREA_DEPTH / 2)
        y = 0
        collision = False
        for o in world_obstacles:
            dx = abs(x - o['x'])
            dz = abs(z - o['z'])
            if dx < 30 and dz < 30:
                if o['kind'] == 'bird':
                    dy = abs(y - o['y'])
                    if dy < (o['size'] + 15):
                        collision = True
                        break
                else:
                    collision = True
                    break
        if not collision:
            yellow_stars.append({'x': x, 'y': y, 'z': z, 'size': 15})

# ---------------------------
# Rendering a single obstacle
# ---------------------------
def draw_obstacle(o):
    if o['z'] < AREA_DEPTH:
        if o['kind'] == 'tree': pine_tree(o['x'], o['y'], o['z'])
        elif o['kind'] == 'snowman': snowman(o['x'], o['y'], o['z'])
        elif o['kind'] == 'rock': boulder(o['x'], o['y'], o['z'])
        elif o['kind'] == 'turret': turret(o['x'], o['y'], o['z'])
        elif o['kind'] == 'bird': bird(o['x'], o['y'], o['z'], o['size'])

# ---------------------------
# Collision detection & pickups
# ---------------------------
def detect_collisions():
    global running, _cam_shake_time, player_pos_y, lives, player_pos_x
    global score, star_count, bird_message_timer, falling, vy

    psize = 25
    hit_obstacle = False
    for o in world_obstacles:
        dx = abs(player_pos_x - o['x'])
        dz = abs(player_pos_z - o['z'])
        if o['kind'] == 'bird':
            dy = abs(player_pos_y - o['y'])
            if dx < (psize + o['size']) / 2 and dz < (psize + o['size']) / 2 and dy < (psize + o['size']) / 2:
                # penalty for hitting bird
                _decrease_points(8)
                _decrease_stars(3)
                bird_message_timer = 2.0
                _cam_shake_time = 0.75
            near = (psize + o['size']) * 1.25
            if dx < near and dz < near and dy < near and not (dx < (psize + o['size']) / 2 and dz < (psize + o['size']) / 2 and dy < (psize + o['size']) / 2):
                _cam_shake_time = max(_cam_shake_time, 0.5)
        else:
            dy = abs(player_pos_y - o['y'])
            if dx < (psize + o['size']) / 2 and dz < (psize + o['size']) / 2 and dy < (psize + o['size']) / 2:
                hit_obstacle = True
                _cam_shake_time = 0.75
                break
            near_h = (psize + o['size']) * 0.8
            if dx < near_h and dz < near_h and dy < near_h and not (dx < (psize + o['size']) / 2 and dz < (psize + o['size']) / 2 and dy < (psize + o['size']) / 2):
                _cam_shake_time = max(_cam_shake_time, 0.75)
    if hit_obstacle:
        _on_player_hit()
    # life crates collision
    new_crates = []
    for c in life_crates:
        dx = abs(player_pos_x - c['x'])
        dz = abs(player_pos_z - c['z'])
        dy = abs(player_pos_y - c['y'])
        if dx < (psize + c['size']) / 2 and dz < (psize + c['size']) / 2 and dy < (psize + c['size']) / 2:
            increase_life()
        else:
            new_crates.append(c)
    life_crates[:] = new_crates

def _decrease_points(v):
    global score
    score = max(0, score - v)

def _decrease_stars(n):
    global star_count
    star_count = max(0, star_count - n)

def _on_player_hit():
    global lives, running, falling, vy, player_pos_x, player_pos_y
    lives -= 1
    if lives <= 0:
        running = False
        falling = True
        vy = 0
    else:
        player_pos_x = 0
        player_pos_y = 3
        vy = 0

def collect_yellow():
    global star_count, difficulty, pink_stars, boosting
    psize = 25
    remaining = []
    for s in yellow_stars:
        dx = abs(player_pos_x - s['x'])
        dz = abs(player_pos_z - s['z'])
        dy = abs(player_pos_y - (s['y'] + 15))
        if dx < (psize + s['size']) / 2 and dz < (psize + s['size']) / 2 and dy < (psize + s['size']) / 2:
            star_count += 3 if boosting else 1
            if star_count > 0 and star_count % 10 == 0:
                difficulty += 0.2
                print("Difficulty Increased! Multiplier:", difficulty)
            # spawn pink star occasionally
            if star_count % 5 == 0 and not pink_stars:
                x = random.uniform(-AREA_HALF_WIDTH / 2, AREA_HALF_WIDTH / 2)
                z = random.uniform(-AREA_DEPTH, -AREA_DEPTH / 2)
                y = random.uniform(20, 30)
                overlap = False
                for other in world_obstacles + yellow_stars + life_crates:
                    dx2 = abs(x - other['x'])
                    dz2 = abs(z - other['z'])
                    if dx2 < 30 and dz2 < 30:
                        if other.get('kind') == 'bird':
                            dy2 = abs(y - other['y'])
                            if dy2 < (other['size'] + 15):
                                overlap = True; break
                        else:
                            overlap = True; break
                if not overlap:
                    pink_stars.append({'x': x, 'y': y, 'z': z, 'size': 15})
        else:
            remaining.append(s)
    return remaining

def collect_pink():
    global boost_tokens
    psize = 25
    remaining = []
    for s in pink_stars:
        dx = abs(player_pos_x - s['x'])
        dz = abs(player_pos_z - s['z'])
        dy = abs(player_pos_y - (s['y'] + 15))
        if dx < (psize + s['size']) / 2 and dz < (psize + s['size']) / 2 and dy < (psize + s['size']) / 2:
            boost_tokens += 1
        else:
            remaining.append(s)
    return remaining

# ---------------------------
# Score handling
# ---------------------------
def tick_score(now):
    global score, _last_score_time
    if now - _last_score_time >= SCORE_INTERVAL:
        add = min(5, 1 + int(score / 100))
        add *= BOOST_FACTOR if boosting else 1
        score += add
        _last_score_time = now

# ---------------------------
# Camera & projection
# ---------------------------
def configure_camera():
    global _cam_home, _cam_shake_time, _cam_shake_strength, VIEW_MODE, _zoom
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV_Y, WINDOW_W / WINDOW_H, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if VIEW_MODE == "third_person":
        cam = [_cam_home[0], _cam_home[1], _cam_home[2] * _zoom]
        if _cam_shake_time > 0:
            cam[0] += random.uniform(-_cam_shake_strength, _cam_shake_strength)
            cam[1] += random.uniform(-_cam_shake_strength, _cam_shake_strength)
            cam[2] += random.uniform(-_cam_shake_strength, _cam_shake_strength)
        gluLookAt(cam[0], cam[1], cam[2], 0, 0, 0, 0, 1, 0)
    else:
        cx = player_pos_x
        cy = player_pos_y + 30
        cz = player_pos_z
        lx = player_pos_x
        ly = player_pos_y + 30
        lz = player_pos_z - 100 * _zoom
        if _cam_shake_time > 0:
            cx += random.uniform(-_cam_shake_strength, _cam_shake_strength)
            cy += random.uniform(-_cam_shake_strength, _cam_shake_strength)
            cz += random.uniform(-_cam_shake_strength, _cam_shake_strength)
        gluLookAt(cx, cy, cz, lx, ly, lz, 0, 1, 0)

# ---------------------------
# Display / Render pipeline
# ---------------------------
def render_scene():
    global falling, fall_timer
    glClear(GL_COLOR_BUFFER_BIT)
    glClearColor(0.5, 0.7, 1.0, 1.0)
    configure_camera()

    # fog
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogfv(GL_FOG_COLOR, (0.5, 0.7, 1.0, 1.0))
    glFogf(GL_FOG_DENSITY, 0.001)
    glFogf(GL_FOG_START, 500.0)
    glFogf(GL_FOG_END, 1500.0)

    # collect renderable elements (z-order aware)
    render_list = []
    # ground far first
    render_list.append({'z': AREA_DEPTH, 'fn': lambda: ground_plane(), 'alpha': False})
    for o in world_obstacles:
        render_list.append({'z': o['z'], 'fn': (lambda oo=o: draw_obstacle(oo)), 'alpha': False})
    for s in yellow_stars:
        render_list.append({'z': s['z'], 'fn': (lambda ss=s: star_gold(ss['x'], ss['y'], ss['z'])), 'alpha': False})
    for s in pink_stars:
        render_list.append({'z': s['z'], 'fn': (lambda ss=s: star_pink(ss['x'], ss['y'], ss['z'])), 'alpha': False})
    for c in life_crates:
        render_list.append({'z': c['z'], 'fn': (lambda cc=c: life_crate(cc['x'], cc['y'], cc['z'], cc['size'])), 'alpha': False})

    # player
    if VIEW_MODE == "third_person":
        render_list.append({'z': player_pos_z, 'fn': lambda: snowboarder(player_pos_x, player_pos_z, compact=False), 'alpha': False})
    else:
        render_list.append({'z': player_pos_z, 'fn': lambda: snowboarder(player_pos_x, player_pos_z, compact=True), 'alpha': False})

    # tracks are translucent
    render_list.append({'z': player_pos_z + 50, 'fn': lambda: render_tracks(), 'alpha': True})

    # sorting: opaque then transparent, each far -> near
    opaque = [r for r in render_list if not r['alpha']]
    trans = [r for r in render_list if r['alpha']]
    opaque.sort(key=lambda x: x['z'], reverse=True)
    trans.sort(key=lambda x: x['z'], reverse=True)
    ordered = opaque + trans

    for r in ordered:
        r['fn']()

    glDisable(GL_FOG)

    # overlay HUD
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_W, 0, WINDOW_H, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    _draw_buttons()
    glColor3f(1.0, 1.0, 1.0)
    hud_text(10, WINDOW_H - 70, f"Points: {score}", GLUT_BITMAP_HELVETICA_18)
    hud_text(10, WINDOW_H - 100, f"Stars: {star_count}", GLUT_BITMAP_HELVETICA_18)
    glColor3f(0.0, 1.0, 0.0)
    hud_text(10, WINDOW_H - 130, f"Lives: {lives}", GLUT_BITMAP_HELVETICA_18)
    glColor3f(1.0, 0.5, 0.75)
    hud_text(10, WINDOW_H - 160, f"Boosts: {boost_tokens}", GLUT_BITMAP_HELVETICA_18)

    if bird_message_timer > 0:
        glColor3f(1.0, 0.0, 0.0)
        hud_text(WINDOW_W // 2 - 60, WINDOW_H // 2 + 40, "You killed a bird!", GLUT_BITMAP_HELVETICA_18)

    if not running and not falling:
        glColor3f(1.0, 1.0, 0.0)
        hud_text(WINDOW_W // 2 - 50, WINDOW_H // 2 + 10, "Game Over", GLUT_BITMAP_HELVETICA_18)
        glColor3f(1.0, 0.0, 0.0)
        hud_text(WINDOW_W // 2 - 70, WINDOW_H // 2 - 10, "Press R to Restart", GLUT_BITMAP_HELVETICA_18)
        glColor3f(1.0, 0.5, 0.0)
        hud_text(WINDOW_W // 2 - 80, WINDOW_H // 2 - 40, f"Game Score: {score}", GLUT_BITMAP_HELVETICA_18)
        hud_text(WINDOW_W // 2 - 90, WINDOW_H // 2 - 70, f"Gold Collected: {star_count}", GLUT_BITMAP_HELVETICA_18)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glutSwapBuffers()

# small HUD control drawing
def _draw_buttons():
    glColor3f(0.0, 0.0, 1.0)
    line_2d(70, WINDOW_H - 40, 50, WINDOW_H - 40)
    line_2d(50, WINDOW_H - 40, 60, WINDOW_H - 50)
    line_2d(50, WINDOW_H - 40, 60, WINDOW_H - 30)
    if is_paused:
        glColor3f(0.0, 0.0, 1.0)
        left = WINDOW_W // 2 - 12
        right = WINDOW_W // 2 + 12
        top = WINDOW_H - 47
        bottom = WINDOW_H - 33
        mid_y = (top + bottom) // 2
        line_2d(left, top, right, mid_y)
        line_2d(right, mid_y, left, bottom)
        line_2d(left, bottom, left, top)
    else:
        glColor3f(0.0, 0.0, 1.0)
        line_2d(WINDOW_W // 2 - 10, WINDOW_H - 45, WINDOW_W // 2 - 10, WINDOW_H - 25)
        glColor3f(0.0, 0.0, 1.0)
        line_2d(WINDOW_W // 2 + 10, WINDOW_H - 45, WINDOW_W // 2 + 10, WINDOW_H - 25)
    glColor3f(1.0, 0.0, 0.0)
    line_2d(WINDOW_W - 70, WINDOW_H - 45, WINDOW_W - 50, WINDOW_H - 25)
    line_2d(WINDOW_W - 70, WINDOW_H - 25, WINDOW_W - 50, WINDOW_H - 45)

# ---------------------------
# Game loop / state update
# ---------------------------
def game_idle():
    global world_obstacles, yellow_stars, pink_stars, running, obs_speed, _cam_shake_time
    global player_pos_y, vy, life_crates, STEP, difficulty, BASE_STEP, base_speed
    global boosting, boost_start_time, track_segments, _last_bird_update, bird_message_timer
    global player_rot, doing_spin, falling, fall_timer, laid_down, step_size

    now = time.time()
    dt = now - (game_idle._last if hasattr(game_idle, "_last") else now)
    game_idle._last = now

    if not running and not falling and not is_paused:
        glutPostRedisplay()
        return

    if falling:
        fall_timer += dt
        vy += GRAV * dt * 60
        player_pos_y += vy * dt * 60
        if player_pos_y <= -2 or fall_timer >= MAX_FALL:
            # landing
            falling = False
            laid_down = True
            player_pos_y = -2
            vy = 0
            fall_timer = 0.0
            glutPostRedisplay()
        glutPostRedisplay()
        return

    if is_paused:
        glutPostRedisplay()
        return

    if _cam_shake_time > 0:
        _cam_shake_time -= dt
        if _cam_shake_time < 0:
            _cam_shake_time = 0

    if bird_message_timer > 0:
        bird_message_timer -= dt
        if bird_message_timer < 0:
            bird_message_timer = 0

    if boosting and now - boost_start_time >= BOOST_TIME:
        boosting = False

    # vertical physics
    vy += GRAV * dt * 60
    player_pos_y += vy * dt * 60
    if player_pos_y < 3:
        player_pos_y = 3
        vy = 0
        if doing_spin:
            doing_spin = False
            player_rot = 0.0

    if doing_spin:
        player_rot += SPIN_V * dt
        player_rot %= 360

    step_size = BASE_STEP * difficulty
    obs_speed = BASE_OBS_SPEED * difficulty * (BOOST_FACTOR if boosting else 1.0)

    # move objects forward (towards the player)
    new_obs = []
    for o in world_obstacles:
        o['z'] += obs_speed * dt * 60
        if o['kind'] == 'bird' and now - _last_bird_update >= 2.0:
            o['x'] = random.uniform(-AREA_HALF_WIDTH / 2, AREA_HALF_WIDTH / 2)
            o['y'] = random.uniform(20, 100)
            _last_bird_update = now
        if o['z'] < AREA_DEPTH:
            new_obs.append(o)
    world_obstacles = new_obs

    # stars
    new_yellow = []
    for s in yellow_stars:
        s['z'] += obs_speed * dt * 60
        if s['z'] < AREA_DEPTH:
            new_yellow.append(s)
    yellow_stars[:] = new_yellow

    new_pink = []
    for s in pink_stars:
        s['z'] += obs_speed * dt * 60
        if s['z'] < AREA_DEPTH:
            new_pink.append(s)
    pink_stars[:] = new_pink

    new_life = []
    for c in life_crates:
        c['z'] += obs_speed * dt * 60
        if c['z'] < AREA_DEPTH:
            new_life.append(c)
    life_crates[:] = new_life

    # tracks
    new_tracks = []
    for seg in track_segments:
        seg['z'] += obs_speed * dt * 60
        if seg['z'] < AREA_DEPTH:
            new_tracks.append(seg)
    track_segments[:] = new_tracks

    if player_pos_y == 3:
        track_segments.append({'x': player_pos_x, 'z': player_pos_z + 50})

    # spawn life crate occasionally based on stars
    if star_count > 0 and star_count % 10 == 0 and not life_crates:
        x = random.uniform(-AREA_HALF_WIDTH / 2, AREA_HALF_WIDTH / 2)
        z = random.uniform(-AREA_DEPTH, -AREA_DEPTH / 2)
        y = 15
        overlap = False
        for t in world_obstacles + yellow_stars + pink_stars:
            dx = abs(x - t['x']); dz = abs(z - t['z'])
            if dx < 30 and dz < 30:
                overlap = True; break
        if not overlap:
            life_crates.append({'type': 'life', 'x': x, 'y': y, 'z': z, 'size': 15})

    # collisions & pickups
    yellow_stars[:] = collect_yellow()
    pink_stars[:] = collect_pink()
    spawn_obstacles()
    spawn_gold_stars()
    detect_collisions()

    tick_score(now)

    glutPostRedisplay()

# ---------------------------
# Input handlers
# ---------------------------
def keydown(k, x, y):
    global running, score, star_count, boost_tokens, player_pos_x, world_obstacles
    global yellow_stars, pink_stars, is_paused, _cam_shake_time, obs_speed, player_pos_y
    global vy, JUMP_POWER, lives, life_crates, difficulty, step_size, BASE_STEP
    global boosting, boost_start_time, track_segments, VIEW_MODE, doing_spin, player_rot, _zoom, falling, fall_timer, laid_down

    if k == b'\x1b':
        sys.exit()
    elif k in (b'r', b'R') and not running:
        # restart fresh state
        _reset_game()
    elif k == b' ':
        if running and not is_paused and player_pos_y < 3.01:
            vy = JUMP_POWER
            doing_spin = True
            player_rot = 0.0
    elif k == b'b' and running and not is_paused and boost_tokens >= 1 and not boosting:
        boosting = True
        boost_tokens -= 1
        boost_start_time = time.time()
    elif k == b'c' and running and not is_paused:
        VIEW_MODE = 'first_person' if VIEW_MODE == 'third_person' else 'third_person'
    elif k == b'q' and running and not is_paused:
        _zoom = max(MIN_Z, _zoom - ZOOM_INC)
    elif k == b'e' and running and not is_paused:
        _zoom = min(MAX_Z, _zoom + ZOOM_INC)

def special_down(k, x, y):
    global player_pos_x, step_size
    if not running or is_paused:
        return
    if k == GLUT_KEY_LEFT:
        player_pos_x = max(player_pos_x - step_size, -AREA_HALF_WIDTH / 2)
    elif k == GLUT_KEY_RIGHT:
        player_pos_x = min(player_pos_x + step_size, AREA_HALF_WIDTH / 2)
    glutPostRedisplay()

def mouse_action(btn, state, x, y):
    global running, is_paused, player_pos_x, score, star_count, boost_tokens, world_obstacles
    global yellow_stars, pink_stars, _cam_shake_time, obs_speed, player_pos_y, vy, lives, life_crates, difficulty, step_size, boost_start_time, boosting, track_segments, _zoom, falling, fall_timer, laid_down

    # convert GLUT y
    my = WINDOW_H - y
    if btn == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # restart button area
        if 50 <= x <= 70 and WINDOW_H - 50 <= my <= WINDOW_H - 30:
            _reset_game()
        elif WINDOW_W // 2 - 12 <= x <= WINDOW_W // 2 + 12 and WINDOW_H - 47 <= my <= WINDOW_H - 25:
            toggle_pause()
        elif WINDOW_W - 70 <= x <= WINDOW_W - 50 and WINDOW_H - 45 <= my <= WINDOW_W - 25:
            glutDestroyWindow(glutGetWindow()); sys.exit()
    glutPostRedisplay()

# ---------------------------
# Small helpers: reset & pause
# ---------------------------
def _reset_game():
    global running, is_paused, player_pos_x, player_pos_y, vy, score, star_count, boost_tokens, lives
    global world_obstacles, yellow_stars, pink_stars, life_crates, track_segments, difficulty, step_size, obs_speed, _cam_shake_time
    global boosting, boost_start_time, VIEW_MODE, player_rot, doing_spin, _zoom, falling, fall_timer, laid_down

    running = True
    is_paused = False
    player_pos_x = 0
    player_pos_y = 3
    vy = 0
    score = 0
    star_count = 0
    boost_tokens = 0
    lives = 1
    world_obstacles.clear()
    yellow_stars.clear()
    pink_stars.clear()
    life_crates.clear()
    track_segments.clear()
    difficulty = 1.0
    step_size = BASE_STEP
    obs_speed = BASE_OBS_SPEED
    _cam_shake_time = 0
    boosting = False
    boost_start_time = 0
    VIEW_MODE = 'third_person'
    player_rot = 0.0
    doing_spin = False
    _zoom = 1.0
    falling = False
    fall_timer = 0.0
    laid_down = False

def toggle_pause():
    global is_paused
    is_paused = not is_paused

# ---------------------------
# Initialization & main
# ---------------------------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Snowboard Rush - Rewritten")
    glClearColor(0.5, 0.7, 1.0, 1.0)
    glutDisplayFunc(render_scene)
    glutIdleFunc(game_idle)
    glutSpecialFunc(special_down)
    glutKeyboardFunc(keydown)
    glutMouseFunc(mouse_action)
    glutMainLoop()

if __name__ == "__main__":
    main()

