from soccersimulator import Vector2D, SoccerAction
from soccersimulator.settings import GAME_GOAL_HEIGHT,GAME_HEIGHT, GAME_WIDTH,BALL_RADIUS,PLAYER_RADIUS

def get_random_vec():
    return Vector2D.create_random(-1,1)

def get_random_SoccerAction():
    return SoccerAction(get_random_vec(),get_random_vec())

class ProxyObj(object):
    def __init__(self,state):
        self._obj = state
    def __getattr__(self,attr):
        return getattr(self._obj,attr)

class SuperState(ProxyObj):
    def __init__(self,state,idt,idp):
        super(SuperState,self).__init__(state)
        self.key = (idt,idp)
    @property
    def my_team(self):
        return self.key[0]
    @property
    def his_team(self):
        return (2 -self.key[0])+1
    @property
    def me(self):
        return self.player_state(*self.key).position
    @property
    def my_goal(self):
        return Vector2D((self.my_team-1)*self.width,self.goal_center)
    @property
    def his_goal(self):
        return Vector2D((self.his_team-1)*self.width,self.goal_center)
    @property
    def ball_p(self):
        return self.ball.position
    @property
    def can_kick(self):
        return self.distance(self.ball_p)<(PLAYER_RADIUS+BALL_RADIUS)
    @property
    def width(self):
        return GAME_WIDTH
    @property
    def height(self):
        return GAME_HEIGHT
    #######################################################################
    @property
    def cornerTopLeft(self):
        return Vector2D(0,self.height)
    @property
    def cornerTopRight(self):
        return Vector2D(self.width,self.height)
    @property
    def cornerBottomLeft(self):
        return Vector2D(0, 0)
    @property
    def cornerBottomRight(self):
        return Vector2D(self.width, 0)
    @property
    def middleTop(self):
        return Vector2D(self.width/2, self.height)
    @property
    def middle(self):
        return Vector2D(self.width/2, self.height/2)
    @property
    def middleBottom(self):
        return Vector2D(self.width/2, 0)
    #######################################################################
    @property
    def goal_center(self):
        return self.height/2. #+ self.goal_radius
    @property
    def goal_radius(self):
        return GAME_GOAL_HEIGHT/2.
    def distance(self,p):
        return self.me.distance(p)
    @property
    def my_config(self):
        return self.player_state(*self.key)
    @property
    def my_vitesse(self):
        return self.player_state(*self.key).vitesse

class Comportement(ProxyObj):
    def __init__(self,obj):
        super(Comportement,self).__init__(obj)
    def run(self,p):
        raise(NotImplementedError)
    def go(self,p):
        raise(NotImplementedError)
    def shoot(self):
        raise(NotImplementedError)
    def degage(self):
        raise(NotImplementedError)
    def allerVers(self, p):
        raise(NotImplementedError)
    def tirerVers(self, p):
        raise(NotImplementedError)
    def intercepter(self):
        raise(NotImplementedError)
