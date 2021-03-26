import random
from soccersimulator import csvHandler
from soccersimulator import Vector2D
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import DistanceMetric
import numpy as np
from itertools import permutations
import scipy

class Entraineur(object):
    def __init__(self, waitRound):
        self.initial_waitRound = waitRound
        self.waitRound = 0
        self.orderStrategies = dict()
        self.csvHandler = csvHandler()
        self.myTeam = None
        self.nbPlayer = None
        pass

    def setter(self, team,nbPlayer):
        self.myTeam = team
        self.nbPlayer = nbPlayer

    def setOrderStrategies(self,orderStrategies):
        self.orderStrategies = orderStrategies

    def getOrderStrategies(self):
        return self.orderStrategies

    def decrementeWaitRound(self):
        self.waitRound -= 1

    def giveOrders(self):
        if(self.waitRound > 0):
            self.decrementeWaitRound()
            return None
        orders = self.thinkOrders()
        self.applyOrders(orders)
        self.waitRound = self.initial_waitRound

    def thinkOrders(self):
        pass

    def applyOrders(self, orders):
        for joueur in self.orderStrategies.keys():
            if(orders.get(joueur,"Continuer") != "Continuer"):
                self.orderStrategies[joueur].addOrder(orders[joueur])

class EntraineurRandom(Entraineur):
    def __init__(self, listeAction, listeCible):
        super(EntraineurRandom,self).__init__(20)
        self.listeAction = listeAction
        self.listeCible = listeCible
        pass

    def thinkOrders(self):
        orders = dict()
        for joueur in self.orderStrategies.keys():
            if(random.randint(0,1) == 1):
                actionIndex = random.randint(0,len(self.listeAction)-1)
                cibleIndex = random.randint(0,len(self.listeCible)-1)
                orders[joueur] = [self.listeAction[actionIndex],self.listeCible[cibleIndex]]
            else:
                orders[joueur] = "Continuer"
        return orders

