import bpy,math,random
from mathutils import Vector
s=bpy.context.scene
s.world.node_tree.nodes.get('Background')
next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=.8
s.view_settings.exposure=1.0
sun=next(o for o in s.objects if o.type=='LIGHT' and o.data.type=='SUN');sun.data.energy=3.;sun.data.angle=math.radians(5);sun.rotation_euler=(math.radians(28),math.radians(-32),math.radians(-115))
for o in s.objects:
    if any(o.name.startswith('Fuji / '+label) for label in ['Concrete terrace','Seat','Canopy support','Roof truss','Grandstand canopy']):o.location.x+=25
    if o.name.startswith('Fuji / Volcanic mountain'):o.location.x-=470
# Replace triangular trees with rough, smooth foliage masses and trunks.
rng=random.Random(104)
old=[o for o in s.objects if o.name.startswith('Fuji / Distant conifer')]
mat=old[0].data.materials[0]
for o in old:
    loc=o.location.copy();height=o.dimensions.z;bpy.data.objects.remove(o,do_unlink=True)
    for k in range(3):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(loc.x+rng.uniform(-.4,.4),loc.y+rng.uniform(-.4,.4),height*(.30+.23*k)))
        ob=bpy.context.object;ob.name='Fuji / Forest crown';ob.scale=(height*(.25-.045*k),height*(.22-.03*k),height*.29);ob.data.materials.append(mat)
        for p in ob.data.polygons:p.use_smooth=True
        tex=bpy.data.textures.new('Leaf clusters','CLOUDS');tex.noise_scale=.35;mod=ob.modifiers.new('Natural foliage','DISPLACE');mod.texture=tex;mod.strength=.18
# Smooth wheel arch rims mask the discrete cutout edge.
paint=next(m for m in bpy.data.materials if m.name.startswith('Pearl white paint'))
for x in [-1.24,1.24]:
    for sign in [-1,1]:
        cu=bpy.data.curves.new('Wheel arch trim','CURVE');cu.dimensions='3D';cu.bevel_depth=.022;cu.bevel_resolution=3;sp=cu.splines.new('POLY');sp.points.add(48)
        for j,p in enumerate(sp.points):a=j/48*math.pi;p.co=(x+.382*math.cos(a),sign*.876,.37+.382*math.sin(a),1)
        o=bpy.data.objects.new('A1 / Wheel arch lip',cu);s.collection.objects.link(o);cu.materials.append(paint);o['nakedeye_part']=True
s.render.filepath=str(ROOT/'blender/FujiA1-realistic-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/FujiA1.blend'),copy=True)
bpy.ops.render.render(write_still=True)
