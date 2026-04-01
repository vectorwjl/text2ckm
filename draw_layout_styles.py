"""
draw_layout_styles.py — 生成8种建筑排布风格的示意图
"""
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['font.family'] = 'WenQuanYi Zen Hei'
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.transforms import Affine2D
import numpy as np

# ── 颜色 ──────────────────────────────────────────────────────────────────
BG   = '#C8005A'   # 粉红背景（城市用地）
BLDG = '#F0E8C8'   # 建筑（米白）
ROAD = '#D0D0D0'   # 道路（浅灰）
EDGE = '#9A8A50'   # 建筑描边


# ── 基础绘图函数 ──────────────────────────────────────────────────────────

def _road(ax, x1, y1, x2, y2, w=8):
    dx, dy = x2-x1, y2-y1
    L = np.hypot(dx, dy)
    if L < 0.1:
        return
    cx, cy = (x1+x2)/2, (y1+y2)/2
    angle = np.degrees(np.arctan2(dy, dx))
    p = mpatches.Rectangle((-L/2, -w/2), L, w,
                            linewidth=0, facecolor=ROAD, zorder=1)
    p.set_transform(Affine2D().rotate_deg(angle).translate(cx, cy) + ax.transData)
    ax.add_patch(p)


def _bldg(ax, cx, cy, w, h, angle=0, color=BLDG):
    p = mpatches.Rectangle((-w/2, -h/2), w, h,
                            linewidth=0.6, edgecolor=EDGE,
                            facecolor=color, zorder=2)
    p.set_transform(Affine2D().rotate_deg(angle).translate(cx, cy) + ax.transData)
    ax.add_patch(p)


def _setup(ax, title):
    ax.set_facecolor(BG)
    ax.set_xlim(-105, 105)
    ax.set_ylim(-105, 105)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=11, fontweight='bold', color='white', pad=6)


# ── 1. 方格网式 ────────────────────────────────────────────────────────────

def draw_orthogonal(ax):
    _setup(ax, '① 方格网式\nOrthogonal Grid')
    rw = 9
    # 纵向道路 x = -42, 0, 42
    for x in (-42, 0, 42):
        _road(ax, x, -105, x, 105, rw)
    # 横向道路 y = -42, 42
    for y in (-42, 42):
        _road(ax, -105, y, 105, y, rw)

    # 6个街区，每块2~3栋建筑（轴对齐）
    blocks = [
        # (block_cx, block_cy, buildings列表 [(dx,dy,w,h), ...])
        (-72,  72, [(-8,  8, 25, 18), ( 8, -8, 18, 22)]),
        (  0,  72, [(-8,  8, 22, 16), ( 8, -8, 16, 20), (0, 0, 0, 0)]),
        ( 72,  72, [(-6,  7, 24, 17), ( 6, -7, 17, 21)]),
        (-72, -72, [(-7, -7, 26, 19), ( 7,  7, 19, 14)]),
        (  0, -72, [(-8, -6, 23, 18), ( 8,  6, 16, 22)]),
        ( 72, -72, [(-6, -7, 25, 16), ( 6,  7, 18, 20)]),
    ]
    for bx, by, blist in blocks:
        for dx, dy, w, h in blist:
            if w > 0:
                _bldg(ax, bx+dx, by+dy, w, h, angle=0)


# ── 2. 斜交网格式 ─────────────────────────────────────────────────────────

def draw_rotated_grid(ax):
    _setup(ax, '② 斜交网格式\nRotated Block Grid')
    θ = 32.0
    rw = 8
    cr, sr = np.cos(np.radians(θ)), np.sin(np.radians(θ))
    # along = (cr, sr),  perp = (-sr, cr)

    span = 130
    # 纵向路：沿 along，在 perp 方向偏移 k*55
    for k in (-1, 0, 1):
        ox, oy = k*55*(-sr), k*55*cr
        _road(ax, ox - span*cr, oy - span*sr,
                  ox + span*cr, oy + span*sr, rw)
    # 横向路：沿 perp，在 along 方向偏移 m*50
    for m in (-1, 1):
        ox, oy = m*50*cr, m*50*sr
        _road(ax, ox - span*(-sr), oy - span*cr,
                  ox + span*(-sr), oy + span*cr, rw)

    # 4 个街区，每块 2~3 栋，rotation=θ
    block_centers = [(-55*(-sr) + (-50)*cr, -55*cr + (-50)*sr),
                     ( 55*(-sr) + (-50)*cr,  55*cr + (-50)*sr),
                     (-55*(-sr) + ( 50)*cr, -55*cr + ( 50)*sr),
                     ( 55*(-sr) + ( 50)*cr,  55*cr + ( 50)*sr)]
    dims = [(24, 16), (18, 22), (20, 14), (26, 18)]
    offsets = [(-8, 8), (8, -8)]
    for (bx, by), (w, h) in zip(block_centers, dims):
        for dpar, dperp in offsets:
            cx = bx + dpar*cr + dperp*(-sr)
            cy = by + dpar*sr + dperp*cr
            _bldg(ax, cx, cy, w, h, angle=θ)


