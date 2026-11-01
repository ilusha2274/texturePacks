"""Рисует текстуры 16x16 для пака Маньяка и превью-лист. Без PIL: свой PNG-кодер."""
import os
import struct
import sys
import zlib

OUT = sys.argv[1]
PREVIEW = sys.argv[2]
N = 16


def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


T = (0, 0, 0, 0)


def blank(w=N, h=N):
    return [[T for _ in range(w)] for _ in range(h)]


def write_png(path, img):
    h = len(img)
    w = len(img[0])
    raw = b''.join(b'\x00' + b''.join(bytes(px) for px in row) for row in img)

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)

    data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(data)


def grid(rows, pal):
    assert len(rows) == N, len(rows)
    img = blank()
    for y, row in enumerate(rows):
        assert len(row) == N, (y, row, len(row))
        for x, ch in enumerate(row):
            if ch != '.':
                img[y][x] = pal[ch]
    return img


def diag(rule, outline=None):
    """rule(u, p) -> цвет или None. u — вдоль оси (низ-лево -> верх-право), p — поперёк (+ к низ-право)."""
    img = blank()
    for y in range(N):
        for x in range(N):
            u = x - y
            p = x + y - 15
            c = rule(u, p)
            if c is not None:
                img[y][x] = c
    if outline:
        add_outline(img, outline)
    return img


