import sys
import random
from soccersimulator import csvHandler
from soccersimulator import Vector2D
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.svm import SVR
from sklearn.multioutput import MultiOutputRegressor
from sklearn.neighbors import DistanceMetric
import numpy as np
from itertools import permutations
import scipy
from soccersimulator import GAME_HEIGHT, GAME_WIDTH

class Entraineur(object):
    def __init__(self, waitRound):
        self.initial_waitRound = waitRound
        self.waitRound = 0
        self.orderStrategies = dict()
        self.csvHandler = None
        self.myTeam = None
        self.nbPlayer = None
        self.ignoredPlayer = None
        pass

    def setter(self, idteam,nbPlayer):
        self.myTeam = idteam
        self.nbPlayer = nbPlayer
        self.csvHandler = csvHandler(self.myTeam,self.nbPlayer)

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
            if(joueur != self.ignoredPlayer):
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

@DeprecationWarning
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

        doPermut = False
        if doPermut:
            closestDist = None
            closestPermutValue = [None, None]
            closestPermutIndex = None
            # Pour chaque permut, faire un knn.predict, puis calculer la metrique entre les deux
            # Pour 24² permuts (=4 joueurs par equipe), il faut parcourir toutes les donnees pour determiner la plus proches... LOL c'est dejà beaucoup trop
            # La permut avec la metrique la plus faible est choisie
            # Il faut ensuite permut les ordres en fonction de la permut choisies...
            #Determiner les permutations possibles
            indexJoueur = [4,4+2*(self.nbPlayer[0]-1),4+2*(self.nbPlayer[0]),4+2*(sum(self.nbPlayer))-2]
            permsTeam1 = [i for i in permutations([i for i in range(self.nbPlayer[0])])] #Car boucles imbriquees d'itertools ne fonctionne pas wtf :(
            permsTeam2 = [i for i in permutations([i for i in range(self.nbPlayer[1])])]
            for permut1 in permsTeam1:
                for permut2 in permsTeam2:
                    #Creation du vecteur State correspondant à la permutation
                    currentPermut = np.zeros(self.currentStateForKNN.shape)
                    currentPermut[:4] = self.currentStateForKNN[:4]
                    for index in range(len(permut1)):
                        positionToAdd = indexJoueur[0]+index*2
                        currentPermut[positionToAdd:positionToAdd+2] = self.currentStateForKNN[indexJoueur[0]+permut1[index]*2:indexJoueur[0]+permut1[index]*2+2]
                    for index in range(len(permut2)):
                        positionToAdd = indexJoueur[2]+index*2
                        currentPermut[positionToAdd:positionToAdd+2] = self.currentStateForKNN[indexJoueur[2]+permut1[index]*2:indexJoueur[2]+permut1[index]*2+2]
                    #Prediction de la donnee la plus proche
                    bestCurrentPermutIndex = self.knn.predict(currentPermut.reshape(1,-1))[0]
                    closestPermutState = self.statesData[bestCurrentPermutIndex]
                    #Calcul de la metrique
                    bothStates = np.zeros((2,currentPermut.shape[0]))
                    bothStates[0,:] = currentPermut
                    bothStates[1,:] = closestPermutState
                    currentPermutDist = self.dist(bothStates)
                    #Maximum sur les metriques
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
            #print("closestOrder :",closestOrder)
            if closestOrder:
                #print("closestOrder[1] :", closestOrder[1])
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

######################################################################################################

class EntraineurDistribueAbs(Entraineur):
    def __init__(self):
        super(EntraineurDistribueAbs, self).__init__(1)
        self.statesData = None
        self.ordersData = None
        self.currentStateForKNN = None
        self.knn = KNeighborsClassifier(n_neighbors=1)
        self.dist = scipy.spatial.distance.pdist

    def setter(self, team, nbPlayer):
        super(EntraineurDistribueAbs, self).setter(team,nbPlayer)
        self.statesData = self.dataToKNNStates(self.csvHandler.readStateCsv('../soccersimulator/etats.csv'))
        self.ordersData = self.csvHandler.readOrderCsv('../soccersimulator/ordres.csv')

    def setCurrentState(self, currentState):
        listeElem = currentState.ball.position.toList()+currentState.ball.nextLikelyPosition.toList()
        for k, p in sorted(currentState.states.items()):
            listeElem+=p.position.toList()
            #print(k,p) ##TODO for combinatoire
        self.currentStateForKNN = np.array(listeElem)

    def thinkOrders(self):
        if(len(self.statesData)==0):
            return dict()
        orders = dict()
        for joueur in self.orderStrategies.keys():
            self.knn.fit(self.statesData, [i for i in range(len(self.ordersData))])
            bestStateIndex = self.knn.predict(self.currentStateForKNN.reshape(1, -1))[0]
            closestOrders = self.ordersData[bestStateIndex]
            closestOrder = closestOrders.get("("+str(self.myTeam)+", "+str(joueur)+")", None)
            #print("closestOrder :",closestOrder)
            if closestOrder:
                #print("closestOrder[1] :", closestOrder[1])
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
        #print(states.shape)
        for iState in range(len(dataStates)):
            state = dataStates[iState]
            currentState = list(state["ball"][0])+list(state["ball"][1])
            for elem in state["team1"]:
                currentState+=list(elem["position"])
            for elem in state["team2"]:
                currentState+=list(elem["position"])
            states[iState] = currentState
        #print(states)
        return states

    def caculSimilarite(self, state1, state2):
        moy = 0
        for i in range(len(state1)):
            moy += state1[i].distance(state2[i])
        return moy

    def distanceEuclidienne(self,Vec1,Vec2):
        return Vector2D(Vec1[0],Vec1[1]).distance(Vector2D(Vec2[0],Vec2[1]))

#########################################################################################

