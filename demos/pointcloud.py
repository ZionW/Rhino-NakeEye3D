"""Deterministic apple surface and a sparse network, metres, Z up."""
import math, random, json
from pathlib import Path

def build():
    rng=random.Random(42); parts={'body':[],'stem':[],'leaf':[]}
    for i in range(88):
        t=math.pi*(i+.5)/88
        for j in range(144):
            a=2*math.pi*j/144
            r=math.sin(t)*(1+.09*math.cos(5*a)*math.sin(t)**2)*(.96+.10*math.cos(t))
            z=1.08*math.cos(t)-.20*math.exp(-(t/.32)**2)+.12*math.exp(-((t-math.pi)/.30)**2)
            parts['body'].append([r*math.cos(a),r*math.sin(a),z])
    for i in range(44):
        t=i/43
        for j in range(12):
            a=j*math.tau/12
            parts['stem'].append([.12*t+.045*math.cos(a),.045*math.sin(a),.88+.48*t])
    for i in range(50):
        t=i/49
        for j in range(17):
            v=(j/8-1)*.24*math.sin(math.pi*t)
            parts['leaf'].append([.13+.77*t,v,1.23+.22*math.sin(math.pi*t)+.09*v])
    nodes=[[rng.uniform(-5,5),rng.uniform(-4,4),rng.uniform(-1,3)] for _ in range(70)]
    edges=[]
    for i,p in enumerate(nodes):
        nearest=sorted(range(len(nodes)),key=lambda j:sum((p[k]-nodes[j][k])**2 for k in range(3)))
        for j in nearest[1:3]:
            if j>i: edges.append([p,nodes[j]])
    return dict(parts=parts,nodes=nodes,edges=edges)
if __name__=='__main__':
    Path(__file__).with_name('cyberspace.json').write_text(json.dumps(build()))
