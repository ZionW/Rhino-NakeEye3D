import unittest
from types import SimpleNamespace as P
from hand_gestures import three_finger_grasp, index_only

def point(x,y,z=0): return P(x=x,y=y,z=z)
def hand():
    p=[point(0,0) for _ in range(21)]
    p[0]=point(0,-1);p[1]=point(-.5,0);p[2]=point(-.5,.4);p[4]=point(0,.9)
    for base,joint,tip,x in [(5,6,8,-.4),(9,10,12,0),(13,14,16,.3),(17,18,20,.6)]:
        p[base]=point(x,0);p[joint]=point(x,1);p[tip]=point(x,2)
    return p
class Gestures(unittest.TestCase):
    def test_tripod_and_scale(self):
        p=hand();p[10]=point(0,.7);p[8]=point(-.1,.85);p[12]=point(.1,.85)
        self.assertTrue(three_finger_grasp(p))
        for q in p:q.x=q.x*3+5;q.y=q.y*3-2;q.z*=3
        self.assertTrue(three_finger_grasp(p))
    def test_open_and_fist(self):
        p=hand();self.assertFalse(three_finger_grasp(p))
        for tip in [8,12,16,20]:p[tip]=point(0,.1)
        self.assertFalse(three_finger_grasp(p))
    def test_index_only(self):
        p=hand()
        for tip in [12,16,20]:p[tip]=point(0,.1)
        self.assertTrue(index_only(p));self.assertFalse(three_finger_grasp(p,True))
    def test_two_finger_pinch_is_not_tripod(self):
        p=hand();p[8]=point(-.1,.85)
        self.assertFalse(three_finger_grasp(p))
if __name__=='__main__':unittest.main()
