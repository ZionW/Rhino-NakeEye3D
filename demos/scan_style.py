"""Deterministic scanner palette: depth bands, speckle and sparse bright returns."""
import math

def scan_color(p, part='body'):
    x,y,z=p
    grain=(math.sin(x*127.1+y*311.7+z*74.7)*43758.5453)%1
    band=.5+.5*math.sin(z*36+y*5)
    t=max(0,min(1,.45+.28*z+.20*math.sin(x*2.8-y*1.7)+.10*(grain-.5)))
    palette=[(.01,.20,.32),(.015,.72,.55),(.08,1.,.80),(.45,.85,1.)]
    if part=='leaf':palette=[(.01,.25,.06),(.12,.70,.18),(.6,1.,.25),(.8,1.,.7)]
    if part=='stem':palette=[(.22,.04,.01),(.65,.22,.025),(1.,.65,.1),(1.,.9,.5)]
    u=t*3;i=min(2,int(u));f=u-i
    gain=(.45+.55*grain)*(.75+.25*band)
    if grain>.975:gain=1.7
    return tuple((palette[i][k]*(1-f)+palette[i+1][k]*f)*gain for k in range(3))