# ── 3. 行列式 ─────────────────────────────────────────────────────────────

def draw_slab_row(ax):
    _setup(ax, '③ 行列式\nSlab Row')
    # 2条平行横向道路
    _road(ax, -105, -28, 105, -28, 9)
    _road(ax, -105,  28, 105,  28, 9)
    # 1条纵向主干道
    _road(ax, 0, -105, 0, 105, 8)

    # 4排长条建筑
    rows = [
        # y中心, angle, 建筑列表 [(cx, w, h), ...]
        ( 65, 0, [(-55, 32, 18), (-15, 28, 16), ( 22, 35, 20), ( 68, 25, 17)]),
        ( 68, 0, []),  # placeholder
        (-65, 0, [(-55, 30, 16), (-12, 33, 19), ( 25, 28, 16), ( 68, 30, 18)]),
    ]
    # 3排，稍微错位
    for y_base, bldgs in [
        ( 62, [(-52, 30, 16), (-14, 26, 18), ( 20, 32, 20), ( 66, 24, 16)]),
        ( 78, [(-60, 25, 13), (-30, 20, 15), (  5, 28, 14), ( 50, 22, 16)]),
        (-62, [(-52, 30, 16), (-14, 26, 18), ( 20, 32, 20), ( 66, 24, 16)]),
        (-78, [(-58, 24, 12), (-28, 22, 16), (  8, 27, 14), ( 52, 20, 15)]),
    ]:
        for cx, w, h in bldgs:
            _bldg(ax, cx, y_base, w, h, angle=0)


# ── 4. 点式散布 ───────────────────────────────────────────────────────────

def draw_point_scatter(ax):
    _setup(ax, '④ 点式散布\nPoint Block Scatter')
    rng = np.random.default_rng(42)
    # 几条短路段
    _road(ax, -105, 0, 105, 0, 7)
    _road(ax, 0, -105, 0, 105, 7)
    # 12栋独立建筑，各自随机旋转
    positions = [(-75,70), (-40,80), (20,85), (72,65), (85,20),
                 (75,-55), (30,-80), (-25,-75), (-78,-60), (-88,10),
                 (-10,35), (45,-20)]
    dims = [(22,18),(16,26),(20,14),(18,22),(24,16),
            (14,20),(22,18),(16,24),(20,16),(18,18),
            (28,22),(18,14)]
    angles = rng.uniform(0, 360, len(positions))
    for (px,py),(w,h),ang in zip(positions, dims, angles):
        _bldg(ax, px, py, w, h, angle=float(ang))


# ── 5. 围合式/庭院式 ──────────────────────────────────────────────────────

def _perimeter_block(ax, cx, cy, ow, ol, tw, angle=0):
    """绘制一个围合式街区：四面建筑围合，中央留空。"""
    # 北/南翼（沿X轴）
    for sign in (-1, 1):
        # 南/北 条（宽全width，薄）
        dy = sign * (ol/2 - tw/2)
        _bldg(ax, cx + dy*np.sin(np.radians(angle)),
                  cy + dy*np.cos(np.radians(angle)),
                  ow, tw, angle=angle)
    # 东/西翼（沿Y轴，中段，避免角部重叠）
    inner_len = ol - 2*tw
    for sign in (-1, 1):
        dx = sign * (ow/2 - tw/2)
        _bldg(ax, cx + dx*np.cos(np.radians(angle)),
                  cy - dx*np.sin(np.radians(angle)),
                  tw, inner_len, angle=angle)


def draw_perimeter(ax):
    _setup(ax, '⑤ 围合式/庭院式\nPerimeter Block')
    _road(ax, -105, 0, 105, 0, 8)
    _road(ax, 0, -105, 0, 105, 8)
    _road(ax, -105, -50, 105, -50, 7)
    _road(ax, -105,  50, 105,  50, 7)
    _road(ax,  -50, -105, -50, 105, 7)
    _road(ax,   50, -105,  50, 105, 7)

    for cx, cy in [(-75, 75), (75, 75), (-75, -75), (75, -75)]:
        _perimeter_block(ax, cx, cy, ow=44, ol=44, tw=10, angle=0)


# ── 6. 放射状 ─────────────────────────────────────────────────────────────

