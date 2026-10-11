"""Run in Blender. Creates a new scene without deleting the current scene."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
exec(compile((ROOT/'demos/scan_style.py').read_text(),'scan_style.py','exec'))
def build():
    data=json.loads((ROOT/'demos/cyberspace.json').read_text())
    scene=bpy.data.scenes.new('NakedEye3D • CYBER APPLE')
    bpy.context.window.scene=scene
    scene.render.engine='CYCLES';scene.cycles.samples=24
    scene.render.resolution_x=1280;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    world=bpy.data.worlds.new('Cyber void');world.use_nodes=True
    world.node_tree.nodes.clear();bg=world.node_tree.nodes.new('ShaderNodeBackground');wo=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],wo.inputs[0]);bg.inputs[0].default_value=(.0005,.003,.006,1)
    bg.inputs[1].default_value=.1;scene.world=world
    def material(name,color,power):
        m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
        n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(*color,1);e.inputs[1].default_value=power;m.node_tree.links.new(e.outputs[0],out.inputs[0]);return m
    cyan=material('Ion cyan',(.03,1,.7),5);green=material('Leaf mint',(1,.75,.12),3);amber=material('Stem amber',(1,.85,.30),3);dim=material('Network blue',(.16,.045,.003),1)
    collection=bpy.data.collections.new('APPLE • Explodable parts');scene.collection.children.link(collection)
    def dots(name,points,mat,size,coll):
        # Low polygon octahedra form luminous points; no thousands of objects.
        verts=[];faces=[]
        for x,y,z in points:
            k=len(verts);verts.extend([(x+size,y,z),(x-size,y,z),(x,y+size,z),(x,y-size,z),(x,y,z+size),(x,y,z-size)])
            faces.extend([tuple(k+j for j in tri) for tri in [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]])
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);coll.objects.link(o);o.data.materials.append(mat)
        if name.startswith('Apple '):
            colors=mesh.color_attributes.new(name='ScanColor',type='FLOAT_COLOR',domain='POINT')
            for i,p in enumerate(points):
                color=(*scan_color(p,name.split()[-1]),1)
                for j in range(6):colors.data[i*6+j].color=color
            scan=bpy.data.materials.new(name+' scanner returns');scan.use_nodes=True
            ns=scan.node_tree.nodes;ns.clear();out=ns.new('ShaderNodeOutputMaterial');e=ns.new('ShaderNodeEmission');a=ns.new('ShaderNodeAttribute');a.attribute_name='ScanColor';e.inputs[1].default_value=2
            scan.node_tree.links.new(a.outputs['Color'],e.inputs[0]);scan.node_tree.links.new(e.outputs[0],out.inputs[0]);o.data.materials[0]=scan
        return o
    for key,mat in [('body',cyan),('stem',amber),('leaf',green)]:
        o=dots('Apple '+key,data['parts'][key],mat,.0055,collection);o['nakedeye_part']=True
        # Put origin at part centre to make positional explosion meaningful.
        center=sum((Vector(p) for p in data['parts'][key]),Vector())/len(data['parts'][key])
        for v in o.data.vertices:v.co-=center
        o.location=center
    dots('Network nodes',data['nodes'],cyan,.025,scene.collection)
    def lines(name,segments,mat,radius):
        curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=0
        for segment in segments:
            s=curve.splines.new('POLY');s.points.add(len(segment)-1)
            for p,xyz in zip(s.points,segment):p.co=(*xyz,1)
        o=bpy.data.objects.new(name,curve);scene.collection.objects.link(o);o.data.materials.append(mat)
    segments=data['edges']
    for i in range(-10,11):
        t=i*.5;segments.extend([[[-5,t,-1.4],[5,t,-1.4]],[[t,-5,-1.4],[t,5,-1.4]]])
    lines('Network lattice',segments,dim,.002)
    rings=[]
    for r in [1.45,1.65,2.1]:rings.append([[r*math.cos(a*math.tau/240),r*math.sin(a*math.tau/240),-1.28] for a in range(241)])
    lines('Scan rings',rings,cyan,.003)
    amb=json.loads((ROOT/'demos/amber_space.json').read_text())
    dots('Suspended data',amb['motes'],green,.018,scene.collection)
    lines('Amber orbital network',amb['gold'],dim,.004)
    blue=material('Signal blue',(.01,.35,1),4)
    lines('Blue data routes',amb['blue'],blue,.012)
    cam=bpy.data.objects.new('Cyber observer',bpy.data.cameras.new('Cyber observer'));scene.collection.objects.link(cam)
    cam.location=(3.4,-6.3,2.8);cam.rotation_euler=(Vector((0,0,.1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=45;scene.camera=cam
    scene.view_settings.view_transform='Standard';scene.view_settings.exposure=-.5
    scene.use_nodes=True;tree=getattr(scene,'node_tree',None)
    if tree is None:
        tree=bpy.data.node_groups.new('Cyber glow','CompositorNodeTree');scene.compositing_node_group=tree
    tree.nodes.clear();r=tree.nodes.new('CompositorNodeRLayers');g=tree.nodes.new('CompositorNodeGlare');
    if hasattr(g,'glare_type'):g.glare_type='FOG_GLOW';g.threshold=1
    else:g.inputs['Type'].default_value='Fog Glow';g.inputs['Threshold'].default_value=1
    
    if bpy.app.version>=(5,0,0):
        tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');out=tree.nodes.new('NodeGroupOutput')
    else:out=tree.nodes.new('CompositorNodeComposite')
    tree.links.new(r.outputs[0],g.inputs[0]);tree.links.new(g.outputs[0],out.inputs[0])
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/CyberApple.blend'),copy=True)
    return scene
if __name__=='__main__':build()
