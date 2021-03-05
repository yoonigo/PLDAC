from soccersimulator  import Strategy, SoccerAction, Vector2D, Simulation
from .tools import SuperState, Comportement, get_random_SoccerAction
from .briques import ComportementNaif, ComportementNew, ConditionAttaque,ConditionDefenseur,fonceur, fonceurNew,defenseur,executeOrder
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
            action = executeOrder(I,self.orderList[0],Simulation.ETAT.states)
            if(action[1] == True):
                self.orderList.pop(0)
                if(self.orderList):
                    action = executeOrder(I, self.orderList[0], Simulation.ETAT.states)
            return action[0]

        return fonceurNew(I)

    def addOrder(self,order):
        self.resetOrders()
        self.orderList.append(order)
        if(order[0] == "tire vers"):
            self.orderList.insert(0,["se déplace vers", "Balle"])
    def resetOrders(self):
        self.orderList = []

    def getCurrentOrder(self):
        if(self.orderList):
            return [self.orderList[-1][0],self.orderList[-1][1]]
        else:
            return None