class EntraineurDistribueRel(Entraineur):
    def __init__(self, orderByCageDist = False, nbNeighbors = 1):
        super(EntraineurDistribueRel, self).__init__(0)
        self.statesData = None
        self.statesOrdonnancement = None
        self.ordersData = None
        self.currentStateForKNN = None
        self.currentStateOrdonnancement = None
        self.nbNeighbors = nbNeighbors
        self.orderByCageDist = orderByCageDist
        self.dist = scipy.spatial.distance.pdist

    def setter(self, team, nbPlayer):
        super(EntraineurDistribueRel, self).setter(team,nbPlayer)
        statesData = self.dataToKNNStates(self.csvHandler.import_csv('../soccersimulator/etats.csv', self.csvHandler.rowToREL))
        self.statesData = statesData[0]
        self.statesOrdonnancement = statesData[1]
        #self.ordersData = self.csvHandler.readOrderCsv('../soccersimulator/ordres.csv')
        self.ordersData = self.csvHandler.encode('../soccersimulator/ordres.csv')
        self.playerOrdersIndex = {}
        if self.orderByCageDist:
            for iData in range(len(self.ordersData)):
                for key in self.ordersData[iData].keys():
                    if (int(key[1]) == team):
                        liste = self.playerOrdersIndex.get(self.statesOrdonnancement[iData][key], None)
                        if (liste):
                            liste.append(iData)
                        else:
                            self.playerOrdersIndex[self.statesOrdonnancement[iData][key]] = [iData]
            self.positionKNN = {}
            for key in self.playerOrdersIndex.keys():
                self.positionKNN[key] = KNeighborsClassifier(n_neighbors=self.nbNeighbors)
                print(len(self.playerOrdersIndex[key]))
                self.positionKNN[key].fit(self.statesData[self.playerOrdersIndex[key]],self.playerOrdersIndex[key])
        else:
            for iData in range(len(self.ordersData)):
                for key in self.ordersData[iData].keys():
                    if(int(key[1]) == team):
                        liste = self.playerOrdersIndex.get(key,None)
                        if (liste):
                            liste.append(iData)
                        else:
                            self.playerOrdersIndex[key] = [iData]
            #print(self.playerOrdersIndex)
            self.playerKNN = {}
            for key in self.playerOrdersIndex.keys():
                self.playerKNN[key] = KNeighborsClassifier(n_neighbors=self.nbNeighbors)
                self.playerKNN[key].fit(self.statesData[self.playerOrdersIndex[key]],self.playerOrdersIndex[key])


    def setCurrentState(self, currentState):
        list=[]
        ordonnancement = {}
        team1Ordonne = []
        team2Ordonne = []
        CageTeam1 = Vector2D(0, GAME_HEIGHT/2)
        CageTeam2 = Vector2D(GAME_WIDTH, GAME_HEIGHT/2)
        distDef1=[]
        distAdv1=[]
        distDef2=[]
        distAdv2=[]
        for k,v in (currentState.players):
            if(not self.orderByCageDist):
                list+=self.getPlayerKNNState(currentState, k,v)
            if k == 1:
                # Distances entre la cage de l'equipe 1 et les joueurs de l'equipe 1
                distDef1.append(CageTeam1.distance(currentState.player_state(k,v).position))
                # Distances entre la cage de l'equipe 2 et les joueurs de l'equipe adverse 1
                distAdv2.append(CageTeam2.distance(currentState.player_state(k,v).position))
                #Pour la version avec permutation
                currentList = team1Ordonne
                distToCage = distDef1[-1]
            else:
                # Distances entre la cage de l'equipe 1 et les joueurs de l'equipe adverse 2
                distAdv1.append(CageTeam1.distance(currentState.player_state(k,v).position))
                # Distances entre la cage de l'equipe 2 et les joueurs de l'equipe 2
                distDef2.append(CageTeam2.distance(currentState.player_state(k,v).position))
                #Pour la version avec permutation
                currentList = team2Ordonne
                distToCage = distDef2[-1]
            if(self.orderByCageDist):
                if len(currentList) == 0:
                    currentList.append((k, v, distToCage))
                else:
                    index = 0
                    isAfter = True
                    while index < len(currentList) and isAfter:
                        if (currentList[index][2] <= distToCage):
                            index += 1
                        else:
                            isAfter = False
                    if (index == len(currentList)):
                        currentList.append((k, v, distToCage))
                    else:
                        currentList.insert(index, (k, v, distToCage))
        if (self.orderByCageDist):
            for iJoueurProximite in range(len(team1Ordonne)):
                ordonnancement["(" + str(team1Ordonne[iJoueurProximite][0]) + ", " + str(team1Ordonne[iJoueurProximite][1]) + ")"] = iJoueurProximite
            for iJoueurProximite in range(len(team2Ordonne)):
                ordonnancement["(" + str(team2Ordonne[iJoueurProximite][0]) + ", " + str(team2Ordonne[iJoueurProximite][1]) + ")"] = iJoueurProximite
            k = 1
            v = 0
            isDone = False
            while not isDone:
                for key in ordonnancement.keys():
                    if(int(key[1]) == k and ordonnancement[key] == v):
                        list += self.getPlayerKNNState(currentState, int(key[1]), int(key[4]))
                        #print(k,v,list)
                        if(v != 3):
                            v+=1
                        else:
                            if(k == 1):
                                k+=1
                                v=0
                            else:
                                isDone = True
        # Distance CageTeam1 et defenseur allie le plus proche
        list.append(min(distDef1))
        # Distance CageTeam1 et attaquant adverse le plus proche
        list.append(min(distAdv1))
        # Distance entre la balle et la cage de l'equipe 1
        list.append(CageTeam1.distance(currentState.ball.position))
        # Distance CageTeam2 et defenseur allie le plus proche
        list.append(min(distDef2))
        # Distance CageTeam2 et attaquant adverse le plus proche
        list.append(min(distAdv2))
        # Distance entre la balle et la cage de l'equipe 2
        list.append(CageTeam2.distance(currentState.ball.position))
        self.currentStateForKNN = np.array(list)
        self.currentStateOrdonnancement = ordonnancement

    def thinkOrders(self):
        if(len(self.statesData)==0):
            return dict()
        orders = dict()
        for joueur in self.orderStrategies.keys():
            positionALaCage = None
            joueurID = "(" + str(self.myTeam) + ", " + str(joueur) + ")"
            bestStateOrdreID = None
            #print("("+str(self.myTeam)+", "+str(joueur)+")")
            #print(self.playerKNN["("+str(self.myTeam)+", "+str(joueur)+")"].predict(self.currentStateForKNN.reshape(1, -1))[0])
            #print(self.playerKNN["("+str(self.myTeam)+", "+str(joueur)+")"].predict_proba(self.currentStateForKNN.reshape(1, -1))[0])
            #sys.exit()
            if self.orderByCageDist:
                #On calcule avant tout la position a la cage du joueur dans l'etat courrant
                positionALaCage = self.currentStateOrdonnancement[joueurID]

                #L'état le plus proche
                bestStateIndex = self.positionKNN[positionALaCage].predict(self.currentStateForKNN.reshape(1, -1))[0]

                #L'identifiant de l'ordre associe a l'etat le plus proche en fonction de la position a la cage
                bestStateOrdreID = self.positionToCageToOrderID(positionALaCage,bestStateIndex,self.myTeam)
                #Enfin les probabilites sur les etats les plus proches
                statesProbas = self.positionKNN[positionALaCage].predict_proba(self.currentStateForKNN.reshape(1, -1))[0]
                #if (joueurID == "(1, 3)"):
                #    print("*** IN THINK ORDER *************************************************")
                #    print("Position à Cage : ", positionALaCage)
                #    print("BestStateIndex : ", bestStateIndex)
                #    print("Etat courrant : ", self.currentStateForKNN)
                #    print("Les probas :\n",statesProbas)
            else:
                bestStateIndex = self.playerKNN[joueurID].predict(self.currentStateForKNN.reshape(1, -1))[0]
                statesProbas = self.playerKNN[joueurID].predict_proba(self.currentStateForKNN.reshape(1, -1))[0]
            indNearestStates=[]
            #if (joueurID == "(1, 3)"):
            #    print("Soit les indices : ", end = "")
            for i in range(self.nbNeighbors):
                index = max(range(len(statesProbas)), key=statesProbas.__getitem__)
                if statesProbas[index] != 0:
                    if(self.orderByCageDist):
                        #if (joueurID == "(1, 3)"):
                        #    print(index,end=" ")
                        indNearestStates.append(self.playerOrdersIndex[positionALaCage][index])
                    else:
                        indNearestStates.append(self.playerOrdersIndex[joueurID][index])
                    statesProbas[index] = 0
            # L'état le plus proche, on le passe en paramètre de decode au cas où on a une égalité entre les cibles/actions #TODO
            if (self.orderByCageDist):
                #if (joueurID == "(1, 3)"):
                #    print("\nSoit les données : ",indNearestStates)
                #    print("Avec la derniere donnee ",len(statesProbas)-1," etant ",self.playerOrdersIndex[positionALaCage][len(statesProbas)-1])
                nearestOrder = self.ordersData[bestStateIndex].get(bestStateOrdreID,None)
                mixedOrder = self.mixOrders(indNearestStates, bestStateOrdreID, positionALaCage)
                #if (joueurID == "(1, 3)"):
                #    print("MixedOrder : ", mixedOrder)
            else:
                nearestOrder = self.ordersData[bestStateIndex].get(joueurID, None)
                mixedOrder = self.mixOrders(indNearestStates, joueurID)
            #if (joueur == 0 and self.myTeam == 1):
            #    print("ORDER A ENCODER : ", mixedOrder)
            closestOrder = self.csvHandler.decode(mixedOrder)
            #if (joueurID == "(1, 3)"):
            #    print("Soit l'ordre decode : ", closestOrder)
            #closestOrders = self.ordersData[bestStateIndex]
            ##closestOrders = self.csvHandler.decode1NN(self.ordersData[bestStateIndex])
            ##closestOrder = closestOrders.get("("+str(self.myTeam)+", "+str(joueur)+")", None)
            #print(closestOrder) --> ['tire vers', 'CageAdverse']
            #if (joueur == 0 and self.myTeam == 1):
            #    print("ORDRE DECODER: ",closestOrder)
            if closestOrder:
                if (self.orderByCageDist):
                    if closestOrder[1][0] == "(":
                        closestOrder[1] = self.csvHandler.strToIntTuple(self.swapPlayerTargetWithPositionToCage(closestOrder[1], bestStateIndex))
                    if len(closestOrder) > 2:
                        if closestOrder[-2][0] == "(":
                            closestOrder[-2] = self.csvHandler.strToIntTuple(self.swapPlayerTargetWithPositionToCage(closestOrder[-2], bestStateIndex))
                        closestOrder[-1] = float(closestOrder[-1])
                else:
                    if closestOrder[1][0] == "(":
                        closestOrder[1] = self.csvHandler.strToIntTuple(closestOrder[1])
                    if len(closestOrder) > 2:
                        if closestOrder[-2][0] == "(":
                            closestOrder[-2] = self.csvHandler.strToIntTuple(closestOrder[-2])
                        closestOrder[-1] = float(closestOrder[-1])
                orders[joueur] = closestOrder
        return orders

    def mixOrders(self, indStates, joueurID, positionToCage = None):
        #Simplement une moyenne des valeurs mixees !
        if self.orderByCageDist:
            order = self.ordersData[indStates[0]].get(self.positionToCageToOrderID(positionToCage,indStates[0],self.myTeam), None).copy()
            #if(joueurID == "(1, 3)"):
            #    print(indStates[0], " : ", order)
        else:
            order = self.ordersData[indStates[0]].get(joueurID, None).copy()
        for iInd in range(1,len(indStates)):
            if self.orderByCageDist:
                order += self.ordersData[indStates[iInd]].get(self.positionToCageToOrderID(positionToCage,indStates[iInd],self.myTeam), None).copy()
                #if (joueurID == "(1, 3)"):
                #    print(indStates[iInd], " : ", self.ordersData[indStates[iInd]].get(self.positionToCageToOrderID(positionToCage,indStates[iInd],self.myTeam), None).copy())
                #    print(indStates[iInd], " : ", self.statesData[indStates[iInd]].copy())
            else:
                order += self.ordersData[indStates[iInd]].get(joueurID, None).copy()
        #if (joueurID == "(1, 3)"):
        #    print("Position derniere donnee : ",len(self.ordersData)-1)
        #    print("Dernier ordre : ", self.ordersData[-1].get(self.positionToCageToOrderID(positionToCage,len(self.ordersData)-1,self.myTeam), None).copy())
        #    print("Derniere donnée : ", self.statesData[-1].copy())
        order = order/len(indStates)
        return order

    def positionToCageToOrderID(self, positionToCage, stateIndex, team):
        for key in self.statesOrdonnancement[stateIndex].keys():
            if(self.statesOrdonnancement[stateIndex][key] == positionToCage and int(key[1]) == team):
                return key

    def swapPlayerTargetWithPositionToCage(self, cible, stateIndex):
        """
        Cette fonction a pour but de modifier la cible d'une action.
        En effet si dans la base de donnee on a tirer vers un Joueur X, on veut en fait tirer vers le joueur qui occupe la position du joueur X.
        """
        positionALaCage = self.statesOrdonnancement[stateIndex][cible]
        for key in self.currentStateOrdonnancement.keys():
            if(self.currentStateOrdonnancement[key] == positionALaCage and int(key[1]) == int(cible[1])):
                return key
        return "none"

    def dataToKNNStates(self,dataStates):#modif
        #print(currentState)
        #shape 0 : nombre de lignes dans le csv etats
        #shape 1 : nombre de donnees
        # => format du csv
        nbValuePerJoueur = 5 #Attention 7 si on rajoute les positions (lignes en commentaires)
        states = np.zeros((len(dataStates),6+nbValuePerJoueur*(sum(self.nbPlayer))))
        ordonnancements = [{} for i in range(len(dataStates))]
        for iState in range(len(dataStates)):
            currentState=[None for i in range(sum(self.nbPlayer)*nbValuePerJoueur)]
            state = dataStates[iState]
            indiceJoueur = 0
            for joueur in state['joueursTeam1']:
                if (self.orderByCageDist): #Soit on selectionne les joueurs dans l'ordre de proximite de la cage (ordre de base)
                    finalIndex = indiceJoueur
                    ordonnancements[iState][str(joueur["id"])] = indiceJoueur
                else: #Soit on selectionne toujours le j0 en premier puis j1 etc (sans la distance a la cage)
                    finalIndex = joueur["id"][1]
                #Position du joueur
                #currentState.append(joueur["position"][0])
                #currentState.append(joueur["position"][1])
                # Distance à l'allie le plus proche
                currentState[0+finalIndex*5] = joueur['distAllieLPP']
                # Distance à l'adversaire le plus proche
                currentState[1+finalIndex*5] = joueur['distAdvLPP']
                # Distance à la Balle
                currentState[2+finalIndex*5] = joueur['distBall']
                # Distance à la cage de son equipe
                currentState[3+finalIndex*5] = joueur['distSaCage']
                # Distance à la cage adversaire
                currentState[4+finalIndex*5] = joueur['distCageAdv']
                indiceJoueur += 1
            indiceJoueur = 0
            nbValueTeam1 = nbValuePerJoueur * self.nbPlayer[0]
            for joueur in state['joueursTeam2']:
                if (self.orderByCageDist): #Soit on selectionne les joueurs dans l'ordre de proximite de la cage (ordre de base)
                    finalIndex = indiceJoueur
                    ordonnancements[iState][str(joueur["id"])] = indiceJoueur
                else: #Soit on selectionne toujours le j0 en premier puis j1 etc (sans la distance a la cage)
                    finalIndex = joueur["id"][1]
                # Position du joueur
                # currentState.append(joueur["position"][0])
                # currentState.append(joueur["position"][1])
                currentState[nbValueTeam1+ 0 + finalIndex * 5] = joueur['distAllieLPP']
                currentState[nbValueTeam1+ 1 + finalIndex * 5] = joueur['distAdvLPP']
                currentState[nbValueTeam1+ 2 + finalIndex * 5] = joueur['distBall']
                currentState[nbValueTeam1+ 3 + finalIndex * 5] = joueur['distSaCage']
                currentState[nbValueTeam1+ 4 + finalIndex * 5] = joueur['distCageAdv']
                indiceJoueur += 1
            equipe=state['positionsTeam1']
            currentState.append(equipe['distAdvLPPCage'])
            currentState.append(equipe['distDefLPPCage'])
            currentState.append(equipe['distBallCage'])
            equipe=state['positionsTeam2']
            currentState.append(equipe['distAdvLPPCage'])
            currentState.append(equipe['distDefLPPCage'])
            currentState.append(equipe['distBallCage'])
            #print(currentState)
            states[iState] = currentState
        return states, ordonnancements

    def caculSimilarite(self, state1, state2):
        moy = 0
        for i in range(len(state1)):
            moy += state1[i].distance(state2[i])
        return moy

    def distanceEuclidienne(self,Vec1,Vec2):
        return Vector2D(Vec1[0],Vec1[1]).distance(Vector2D(Vec2[0],Vec2[1]))


    def getPlayerKNNState(self, currentState, team, id):
        playerPosition = currentState.player_state(team, id).position
        #playerType = self.get_team(team).player_type(id)

        if(team == 1):
            # Distance à la cage de son equipe
            SaCage = Vector2D(0, GAME_HEIGHT/2)
            distCage = playerPosition.distance(SaCage)
            # Distance à la cage adverse
            CageAdverse = Vector2D(GAME_WIDTH, GAME_HEIGHT/2)
            distCageAdverse = playerPosition.distance(CageAdverse)
        else:
            # Distance à la cage de son equipe
            SaCage = Vector2D(GAME_WIDTH, GAME_HEIGHT/2)
            distCage = playerPosition.distance(SaCage)
            # Distance à la cage adverse
            CageAdverse = Vector2D(0, GAME_HEIGHT/2)
            distCageAdverse = playerPosition.distance(CageAdverse)

        # Distances à l'allie le plus proche et à l'adversaire le plus proche + leurs types
        allieDist=[]
        #allieType=[]
        advDist=[]
        #advType=[]

        for k, v in currentState.players:
            if k == team and id == v:
                continue
            if k == team:
                # distance à l'allie le plus proche + type
                distance = currentState.player_state(k,v).position.distance(playerPosition)
                #type = self.get_team(k).player_type(v)
                allieDist.append(distance)
                #allieType.append(type)
            else:
                #distance à l'adversaire le plus proche + type
                distance = currentState.player_state(k,v).position.distance(playerPosition)
                #type = self.get_team(k).player_type(v)
                advDist.append(distance)
                #advType.append(type)

        # distance à l'allie le plus proche + type
        index = min(range(len(allieDist)), key=allieDist.__getitem__)
        APP = allieDist[index]
        #typeAPP = allieType[index]

        #distance à l'adversaire le plus proche + type
        index = min(range(len(advDist)), key=advDist.__getitem__)
        AdvPP = advDist[index]
        #typeAdvPP = advType[index]

        # Distance à la Balle
        dist2Ball = playerPosition.distance(currentState.ball.position)

        #res = [playerPosition.x, playerPosition.y, APP, AdvPP, dist2Ball, distCage, distCageAdverse] #Sans Position pour le Relatif !
        res = [APP, AdvPP, dist2Ball, distCage, distCageAdverse]
        return res

