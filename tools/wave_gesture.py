from collections import deque

class WaveDetector:
    """One lateral sweep triggers once; require stillness before another sweep."""
    def __init__(self):
        self.history={side:deque() for side in ('Right','Left')}
        self.armed=True
        self.cooldown=0
        self.still_since=None
        self.event_id=0
        self.direction=0

    def update(self,hands,now):
        moving=False
        trigger=0
        for side in ('Right','Left'):
            history=self.history[side]
            if side not in hands:
                history.clear(); continue
            x=hands[side]
            history.append((now,x))
            while history and now-history[0][0]>.65: history.popleft()
            if len(history)<2: continue
            duration=now-history[0][0]
            displacement=abs(x-history[0][1])
            recent=[p for p in history if now-p[0]<=.2]
            moving=moving or (len(recent)>1 and abs(x-recent[0][1])>.025)
            if duration>=.12 and displacement>=.16 and displacement/max(duration,.001)>.35:
                trigger=1 if side=='Right' else -1
        if not self.armed:
            if moving: self.still_since=None
            elif self.still_since is None: self.still_since=now
            elif now>=self.cooldown and now-self.still_since>=.3:
                self.armed=True
                for h in self.history.values(): h.clear()
        elif trigger:
            self.event_id+=1; self.direction=trigger
            self.armed=False; self.cooldown=now+1.2; self.still_since=None
        return self.event_id,self.direction
