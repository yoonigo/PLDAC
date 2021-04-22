import csv
import os
import numpy as np
from .settings import GAME_WIDTH
from .utils import Vector2D
from .databaseSettings import *
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

class csvHandler(object):

    def __init__(self, myTeam = None, nbPlayer = None):
        self.lastStateSaved = None
        self.myTeam = myTeam
        self.nbPlayer = nbPlayer

    def import_csv(self, filename, readFunction = None):
        data = []
        with open(filename, "r") as f:
            reader = csv.reader(f, delimiter='_')
            for row in reader:
                if row:
                    if(readFunction):
                        data.append(readFunction(row))
                    else:
                        data.append(row)
        if(readFunction):
            return data[1:]
        return data

    def saveStateInCSV(self, currentState, absolu):
        if os.path.isfile(CSVFEATURES) == False:
            with open(CSVFEATURES, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                if False:
                    writer.writerow(['ballPos', "nextLikelyPosition", "posTeam1", "typeTeam1", "posTeam2", "typeTeam2", "ballWithTeam"])
                else:
                    writer.writerow(['idPlayer','posPlayer', 'typePlayer', 'distAllieLPP', 'typeAllieLPP', 'distAdvLPP', 'typeAdvLPP', 'distBall', 'distSaCage', 'distCageAdv',
                        'distDefCage1', 'typeDefCage1', 'distAdvCage1', 'typeAdvCage1', 'distBallCage1', 'distDefCage2', 'typeDefCage2', 'distAdvCage2', 'typeAdvCage2', 'distBallCage2', 'ballPos', 'nextLikelyPosition', 'ballWithTeam'])
        with open(CSVFEATURES, 'a', newline='') as f:
            writer = csv.writer(f, delimiter='_')
            writer.writerow(currentState)

    def saveOrderInCSV(self, order, appendFile = False):
        if os.path.isfile(CSVLABELS) == False:
            with open(CSVLABELS, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                writer.writerow(['joueur', 'action', 'cible'])
        if appendFile:
            data = self.import_csv(CSVLABELS)
            # print("##DATA: ",data)
            lastRow = data[-1]
            # print("##LASTROW: ",lastRow)
            with open(CSVLABELS, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                for row in data:
                    if row == lastRow:
                        if lastRow[0] == 'joueur':
                            writer.writerow(order)
                        else:
                            list = []
                            for ordre in lastRow:
                                if(int(ordre[2]) != order[0][0] or int(ordre[5]) != order[0][1]):
                                    list.append((ordre))
                            list.append(order)
                            writer.writerow(list)
                    else:
                        writer.writerow((row))
        else:
            with open(CSVLABELS, 'a', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                for elt in order:
                    if elt == "se deplace vers":
                        elt.replace("deplace", "deplace")
                writer.writerow([order])

    def addDataToCSVs(self, order, currentState, absolu):
        if (self.lastStateSaved is None) or self.lastStateSaved != currentState:
            self.lastStateSaved = currentState
            appendFile = False
        elif self.lastStateSaved == currentState:
            appendFile = True
        self.saveOrderInCSV(order, appendFile=appendFile)
        if not appendFile:
            self.saveStateInCSV(currentState, absolu)

    def combineCsv(self, filePath1, filePath2, outputPath, mode='w'):
        data1 = self.import_csv(filePath1)
        data2 = self.import_csv(filePath2)
        for row in data2[1:]:
            data1.append(row)

        with open(outputPath, mode, newline='') as f:
            if mode == 'w':
                first = 0
            elif mode == 'a':
                first = 1
            writer = csv.writer(f, delimiter='_')
            for row in data1[first:]:
                writer.writerow(row)

    def rowToABS(self, state):
        if(state[0] == "idPlayer" or state[0] == "posPlayer"):
            return state
        newState = dict()
        ballList = []
        for ball in state[-3:-1]:
            ballList.append(self.strToFloatTuple(ball))
        ballList.append(state[-1])
        newState["ball"] = ballList
        # Les Joueurs !
        team1 = []
        team2 = []
        for i in range(len(state)-13):
            currentJoueur = state[i].split(",")
            currentPosition = currentJoueur[2][1:] + "," + currentJoueur[3]
            currentType = currentJoueur[4][2:-1]
            if(currentJoueur[0][2] == "1"):
                team1.append({"position": self.strToFloatTuple(currentPosition), "type": currentType, "id":self.strToIntTuple(currentJoueur[0][1:] + "," + currentJoueur[1])})
            else:
                team2.append({"position": self.strToFloatTuple(currentPosition), "type": currentType, "id":self.strToIntTuple(currentJoueur[0][1:] + "," + currentJoueur[1])})

        newState["team1"] = team1
        newState["team2"] = team2
        newState["ballControl"] = state[-1]
        return newState

    def rowToREL(self,state):
        if (state[0] == "idPlayer" or state[0] == "posPlayer"):
            return state
        newState = dict()
        # Calcul des nombres de joueurs par equipe !
        nbJoueurTot = sum(self.nbPlayer)
        nbJoueurTeam0 = self.nbPlayer[0]
        # Joueur de l'equipe 0
        team1 = []
        for i in range(nbJoueurTeam0):
            id = self.strToIntTuple(state[i][1:7])
            pos = state[i][9:].split(")")
            joueur = pos[1].split(",")
            type = joueur[1][2:-1]
            distAllieLPP = float(joueur[2][1:])
            typeAllieLPP = joueur[3][2:-1]
            distAdvLPP = float(joueur[4][1:])
            typeAdvLPP = joueur[5][2:-1]
            distBall = float(joueur[6][1:])
            distSaCage = float(joueur[7][1:])
            distCageAdv = float(joueur[8][1:-1])
            team1.append({"id":id,"position": self.strToFloatTuple(pos[0] + ")"), "type": type, "distAllieLPP": distAllieLPP,
                          "typeAllieLPP": typeAllieLPP, "distAdvLPP": distAdvLPP, "typeAdvLPP": typeAdvLPP,
                          "distBall": distBall, "distSaCage": distSaCage, "distCageAdv": distCageAdv})
        newState["joueursTeam1"] = team1
        # Joueur de l'equipe 1
        team1 = []
        for i in range(nbJoueurTeam0,nbJoueurTot):
            id = self.strToIntTuple(state[i][1:7])
            pos = state[i][9:].split(")")
            joueur = pos[1].split(",")
            type = joueur[1][2:-1]
            distAllieLPP = float(joueur[2][1:])
            typeAllieLPP = joueur[3][2:-1]
            distAdvLPP = float(joueur[4][1:])
            typeAdvLPP = joueur[5][2:-1]
            distBall = float(joueur[6][1:])
            distSaCage = float(joueur[7][1:])
            distCageAdv = float(joueur[8][1:-1])
            team1.append(
                {"id":id,"position": self.strToFloatTuple(pos[0] + ")"), "type": type, "distAllieLPP": distAllieLPP,
                 "typeAllieLPP": typeAllieLPP, "distAdvLPP": distAdvLPP, "typeAdvLPP": typeAdvLPP,
                 "distBall": distBall, "distSaCage": distSaCage, "distCageAdv": distCageAdv})
        newState["joueursTeam2"] = team1
        # Position de l'equipe 0
        posit1 = dict()
        startIndex = nbJoueurTot
        posit1["distAdvLPPCage"] = state[startIndex]
        posit1["typeAdvLPPCage"] = state[startIndex + 1]
        posit1["distDefLPPCage"] = state[startIndex + 2]
        posit1["typeDefLPPCage"] = state[startIndex + 3]
        posit1["distBallCage"] = state[startIndex + 4]
        newState["positionsTeam1"] = posit1
        # Position de l'equipe 1
        posit2 = dict()
        startIndex = nbJoueurTot + 5
        posit2["distAdvLPPCage"] = state[startIndex]
        posit2["typeAdvLPPCage"] = state[startIndex + 1]
        posit2["distDefLPPCage"] = state[startIndex + 2]
        posit2["typeDefLPPCage"] = state[startIndex + 3]
        posit2["distBallCage"] = state[startIndex + 4]
        newState["positionsTeam2"] = posit2
        # Ajout au resultat final
        return newState

    @DeprecationWarning
    def readStateCsv(self,stateFilePath):
        stateData = self.import_csv(stateFilePath)[1:]
        result = []
        for state in stateData:
            newState = dict()
            ballList = []
            for ball in state[:2]:
                ballList.append(self.strToFloatTuple(ball))
            ballList.append(state[-1])
            newState["ball"] = ballList
            # L'equipe 1
            team1 = []
            joueur = state[2].split("/")
            type = state[3].split("/")
            for i in range(len(joueur)):
                team1.append({"position":self.strToFloatTuple(joueur[i]),"type":type[i]})
            newState["team1"] = team1
            # L'equipe 2
            team1 = []
            joueur = state[4].split("/")
            type = state[5].split("/")
            for i in range(len(joueur)):
                team1.append({"position": self.strToFloatTuple(joueur[i]), "type": type[i]})
            newState["team2"] = team1
            newState["ballControl"] = state[6]
            result.append(newState)
        return result

    def readOrderCsv(self,orderFilePath):
        ordersData = self.import_csv(orderFilePath)[1:]
        result = []
        for orders in ordersData:
            ordersDico = dict()
            for order in orders:
                liste = self.orderStrToList(order)
                ordersDico[liste[0]] = liste[1:]
            result.append(ordersDico)
        return result


    def newReadStateCsv(self,stateFilePath):
        stateData = self.import_csv(stateFilePath)[1:]
        result = []
        for state in stateData:
            newState = dict()
            #Calcul des nombres de joueurs par equipe !
            nbJoueurTot = sum(self.nbPlayer)
            nbJoueurTeam0 = self.nbPlayer[0]
            #Joueur de l'equipe 0
            team1 = []
            for i in range(nbJoueurTeam0):
                pos = state[i][1:].split(")")
                joueur = pos[1].split(",")
                type = joueur[1][2:-1]
                distAllieLPP = float(joueur[2][1:])
                typeAllieLPP = joueur[3][2:-1]
                distAdvLPP = float(joueur[4][1:])
                typeAdvLPP = joueur[5][2:-1]
                distBall = float(joueur[6][1:])
                distSaCage = float(joueur[7][1:])
                distCageAdv = float(joueur[8][1:-1])
                team1.append({"position": self.strToFloatTuple(pos[0]+")"), "type": type, "distAllieLPP":distAllieLPP,"typeAllieLPP":typeAllieLPP,"distAdvLPP":distAdvLPP,"typeAdvLPP":typeAdvLPP,"distBall":distBall,"distSaCage":distSaCage,"distCageAdv":distCageAdv})
            newState["joueursTeam1"] = team1
            # Joueur de l'equipe 1
            team1 = []
            for i in range(nbJoueurTot-nbJoueurTeam0):
                pos = state[i][1:].split(")")
                joueur = pos[1].split(",")
                type = joueur[1][2:-1]
                distAllieLPP = float(joueur[2][1:])
                typeAllieLPP = joueur[3][2:-1]
                distAdvLPP = float(joueur[4][1:])
                typeAdvLPP = joueur[5][2:-1]
                distBall = float(joueur[6][1:])
                distSaCage = float(joueur[7][1:])
                distCageAdv = float(joueur[8][1:-1])
                team1.append(
                    {"position": self.strToFloatTuple(pos[0] + ")"), "type": type, "distAllieLPP": distAllieLPP,
                     "typeAllieLPP": typeAllieLPP, "distAdvLPP": distAdvLPP, "typeAdvLPP": typeAdvLPP,
                     "distBall": distBall, "distSaCage": distSaCage, "distCageAdv": distCageAdv})
            newState["joueursTeam2"] = team1
            # Position de l'equipe 0
            posit1 = dict()
            startIndex = nbJoueurTot
            posit1["distAdvLPPCage"] = state[startIndex]
            posit1["typeAdvLPPCage"] = state[startIndex+1]
            posit1["distDefLPPCage"] = state[startIndex+2]
            posit1["typeDefLPPCage"] = state[startIndex+3]
            posit1["distBallCage"] = state[startIndex+4]
            newState["positionsTeam1"] = posit1
            # Position de l'equipe 1
            posit2 = dict()
            startIndex = nbJoueurTot+5
            posit2["distAdvLPPCage"] = state[startIndex]
            posit2["typeAdvLPPCage"] = state[startIndex + 1]
            posit2["distDefLPPCage"] = state[startIndex + 2]
            posit2["typeDefLPPCage"] = state[startIndex + 3]
            posit2["distBallCage"] = state[startIndex + 4]
            newState["positionsTeam2"] = posit2
            #Ajout au resultat final
            result.append(newState)
        return result

    def encode(self, orderFilePath):
        orders = self.readOrderCsv(orderFilePath)
        # se déplace | tire vers | dribble vers | sacage | cageadv | CornerTopLeft | CornerTopRight | CornerBottomLeft | CornerBottomRight | MiddleTop | MiddleBottom | middle | balle | balleprochaine | (1,0) | (1,1) ... | (2,3) | MIX
        # nb cibles : 2 cages, 7 positions sur le terrain, nbjoueurs, 1 val mix, 2 positions de balle
        # nb actions : 3
        # taille array : 15 + nbplayer
        nbJoueurTot = sum(self.nbPlayer)
        taille = 15 + nbJoueurTot
        res = []
        for order in orders:
            # print("order", order)
            ordersDico = dict()
            for player in order:
                # On encode l'action
                encoded_order = [0] * taille
                if order[player][0] == "se deplace vers":
                    encoded_order[0] = 1
                if order[player][0] == "tire vers":
                    encoded_order[1] = 1
                if order[player][0] == "dribble vers":
                    encoded_order[2] = 1
                # On encode la/les cible(s)
                if order[player][1] == "SaCage" or (len(order[player]) == 4 and order[player][2] == "SaCage"):
                    encoded_order[3] = 1
                if order[player][1] == "CageAdverse" or (len(order[player]) == 4 and order[player][2] == "CageAdverse"):
                    encoded_order[4] = 1
                if order[player][1] == "CornerTopLeft" or (
                        len(order[player]) == 4 and order[player][2] == "CornerTopLeft"):
                    encoded_order[5] = 1
                if order[player][1] == "CornerTopRight" or (
                        len(order[player]) == 4 and order[player][2] == "CornerTopRight"):
                    encoded_order[6] = 1
                if order[player][1] == "CornerBottomLeft" or (
                        len(order[player]) == 4 and order[player][2] == "CornerBottomLeft"):
                    encoded_order[7] = 1
                if order[player][1] == "CornerBottomRight" or (
                        len(order[player]) == 4 and order[player][2] == "CornerBottomRight"):
                    encoded_order[8] = 1
                if order[player][1] == "MiddleTop" or (len(order[player]) == 4 and order[player][2] == "MiddleTop"):
                    encoded_order[9] = 1
                if order[player][1] == "MiddleBottom" or (
                        len(order[player]) == 4 and order[player][2] == "MiddleBottom"):
                    encoded_order[10] = 1
                if order[player][1] == "Middle" or (len(order[player]) == 4 and order[player][2] == "Middle"):
                    encoded_order[11] = 1
                if order[player][1] == "Balle" or (len(order[player]) == 4 and order[player][2] == "Balle"):
                    encoded_order[12] = 1
                if order[player][1] == "BalleProchaine" or (
                        len(order[player]) == 4 and order[player][2] == "BalleProchaine"):
                    encoded_order[13] = 1
                for id in range(int(nbJoueurTot / 2)):
                    if (order[player][1] == "(1, " + str(id) + ")") or (
                            len(order[player]) == 4 and order[player][2] == "(1, " + str(id) + ")"):
                        encoded_order[14 + id] = 1
                    if (order[player][1] == "(2, " + str(id) + ")") or (
                            len(order[player]) == 4 and order[player][2] == "(2, " + str(id) + ")"):
                        encoded_order[14 + id + int(nbJoueurTot / 2)] = 1
                # On ajoute la valeur de mixage si elle existe
                if len(order[player]) == 4:
                    encoded_order[-1] = float(order[player][-1])
                else:
                    encoded_order[-1] = 1.0
                ordersDico[player] = np.array(encoded_order)
            res.append(ordersDico)
        return res

    def decode(self, mixOrder, nearestOrder,redo = 0):
        # Entrée : [0,1,0,0,0,0,0,1,0...], [0,1,0,0,0,0,0,1,0...]
        # On crée la liste des valeurs possibles pour y accéder par indice
        ordre = []
        choix = ["se deplace vers", "tire vers", "dribble vers", "SaCage", "CageAdverse", "CornerTopLeft", "CornerTopRight",
                 "CornerBottomLeft", "CornerBottomRight", "MiddleTop", "MiddleBottom", "Middle", "Balle",
                 "BalleProchaine"]
        nbJoueurTot = sum(self.nbPlayer)
        for id in range(int(nbJoueurTot / 2)):
            choix.append("(1, " + str(id) + ")")
        for id in range(int(nbJoueurTot / 2)):
            choix.append("(2, " + str(id) + ")")

        # Décoder l'action
        if mixOrder[0] > mixOrder[1] and mixOrder[0] > mixOrder[2]:
            ordre.append(choix[0])
        elif mixOrder[1] > mixOrder[2] and mixOrder[1] > mixOrder[0]:
            ordre.append(choix[1])
        elif mixOrder[2] > mixOrder[1] and mixOrder[2] > mixOrder[0]:
            ordre.append(choix[2])
        else:  # s'il y a des égalités, choisir l'action de l'état le plus proche
            ordre.append(choix[max(range(3), key=nearestOrder.__getitem__)])
        #print("Action : ", ordre)

        # Décoder la/les cible(s)
        #Calcul des deux valeurs maximales !
        cibles = np.array(mixOrder[3:-1])
        indicesWhitoutMax = [i for i in range(len(cibles))]
        indicesWhitoutMax.remove(np.argmax(cibles))
        maxi = [np.amax(cibles),np.amax(cibles[indicesWhitoutMax])]
        #print(maxi)
        if(maxi[0] == maxi[1]): #Si c'est la même valeur
            indices = np.where(cibles == maxi[0])[0] #Combien ont cette valeur ?
            if(len(indices) == 2): #Deux ? C'est un ordre mixé
                ordre.append(choix[3 +indices[0]])
                ordre.append(choix[3 +indices[1]])
                ordre.append(mixOrder[-1])
            else: #Plus de deux ? On a une égalité, il faut trancher
                newMixOrder = np.zeros(mixOrder.shape)
                newMixOrder[:3] = mixOrder[:3]
                newMixOrder[-1] = mixOrder[-1]
                newMixOrder[3:-1] = np.array(mixOrder[3:-1]) + np.array(nearestOrder[3:-1]) #Valorisation de l'ordre le plus proche
                return self.decode(newMixOrder, nearestOrder, redo = 1)
        else: #Les valeurs maximales sont différentes !
            #Valide la première cible
            indicesGood = np.where(cibles == maxi[0])[0][0]
            ordre.append(choix[3 + indicesGood])
            if (maxi[1] != 0):  #Si non unicité de la cible, i.e. mixage necessaire)
                #Combien ont la valeur de la deuxième ?
                indices = np.where(cibles == maxi[1])[0]
                if (len(indices) == 1):  # Une seule ? Parfait on l'ajoute avec le mixage
                    ordre.append(choix[3 + indices[0]])
                    ordre.append(mixOrder[-1])
                else:  # Plus d'une ? On a une égalité, il faut trancher
                    newMixOrder = np.zeros(mixOrder.shape)
                    newMixOrder[:3] = mixOrder[:3]
                    newMixOrder[-1] = mixOrder[-1]
                    newMixOrder[3:-1] = np.array(mixOrder[3:-1]) + np.array(nearestOrder[3:-1]) #On valorise l'ordre le plus proche
                    if(redo == 1): #Si on valorise une cible unique par rapport à une cible mixée, on garde la cible unique
                        return self.decode(nearestOrder,nearestOrder) #En gros on execute le nearest order
                    return self.decode(newMixOrder, nearestOrder, redo = 1)


        """
        index = max(range(len(mixOrder[3:-1])), key=mixOrder.__getitem__)
        maxValue = mixOrder[3 + index]
        mix = np.array(mixOrder[3:-1])
        indices = np.where(mix == maxValue)[0]
        # S'il y a une autre cible avec la même valeur:
        if(len(indices) == 1):
            ordre.append(choix[3 + index])
        if len(indices) > 1:
            # On prend la cible de l'état le plus proche
            index = max(range(len(nearestOrder[3:-1])), key=nearestOrder.__getitem__)
            maxValue = nearestOrder[3 + maxValue]
            nearest = np.array(nearestOrder[3:-1])
            inds = np.where(nearest == maxValue)[0]
            if len(inds) > 1:  # mixage de cibles
                ordre.append(choix[3 + inds[0]])
                ordre.append(choix[3 + inds[1]])
                ordre.append(nearestOrder[-1])
        """
        return ordre

    @DeprecationWarning
    def duplicateData(self,stateFilePath,orderFilePath, outputStatePath, outputOrderPath, addOnlySymetric = False):
        """
        DEPRECATED
        """
        #Lecture des donnees
        orderData = self.import_csv(orderFilePath)
        stateData = self.import_csv(stateFilePath)
        if(len(orderData) != len(stateData)):
            raise ImportError
        #Creation si besoin des fichiers de sorties
        if os.path.isfile(outputOrderPath) == False:
            with open(outputOrderPath, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                writer.writerow(['joueur', 'action', 'cible'])
        if os.path.isfile(outputStatePath) == False:
            with open(outputStatePath, 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                writer.writerow(['ballPos', "nextLikelyPosition", "posTeam1", "typeTeam1", "posTeam2", "typeTeam2",
                                 "ballWithTeam"])
        #Traitement iteratif des donnees
        for i in range(1,len(orderData)):
            #Calcule de la situation symetrique
            symetric = [self.getSymetricState(stateData[i]),self.getSymetricOrder(orderData[i])]
            #Ajout dans les fichiers de sorties
            with open(outputStatePath, 'a', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                if addOnlySymetric == False:
                    writer.writerow(stateData[i])
                writer.writerow(symetric[0])
            with open(outputOrderPath, 'a', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                if addOnlySymetric == False:
                    writer.writerow(orderData[i])
                writer.writerow(symetric[1])

    def orderStrToList(self, order):
        liste = []
        current = ""
        isInTuple = False
        for carac in order[1:-1]:
            if (not (carac == " " and len(current) == 0 and len(liste) > 0)):
                if carac == ',' and not isInTuple:
                    if current == "se deplace vers":
                        current = "se deplace vers"
                    liste.append(current)
                    current = ""
                else:
                    if carac != "'":
                        if carac == '(':
                            isInTuple = True
                        if carac == ')':
                            isInTuple = False
                        current += carac
        liste.append(current)
        return liste.copy()

    @DeprecationWarning
    def getSymetricOrder(self, orders):
        newOrders = []
        for order in orders:
            newOrder = "["
            liste = self.orderStrToList(order)
            for i in range(len(liste)):
                newOrder += self.getSymetricTarget(liste[i])
                if i != len(liste)-1:
                    newOrder += ", "
            newOrder += "]"
            newOrders.append(newOrder)
        return newOrders

    @DeprecationWarning
    def getSymetricState(self, state):
        #print("Etat initiale : ", state)
        newState = []
        #La Balle
        for ball in state[:2]:
            newState.append(self.strToTupleToSymToStr(ball))
        #L'equipe 1
        newJoueurTeam1 = ""
        newTypeTeam1 = state[3]
        for joueur in state[2].split("/"):
            newJoueurTeam1 += self.strToTupleToSymToStr(joueur) + "/"
        newJoueurTeam1 = newJoueurTeam1[:-1]
        #L'equipe 2
        newJoueurTeam2 = ""
        newTypeTeam2 = state[5]
        for joueur in state[4].split("/"):
            newJoueurTeam2 += self.strToTupleToSymToStr(joueur) + "/"
        newJoueurTeam2 = newJoueurTeam2[:-1]
        newState.append(newJoueurTeam2)
        newState.append(newTypeTeam2)
        newState.append(newJoueurTeam1)
        newState.append(newTypeTeam1)
        newState.append(state[-1])
        #print("New state = ", newState)
        return newState

    @DeprecationWarning
    def getSymetricPosition(self,tupl):
        middle = GAME_WIDTH / 2
        newWidthPos = round(middle + (middle - float(tupl[0])),9)
        return (newWidthPos,tupl[1])

    @DeprecationWarning
    def getSymetricTarget(self, target):
        if(target == "CornerTopLeft"):
            return "CornerTopRight"
        if (target == "CornerTopRight"):
            return "CornerTopLeft"
        if (target == "CornerBottomLeft"):
            return "CornerBottomRight"
        if (target == "CornerBottomRight"):
            return "CornerBottomLeft"
        if(target[0] == '('):
            return '(' + str(2 - (int(target[1])-1)) + ", " + target[4] + ")"
        return "'" + target + "'"


    def strToSomething(self,string,type):
        res = string.split(",")
        firstValue = res[0][1:]
        secondValue = res[1][:-1]
        if type == "floatTuple":
            return (float(firstValue),float(secondValue))
        elif type == "floatList":
            return [float(firstValue),float(secondValue)]
        elif type == "intTuple":
            return (int(firstValue), int(secondValue))
        elif type == "Vector2D":
            return Vector2D(float(firstValue),float(secondValue))

    def strToFloatTuple(self, string):
        return self.strToSomething(string, "floatTuple")

    def strToFloatList(self, string):
        return self.strToSomething(string, "floatList")

    def strToIntTuple(self, string):
        return self.strToSomething(string, "intTuple")

    def strToVector2D(self, string):
        return self.strToSomething(string, "Vector2D")

    def floatTupleToStr(self, tupl):
        return "("+str(tupl[0])+","+str(tupl[1])+")"

    @DeprecationWarning
    def strToTupleToSymToStr(self, string):
        tupl = self.strToFloatTuple(string)
        symTuple = self.getSymetricPosition(tupl)
        return self.floatTupleToStr(symTuple)

    def drawTSNE(self,readFunction = None):
        dataX = self.dataToNumpyArray(self.import_csv(CSVFEATURES,readFunction)[1:])
        print(type(dataX))
        print(len(dataX))
        print(dataX[0])
        dataX_embedded = TSNE(n_components=2, perplexity=40, verbose=2).fit_transform(dataX)
        print(dataX_embedded)
        plt.scatter(dataX_embedded[:,0],dataX_embedded[:,1])
        plt.savefig("Dessin")

    def findLowdensityState(self, nbState = 1,offset = 2):
        #print("In findLowDensityState")
        dataX = self.dataToStateNpArray(self.import_csv(CSVFEATURES,self.rowToABS)[1:])
        indexMaxMinDists = [-1 for i in range(nbState+offset)]
        indexMoyDists = [-1 for i in range(nbState+offset)]
        maxMinDists = [-1 for i in range(nbState+offset)]
        moyDists = [0 for i in range(nbState+offset)]
        for iData in range(len(dataX)):
            currentMoyDist = 0
            currentMinDist = -1
            for data in dataX:
                #Calcul des distances
                currentDist = np.linalg.norm(dataX[iData]-data)
                #Calcul iteratif de la moyenne
                currentMoyDist += currentDist
                #Calcul de la distance minimale
                if(currentDist != 0):
                    if(currentMinDist == -1):
                        currentMinDist = currentDist
                    else:
                        if(currentDist < currentMinDist):
                            currentMinDist = currentDist
            #Calcul du max des distances minimales !
            iMaxMinDist = 0
            haveUpdatedMaxMin = False
            while (iMaxMinDist<len(maxMinDists) and not haveUpdatedMaxMin):
                if(currentMinDist > maxMinDists[iMaxMinDist]):
                    for index in range(len(maxMinDists)-2,iMaxMinDist-1,-1):
                        indexMaxMinDists[index+1] = indexMaxMinDists[index]
                        maxMinDists[index+1] = maxMinDists[index]
                    indexMaxMinDists[iMaxMinDist] = iData
                    maxMinDists[iMaxMinDist] = currentMinDist
                    haveUpdatedMaxMin = True
                iMaxMinDist += 1
            #Calcul du max des moyenne des distances
            currentMoyDist /= len(dataX)-1
            iMoyDist = 0
            haveUpdatedMoy = False
            while (iMoyDist < len(moyDists) and not haveUpdatedMoy):
                if (currentMoyDist > moyDists[iMoyDist]):
                    for index in range(len(moyDists) - 2, iMoyDist - 1, -1):
                        indexMoyDists[index + 1] = indexMoyDists[index]
                        moyDists[index + 1] = moyDists[index]
                    indexMoyDists[iMoyDist] = iData
                    moyDists[iMoyDist] = currentMoyDist
                    haveUpdatedMoy = True
                iMoyDist += 1
        #print(indexMaxMinDists, indexMoyDists, iData)
        #print(maxMinDists,moyDists)
        #Comptage des valeurs rencontrées en fonction de leur ordre.
        allIndexValuate = {}
        for iValue in range(len(indexMaxMinDists)):
            oldValue = allIndexValuate.get(indexMaxMinDists[iValue],0)
            allIndexValuate[indexMaxMinDists[iValue]] = oldValue + (-iValue+nbState+offset)
            oldValue = allIndexValuate.get(indexMoyDists[iValue],0)
            allIndexValuate[indexMoyDists[iValue]] = oldValue + (-iValue+nbState+offset)
        #print(allIndexValuate)
        #Tri des index en fonction de leur valeur de comptage
        sortedIndexValuate = []
        for key in allIndexValuate.keys():
            if(not sortedIndexValuate):
                sortedIndexValuate.append((key,allIndexValuate[key]))
            else:
                currentSortedindex = 0
                isAdded = False
                while(currentSortedindex < len(sortedIndexValuate) and not isAdded):
                    if(sortedIndexValuate[currentSortedindex][1] > allIndexValuate[key]):
                        currentSortedindex+=1
                    else:
                        sortedIndexValuate.insert(currentSortedindex,(key,allIndexValuate[key]))
                        isAdded = True
                if(not isAdded):
                    sortedIndexValuate.append((key,allIndexValuate[key]))
        #print(sortedIndexValuate)
        #Selection des nbState index voulu
        wantedIndex = []
        valueComptage = sortedIndexValuate[0][1]
        currentIndex = 0
        while len(wantedIndex) != nbState: #Choix parmi ceux qui on la valeur de comptage la plus elevee
            possibleIndex = [sortedIndexValuate[currentIndex][0]]
            currentIndex+=1
            while valueComptage == sortedIndexValuate[currentIndex][1]:
                currentIndex+=1
                possibleIndex.append(sortedIndexValuate[currentIndex][0])
            if(len(possibleIndex)+len(wantedIndex) > nbState): #Si on a trop de choix possible : choix aleatoire !
                nbIndexManquant = nbState - len(wantedIndex)
                for i in range(nbIndexManquant):
                    randomIndex = np.random.randint(len(possibleIndex))
                    wantedIndex.append(possibleIndex[randomIndex])
                    possibleIndex.pop(randomIndex)
            else:
                #Ajout de tous les indexs possibles courants
                for index in possibleIndex:
                    wantedIndex.append(index)
        return dataX[wantedIndex]

    def evaluateDensity(self,state):
        #Retourne la distance minimale a un autre etat ainsi que la moyenne des distances
        dataX = self.dataToStateNpArray(self.import_csv(CSVFEATURES, self.rowToABS)[1:])
        minDist = -1
        moyDist = 0
        for data in dataX:
            currentDist = np.linalg.norm(state - data)
            if(minDist == -1):
                minDist = currentDist
            moyDist += currentDist
            if(currentDist<minDist):
                minDist=currentDist
        moyDist /= len(dataX)
        return(minDist,moyDist)



    def dataToStateNpArray(self, dataStates):
        nbValuePerJoueur = 2  # Attention 7 si on rajoute les positions (lignes en commentaires)
        states = np.zeros((len(dataStates), 4 + nbValuePerJoueur * (sum(self.nbPlayer))))
        for iState in range(len(dataStates)):
            currentState = [None for i in range(sum(self.nbPlayer) * nbValuePerJoueur)]
            state = dataStates[iState]
            for joueur in state['team1']:
                finalIndex = joueur["id"][1]
                # Position du joueur
                currentState[0 + finalIndex * nbValuePerJoueur] = joueur["position"][0]
                currentState[1 + finalIndex * nbValuePerJoueur] = joueur["position"][1]
            nbValueTeam1 = nbValuePerJoueur * self.nbPlayer[0]
            for joueur in state['team2']:
                finalIndex = joueur["id"][1]
                # Position du joueur
                currentState[nbValueTeam1 + 0 + finalIndex * nbValuePerJoueur] = joueur["position"][0]
                currentState[nbValueTeam1 + 1 + finalIndex * nbValuePerJoueur] = joueur["position"][1]
            currentState.append(state["ball"][0][0])
            currentState.append(state["ball"][0][1])
            currentState.append(state["ball"][1][0])
            currentState.append(state["ball"][1][1])
            states[iState] = currentState
        return states

    def dataToNumpyArray(self, dataStates):
        # print(currentState)
        # shape 0 : nombre de lignes dans le csv etats
        # shape 1 : nombre de donnees
        # => format du csv
        nbValuePerJoueur = 7  # Attention 7 si on rajoute les positions (lignes en commentaires)
        states = np.zeros((len(dataStates), 6 + nbValuePerJoueur * (sum(self.nbPlayer))))
        for iState in range(len(dataStates)):
            currentState = [None for i in range(sum(self.nbPlayer) * nbValuePerJoueur)]
            state = dataStates[iState]
            indiceJoueur = 0
            for joueur in state['joueursTeam1']:
                finalIndex = joueur["id"][1]
                # Position du joueur
                currentState[0 + finalIndex * nbValuePerJoueur] = joueur["position"][0]
                currentState[1 + finalIndex * nbValuePerJoueur] = joueur["position"][1]
                # Distance à l'allie le plus proche
                currentState[2 + finalIndex * nbValuePerJoueur] = joueur['distAllieLPP']
                # Distance à l'adversaire le plus proche
                currentState[3 + finalIndex * nbValuePerJoueur] = joueur['distAdvLPP']
                # Distance à la Balle
                currentState[4 + finalIndex * nbValuePerJoueur] = joueur['distBall']
                # Distance à la cage de son equipe
                currentState[5 + finalIndex * nbValuePerJoueur] = joueur['distSaCage']
                # Distance à la cage adversaire
                currentState[6 + finalIndex * nbValuePerJoueur] = joueur['distCageAdv']
                indiceJoueur += 1
            indiceJoueur = 0
            nbValueTeam1 = nbValuePerJoueur * self.nbPlayer[0]
            for joueur in state['joueursTeam2']:
                finalIndex = joueur["id"][1]
                # Position du joueur
                currentState[nbValueTeam1 + 0 + finalIndex * nbValuePerJoueur] = joueur["position"][0]
                currentState[nbValueTeam1 + 1 + finalIndex * nbValuePerJoueur] = joueur["position"][1]
                currentState[nbValueTeam1 + 2 + finalIndex * nbValuePerJoueur] = joueur['distAllieLPP']
                currentState[nbValueTeam1 + 3 + finalIndex * nbValuePerJoueur] = joueur['distAdvLPP']
                currentState[nbValueTeam1 + 4 + finalIndex * nbValuePerJoueur] = joueur['distBall']
                currentState[nbValueTeam1 + 5 + finalIndex * nbValuePerJoueur] = joueur['distSaCage']
                currentState[nbValueTeam1 + 6 + finalIndex * nbValuePerJoueur] = joueur['distCageAdv']
                indiceJoueur += 1
            equipe = state['positionsTeam1']
            currentState.append(equipe['distAdvLPPCage'])
            currentState.append(equipe['distDefLPPCage'])
            currentState.append(equipe['distBallCage'])
            equipe = state['positionsTeam2']
            currentState.append(equipe['distAdvLPPCage'])
            currentState.append(equipe['distDefLPPCage'])
            currentState.append(equipe['distBallCage'])
            states[iState] = currentState
        return states