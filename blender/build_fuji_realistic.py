"""Solid, daylight Fuji-inspired circuit scene; no point-cloud geometry or titles."""
import bpy,math,random
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/zionw/Desktop/Codex/裸視3D');rng=random.Random(104)
s=bpy.data.scenes.new('Fuji Speedway • Audi A1 / Daylight');bpy.context.window.scene=s
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.render.resolution_x=1440;s.render.resolution_y=900;s.render.resolution_percentage=70
s.view_settings.view_transform='AgX';s.view_settings.exposure=.1
# Physically shaded paint, rubber, glass and rough circuit surfaces.
def material(name,color,rough=.4,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m
white=material('Pearl white paint',(.84,.86,.88),.22,.25)
p=next(n for n in white.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Coat Weight'].default_value=.55;p.inputs['Coat Roughness'].default_value=.12
red=material('Race red paint',(.54,.008,.012),.25,.2);black=material('Gloss black details',(.007,.009,.012),.23,.25)
rubber=material('Tire rubber',(.012,.013,.014),.82);alloy=material('Brushed aluminium',(.55,.6,.65),.23,.85)
glass=material('Tinted automotive glass',(.012,.035,.047),.1,.15)
p=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Transmission Weight'].default_value=.3;p.inputs['IOR'].default_value=1.46
lamp=material('Headlamp lenses',(.6,.8,.95),.12,.45)
concrete=material('Concrete',(.42,.44,.46),.85);seat=material('Grandstand silver',(.42,.48,.54),.5,.65)
grass=material('Grass verge',(.06,.12,.035),.95);asphalt=material('Asphalt aggregate',(.032,.038,.045),.91)
def noise_bump(m,scale,strength,distance):
    t=m.node_tree;p=next(n for n in t.nodes if n.type=='BSDF_PRINCIPLED');tex=t.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
    bump=t.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength;bump.inputs['Distance'].default_value=distance;t.links.new(tex.outputs['Fac'],bump.inputs['Height']);t.links.new(bump.outputs['Normal'],p.inputs['Normal'])
noise_bump(asphalt,170,.55,.018);noise_bump(rubber,95,.28,.006);noise_bump(concrete,35,.3,.035)
def mesh(name,verts,faces,mat,part=False,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);s.collection.objects.link(o);me.materials.append(mat)
    if smooth:
        for p in me.polygons:p.use_smooth=True
    if part:
        center=sum((v.co for v in me.vertices),Vector())/max(1,len(me.vertices))
        for v in me.vertices:v.co-=center
        o.location=center;o['nakedeye_part']=True
    return o
def cube(name,loc,scale,mat,bevel=0,part=False):
    x,y,z=scale;verts=[(a*x+loc[0],b*y+loc[1],c*z+loc[2]) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=mesh(name,verts,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat,part)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
        mod=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def sheet(name,points,mat,part=True):return mesh(name,points,[tuple(range(len(points)))],mat,part)
def tube(name,points,mat,r=.015,closed=False,part=False):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.bevel_depth=r;cu.bevel_resolution=3
    sp=cu.splines.new('POLY');sp.points.add(len(points)-1)
    for p,xyz in zip(sp.points,points):p.co=(*xyz,1)
    sp.use_cyclic_u=closed;o=bpy.data.objects.new(name,cu);s.collection.objects.link(o);cu.materials.append(mat)
    if part:o['nakedeye_part']=True
    return o
def cylinder(name,a,b,r,mat,vertices=32,part=False):
    direction=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=direction.length,location=mid)
    o=bpy.context.object;o.name=name;o.rotation_euler=direction.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    if part:o['nakedeye_part']=True
    return o
# Connected curved lower body with open wheel arches.
profiles=[(-2,.60,.77),(-1.88,.80,.97),(-1.4,.88,1.01),(-.6,.89,.98),(.6,.87,.91),(1.28,.84,.87),(1.78,.78,.80),(1.96,.65,.68)]
verts=[];faces=[];steps=18;ring=96
for n in range(len(profiles)-1):
    a,b=profiles[n:n+2]
    for i in range(steps):
        t=i/steps;x=a[0]*(1-t)+b[0]*t;w=a[1]*(1-t)+b[1]*t;top=a[2]*(1-t)+b[2]*t
        for j in range(ring):
            th=j/ring*math.tau;y=w*math.copysign(abs(math.cos(th))**.28,math.cos(th));z=.27+(top-.27)*(1+math.copysign(abs(math.sin(th))**.42,math.sin(th)))/2;verts.append((x,y,z))
rows=len(verts)//ring
for i in range(rows-1):
    for j in range(ring):
        ids=[i*ring+j,i*ring+(j+1)%ring,(i+1)*ring+(j+1)%ring,(i+1)*ring+j]
        p=sum((Vector(verts[k]) for k in ids),Vector())/4
        if abs(p.y)>.63 and any((p.x-x)**2+(p.z-.37)**2<.385**2 for x in [-1.24,1.24]):continue
        faces.append(tuple(ids))
faces.extend([tuple(range(ring-1,-1,-1)),tuple((rows-1)*ring+j for j in range(ring))])
body=mesh('A1 / Sculpted body shell',verts,faces,white,True,True)
# Hatchback roof and opaque cabin with glass panels inset in a white perimeter.
roof=cube('A1 / Roof',(-.32,0,1.43),(.78,.65,.035),white,.07,True)
front=[(.46,-.64,1.43),(1.05,-.76,.93),(1.05,.76,.93),(.46,.64,1.43)]
rear=[(-1.08,.64,1.43),(-1.7,.78,1.01),(-1.7,-.78,1.01),(-1.08,-.64,1.43)]
sheet('A1 / Windscreen',front,glass);sheet('A1 / Rear window',rear,glass)
for sign in [-1,1]:
    outline=[(-1.6,sign*.79,1.02),(.94,sign*.79,.95),(.45,sign*.65,1.43),(-1.06,sign*.65,1.43)]
    sheet('A1 / Side glazing',outline,glass);tube('A1 / Window frame',outline,white,.032,True,True)
    tube('A1 / B pillar',[(-.38,sign*.795,1.0),(-.38,sign*.655,1.43)],black,.055,False,True)
    tube('A1 / Door seam',[(-.3,sign*.892,.97),(-.3,sign*.893,.42),(.85,sign*.866,.42),(.92,sign*.83,.9)],black,.004,False,True)
    cube('A1 / Handle',(.48,sign*.88,.83),(.09,.018,.018),alloy,.015,True)
    cube('A1 / Mirror',(.66,sign*.98,1.01),(.14,.12,.055),white,.05,True)
    # Red racing panel follows the side rather than floating through the body.
    sheet('A1 / Red door panel',[(-1.02,sign*.894,.50),(-.34,sign*.895,.50),(-.34,sign*.895,.90),(-1.02,sign*.894,.94)],red)
    sheet('A1 / Sill red accent',[(-.92,sign*.876,.30),(.87,sign*.866,.30),(.87,sign*.875,.34),(-.92,sign*.885,.34)],red)
for points in [front,rear]:tube('A1 / Glass surround',points,white,.03,True,True)
# Bonnet black stripe, detailed grille, headlamps and bumper.
sheet('A1 / Bonnet stripe',[(1.09,-.17,.885),(1.80,-.16,.804),(1.80,.16,.804),(1.09,.17,.885)],black)
cube('A1 / Single-frame grille',(1.975,0,.50),(.03,.49,.205),black,.065,True)
tube('A1 / Grille chrome surround',[(2.01,-.46,.34),(2.01,.46,.34),(2.01,.48,.69),(2.01,-.48,.69)],alloy,.012,True,True)
for z in [.38,.43,.48,.53,.58]:tube('A1 / Grille slat',[(2.018,-.44,z),(2.018,.44,z)],black,.012,False,True)
for y in [i*.07 for i in range(-6,7)]:tube('A1 / Grille mesh',[(2.015,y,.34),(2.015,y,.67)],alloy,.002,False,True)
for cy in [-.165,-.055,.055,.165]:tube('Audi / Four rings',[(2.03,cy+.071*math.cos(i/64*math.tau),.625+.047*math.sin(i/64*math.tau)) for i in range(64)],alloy,.008,True,True)
for sign in [-1,1]:
    points=[(1.94,sign*.49,.67),(1.90,sign*.77,.65),(1.83,sign*.77,.78),(1.91,sign*.49,.80)]
    sheet('A1 / Headlamp cluster',points,lamp);tube('A1 / Lamp frame',points,black,.012,True,True)
    cylinder('A1 / Projector',(1.938,sign*.60,.721),(1.951,sign*.60,.721),.042,alloy,24,True)
    tube('A1 / LED signature',[(1.94,sign*.50,.68),(1.91,sign*.72,.67)],lamp,.008,False,True)
    cube('A1 / Lower intake',(1.93,sign*.67,.31),(.028,.14,.067),black,.025,True)
    sheet('A1 / Tail lamp',[(-1.94,sign*.46,.73),(-1.87,sign*.77,.73),(-1.85,sign*.77,.86),(-1.93,sign*.46,.86)],red)
cube('A1 / Interior seats',(-.35,0,.98),(.53,.53,.22),black,.07,True)
# Real closed tires, polished rims, brake discs and ten spokes.
for x in [-1.24,1.24]:
    for sign in [-1,1]:
        y=sign*.86;z=.37
        bpy.ops.mesh.primitive_torus_add(major_radius=.264,minor_radius=.083,major_segments=64,minor_segments=16,location=(x,y,z),rotation=(math.pi/2,0,0))
        tire=bpy.context.object;tire.name='A1 / Tire';tire.data.materials.append(rubber);tire['nakedeye_part']=True
        for p in tire.data.polygons:p.use_smooth=True
        cylinder('A1 / Brake disc',(x,y-sign*.02,z),(x,y+sign*.015,z),.22,alloy,64,True)
        cylinder('A1 / Wheel hub',(x,y+sign*.06,z),(x,y+sign*.092,z),.062,alloy,32,True)
        tube('A1 / Rim',[(x+.247*math.cos(i/80*math.tau),y+sign*.086,z+.247*math.sin(i/80*math.tau)) for i in range(80)],alloy,.016,True,True)
        for j in range(10):
            a=j/10*math.tau;cylinder('A1 / Spoke',(x+.05*math.cos(a),y+sign*.09,z+.05*math.sin(a)),(x+.234*math.cos(a+.08),y+sign*.088,z+.234*math.sin(a+.08)),.012,alloy,10,True)
        for j in range(5):
            a=j/5*math.tau;cylinder('A1 / Lug bolt',(x+.04*math.cos(a),y+sign*.093,z+.04*math.sin(a)),(x+.04*math.cos(a),y+sign*.10,z+.04*math.sin(a)),.007,black,8,True)
# Circuit and red/white kerbs. No text objects or signs.
cube('Fuji / Grass terrain',(0,0,-.22),(250,300,.2),grass)
cube('Fuji / Asphalt straight',(0,0,-.035),(75,6,.035),asphalt)
paint=material('Road marking white',(.76,.77,.73),.87)
for y in [-5.8,5.8]:cube('Fuji / Edge line',(0,y,.007),(75,.06,.006),paint)
for y in [-6.25,6.25]:
    for i in range(-60,60):cube('Fuji / Kerb',(i*1.15,y,.025),(.57,.40,.04),red if i%2 else paint)
for x in [-4,4]:cube('Fuji / Starting box',(x,0,.005),(.035,1.3,.006),paint)
# Safety barriers, posts and catch fencing.
for y in [7.2,-8]:
    for z in [.45,.70,.95]:tube('Fuji / Armco rail',[(-75,y,z),(75,y,z)],alloy,.065)
    for x in range(-72,73,3):
        cylinder('Fuji / Fence post',(x,y,0),(x,y,2.4),.045,alloy,12)
    for z in [1.2,1.6,2.0,2.4]:tube('Fuji / Fence wire',[(-75,y,z),(75,y,z)],alloy,.006)
# Grandstand concrete tiers and many individual seats.
for row in range(12):
    y=11+row*.65;z=.3+row*.3
    cube('Fuji / Concrete terrace',(2,y,z),(18,.35,.15),concrete)
    for col in range(60):
        x=-15+col*.57;cube('Fuji / Seat',(x,y,z+.20),(.22,.22,.04),seat,.025)
        cube('Fuji / Seat back',(x,y+.20,z+.40),(.22,.04,.18),seat,.025)
for x in [-16,-7,2,11,20]:
    cylinder('Fuji / Canopy support',(x,15,0),(x,15,5.4),.12,alloy,16)
    tube('Fuji / Roof truss',[(x,10,5.7),(x,19,5.7),(x,15,5.1),(x,10,5.7)],alloy,.07)
cube('Fuji / Grandstand canopy',(2,14.5,5.8),(19,5,.10),paint,.05)
# Fuji stratovolcano and its irregular snowline; actual solid terrain.
rock=material('Fuji volcanic rock',(.065,.09,.105),.95)
snow=material('Fuji snow',(.83,.87,.90),.82)
verts=[];faces=[];rings=100;segments=160
for row in range(rings):
    r=.4+row*3.8
    for j in range(segments):
        a=j/segments*math.tau;h=205*(1-(r/380)**.78)+4*math.sin(a*13+r*.025)*(r/380)+2*math.sin(a*23+r*.07)
        verts.append((-180+r*math.cos(a),1100+r*math.sin(a),max(-1,h)))
for row in range(rings-1):
    for j in range(segments):faces.append((row*segments+j,row*segments+(j+1)%segments,(row+1)*segments+(j+1)%segments,(row+1)*segments+j))
mount=mesh('Fuji / Volcanic mountain',verts,faces,rock,smooth=True);mount.data.materials.append(snow)
for p in mount.data.polygons:
    c=p.center;angle=math.atan2(c.y-1100,c.x+180);p.material_index=1 if c.z>145+14*math.sin(angle*5)+6*math.sin(angle*11) else 0
noise_bump(rock,1,.45,1.4);noise_bump(snow,2,.25,.5)
# Tree belt, with clustered foliage rather than luminous particles.
foliage=material('Forest foliage',(.018,.055,.024),1)
for i in range(95):
    x=rng.uniform(-170,170);y=rng.uniform(30,70);h=rng.uniform(3.5,8)
    bpy.ops.mesh.primitive_cone_add(vertices=9,radius1=h*.34,radius2=.12,depth=h,location=(x,y,h*.5))
    o=bpy.context.object;o.name='Fuji / Distant conifer';o.data.materials.append(foliage)
# Clear daytime sky and soft sunlight.
w=bpy.data.worlds.new('Fuji daylight sky');w.use_nodes=True;s.world=w;t=w.node_tree;t.nodes.clear();sky=t.nodes.new('ShaderNodeTexSky');sky.sky_type='HOSEK_WILKIE';sky.sun_direction=(.3,-.4,.85);sky.turbidity=2.2;sky.ground_albedo=.3
bg=t.nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.35;out=t.nodes.new('ShaderNodeOutputWorld');t.links.new(sky.outputs[0],bg.inputs[0]);t.links.new(bg.outputs[0],out.inputs[0])
light=bpy.data.objects.new('Fuji / Sun',bpy.data.lights.new('Fuji / Sun','SUN'));s.collection.objects.link(light);light.data.energy=2.4;light.data.angle=math.radians(3);light.rotation_euler=(math.radians(25),math.radians(-25),math.radians(-35))
cam=bpy.data.objects.new('Fuji / Observer',bpy.data.cameras.new('Fuji / Observer'));s.collection.objects.link(cam);cam.location=(5.6,-8,2.1);cam.rotation_euler=(Vector((0,1,1.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=35;s.camera=cam
s.render.filepath=str(ROOT/'blender/FujiA1-realistic-preview.png')
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/FujiA1.blend'),copy=True)
bpy.ops.render.render(write_still=True)
