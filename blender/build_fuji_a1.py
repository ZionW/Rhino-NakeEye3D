import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
d=json.loads((ROOT/'demos/fuji_a1.json').read_text())
s=bpy.data.scenes.new('裸視3D • FUJI / A1');bpy.context.window.scene=s
s.render.engine='CYCLES';s.cycles.samples=16;s.render.resolution_x=1280;s.render.resolution_y=800;s.render.resolution_percentage=75
s.world=bpy.data.worlds.new('Fuji night scan');s.world.use_nodes=True
next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND').inputs[0].default_value=(.0003,.002,.005,1);next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND').inputs[1].default_value=.1
s.view_settings.view_transform='Standard';s.view_settings.exposure=-.6
axes=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
tris=[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]
def dots(name,points,colors,size,power,part=False):
    verts=[];faces=[]
    for p in points:
        k=len(verts);verts.extend([tuple(p[i]+a[i]*size for i in range(3)) for a in axes]);faces.extend([tuple(k+j for j in t) for t in tris])
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
    a=m.color_attributes.new(name='ScanColor',type='FLOAT_COLOR',domain='POINT')
    for i,c in enumerate(colors):
        for j in range(6):a.data[i*6+j].color=(*c,1)
    mat=bpy.data.materials.new(name+' neon');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');v=n.new('ShaderNodeAttribute');v.attribute_name='ScanColor';e.inputs[1].default_value=power
    mat.node_tree.links.new(v.outputs['Color'],e.inputs[0]);mat.node_tree.links.new(e.outputs[0],out.inputs[0]);m.materials.append(mat)
    o=bpy.data.objects.new(name,m);s.collection.objects.link(o)
    if part:
        center=sum((Vector(p) for p in points),Vector())/len(points)
        for v in m.vertices:v.co-=center
        o.location=center;o['nakedeye_part']=True
    return o
for key,label in [('body','A1 • Body and livery'),('stem','A1 • Wheels'),('leaf','A1 • Glass')]:dots(label,d['parts'][key],d['colors'][key],.0065,2.3,True)
dots('Fuji • Track stands and mountain',d['environment'],d['environment_colors'],.013,1.3)
cam=bpy.data.objects.new('Fuji observer',bpy.data.cameras.new('Fuji observer'));s.collection.objects.link(cam);cam.location=(5,-7.5,3.1);cam.rotation_euler=(Vector((0,1,1.4))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=36;s.camera=cam
s.use_nodes=True;t=getattr(s,'node_tree',None)
if t is None:t=bpy.data.node_groups.new('Fuji fluorescence','CompositorNodeTree');s.compositing_node_group=t
r=t.nodes.new('CompositorNodeRLayers');g=t.nodes.new('CompositorNodeGlare')
if hasattr(g,'glare_type'):g.glare_type='FOG_GLOW';g.threshold=.7
else:g.inputs['Type'].default_value='Fog Glow';g.inputs['Threshold'].default_value=.7
if bpy.app.version>=(5,0,0):t.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');out=t.nodes.new('NodeGroupOutput')
else:out=t.nodes.new('CompositorNodeComposite')
t.links.new(r.outputs[0],g.inputs[0]);t.links.new(g.outputs[0],out.inputs[0])
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
s.render.filepath=str(ROOT/'blender/FujiA1-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/FujiA1.blend'),copy=True)
bpy.ops.render.render(write_still=True)
