"""Remove the region markers, dashed leader lines and labels from the reference
figure, and export a transparent PNG of the body for the joint-count screen."""
import cv2, numpy as np, sys

SRC = sys.argv[1]
im = cv2.imread(SRC)
CROP = (95, 1400, 330, 850)                      # y0, y1, x0, x1
MARKERS = [(475, 337), (430, 560), (388, 776), (507, 976), (479, 1286)]
SHIFT_MARKERS = []
MIRROR_COPY = [(693, 750)]                   # hip: direct mirrored copy (symmetric shorts edge)
INPAINT_MARKERS = []
CENTRE_MARKER = (589, 643)                        # lumbar: on the midline, no clean mirror
LABELS = [(120, 40, 510, 92), (195, 312, 340, 362), (235, 538, 340, 582), (140, 752, 345, 800),
          (248, 952, 345, 1000), (150, 1268, 345, 1318), (845, 592, 1045, 665), (845, 742, 905, 788)]
SHORTS = (665, 852, 458, 728)          # y0, y1, x0, x1 in source coords (protected)

def purple_mask(img, s_min=30, v_min=95):
    h, s, v = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2HSV))
    return ((h >= 122) & (h <= 168) & (s > s_min) & (v > v_min))

out = im.copy()
for x0, y0, x1, y1 in LABELS:
    out[y0:y1, x0:x1] = 255

lines = cv2.dilate(purple_mask(im).astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=2)
circ = np.zeros_like(lines)
for x, y in MARKERS + MIRROR_COPY + [c for c, _ in SHIFT_MARKERS] + [CENTRE_MARKER]:
    cv2.circle(circ, (x, y), 31, 255, -1)

# 1) dashed lines: copy the mirror-image pixels where the mirror side is clean
flip = cv2.flip(out, 1)
bad = (lines > 0) | (circ > 0)
badf = cv2.flip(bad.astype(np.uint8), 1) > 0
L = (lines > 0) & (circ == 0)
out[L & ~badf] = flip[L & ~badf]
out = cv2.inpaint(out, (L & badf).astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA)

# 2) markers: Poisson-blend the cleaned mirror side in
flip = cv2.flip(out, 1)
for x, y in MARKERS:
    m = np.zeros(im.shape[:2], np.uint8)
    cv2.circle(m, (x, y), 33 if y > 1200 else 31, 255, -1)
    out = cv2.seamlessClone(flip, out, m, (x, y), cv2.NORMAL_CLONE)
for x, y in MIRROR_COPY:
    m = np.zeros(im.shape[:2], np.uint8); cv2.circle(m, (x, y), 31, 255, -1)
    out[m > 0] = flip[m > 0]
for (x, y), dy in SHIFT_MARKERS:
    m = np.zeros(im.shape[:2], np.uint8); cv2.circle(m, (x, y), 31, 255, -1)
    src = np.roll(out, dy, axis=0); out[m > 0] = src[m > 0]
m = np.zeros(im.shape[:2], np.uint8)
for c in INPAINT_MARKERS + [CENTRE_MARKER]: cv2.circle(m, c, 31, 255, -1)
out = cv2.inpaint(out, m, 10, cv2.INPAINT_TELEA)

# 3) any purple left (dash ends at the silhouette), never inside the shorts
h_, s_, v_ = cv2.split(cv2.cvtColor(out, cv2.COLOR_BGR2HSV))
left = purple_mask(out, 22, 70) | ((h_ >= 115) & (s_ > 18) & (v_ > 90))
sy0, sy1, sx0, sx1 = SHORTS
left[sy0:sy1, sx0:sx1] = False
left = cv2.dilate(left.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=2) > 0

y0, y1, x0, x1 = CROP
crop = out[y0:y1, x0:x1].copy(); leftc = left[y0:y1, x0:x1]

# 4) background = bright, unsaturated region connected to the border
hs = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
cand = ((hs[..., 1] < 45) & (hs[..., 2] > 170)).astype(np.uint8)
n, lab = cv2.connectedComponents(cand, connectivity=4)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
bg = np.isin(lab, list(border))
a = np.where(bg, 0, 255).astype(np.uint8)

edge = cv2.dilate((a < 128).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
a[leftc & edge] = 0
crop = cv2.inpaint(crop, (leftc & ~edge).astype(np.uint8) * 255, 4, cv2.INPAINT_TELEA)

# 5) keep only the figure itself
fg = cv2.morphologyEx((a > 40).astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(fg, 8)
keep = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
a[cv2.dilate(keep, np.ones((7, 7), np.uint8)) == 0] = 0
n, lab, st, _ = cv2.connectedComponentsWithStats((a > 40).astype(np.uint8), 8)
big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); a[(lab != big) & (lab > 0)] = 0
a = cv2.morphologyEx(a, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
a = cv2.GaussianBlur(a, (3, 3), 0)

cv2.imwrite("body_clean.png", np.dstack([crop, a]))
al = a[..., None] / 255.0
cv2.imwrite("clean_crop.png", (crop * al + 255 * (1 - al)).astype(np.uint8))
print("ok", crop.shape)