class EntraineurKNN(Entraineur):
    def __init__(self):
        super(EntraineurKNN, self).__init__(1)
        self.statesData = None
        self.ordersData = None
        self.currentStateForKNN = None
        self.knn = KNeighborsClassifier(n_neighbors=1)
        self.dist = scipy.spatial.distance.pdist

    def setter(self, team, nbPlayer):
        super(EntraineurKNN, self).setter(team,nbPlayer)
        self.statesData = self.dataToKNNStates(self.csvHandler.readStateCsv('../soccersimulator/etats.csv'))
        self.ordersData = self.csvHandler.readOrderCsv('../soccersimulator/ordres.csv')
        self.knn.fit(self.statesData, [i for i in range(len(self.ordersData))])

    def setCurrentState(self, currentState):
        listeElem = currentState.ball.position.toList()+currentState.ball.nextLikelyPosition.toList()
        for k, p in sorted(currentState.states.items()):
            listeElem+=p.position.toList()
            #print(k,p) ##TODO for combinatoire
        self.currentStateForKNN = np.array(listeElem)

    def thinkOrders(self):
        if(len(self.statesData)==0):
            return dict()

        doPermut = True
        if doPermut:
            closestDist = None
            closestPermutValue = [None, None]
            closestPermutIndex = None
            # Pour chaque permut, faire un knn.predict, puis calculer la metrique entre les deux
            # Pour 24² permuts (=4 joueurs par équipe), il faut parcourir toutes les données pour déterminer la plus proches... LOL c'est déjà beaucoup trop
            # La permut avec la metrique la plus faible est choisie
            # Il faut ensuite permut les ordres en fonction de la permut choisies...
            #Determiner les permutations possibles
            indexJoueur = [4,4+2*(self.nbPlayer[0]-1),4+2*(self.nbPlayer[0]),4+2*(sum(self.nbPlayer))-2]
            permsTeam1 = [i for i in permutations([i for i in range(self.nbPlayer[0])])] #Car boucles imbriquees d'itertools ne fonctionne pas wtf :(
            permsTeam2 = [i for i in permutations([i for i in range(self.nbPlayer[1])])]
            for permut1 in permsTeam1:
                for permut2 in permsTeam2:
                    #Création du vecteur State correspondant à la permutation
                    currentPermut = np.zeros(self.currentStateForKNN.shape)
                    currentPermut[:4] = self.currentStateForKNN[:4]
                    for index in range(len(permut1)):
                        positionToAdd = indexJoueur[0]+index*2
                        currentPermut[positionToAdd:positionToAdd+2] = self.currentStateForKNN[indexJoueur[0]+permut1[index]*2:indexJoueur[0]+permut1[index]*2+2]
                    for index in range(len(permut2)):
                        positionToAdd = indexJoueur[2]+index*2
                        currentPermut[positionToAdd:positionToAdd+2] = self.currentStateForKNN[indexJoueur[2]+permut1[index]*2:indexJoueur[2]+permut1[index]*2+2]
                    #Prédiction de la donnée la plus proche
                    bestCurrentPermutIndex = self.knn.predict(currentPermut.reshape(1,-1))[0]
                    closestPermutState = self.statesData[bestCurrentPermutIndex]
                    #Calcul de la métrique
                    bothStates = np.zeros((2,currentPermut.shape[0]))
                    bothStates[0,:] = currentPermut
                    bothStates[1,:] = closestPermutState
                    currentPermutDist = self.dist(bothStates)
                    #Maximum sur les métriques
                    if(not closestDist):
                        closestDist = currentPermutDist
                        closestPermutValue[0], closestPermutValue[1] = permut1, permut2
                        closestPermutIndex = bestCurrentPermutIndex
                    if(closestDist>currentPermutDist):
                        closestDist = currentPermutDist
                        closestPermutValue[0],closestPermutValue[1] = permut1,permut2
                        closestPermutIndex = bestCurrentPermutIndex
            #print(closestDist,closestPermutValue, closestPermutIndex)
            #Si on a une autre permut que celle initiale, on doit modifier les ordres à donner !
            if(closestPermutValue[self.myTeam-1] != tuple([i for i in range(self.nbPlayer[self.myTeam-1])])):
                noPermutOrder = self.ordersData[closestPermutIndex]
                closestOrders = noPermutOrder.copy()
                for i in range(len(closestPermutValue[self.myTeam-1])):
                    iOrder = noPermutOrder.get(str((self.myTeam, i)),None)
                    if(iOrder):
                        closestOrders[str((self.myTeam,closestPermutValue[self.myTeam-1][i]))] = iOrder
            else:
                closestOrders = self.ordersData[closestPermutIndex]
        #Cas sans permutation
        else:
            bestStateIndex = self.knn.predict(self.currentStateForKNN.reshape(1, -1))[0]
            closestOrders = self.ordersData[bestStateIndex]

        #Application des ordres
        orders = dict()
        for joueur in self.orderStrategies.keys():
            closestOrder = closestOrders.get("("+str(self.myTeam)+", "+str(joueur)+")", None)
            if closestOrder:
                if closestOrder[1][0] == "(":
                    closestOrder[1] = self.csvHandler.strToIntTuple(closestOrder[1])
                if len(closestOrder) > 2:
                    if closestOrder[-2][0] == "(":
                        closestOrder[-2] = self.csvHandler.strToIntTuple(closestOrder[-2])
                    if closestOrder[-2][0] == "(":
                        closestOrder[-2] = self.csvHandler.strToIntTuple(closestOrder[-2])
                    closestOrder[-1] = float(closestOrder[-1])
                orders[joueur] = closestOrder
        return orders

    def dataToKNNStates(self,dataStates):
        states = np.zeros((len(dataStates),4+2*(sum(self.nbPlayer))))
        for iState in range(len(dataStates)):
            state = dataStates[iState]
            currentState = list(state["ball"][0])+list(state["ball"][1])
            for elem in state["team1"]:
                currentState+=list(elem["position"])
            for elem in state["team2"]:
                currentState+=list(elem["position"])
            states[iState] = currentState
        return states

    def caculSimilarite(self, state1, state2):
        moy = 0
        for i in range(len(state1)):
            moy += state1[i].distance(state2[i])
        return moy

    def distanceEuclidienne(self,Vec1,Vec2):
        return Vector2D(Vec1[0],Vec1[1]).distance(Vector2D(Vec2[0],Vec2[1]))