#############################################

class EntraineurSVM(Entraineur):
    def __init__(self, orderByCageDist = False):
        super(EntraineurSVM, self).__init__(0)
        self.statesData = None
        self.ordersData = None
        self.currentStateForSVM = None

        self.statesOrdonnancement = None
        self.currentStateOrdonnancement = None
        self.orderByCageDist = orderByCageDist

    def setter(self, team, nbPlayer):
        super(EntraineurSVM, self).setter(team,nbPlayer)
        #self.statesData = self.dataToSVMStates(self.csvHandler.import_csv('../soccersimulator/etats.csv', self.csvHandler.rowToREL))
        statesData = self.dataToSVMStates(self.csvHandler.import_csv('../soccersimulator/etats.csv', self.csvHandler.rowToREL))
        self.statesData = statesData[0]
        self.statesOrdonnancement = statesData[1]
        self.ordersData = self.csvHandler.encode('../soccersimulator/ordres.csv')
        self.playerOrdersIndex = {}
        self.playerOrdersEncoding = {}

        if self.orderByCageDist:
            for iData in range(len(self.ordersData)):
                idPlayers = self.ordersData[iData].keys()
                for id in idPlayers: # team + num
                    if (int(id[1]) == team):
                        position = self.statesOrdonnancement[iData][id]
                        liste = self.playerOrdersIndex.get(position, None)
                        listeEncode = self.playerOrdersEncoding.get(position, None)
                        if (liste):
                            liste.append(iData)
                        else:
                            self.playerOrdersIndex[position] = [iData]
                        if (not listeEncode is None):
                            self.playerOrdersEncoding[position] = np.concatenate((listeEncode, self.ordersData[iData][id]), axis=0)
                        else:
                            self.playerOrdersEncoding[position] = np.array(self.ordersData[iData][id])

            self.positionSVR_deplace = {}
            self.positionSVR_tire = {}
            self.positionSVR_dribble = {}
            self.positionSVC = {}
            for idJoueur in self.playerOrdersIndex.keys():
                self.positionSVR_deplace[idJoueur] = MultiOutputRegressor(SVR(kernel='rbf'))
                self.positionSVR_dribble[idJoueur] = MultiOutputRegressor(SVR(kernel='rbf'))
                self.positionSVR_tire[idJoueur] = MultiOutputRegressor(SVR(kernel='rbf'))
                self.positionSVC[idJoueur] = SVC(kernel='rbf', probability=True)

                #etats_deplace = np.array([self.statesData[ind] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[0]==1])
                #etats_tire = np.array([self.statesData[ind] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[1]==1])
                #etats_dribble = np.array([self.statesData[ind] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[2]==1])

                #cibles_deplace = np.array([self.ordersData[ind].get(idJoueur)[3:] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[0]==1])

                etats = self.statesData[self.playerOrdersIndex[idJoueur]]
                ordresIndices = self.playerOrdersIndex[idJoueur]
                ordresEncoding = self.playerOrdersEncoding[idJoueur].reshape((int(self.playerOrdersEncoding[idJoueur].shape[0] / 23), 23))

                etats_deplace = np.array([self.statesData[ordresIndices[i]] for i in range(len(ordresIndices)) if ordresEncoding[i][0]==1])
                etats_tire = np.array([self.statesData[ordresIndices[i]] for i in range(len(ordresIndices)) if ordresEncoding[i][1]==1])
                etats_dribble = np.array([self.statesData[ordresIndices[i]] for i in range(len(ordresIndices)) if ordresEncoding[i][2]==1])
                #print(etats_deplace.shape,etats_tire.shape,etats_dribble.shape)

                cibles_deplace = np.array([ord[3:] for ord in ordresEncoding if ord[0] == 1])
                cibles_tire = np.array([ord[3:] for ord in ordresEncoding if ord[1] == 1])
                cibles_dribble = np.array([ord[3:] for ord in ordresEncoding if ord[2] == 1])

                #print(etats_deplace.shape, cibles_deplace.shape)
                #print(etats_tire.shape, cibles_tire.shape)
                #print(etats_dribble.shape, cibles_dribble.shape)

                if etats_deplace.shape[0] != 0:
                    self.positionSVR_deplace[idJoueur].fit(etats_deplace, cibles_deplace)
                if etats_tire.shape[0] != 0:
                    self.positionSVR_tire[idJoueur].fit(etats_tire, cibles_tire)
                if etats_dribble.shape[0] != 0:
                    self.positionSVR_dribble[idJoueur].fit(etats_dribble, cibles_dribble)
                self.positionSVC[idJoueur].fit(etats, ordresIndices, sample_weight=None)
        else:
            for iData in range(len(self.ordersData)):
                for key in self.ordersData[iData].keys():
                    if(int(key[1]) == team):
                        liste = self.playerOrdersIndex.get(key,None)
                        if (liste):
                            liste.append(iData)
                        else:
                            self.playerOrdersIndex[key] = [iData]

            self.playerSVC = {}
            self.playerSVR_tire = {}
            self.playerSVR_deplace = {}
            self.playerSVR_dribble = {}
            for idJoueur in self.playerOrdersIndex.keys():
                etats = self.statesData[self.playerOrdersIndex[idJoueur]]
                ordres = np.array([self.ordersData[ind].get(idJoueur) for ind in self.playerOrdersIndex[idJoueur]])
                #### Pour les actions
                self.playerSVC[idJoueur] = SVC(kernel = 'rbf', probability = True)
                #actions = np.array([self.ordersData[ind].get(idJoueur)[:3] for ind in self.playerOrdersIndex[idJoueur]])
                self.playerSVC[idJoueur].fit(etats, self.playerOrdersIndex[idJoueur])
                #### Pour les cibles
                self.playerSVR_tire[idJoueur] = MultiOutputRegressor(SVR(kernel = 'rbf'))
                self.playerSVR_deplace[idJoueur] = MultiOutputRegressor(SVR(kernel = 'rbf'))
                self.playerSVR_dribble[idJoueur] = MultiOutputRegressor(SVR(kernel = 'rbf'))

                etats_deplace = np.array([self.statesData[ind] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[0]==1])
                cibles_deplace = np.array([self.ordersData[ind].get(idJoueur)[3:] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[0]==1])
                etats_tire = np.array([self.statesData[ind] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[1]==1])
                cibles_tire = np.array([self.ordersData[ind].get(idJoueur)[3:] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[1]==1])
                etats_dribble = np.array([self.statesData[ind] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[2]==1])
                cibles_dribble = np.array([self.ordersData[ind].get(idJoueur)[3:] for ind in self.playerOrdersIndex[idJoueur] if self.ordersData[ind].get(idJoueur)[2]==1])

                if etats_deplace.shape[0] != 0:
                    self.playerSVR_deplace[idJoueur].fit(etats_deplace, cibles_deplace)
                if etats_tire.shape[0] != 0:
                    self.playerSVR_tire[idJoueur].fit(etats_tire, cibles_tire)
                if etats_dribble.shape[0] != 0:
                    self.playerSVR_dribble[idJoueur].fit(etats_dribble, cibles_dribble)


    def setCurrentState(self, currentState):
        list=[]
        ordonnancement = {}
        team1Ordonne = []
        team2Ordonne = []
        CageTeam1 = Vector2D(0, GAME_HEIGHT/2)
        CageTeam2 = Vector2D(GAME_WIDTH, GAME_HEIGHT/2)
        distDef1=[]
        distAdv1=[]
        distDef2=[]
        distAdv2=[]
        for k,v in (currentState.players):
            if (not self.orderByCageDist):
                list += self.getPlayerSVMState(currentState, k, v)
            if k == 1:
                # Distances entre la cage de l'equipe 1 et les joueurs de l'equipe 1
                distDef1.append(CageTeam1.distance(currentState.player_state(k,v).position))
                # Distances entre la cage de l'equipe 2 et les joueurs de l'equipe adverse 1
                distAdv2.append(CageTeam2.distance(currentState.player_state(k,v).position))
                #Pour la version avec permutation
                currentList = team1Ordonne
                distToCage = distDef1[-1]
            else:
                # Distances entre la cage de l'equipe 1 et les joueurs de l'equipe adverse 2
                distAdv1.append(CageTeam1.distance(currentState.player_state(k,v).position))
                # Distances entre la cage de l'equipe 2 et les joueurs de l'equipe 2
                distDef2.append(CageTeam2.distance(currentState.player_state(k,v).position))
                #Pour la version avec permutation
                currentList = team2Ordonne
                distToCage = distDef2[-1]
            if(self.orderByCageDist):
                if len(currentList) == 0:
                    currentList.append((k, v, distToCage))
                else:
                    index = 0
                    isAfter = True
                    while index < len(currentList) and isAfter:
                        if (currentList[index][2] <= distToCage):
                            index += 1
                        else:
                            isAfter = False
                    if (index == len(currentList)):
                        currentList.append((k, v, distToCage))
                    else:
                        currentList.insert(index, (k, v, distToCage))
        if (self.orderByCageDist):
            for iJoueurProximite in range(len(team1Ordonne)):
                ordonnancement["(" + str(team1Ordonne[iJoueurProximite][0]) + ", " + str(
                    team1Ordonne[iJoueurProximite][1]) + ")"] = iJoueurProximite
            for iJoueurProximite in range(len(team2Ordonne)):
                ordonnancement["(" + str(team2Ordonne[iJoueurProximite][0]) + ", " + str(
                    team2Ordonne[iJoueurProximite][1]) + ")"] = iJoueurProximite
            k = 1
            v = 0
            isDone = False
            while not isDone:
                for key in ordonnancement.keys():
                    if (int(key[1]) == k and ordonnancement[key] == v):
                        list += self.getPlayerSVMState(currentState, int(key[1]), int(key[4]))
                        # print(k,v,list)
                        if (v != 3):
                            v += 1
                        else:
                            if (k == 1):
                                k += 1
                                v = 0
                            else:
                                isDone = True
        # Distance CageTeam1 et defenseur allie le plus proche
        list.append(min(distDef1))
        # Distance CageTeam1 et attaquant adverse le plus proche
        list.append(min(distAdv1))
        # Distance entre la balle et la cage de l'equipe 1
        list.append(CageTeam1.distance(currentState.ball.position))
        # Distance CageTeam2 et defenseur allie le plus proche
        list.append(min(distDef2))
        # Distance CageTeam2 et attaquant adverse le plus proche
        list.append(min(distAdv2))
        # Distance entre la balle et la cage de l'equipe 2
        list.append(CageTeam2.distance(currentState.ball.position))
        self.currentStateForSVM = np.array(list)
        self.currentStateOrdonnancement = ordonnancement

    def thinkOrders(self):
        if(len(self.statesData)==0):
            return dict()
        orders = dict()
        for joueur in self.orderStrategies.keys():
            positionALaCage = None
            joueurID = "(" + str(self.myTeam) + ", " + str(joueur) + ")"
            bestStateOrdreID = None
            ###### Permutations
            if self.orderByCageDist:
                #On calcule avant tout la position a la cage du joueur dans l'etat courrant
                positionALaCage = self.currentStateOrdonnancement[joueurID]
                #L'état le plus proche
                bestStateIndex = self.positionSVC[positionALaCage].predict(self.currentStateForSVM.reshape(1, -1))[0]
                #print(bestStateIndex)
                #L'identifiant de l'ordre associe a l'etat le plus proche en fonction de la position a la cage
                bestStateOrdreID = self.positionToCageToOrderID(positionALaCage,bestStateIndex,self.myTeam)
                actions = self.ordersData[bestStateIndex].get(bestStateOrdreID, None)[:3]

                if actions[0] == 1: #deplace
                    cibles = self.positionSVR_deplace[positionALaCage].predict(self.currentStateForSVM.reshape(1, -1))[0]
                if actions[1] == 1: #tire
                    cibles = self.positionSVR_tire[positionALaCage].predict(self.currentStateForSVM.reshape(1, -1))[0]
                if actions[2] == 1: #dribble
                    cibles = self.positionSVR_dribble[positionALaCage].predict(self.currentStateForSVM.reshape(1, -1))[0]

                ordre = np.concatenate((actions,cibles))
                closestOrder = self.csvHandler.decode(ordre)

                #print("Closest order :", closestOrder)
                #if (joueur == 0 and self.myTeam == 2):
                #    pass
                    #print("Position à la cage : ", positionALaCage)
                    #print(joueurID, bestStateOrdreID)

                # Pour SVR
                #bestOrder = self.positionSVR[positionALaCage].predict(self.currentStateForSVM.reshape(1, -1))[0]
                #print("bestOrder : ", bestOrder)
                #closestOrder = self.csvHandler.decode(bestOrder, SVMOrder)
                #print("closestOrder : ", closestOrder)

            else:
                # Prédire l'action
                bestStateIndex = self.playerSVC[joueurID].predict(self.currentStateForSVM.reshape(1, -1))[0]
                actions = self.ordersData[bestStateIndex].get(joueurID, None)[:3]
                # Prédire la/les cible(s)
                if actions[0] == 1: #deplace
                    cibles = self.playerSVR_deplace[joueurID].predict(self.currentStateForSVM.reshape(1, -1))[0]
                if actions[1] == 1: #tire
                    cibles = self.playerSVR_tire[joueurID].predict(self.currentStateForSVM.reshape(1, -1))[0]
                if actions[2] == 1: #dribble
                    cibles = self.playerSVR_dribble[joueurID].predict(self.currentStateForSVM.reshape(1, -1))[0]

                ordre = np.concatenate((actions,cibles))
                closestOrder = self.csvHandler.decode(ordre)
                #print("closestOrder : ", closestOrder)

            if closestOrder:
                if (self.orderByCageDist):
                    if closestOrder[1][0] == "(":
                        closestOrder[1] = self.csvHandler.strToIntTuple(self.swapPlayerTargetWithPositionToCage(closestOrder[1], bestStateIndex))
                    if len(closestOrder) > 2:
                        if closestOrder[-2][0] == "(":
                            closestOrder[-2] = self.csvHandler.strToIntTuple(self.swapPlayerTargetWithPositionToCage(closestOrder[-2], bestStateIndex))
                        closestOrder[-1] = float(closestOrder[-1])
                else:
                    if closestOrder[1][0] == "(":
                        closestOrder[1] = self.csvHandler.strToIntTuple(closestOrder[1])
                    if len(closestOrder) > 2:
                        if closestOrder[-2][0] == "(":
                            closestOrder[-2] = self.csvHandler.strToIntTuple(closestOrder[-2])
                        closestOrder[-1] = float(closestOrder[-1])
                orders[joueur] = closestOrder
        return orders

    def positionToCageToOrderID(self, positionToCage, stateIndex, team):
        for key in self.statesOrdonnancement[stateIndex].keys():
            if(self.statesOrdonnancement[stateIndex][key] == positionToCage and int(key[1]) == team):
                return key

    def swapPlayerTargetWithPositionToCage(self, cible, stateIndex):
        """
        Cette fonction a pour but de modifier la cible d'une action.
        En effet si dans la base de donnee on a tirer vers un Joueur X, on veut en fait tirer vers le joueur qui occupe la position du joueur X.
        """
        positionALaCage = self.statesOrdonnancement[stateIndex][cible]
        for key in self.currentStateOrdonnancement.keys():
            if(self.currentStateOrdonnancement[key] == positionALaCage and int(key[1]) == int(cible[1])):
                return key
        return "none"

    def dataToSVMStates(self,dataStates):#modif
        #print(currentState)
        #shape 0 : nombre de lignes dans le csv etats
        #shape 1 : nombre de donnees
        # => format du csv
        nbValuePerJoueur = 5 #7 avant
        states = np.zeros((len(dataStates),6+nbValuePerJoueur*(sum(self.nbPlayer))))
        ordonnancements = [{} for i in range(len(dataStates))]
        for iState in range(len(dataStates)):
            currentState=[None for i in range(sum(self.nbPlayer)*nbValuePerJoueur)]
            state = dataStates[iState]
            indiceJoueur = 0
            for joueur in state['joueursTeam1']:
                if (self.orderByCageDist): #Soit on selectionne les joueurs dans l'ordre de proximite de la cage (ordre de base)
                    finalIndex = indiceJoueur
                    ordonnancements[iState][str(joueur["id"])] = indiceJoueur
                else: #Soit on selectionne toujours le j0 en premier puis j1 etc (sans la distance a la cage)
                    finalIndex = joueur["id"][1]
                #Position du joueur
                #currentState.append(joueur["position"][0])
                #currentState.append(joueur["position"][1])
                # Distance à l'allie le plus proche
                currentState[0+finalIndex*5] = joueur['distAllieLPP']
                # Distance à l'adversaire le plus proche
                currentState[1+finalIndex*5] = joueur['distAdvLPP']
                # Distance à la Balle
                currentState[2+finalIndex*5] = joueur['distBall']
                # Distance à la cage de son equipe
                currentState[3+finalIndex*5] = joueur['distSaCage']
                # Distance à la cage adversaire
                currentState[4+finalIndex*5] = joueur['distCageAdv']
                indiceJoueur += 1
            indiceJoueur = 0
            nbValueTeam1 = nbValuePerJoueur * self.nbPlayer[0]
            for joueur in state['joueursTeam2']:
                if (self.orderByCageDist): #Soit on selectionne les joueurs dans l'ordre de proximite de la cage (ordre de base)
                    finalIndex = indiceJoueur
                    ordonnancements[iState][str(joueur["id"])] = indiceJoueur
                else: #Soit on selectionne toujours le j0 en premier puis j1 etc (sans la distance a la cage)
                    finalIndex = joueur["id"][1]
                # Position du joueur
                # currentState.append(joueur["position"][0])
                # currentState.append(joueur["position"][1])
                currentState[nbValueTeam1+ 0 + finalIndex * 5] = joueur['distAllieLPP']
                currentState[nbValueTeam1+ 1 + finalIndex * 5] = joueur['distAdvLPP']
                currentState[nbValueTeam1+ 2 + finalIndex * 5] = joueur['distBall']
                currentState[nbValueTeam1+ 3 + finalIndex * 5] = joueur['distSaCage']
                currentState[nbValueTeam1+ 4 + finalIndex * 5] = joueur['distCageAdv']
                indiceJoueur += 1
            equipe=state['positionsTeam1']
            currentState.append(equipe['distAdvLPPCage'])
            currentState.append(equipe['distDefLPPCage'])
            currentState.append(equipe['distBallCage'])
            equipe=state['positionsTeam2']
            currentState.append(equipe['distAdvLPPCage'])
            currentState.append(equipe['distDefLPPCage'])
            currentState.append(equipe['distBallCage'])
            #print(currentState)
            states[iState] = currentState
        return states, ordonnancements

    def getPlayerSVMState(self, currentState, team, id):
        playerPosition = currentState.player_state(team, id).position
        #playerType = self.get_team(team).player_type(id)

        if(team == 1):
            # Distance à la cage de son equipe
            SaCage = Vector2D(0, GAME_HEIGHT/2)
            distCage = playerPosition.distance(SaCage)
            # Distance à la cage adverse
            CageAdverse = Vector2D(GAME_WIDTH, GAME_HEIGHT/2)
            distCageAdverse = playerPosition.distance(CageAdverse)
        else:
            # Distance à la cage de son equipe
            SaCage = Vector2D(GAME_WIDTH, GAME_HEIGHT/2)
            distCage = playerPosition.distance(SaCage)
            # Distance à la cage adverse
            CageAdverse = Vector2D(0, GAME_HEIGHT/2)
            distCageAdverse = playerPosition.distance(CageAdverse)

        # Distances à l'allie le plus proche et à l'adversaire le plus proche + leurs types
        allieDist=[]
        #allieType=[]
        advDist=[]
        #advType=[]

        for k, v in currentState.players:
            if k == team and id == v:
                continue
            if k == team:
                # distance à l'allie le plus proche + type
                distance = currentState.player_state(k,v).position.distance(playerPosition)
                #type = self.get_team(k).player_type(v)
                allieDist.append(distance)
                #allieType.append(type)
            else:
                #distance à l'adversaire le plus proche + type
                distance = currentState.player_state(k,v).position.distance(playerPosition)
                #type = self.get_team(k).player_type(v)
                advDist.append(distance)
                #advType.append(type)

        # distance à l'allie le plus proche + type
        index = min(range(len(allieDist)), key=allieDist.__getitem__)
        APP = allieDist[index]
        #typeAPP = allieType[index]

        #distance à l'adversaire le plus proche + type
        index = min(range(len(advDist)), key=advDist.__getitem__)
        AdvPP = advDist[index]
        #typeAdvPP = advType[index]

        # Distance à la Balle
        dist2Ball = playerPosition.distance(currentState.ball.position)

        #res = [playerPosition.x, playerPosition.y, APP, AdvPP, dist2Ball, distCage, distCageAdverse] #Sans Position pour le Relatif !
        res = [APP, AdvPP, dist2Ball, distCage, distCageAdverse]
        return res
