import bpy,json
from pathlib import Path
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D')
exec(compile((ROOT/'demos/scan_style.py').read_text(),'scan_style.py','exec'))
data=json.loads((ROOT/'demos/cyberspace.json').read_text())
s=bpy.context.scene
for o in s.objects:
    if not o.name.startswith('Apple '):continue
    part=o.name.split()[1].split('.')[0];points=data['parts'][part];mesh=o.data
    a=mesh.color_attributes.get('ScanColor') or mesh.color_attributes.new(name='ScanColor',type='FLOAT_COLOR',domain='POINT')
    for i,p in enumerate(points):
        color=(*scan_color(p,part),1)
        center=sum((mesh.vertices[i*6+j].co for j in range(6)),mesh.vertices[i*6].co*0)/6
        for j in range(6):
            a.data[i*6+j].color=color
            mesh.vertices[i*6+j].co=center+(mesh.vertices[i*6+j].co-center).normalized()*.0055
    m=bpy.data.materials.new('Scanner '+part);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');e=n.new('ShaderNodeEmission');v=n.new('ShaderNodeAttribute');v.attribute_name='ScanColor';e.inputs[1].default_value=2
    m.node_tree.links.new(v.outputs['Color'],e.inputs[0]);m.node_tree.links.new(e.outputs[0],out.inputs[0]);mesh.materials[0]=m
next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND').inputs[0].default_value=(.0005,.003,.006,1)
s.view_settings.view_transform='Standard';s.view_settings.exposure=-.5
s.render.resolution_percentage=70;s.cycles.samples=16
s.render.filepath=str(ROOT/'blender/CyberApple-scan-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/CyberApple.blend'),copy=True)
bpy.ops.render.render(write_still=True)
