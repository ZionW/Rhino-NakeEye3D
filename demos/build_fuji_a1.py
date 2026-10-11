"""Reference-inspired A1 race car and Fuji Speedway, procedural colored scan."""
import math,json,random
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]; rng=random.Random(104)
parts={k:[] for k in ['body','stem','leaf']}; colors={k:[] for k in parts}; env=[]; ec=[];edges=[]
WHITE=(.62,.75,.8);RED=(.9,.025,.045);BLACK=(.025,.035,.045);GLASS=(.015,.13,.20)
def add(key,p,c):
    grain=rng.uniform(.65,1.05)
    (env if key=='env' else parts[key]).append([round(v,4) for v in p]);(ec if key=='env' else colors[key]).append([round(v*grain,4) for v in c])
def patch(key,a,b,c,d,color,nu=70,nv=30):
    for i in range(nu+1):
        u=i/nu
        for j in range(nv+1):
            v=j/nv;p=[(1-u)*((1-v)*a[k]+v*d[k])+u*((1-v)*b[k]+v*c[k]) for k in range(3)]
            add(key,p,color(p) if callable(color) else color)
def text(key,label,origin,axis_u,axis_v,size,color):
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',48)
    box=font.getbbox(label);im=Image.new('L',(box[2]+4,60));ImageDraw.Draw(im).text((0,-box[1]),label,font=font,fill=255)
    for y in range(0,im.height,2):
        for x in range(0,im.width,2):
            if im.getpixel((x,y))>150:add(key,[origin[k]+axis_u[k]*x*size+axis_v[k]*y*size for k in range(3)],color)
# Main lower body: lofted curved sheet, wheel arch cutouts on the sides.
profiles=[(-2,.60,.78),(-1.8,.82,.98),(-1.35,.89,1.02),(-.6,.88,.98),(.6,.87,.91),(1.3,.83,.85),(1.8,.77,.76),(2,.62,.64)]
for n in range(len(profiles)-1):
    a,b=profiles[n:n+2]
    for i in range(24):
        t=i/24;x=a[0]*(1-t)+b[0]*t;w=a[1]*(1-t)+b[1]*t;top=a[2]*(1-t)+b[2]*t
        for j in range(130):
            theta=j/130*math.tau;y=w*math.copysign(abs(math.cos(theta))**.32,math.cos(theta));z=.28+(top-.28)*(1+math.copysign(abs(math.sin(theta))**.45,math.sin(theta)))/2
            if abs(y)>.65 and any((x-wx)**2+(z-.39)**2<.39**2 for wx in [-1.25,1.25]):continue
            col=WHITE
            if abs(y)>.76 and -.95<x<-.15 and .48<z<.87:col=RED
            if x>1.05 and abs(y)<.18 and z>.7:col=BLACK
            if x<-.8 and z>.78:col=WHITE
            add('body',(x,y,z),col)
# Roof, windshield, rear glass and quarter windows.
patch('body',(-1.05,-.67,1.48),(.45,-.65,1.48),(.45,.65,1.48),(-1.05,.67,1.48),WHITE,65,38)
patch('leaf',(.45,-.64,1.47),(1.05,-.76,.91),(1.05,.76,.91),(.45,.64,1.47),GLASS,45,65)
patch('leaf',(-1.05,-.66,1.47),(-1.72,-.77,1.0),(-1.72,.77,1.0),(-1.05,.66,1.47),GLASS,40,60)
for sign in [-1,1]:
    patch('leaf',(-1.55,sign*.80,1.02),(.94,sign*.80,.94),(.43,sign*.66,1.43),(-1.04,sign*.68,1.43),GLASS,100,22)
    # Window frames, B pillar, sill and mirror.
    for x1,x2 in [(-1.12,-1.02),(-.46,-.34)]:patch('body',(x1,sign*.79,1.0),(x2,sign*.79,1.0),(x2,sign*.67,1.46),(x1,sign*.67,1.46),WHITE,5,25)
    patch('body',(-1.57,sign*.82,.98),(.95,sign*.82,.94),(.95,sign*.82,.99),(-1.57,sign*.82,1.03),WHITE,120,3)
    patch('body',(.55,sign*.81,1.02),(.8,sign*.81,1.02),(.8,sign*1.01,1.09),(.55,sign*1.01,1.09),WHITE,14,12)
    text('body','104',(-.85,sign*.892,.79),(1,0,0),(0,0,-1),.0035,(1,.95,.83))
    text('body','A1 CUP',(-1.6,sign*.891,.65),(1,0,0),(0,0,-1),.002,RED)
