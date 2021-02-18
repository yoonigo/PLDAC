from .tools import SuperState, Comportement, ProxyObj
from soccersimulator import Vector2D,SoccerAction
from soccersimulator.settings import maxPlayerShoot, maxPlayerSpeed,maxPlayerAcceleration

class ComportementNaif(Comportement):
    RUN_COEF = maxPlayerAcceleration
    GO_COEF = maxPlayerAcceleration/3.
    SHOOT_COEF = maxPlayerShoot/3.
    THROW_COEF = maxPlayerShoot
    def __init__(self,state):
        super(ComportementNaif,self).__init__(state)
    def run(self,p):

        return SoccerAction(acceleration=(p-self.me).normalize()*self.RUN_COEF)
    def go(self,p):
        return SoccerAction(acceleration=(p-self.me).normalize()*self.GO_COEF)
    def shoot(self,shoot_coef=None):
        if shoot_coef is None:
            shoot_coef = self.SHOOT_COEF
        if self.can_kick:
            return SoccerAction(shoot=(self.his_goal-self.ball_p).normalize()*self.SHOOT_COEF)
        return SoccerAction()
    def degage(self):
        if self.can_kick:
            return SoccerAction(shoot=(self.his_goal-self.ball_p).normalize()*self.THROW_COEF)
        return SoccerAction()

class ComportementNew(Comportement):
    RUN_COEF = maxPlayerAcceleration
    SHOOT_COEF = maxPlayerShoot/3.

    def __init__(self,state):
        super(ComportementNew,self).__init__(state)

    def allerVers(self, p):
        return SoccerAction(acceleration=(p-self.me).normalize()*RUN_COEF)

    def tirerVers(self, p):
        if self.can_kick:
            return SoccerAction(shoot=(p-self.ball_p).normalize()*SHOOT_COEF)
        return SoccerAction()

    def intercepter(self):
        return self.allerVers(self.ball_position_finale)

class ConditionDefenseur(ProxyObj):
    COEF_DEF = 0.3
    def __init__(self,state):
        super(ConditionDefenseur,self).__init__(state)
    def is_defense(self):
        return self.ball_p.distance(self.my_goal)<self.COEF_DEF*self.width

class ConditionAttaque(ProxyObj):
    COEF_SHOOT = 0.2
    COEF_BALL = 0.1
    def __init__(self,state):
        super(ConditionAttaque,self).__init__(state)
    def close_goal(self):
        return self.me.distance(self.his_goal)<self.COEF_SHOOT*self.width
    def close_ball(self):
        return self.me.distance(self.ball_p)<self.COEF_BALL*self.width

def fonceur(I):
    if not I.can_kick:
        if I.close_ball():
            return I.go(I.ball_p)
        else:
            return I.run(I.ball_p)
    else:
        if I.close_goal():
            return I.shoot()
    return I.degage()

def defenseur(I):
    if I.is_defense():
        return I.degage()+I.run(I.ball_p)
    return I.go((I.ball_p-I.my_goal).normalize()*I.width*0.1+I.my_goal)
