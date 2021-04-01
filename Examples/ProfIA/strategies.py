from soccersimulator  import Strategy, SoccerAction, Vector2D, Simulation
from .tools import SuperState, Comportement, get_random_SoccerAction
from .briques import ComportementNaif, ComportementNew, ConditionAttaque,ConditionDefenseur,fonceur, fonceurNew,defenseur
import pickle

class RandomStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self,"Random")
    def compute_strategy(self,state,id_team,id_player):
        return get_random_SoccerAction()

class FonceurStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self,"Fonceur")
    def compute_strategy(self,state,id_team,id_player):
        I = ConditionAttaque(ComportementNaif(SuperState(state,id_team,id_player)))
        #I = ConditionAttaque(ComportementNew(SuperState(state,id_team,id_player)))
        return fonceur(I)

class DefenseurStrategy(Strategy):
    def __init__(self):
        Strategy.__init__(self, "Defenseur")
    def compute_strategy(self,state,id_team,id_player):
        I = ConditionDefenseur(ComportementNaif(SuperState(state,id_team,id_player)))
        return defenseur(I)

class FonceurTestStrategy(Strategy):
    def __init__(self, strength=None,fn=None):
        Strategy.__init__(self,"Fonceur")
        self.strength = strength
        self.best_force = None
        if fn is not None:
            import os
            fn=os.path.join(os.path.dirname(os.path.realpath(__file__)),fn)
            with open(fn,"rb") as f:
                self.best_force = pickle.load(f)
    def compute_strategy(self,state,id_team,id_player):
        C = ComportementNaif(SuperState(state,id_team,id_player))
        shoot_coef = self.get_force(C.me)
        if shoot_coef is not None:
            C.SHOOT_COEF = shoot_coef
        I = ConditionAttaque(C)
        return fonceur(I)
    def get_force(self,position):
        if self.best_force is not None:
            return sorted([ ((position.x-k[0])**2+(position.y-k[1])**2,v) for (k,v) in self.best_force.items()])[0][1]
        if self.strength is not None:
            return self.strength
        return None 

####Stratégies 2021######################################################################################################################################

class FonceurStrategyWithOrder(Strategy):
    def __init__(self):
        Strategy.__init__(self,"FonceurOrder")
        self.orderList = []


    def compute_strategy(self,state,id_team,id_player):
        I = ComportementNew(SuperState(state, id_team, id_player))
        if(self.orderList):
            action = self.executeOrder(I,self.orderList[0],Simulation.ETAT.states)
            if(action[1] == True):
                self.orderList.pop(0)
                if(self.orderList):
                    action = self.executeOrder(I, self.orderList[0], Simulation.ETAT.states)
            return action[0]
        #return None
        return fonceurNew(I)

    def executeOrder(self, I, order, state):
        def getCible(cible):
            if (cible == "CageAdverse"):
                return I.his_goal
            if (cible == "SaCage"):
                return I.my_goal
            if (cible == "Balle"):
                return I.ball_p
            if (cible == "BalleProchaine"):
                return I.ball_np
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

        if (len(order) == 2):  # TargetingType = 0
            cible = getCible(order[1])
        else:  # TargetingType = 1
            cibleA = getCible(order[1])
            cibleB = getCible(order[2])
            cible = cibleA.mixage(cibleB, order[3])
        if (order[0] == "se déplace vers"):
            actionMustStop = I.proximiteAtteinte(cible)
            return (I.allerVers(cible), actionMustStop)
        elif (order[0] == "tire vers"):
            return (I.tirerVers(cible), True)
        elif (order[0] == "tire versL"):
            return (I.tirerVers(cible, low=True), True)
        elif (order[0] == "dribble vers"):
            actionMustStop = I.proximiteAtteinte(cible)
            if (not actionMustStop):
                self.addOrder(order)
            return (I.allerVers(cible), actionMustStop)

    def addOrder(self,order):
        self.resetOrders()
        if (order[0] == "tire vers"):
            self.orderList.append(["se déplace vers", "Balle"])
        if (order[0] == "dribble vers"):
            self.orderList.append(["se déplace vers","Balle"])
            orderTmp = order.copy()
            orderTmp[0] = "tire versL"
            self.orderList.append(orderTmp)
        self.orderList.append(order)

    def resetOrders(self):
        self.orderList = []

    def getCurrentOrder(self):
        if(self.orderList):
            return self.orderList[-1]
            return [self.orderList[-1][0],self.orderList[-1][1]]
        else:
            return None