def add_outline(img, color):
    filled = [[img[y][x][3] > 0 for x in range(N)] for y in range(N)]
    for y in range(N):
        for x in range(N):
            if filled[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < N and 0 <= ny < N and filled[ny][nx]:
                    img[y][x] = color
                    break


def shade(c, k):
    return (min(255, int(c[0] * k)), min(255, int(c[1] * k)), min(255, int(c[2] * k)), c[3])


# ---------------------------------------------------------------- аптечка
MEDKIT = grid([
    "................",
    "................",
    ".....DDDDDD.....",
    ".....DMMMMD.....",
    ".DDDDDDDDDDDDDD.",
    ".DLLLLLLLLLLLLD.",
    ".DLRRRRWWRRRRSD.",
    ".DLRRRRWWRRRRSD.",
    ".DLRRWWWWWWRRSD.",
    ".DLRRGGWWGGRRSD.",
    ".DLRRRRWWRRRRSD.",
    ".DLRRRRGGRRRRSD.",
    ".DLRRRRRRRRRRSD.",
    ".DSSSSSSSSSSSSD.",
    ".DDDDDDDDDDDDDD.",
    "................",
], {
    'D': hexc('4a0d10'), 'M': hexc('2a2a2a', 0),
    'L': hexc('f0605a'), 'R': hexc('d42a2a'), 'S': hexc('961a1c'),
    'W': hexc('ffffff'), 'G': hexc('d9d9e0'),
})
# ручка — прозрачная внутри
for x in range(6, 10):
    MEDKIT[3][x] = T

# ---------------------------------------------------------------- канистра бензина
FUEL = grid([
    "................",
    "..DDDDD.....DD..",
    "..D...D....DMMD.",
    ".DDDDDDDDDDDMDD.",
    ".DLLLLLLLLLLLRD.",
    ".DLRRRRRRRRRRSD.",
    ".DLRXRRRRRRXRSD.",
    ".DLRRXRRRRXRRSD.",
    ".DLRRRXRRXRRRSD.",
    ".DLRRRRXXRRRRSD.",
    ".DLRRRXRRXRRRSD.",
    ".DLRRXRRRRXRRSD.",
    ".DLRXRRRRRRXRSD.",
    ".DLRRRRRRRRRRSD.",
    ".DSSSSSSSSSSSSD.",
    ".DDDDDDDDDDDDDD.",
], {
    'D': hexc('3d0b0a'), 'M': hexc('a8a8a8'),
    'L': hexc('ec6a52'), 'R': hexc('c8281e'), 'S': hexc('8a1612'), 'X': hexc('8f1a15'),
})


# ---------------------------------------------------------------- адреналин (шприц)
def syringe(u, p):
    ap = abs(p)
    if 6 <= u <= 13 and p == 0:
        return hexc('e8eef2') if u >= 12 else hexc('b8c2c8')
    if 4 <= u <= 5 and ap <= 1:
        return hexc('5a6670')
    if -7 <= u <= 3 and ap <= 2:
        if u in (-7, 3) or ap == 2:
            return hexc('31414f')
        if u >= -3:
            if p == -1:
                return hexc('ffb3ef')
            if p == 1:
                return hexc('c2329c')
            return hexc('ff5fd2')
        return hexc('dceff6') if p <= 0 else hexc('a9c4d0')
    if -11 <= u <= -8 and p == 0:
        return hexc('9aa4aa')
    if -13 <= u <= -12 and ap <= 2:
        return hexc('31414f') if ap == 2 else hexc('c9d2d8')
    return None


ADRENALINE = diag(syringe)


# ---------------------------------------------------------------- газовый ключ
def wrench(u, p):
    ap = abs(p)
    steel_l, steel, steel_d = hexc('e4e9ee'), hexc('a8b2ba'), hexc('6c7781')
    # рукоять: красная, с концевой заглушкой
    if -14 <= u <= -1 and ap <= 1:
        if u <= -13:
            return hexc('2e2e2e')
        return {-1: hexc('e2533f'), 0: hexc('b42318'), 1: hexc('701309')}[p]
    # стальной корпус до головы
    if 0 <= u <= 9 and ap <= 1:
        return {-1: steel_l, 0: steel, 1: steel_d}[p]
    # неподвижная губка-крюк на конце
    if 8 <= u <= 10 and -6 <= p <= -2:
        if u == 8 and p in (-5, -3):
            return hexc('3a4148')  # зубья в пасть
        return steel_l if u == 9 else steel
    # подвижная губка
    if 2 <= u <= 4 and -5 <= p <= -2:
        if u == 4 and p in (-4, -2):
            return hexc('3a4148')
        return steel if u < 4 else steel_l
    # гайка-барашек (насечка)
    if 4 <= u <= 7 and p == -2:
        return hexc('5d666e') if u % 2 else hexc('c3cbd2')
    return None


GAS_WRENCH = diag(wrench, outline=hexc('22262b'))


# ---------------------------------------------------------------- меч
def sword(u, p):
    ap = abs(p)
    if 13 <= u <= 14 and p == 0:
        return hexc('d6d6d6')
    if -3 <= u <= 12 and ap <= 1:
        return {-1: hexc('d0d0d0'), 0: hexc('9a9a9a'), 1: hexc('5f5f5f')}[p]
    if -5 <= u <= -4 and ap <= 3:
        return hexc('6b4a2a') if ap < 3 else hexc('3b2614')
    if -11 <= u <= -6 and ap <= 1:
        return hexc('8a5a30') if p <= 0 else hexc('5a3518')
    if -13 <= u <= -12 and ap <= 1:
        return hexc('4a4a4a')
    return None


SWORD = diag(sword, outline=hexc('262626'))


# ---------------------------------------------------------------- арбалет
def limb_u(p):
    return 3 - (p * p) // 14


def crossbow(loaded):
    def rule(u, p):
        ap = abs(p)
        if loaded:
            # наконечник
            if 9 <= u <= 11 and ap <= 11 - u:
                return hexc('dfe6ea') if p <= 0 else hexc('7d878d')
            # древко поверх ложа
            if -6 <= u <= 8 and p == 0:
                return hexc('e0bf86')
            # оперение
            if -7 <= u <= -5 and ap == 1:
                return hexc('f4f4f4')
        # дуги: толстые, к концам — железные
        if ap <= 9:
            lu = limb_u(p)
            if lu - 2 <= u <= lu:
                if ap >= 8:
                    return hexc('3c4046')
                return hexc('8a5c30') if u == lu else hexc('5a3a1c')
        # тетива
        if ap <= 7:
            tip = limb_u(8) - 2
            su = (-5 + round(ap * (tip + 5) / 8)) if loaded else tip
            if su - 1 <= u <= su:
                return hexc('cfc6b0')
        # ложе
        if -13 <= u <= 3 and ap <= 1:
            if u <= -12:
                return hexc('3e2410')
            return {-1: hexc('b07a42'), 0: hexc('84562c'), 1: hexc('55361a')}[p]
        if -9 <= u <= -7 and 2 <= p <= 3:
            return hexc('3c4046')  # спуск
        return None
    img = diag(rule, outline=hexc('241a12'))
    # Ванильные повороты модели арбалета в руке рассчитаны на текстуру, где перед смотрит в
    # верхний ЛЕВЫЙ угол, а рукоять - в нижний правый. Рисуем в своих координатах и зеркалим.
    return [list(reversed(row)) for row in img]


CROSSBOW_ARROW = crossbow(True)
CROSSBOW_STANDBY = crossbow(False)

# ---------------------------------------------------------------- динамит (блок)
STICK = [hexc('6e1410'), hexc('c0261c'), hexc('e0442e'), hexc('9c1c14')]  # по 4 колонки на шашку
TAPE = hexc('2a2622')
TAPE_L = hexc('4a443c')


def dynamite_side(glow):
    img = blank()
    for y in range(N):
        for x in range(N):
            c = STICK[x % 4]
            if y in (0, 15):
                c = shade(c, 0.75)
            if 6 <= y <= 9:
                c = TAPE_L if y == 6 else TAPE
                if 7 <= y <= 8 and 5 <= x <= 10:
                    c = hexc('e8d9a8') if y == 7 else hexc('c4b484')
            elif glow:
                # «тлеет»: тёплое свечение снизу вверх
                k = 1.0 + glow * (1.0 - abs(y - 7.5) / 8.0) * 0.35
                c = shade(c, k)
            img[y][x] = c
    # значок-«!» на этикетке
    for x, y in ((7, 7), (8, 7)):
        img[y][x] = hexc('b01e14')
    return img


def dynamite_top(spark, with_fuse=True):
    img = blank()
    ring = {(1, 0), (2, 0), (0, 1), (0, 2), (3, 1), (3, 2), (1, 3), (2, 3)}
    for cy in range(4):
        for cx in range(4):
            for dy in range(4):
                for dx in range(4):
                    x, y = cx * 4 + dx, cy * 4 + dy
                    if (dx, dy) in ring:
                        # бумага шашки: свет сверху-слева, тень снизу-справа
                        c = hexc('d8382a') if dx + dy <= 2 else hexc('8e1a14')
                    elif dx in (1, 2) and dy in (1, 2):
                        c = hexc('9c6a3c') if (dx, dy) != (1, 1) else hexc('c0915a')  # торец
                    else:
                        c = hexc('1e0806')  # щель между шашками
                    img[y][x] = c
    if with_fuse:
        # фитиль торчит из щели в центре, кончик искрит
        for x, y in ((7, 7), (8, 8), (8, 7), (7, 8)):
            img[y][x] = hexc('4a4a4a')
        sparks = [
            [((7, 7), 'fff6c0'), ((8, 8), 'ff9a1a'), ((6, 6), 'ffd040')],
            [((8, 7), 'ffe060'), ((7, 8), 'ff5a10'), ((9, 6), 'fff6c0')],
            [((8, 8), 'fff6c0'), ((7, 7), 'ff9a1a'), ((9, 9), 'ffb030')],
            [((7, 8), 'ffe060'), ((8, 7), 'ff5a10'), ((6, 9), 'fff6c0')],
        ][spark]
        for (x, y), h in sparks:
            img[y][x] = hexc(h)
    return img


def strip(frames):
    out = []
    for f in frames:
        out.extend(f)
    return out


TEXTURES = {
    'medkit': MEDKIT,
    'fuel': FUEL,
    'adrenaline': ADRENALINE,
    'gas_wrench': GAS_WRENCH,
    'sword': SWORD,
    'crossbow_arrow': CROSSBOW_ARROW,
    'crossbow_standby': CROSSBOW_STANDBY,
    'dynamite_side': strip([dynamite_side(g) for g in (0.0, 0.5, 1.0, 0.5)]),
    'dynamite_top': strip([dynamite_top(s) for s in range(4)]),
    'dynamite_bottom': dynamite_top(0, with_fuse=False),
}

os.makedirs(OUT, exist_ok=True)
for name, img in TEXTURES.items():
    write_png(os.path.join(OUT, name + '.png'), img)

# превью: каждый первый кадр x12 на сером фоне, в ряд
SCALE = 12
GAP = 4
names = list(TEXTURES)
W = len(names) * (N * SCALE + GAP) + GAP
H = N * SCALE + 2 * GAP
sheet = [[hexc('8c8c8c') for _ in range(W)] for _ in range(H)]
for i, name in enumerate(names):
    img = TEXTURES[name]
    ox = GAP + i * (N * SCALE + GAP)
    for y in range(N * SCALE):
        for x in range(N * SCALE):
            px = img[y // SCALE][x // SCALE]
            if px[3]:
                sheet[GAP + y][ox + x] = px
            elif ((x // 6) + (y // 6)) % 2:
                sheet[GAP + y][ox + x] = hexc('7a7a7a')
write_png(PREVIEW, sheet)
print('ok:', ', '.join(names))