def draw_radial(ax):
    _setup(ax, '⑥ 放射状\nRadial')
    # 6条放射路，间隔60°
    for ang_deg in range(0, 360, 60):
        a = np.radians(ang_deg)
        ex, ey = 110*np.cos(a), 110*np.sin(a)
        _road(ax, 0, 0, ex, ey, 8)

    # 沿每条路在两侧放置建筑
    bldg_params = [
        (14,12),(20,16),(18,14),(22,18),(16,12),(24,16),
        (18,14),(20,12),(16,18),(22,14),(14,16),(20,18),
        (24,14),(16,12),(18,16),(22,18),(14,20),(20,14),
        (18,12),(16,18),(22,14),(24,16),(14,14),(20,18),
    ]
    idx = 0
    for ang_deg in range(0, 360, 60):
        a = np.radians(ang_deg)
        pa = a + np.pi/2
        for dist in (40, 72):
            for side in (-1, 1):
                cx = dist*np.cos(a) + side*14*np.cos(pa)
                cy = dist*np.sin(a) + side*14*np.sin(pa)
                w, h = bldg_params[idx % len(bldg_params)]
                idx += 1
                _bldg(ax, cx, cy, w, h, angle=ang_deg)


# ── 7. 簇状/组团式 ────────────────────────────────────────────────────────

def draw_cluster(ax):
    _setup(ax, '⑦ 簇状/组团式\nCluster')
    # 4个组团，之间有内部小路
    clusters = [
        (-58,  58, [(-10, 8,20,14,5), (10,-8,16,18,10), (-8,-12,14,12,-5)]),
        ( 58,  58, [(  8, 8,18,16,8), (-10,-8,22,14,-3), (8,-14,15,11,12)]),
        (-58, -58, [(-8,-10,20,15,8), (10, 8,17,19,3), (-8, 12,13,14,-8)]),
        ( 58, -58, [(10,-8,21,14,-5), (-8,10,16,18,7), (8,  8,14,12, 15)]),
    ]
    # 组团间连接路
    _road(ax, -105,  0, 105,  0, 6)
    _road(ax,    0,-105,   0, 105, 6)
    _road(ax,  -30, 30, 30,  30, 5)
    _road(ax,  -30,-30, 30, -30, 5)
    _road(ax,   30,-30, 30,  30, 5)
    _road(ax,  -30,-30,-30,  30, 5)

    for cx, cy, blist in clusters:
        for dx, dy, w, h, ang in blist:
            _bldg(ax, cx+dx, cy+dy, w, h, angle=ang)


# ── 8. 有机/不规则式 ──────────────────────────────────────────────────────

def draw_organic(ax):
    _setup(ax, '⑧ 有机/不规则式\nOrganic / Irregular')
    # 弯曲道路用多段折线近似
    def curved_road(ax, pts, w=7):
        for i in range(len(pts)-1):
            x1,y1 = pts[i]; x2,y2 = pts[i+1]
            _road(ax, x1, y1, x2, y2, w)

    curved_road(ax, [(-105,-60),(-60,-40),(-20,-10),(30,20),(80,55),(105,70)], 8)
    curved_road(ax, [(-80, 105),(-50,65),(-10,30),(20,-10),(50,-50),(70,-105)], 8)
    curved_road(ax, [(-105,30),(-55,20),(0,0),(55,-15),(105,-25)], 7)

    # 不规则建筑，各自不同角度和尺寸
    buildings = [
        (-80,  80, 22, 15, 25), (-45,  70, 18, 24, -15), (-10,  85, 25, 12, 40),
        ( 35,  75, 16, 20, -30),( 75,  85, 22, 14, 10), ( 88,  40, 14, 26, 55),
        ( 70,  -5, 24, 18, -20),( 40, -35, 18, 22, 35), ( 80, -75, 20, 16, -45),
        (  0, -50, 26, 14, 15), (-40, -65, 20, 18, -25),(-80, -45, 16, 24, 60),
        (-70,  15, 18, 20, -10),( 10,  15, 22, 16, 45), (-30,  40, 14, 18, -35),
    ]
    for cx, cy, w, h, ang in buildings:
        _bldg(ax, cx, cy, w, h, angle=ang)


# ── 主函数 ────────────────────────────────────────────────────────────────

def main():
    fig, axes = plt.subplots(2, 4, figsize=(22, 11))
    fig.patch.set_facecolor('#18182A')
    fig.suptitle('建筑排布风格 — 8种类别示意图', fontsize=15,
                 color='white', fontweight='bold', y=1.01)

    draw_fns = [
        draw_orthogonal,
        draw_rotated_grid,
        draw_slab_row,
        draw_point_scatter,
        draw_perimeter,
        draw_radial,
        draw_cluster,
        draw_organic,
    ]

    for ax, fn in zip(axes.flat, draw_fns):
        fn(ax)

    plt.tight_layout(pad=1.8)
    out = 'layout_styles.png'
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#18182A')
    print(f'Saved: {out}')
    plt.close()


if __name__ == '__main__':
    main()
