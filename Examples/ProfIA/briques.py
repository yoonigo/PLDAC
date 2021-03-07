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

####Stratégies 2021######################################################################################################################################
class ComportementNew(Comportement):
    RUN_COEF = maxPlayerAcceleration
    SHOOT_COEF = maxPlayerShoot
    LOW_SHOOT_COEF = maxPlayerShoot / 3.
    COEF_BALL = 1.5

    def __init__(self,state):
        super(ComportementNew,self).__init__(state)

    def allerVers(self, p):
        return SoccerAction(acceleration=(p-self.me).normalize()*self.RUN_COEF)

    def tirerVers(self, p, low = False):
        if self.can_kick:
            if(not low):
                return SoccerAction(shoot=(p-self.ball_p).normalize()*self.SHOOT_COEF)
            else:
                return SoccerAction(shoot=(p - self.ball_p).normalize() * self.LOW_SHOOT_COEF)
        return SoccerAction()

    def intercepter(self):
        return self.allerVers(self.ball_position_finale)

    def proximiteAtteinte(self,cible):
        return self.me.distance(cible) < self.COEF_BALL

def fonceurNew(I):
    if not I.can_kick:
        return I.allerVers(I.ball_p)
    else:
        return I.tirerVers(I.his_goal)

def executeOrder(I,order, state):
    def getCible(cible):
        if (cible == "CageAdverse"):
            return I.his_goal
        if (cible == "SaCage"):
            return I.my_goal
        if (cible == "Balle"):
            return I.ball_p
        if (cible == "CornerTopLeft"):
            return I.cornerTopLeft
        if (cible == "CornerTopRight"):
            return I.cornerTopRight
        if (cible == "CornerBottomLeft"):
            return I.cornerBottomLeft
        if (cible == "CornerBottomRight"):
            return I.cornerBottomRight
        if (cible == "MiddleTop"):
            return I.middleTop
        if (cible == "MiddleBottom"):
            return I.middleBottom
        if (cible == "Middle"):
            return I.middle
        else:
            return state[cible].position

    if(len(order) == 2): #TargetingType = 0
        cible = getCible(order[1])
    else: #TargetingType = 1
        print(order)
        cibleA = getCible(order[1])
        cibleB = getCible(order[2])
        cible = cibleA.mixage(cibleB,order[3])
    if(order[0] == "se déplace vers"):
        actionMustStop = I.proximiteAtteinte(cible)
        return (I.allerVers(cible),actionMustStop)
    elif(order[0] == "tire vers"):
        return (I.tirerVers(cible),True)