# Black grille, lamp clusters, four rings and bumper intakes.
patch('body',(2.015,-.48,.34),(2.015,.48,.34),(2.015,.48,.71),(2.015,-.48,.71),BLACK,45,18)
for sign in [-1,1]:
    patch('body',(1.94,sign*.49,.66),(1.91,sign*.78,.64),(1.85,sign*.78,.77),(1.92,sign*.49,.79),(.3,.65,1),25,8)
    patch('body',(1.95,sign*.48,.27),(1.89,sign*.78,.27),(1.90,sign*.78,.41),(1.99,sign*.48,.41),BLACK,20,8)
    patch('body',(-1.92,sign*.45,.72),(-1.84,sign*.78,.73),(-1.82,sign*.78,.84),(-1.93,sign*.45,.84),RED,20,6)
for cy in [-.165,-.055,.055,.165]:
    for i in range(70):
        a=i/70*math.tau;add('body',(2.024,cy+.071*math.cos(a),.635+.047*math.sin(a)),(.85,.92,1))
# Tire point returns and radial alloy wheel spokes.
for x in [-1.25,1.25]:
    for sign in [-1,1]:
        for j in range(100):
            a=j/100*math.tau
            for k in range(12):
                y=sign*(.78+k*.018);add('stem',(x+.34*math.cos(a),y,.39+.34*math.sin(a)),(.025,.035,.05))
            for radius in [.22,.24]:add('stem',(x+radius*math.cos(a),sign*1.005,.39+radius*math.sin(a)),(.3,.42,.5))
        for j in range(10):
            a=j/10*math.tau
            for k in range(22):
                r=k*.010;add('stem',(x+r*math.cos(a),sign*1.01,.39+r*math.sin(a)),(.5,.66,.72))
# Broad asphalt pad, white start lines and red-white curbing.
patch('env',(-18,-5,0),(18,-5,0),(18,5,0),(-18,5,0),(.008,.018,.023),230,65)
for y in [-5,5]:
    for i in range(150):
        x=-18+i*.24;patch('env',(x,y,.012),(x+.24,y,.012),(x+.24,y+.5,.012),(x,y+.5,.012),RED if i%2 else WHITE,3,3)
for x in [-4,4]:patch('env',(x,-4,.015),(x+.08,-4,.015),(x+.08,4,.015),(x,4,.015),(.3,.5,.55),2,55)
# Grandstand to the right with stepped seating, cyan rails and white canopy.
for row in range(13):
    y=7+row*.42;z=.25+row*.22
    patch('env',(-11,y,z),(12,y,z),(12,y+.25,z),(-11,y+.25,z),(.07,.18,.22),180,3)
    edges.append([[-11,y,z+.25],[12,y,z+.25]])
patch('env',(-11,7,3.7),(12,7,3.7),(12,12.5,3.7),(-11,12.5,3.7),(.08,.24,.27),100,20)
# Mount Fuji: snow cap over layered, slightly irregular conical terrain.
for row in range(1,100):
    r=row*.11;h=6.0*(1-(r/11)**.72)
    for j in range(200):
        a=j/200*math.tau;z=h+.12*math.sin(a*9+row*.2);p=(r*math.cos(a)-4,22+r*math.sin(a),z)
        snow=z>4.2+.45*math.sin(a*5)+.15*math.cos(a*13)
        add('env',p,(.4,.65,.8) if snow else (.015,.05+.08*z/10,.11+.10*z/10))
# Raceway identity signage, no title graphics from the reference photo.
patch('env',(-5,6,2.1),(5,6,2.1),(5,6,3.15),(-5,6,3.15),(.005,.025,.035),80,10)
text('env','FUJI SPEEDWAY',(-4.4,5.98,2.95),(1,0,0),(0,0,-1),.013,(.06,.65,.8))
result={'parts':parts,'colors':colors,'environment':env,'environment_colors':ec,'edges':edges,'nodes':[],'description':'Procedural approximation inspired by Audi A1 Fun Cup reference; not manufacturer CAD or surveyed Fuji track.'}
(ROOT/'demos/fuji_a1.json').write_text(json.dumps(result,separators=(',',':')))
print({k:len(v) for k,v in parts.items()},'environment',len(env))
