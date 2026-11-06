import bpy, json, math, os, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

OBJ = "/home/claude/assets/base.obj"
OUT = "/home/claude/blender/out_mh"
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=OBJ, use_split_groups=True)
objs = {o.name: o for o in bpy.context.scene.objects}

def center(name):
    o = objs[name]
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    return sum(vs, Vector()) / len(vs)

body = objs["body"]
for n, o in objs.items():
    if o is not body:
        o.hide_render = True; o.hide_viewport = True

# skin material
m = bpy.data.materials.new("skin"); m.use_nodes = True
nt = m.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.70, 0.35, 0.21, 1)
b.inputs["Roughness"].default_value = 0.58
b.inputs["Subsurface Weight"].default_value = 0.35
b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
b.inputs["Subsurface Scale"].default_value = 0.4
b.inputs["Specular IOR Level"].default_value = 0.25
# subtle skin micro-bump
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 220; noise.inputs["Detail"].default_value = 6
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.06; bump.inputs["Distance"].default_value = 0.002
nt.links.new(noise.outputs["Fac"], bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
body.data.materials.clear(); body.data.materials.append(m)
for p in body.data.polygons: p.use_smooth = True
sub = body.modifiers.new("sub", "SUBSURF"); sub.levels = 2; sub.render_levels = 3

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 96; sc.cycles.use_denoising = True
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "Medium Contrast"; sc.view_settings.exposure = -0.95
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

cam_d = bpy.data.cameras.new("cam"); cam_d.type = "ORTHO"
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x = 900; sc.render.resolution_y = 1100

def light(name, kind="AREA"):
    l = bpy.data.lights.new(name, kind); o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); return o
key = light("key"); fill = light("fill"); rim = light("rim")

import bmesh
print("R hand x:", center("joint-r-hand").x)
base_mesh = body.data.copy()
result = {}
for side in ("r", "l"):
    me = base_mesh.copy(); body.data = me
    w0 = center(f"joint-{side}-hand"); el = center(f"joint-{side}-elbow")
    bm = bmesh.new(); bm.from_mesh(me)
    inv = body.matrix_world.inverted()
    w0l = inv @ w0; ell = inv @ el
    axis = (w0l - ell).normalized()
    kill = [v for v in bm.verts if (v.co - w0l).dot(axis) < -0.9 or (v.co - w0l).length > 3.2]
    print(side, "kept", len(bm.verts) - len(kill), "of", len(bm.verts))
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(me); bm.free()
    wrist = center(f"joint-{side}-hand")
    mcp = {d: center(f"joint-{side}-finger-{d}-1") for d in range(2, 6)}
    jn = {}
    # fingers 2-5: -1 MCP, -2 PIP ; thumb: -2 MCP, -3 IP
    for d in range(2, 6):
        jn[f"MCP{d}"] = center(f"joint-{side}-finger-{d}-1")
        jn[f"PIP{d}"] = center(f"joint-{side}-finger-{d}-2")
    jn["MCP1"] = center(f"joint-{side}-finger-1-2")
    jn["PIP1"] = center(f"joint-{side}-finger-1-3")
    jn["WR"] = wrist
    tip3 = center(f"joint-{side}-finger-3-4")
    up = (tip3 - wrist).normalized()
    across = (mcp[2] - mcp[5]).normalized()
    nrm = across.cross(up).normalized()
    # dorsal side faces world +Z in the A-pose (palms down)
    # right hand: (index-little) x (wrist->tip) points to the palm; left hand: to the back
    if side == "r": nrm = -nrm
    right = up.cross(nrm).normalized()
    up = nrm.cross(right).normalized()
    span = (tip3 - wrist).length
    ctr = (wrist + tip3) / 2 + up * span * 0.04
    rot = Matrix((right, up, nrm)).transposed().to_4x4()
    cam_d.ortho_scale = span * 1.55
    cam.matrix_world = Matrix.Translation(ctr + nrm * 20.0) @ rot
    # lights relative to hand frame
    for o, (dx, dy, dz, size, power) in ((key, (-0.6, 0.6, 1.0, 1.2, 260)), (fill, (0.8, -0.2, 0.8, 1.8, 110)), (rim, (0.0, 0.9, -0.3, 1.0, 160))):
        pos = ctr + (right * dx + up * dy + nrm * dz) * span * 1.6
        o.location = pos; o.data.size = size; o.data.energy = power
        o.rotation_euler = (ctr - pos).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, f"hand_{side}.png")
    bpy.ops.render.render(write_still=True)
    pts = {}
    for k, p in jn.items():
        c = world_to_camera_view(sc, cam, p + nrm * 0.0)
        pts[k] = [round(c.x, 4), round(1 - c.y, 4)]
    result[side.upper()] = pts

json.dump(result, open(os.path.join(OUT, "hand_joints.json"), "w"), indent=1)
print("DONE")
