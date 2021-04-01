import csv
import os
from .settings import GAME_WIDTH
from .utils import Vector2D

class csvHandler(object):

    def __init__(self, myTeam, nbPlayer):
        self.lastStateSaved = None
        self.myTeam = myTeam
        self.nbPlayer = nbPlayer

    def import_csv(self, filename):
        data = []
        with open(filename, "r") as f:
            reader = csv.reader(f, delimiter='_')
            for row in reader:
                if row:
                    data.append(row)
        return data

    def saveStateInCSV(self, currentState, absolu):
        if os.path.isfile('../soccersimulator/etats.csv') == False:
            with open('../soccersimulator/etats.csv', 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                if absolu:
                    writer.writerow(['ballPos', "nextLikelyPosition", "posTeam1", "typeTeam1", "posTeam2", "typeTeam2", "ballWithTeam"])
                else:
                    writer.writerow(['posPlayer', 'typePlayer', 'distAllieLPP', 'typeAllieLPP', 'distAdvLPP', 'typeAdvLPP', 'distBall', 'distSaCage', 'distCageAdv',
                        'distDefCage1', 'typeDefCage1', 'distAdvCage1', 'typeAdvCage1', 'distBallCage1', 'distDefCage2', 'typeDefCage2', 'distAdvCage2', 'typeAdvCage2', 'distBallCage2',  ])
        with open('../soccersimulator/etats.csv', 'a', newline='') as f:
            writer = csv.writer(f, delimiter='_')
            writer.writerow(currentState)

    def saveOrderInCSV(self, order, appendFile = False):
        if os.path.isfile('../soccersimulator/ordres.csv') == False:
            with open('../soccersimulator/ordres.csv', 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                writer.writerow(['joueur', 'action', 'cible'])
        if appendFile:
            data = self.import_csv('../soccersimulator/ordres.csv')
            # print("##DATA: ",data)
            lastRow = data[-1]
            # print("##LASTROW: ",lastRow)
            with open('../soccersimulator/ordres.csv', 'w', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                for row in data:
                    if row == lastRow:
                        if lastRow[0] == 'joueur':
                            writer.writerow(order)
                        else:
                            list = []
                            for ordre in lastRow:
                                list.append((ordre))
                            list.append(order)
                            writer.writerow(list)
                    else:
                        writer.writerow((row))
        else:
            with open('../soccersimulator/ordres.csv', 'a', newline='') as f:
                writer = csv.writer(f, delimiter='_')
                for elt in order:
                    if elt == "se déplace vers":
                        elt.replace("déplace", "deplace")
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
            #Calcul des nombres de joueurs par équipe !
            nbJoueurTot = sum(self.nbPlayer)
            nbJoueurTeam0 = self.nbPlayer[0]
            #Joueur de l'équipe 0
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
            # Joueur de l'équipe 1
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
            # Position de l'équipe 0
            posit1 = dict()
            startIndex = nbJoueurTot
            posit1["distAdvLPPCage"] = state[startIndex]
            posit1["typeAdvLPPCage"] = state[startIndex+1]
            posit1["distDefLPPCage"] = state[startIndex+2]
            posit1["typeDefLPPCage"] = state[startIndex+3]
            posit1["distBallCage"] = state[startIndex+4]
            newState["positionsTeam1"] = posit1
            # Position de l'équipe 1
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

    def duplicateData(self,stateFilePath,orderFilePath, outputStatePath, outputOrderPath, addOnlySymetric = False):
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
                        current = "se déplace vers"
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

    def getSymetricPosition(self,tupl):
        middle = GAME_WIDTH / 2
        newWidthPos = round(middle + (middle - float(tupl[0])),9)
        return (newWidthPos,tupl[1])

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

    def strToTupleToSymToStr(self, string):
        tupl = self.strToFloatTuple(string)
        symTuple = self.getSymetricPosition(tupl)
        return self.floatTupleToStr(symTuple)
