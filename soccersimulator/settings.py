# -*- coding: utf-8 -*-
### DEFINITION DES CONSTANTES
GAME_WIDTH = 150
GAME_HEIGHT = 90
GAME_GOAL_HEIGHT = 10
PLAYER_RADIUS = 1.
BALL_RADIUS = 0.70
maxPlayerSpeed = 1.
maxPlayerAcceleration = 0.2
playerBrackConstant = 0.1
nbWithoutShoot = 10 #Le joueur doit attendre nbWithoutShoot rounds entre deux frappes
maxPlayerShoot = 6.
maxBallAcceleration = 6.
shootRandomAngle = 0.0
ballBrakeConstant = 0.06
ballBrakeSquare = 0.01
MAX_GAME_STEPS = 2000
PREC=4

###DEFINITION DES CARACTERISTIQUES DES JOUEURS :
joueurAgile = {"agility" : 1.2, "speed" : 1.0, "strength" : 0.83}
joueurRapide = {"agility" : 1.0, "speed" : 1.2, "strength" : 0.7}
joueurFort = {"agility" : 0.9, "speed" : 0.9, "strength" : 1.}

#Mutation ou Interpolation
shouldDoMutation = False