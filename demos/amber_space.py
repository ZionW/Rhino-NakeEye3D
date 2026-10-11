import random,math,json
from pathlib import Path
r=random.Random(19);gold=[];blue=[];motes=[]
def ring(center,radius,plane=0):
    points=[]
    for i in range(97):
        a=i*math.tau/96;p=[radius*math.cos(a),radius*math.sin(a),0]
        if plane==1:p=[p[0],0,p[1]]
        if plane==2:p=[0,p[0],p[1]]
        points.append([center[k]+p[k] for k in range(3)])
    return points
for i in range(950):
    a=r.uniform(0,math.tau);rad=r.uniform(2.3,8);motes.append([rad*math.cos(a),rad*math.sin(a),r.uniform(-1.3,4)])
centers=[]
for i in range(22):
    a=i*math.tau/22;rad=r.uniform(2.7,6.5);c=[rad*math.cos(a),rad*math.sin(a),r.uniform(-.5,2.7)];centers.append(c);size=r.uniform(.12,.34)
    for plane in range(3):gold.append(ring(c,size,plane))
    gold.append(ring(c,size*1.4))
    for j in range(30):
        a=r.uniform(0,math.tau);z=r.uniform(-1,1);xy=math.sqrt(1-z*z);motes.append([c[0]+size*xy*math.cos(a),c[1]+size*xy*math.sin(a),c[2]+size*z])
for z in [-1.5,-1.1,2.8,3.4]:
    for radius in [2.7,3.5,4.5,6,8]:gold.append(ring([0,0,z],radius))
for i in range(28):
    a=i*math.tau/28;gold.append([[rad*math.cos(a+.06*rad),rad*math.sin(a+.06*rad),-1.5] for rad in [j*.12 for j in range(76)]])
for i in range(0,22,3):blue.append([centers[i],centers[(i+4)%22],centers[(i+9)%22]])
Path(__file__).with_name('amber_space.json').write_text(json.dumps(dict(motes=motes,gold=gold,blue=blue)))
