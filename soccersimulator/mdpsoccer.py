# -*- coding: utf-8 -*-<
import math
import threading
from collections import namedtuple
from threading import Lock
from copy import deepcopy
from .utils import Vector2D, MobileMixin
from .events import SoccerEvents
from . import settings
from .utils import dict_to_json
import random
import time
import zipfile
import traceback
import logging
from .database import csvHandler
import numpy as np

logger = logging.getLogger("soccersimulator.mdpsoccer")
###############################################################################
# SoccerAction
###############################################################################


class SoccerAction(object):
    """ Action d'un joueur : comporte un vecteur acceleration et un vecteur shoot.
    """
    def __init__(self, acceleration=None, shoot=None,name=None):
        self.acceleration = acceleration or Vector2D()
        self.shoot = shoot or Vector2D()
        self.name = name or ""
    def copy(self):
        return deepcopy(self)
    def set_name(self,name):
        self.name = name
        return self
    def __str__(self):
        return "Acc:%s, Shoot:%s, Name:%s" % (str(self.acceleration), str(self.shoot), str(self.name))
    def __repr__(self):
        return "SoccerAction(%s,%s,%s)" % (self.acceleration.__repr__(),self.shoot.__repr__(),self.name)
    def __eq__(self, other):
        return (other.acceleration == self.acceleration) and (other.shoot == self.shoot)
    def __add__(self, other):
        return SoccerAction(self.acceleration + other.acceleration, self.shoot + other.shoot)
    def __sub__(self, other):
        return Vector2D(self.acceleration - other.acceleration, self.shoot - other.shoot)
    def __iadd__(self, other):
        self.acceleration += other.acceleration
        self.shoot += other.shoot
        return self
    def __isub__(self, other):
        self.acceleration -= other.acceleration
        self.shoot -= other.shoot
        return self
    def to_dict(self):
        return {"acceleration":self.acceleration,"shoot":self.shoot,"name":self.name}

###############################################################################
# Ball
###############################################################################
class Ball(MobileMixin):
    def __init__(self,position=None,vitesse=None,**kwargs):
        super(Ball,self).__init__(position,vitesse,**kwargs)
    def next(self,shoot):
        vitesse = self.vitesse.copy()
        vitesse.norm = self.vitesse.norm - settings.ballBrakeSquare * self.vitesse.norm ** 2 - settings.ballBrakeConstant * self.vitesse.norm
        ## decomposition selon le vecteur unitaire de ball.speed
        snorm = shoot.norm
        if snorm > 0:
            u_s = shoot.copy()
            u_s.normalize()
            #u_t = Vector2D(-u_s.y, u_s.x)
            speed_abs = abs(vitesse.dot(u_s))
            #speed_ortho = vitesse.dot(u_t)
            #speed_tmp = Vector2D(speed_abs * u_s.x - speed_ortho * u_s.y, speed_abs * u_s.y + speed_ortho * u_s.x)
            speed_tmp = Vector2D(speed_abs * u_s.x, speed_abs * u_s.y)
            speed_tmp += shoot
            vitesse = speed_tmp
        self.vitesse = vitesse.norm_max(settings.maxBallAcceleration).copy()
        self.position += self.vitesse

    def inside_goal(self):
        return (self.position.x < 0 or self.position.x > settings.GAME_WIDTH)\
                and abs(self.position.y - (settings.GAME_HEIGHT / 2.)) < settings.GAME_GOAL_HEIGHT / 2.

    @property
    def nextLikelyPosition(self):
        ## predit la position du ballon apres une passe ou un tir vers le goal pour permettre une interception
        currentVitesse = self.vitesse.copy()
        currentPos = self.position.copy() + currentVitesse
        while currentVitesse.norm > 0.1:
            currentVitesse.norm = currentVitesse.norm - settings.ballBrakeSquare * currentVitesse.norm ** 2 - settings.ballBrakeConstant * currentVitesse.norm
            currentPos += currentVitesse
        return currentPos

    def __repr__(self):
        return "Ball(%s,%s)" % (self.position.__repr__(),self.vitesse.__repr__())
    def __str__(self):
        return "Ball: pos: %s, vit: %s, nextPos: %s" %(str(self.position),str(self.vitesse), str(self.nextLikelyPosition))

###############################################################################
# PlayerState
###############################################################################

class PlayerState(MobileMixin):
    """ Represente la configuration d'un joueur : un etat  mobile (position, vitesse), et une action SoccerAction
    """
    def __init__(self, position=None, vitesse=None,**kwargs):
        """
        :param position: position du  joueur
        :param acceleration: acceleration du joueur
        :param action: action SoccerAction du joueur
        :return:
        """
        super(PlayerState,self).__init__(position,vitesse)
        self.action = kwargs.pop('action', SoccerAction())
        self.last_shoot = kwargs.pop('last_shoot', 0)
        self.__dict__.update(kwargs)
    def to_dict(self):
        return {"position":self.position,"vitesse":self.vitesse,"action":self.action,"last_shoot":self.last_shoot}
    def __str__(self):
        return "pos: %s, vit: %s, action:%s" %(str(self.position),str(self.acceleration),str(self.action))
    def __repr__(self):
        return "PlayerState(position=%s,vitesse=%s,action=%s,last_shoot=%d)" %  \
                            (self.position.__repr__(),self.vitesse.__repr__(),self.action.__repr__(),self.last_shoot)
    @property
    def acceleration(self):
        """
        :return: Vector2D Action acceleration du joueur
        """
        return self.action.acceleration.norm_max(settings.maxPlayerAcceleration)
    @acceleration.setter
    def acceleration(self,v):
        self.action.acceleration = v
    @property
    def shoot(self):
        """ Vector2D Action shoot du joueur
        :return:
        """
        return self.action.shoot.norm_max(settings.maxPlayerShoot)
    @shoot.setter
    def shoot(self,v):
        self.action.shoot = v
    def next(self, ball, action=None, playerSpeedCoef = 1.):
        """ Calcul le prochain etat en fonction de l'action et de la position de la balle
        :param ball:
        :param action:
        :return: Action shoot effectue
        """
        if not (hasattr(action,"acceleration") and hasattr(action,"shoot")):
            action = SoccerAction()
        self.action = action.copy()
        self.vitesse *= (1 - settings.playerBrackConstant)
        self.vitesse = (self.vitesse + self.acceleration).norm_max(settings.maxPlayerSpeed*playerSpeedCoef)
        self.position += self.vitesse
        if self.position.x < 0 or self.position.x > settings.GAME_WIDTH \
                or self.position.y < 0 or self.position.y > settings.GAME_HEIGHT:
            self.position.x = max(0, min(settings.GAME_WIDTH, self.position.x))
            self.position.y = max(0, min(settings.GAME_HEIGHT, self.position.y))
            self.vitesse = Vector2D()
        if self.shoot.norm == 0 or not self.can_shoot():
            self._dec_shoot()
            return Vector2D()
        self._reset_shoot()
        if self.position.distance(ball.position) > (settings.PLAYER_RADIUS + settings.BALL_RADIUS):
            return Vector2D()
        return self._rd_angle(self.shoot,(self.vitesse.angle-self.shoot.angle)*(0 if self.vitesse.norm==0 else 1),\
                    self.position.distance(ball.position)/(settings.PLAYER_RADIUS+settings.BALL_RADIUS))
    @staticmethod
    def _rd_angle(shoot,dangle,dist):
        eliss = lambda x, alpha: (math.exp(alpha*x)-1)/(math.exp(alpha)-1)
        dangle = abs((dangle+math.pi*2) %(math.pi*2) -math.pi)
        dangle_factor =eliss(1.-max(dangle-math.pi/2,0)/(math.pi/2.),5)
        norm_factor = eliss(shoot.norm/settings.maxPlayerShoot,4)
        dist_factor = eliss(dist,10)
        angle_prc = (1-(1.-dangle_factor)*(1.-norm_factor)*(1.-0.5*dist_factor))*settings.shootRandomAngle*math.pi/2.
        norm_prc = 1-0.3*dist_factor*dangle_factor
        return Vector2D(norm=shoot.norm*norm_prc,
                        angle=shoot.angle+2*(random.random()-0.5)*angle_prc)
    def can_shoot(self):
        """ Le joueur peut-il shooter
        :return:
        """
        return self.last_shoot <= 0
    def _dec_shoot(self):
        self.last_shoot -= 1
    def _reset_shoot(self):
        self.last_shoot = settings.nbWithoutShoot
    def copy(self):
        return deepcopy(self)

###############################################################################
# SoccerState
###############################################################################

class SoccerState(object):
    """ Etat d'un tour du jeu. Contient la balle, l'ensemble des etats des joueurs, le score et
    le numero de l'etat.
    """


    def __init__(self,states=None,ball=None,**kwargs):
        self.states = states or dict()
        self.ball = ball or Ball()
        self.strategies = kwargs.pop('strategies',dict())
        self.score = kwargs.pop('score', {1: 0, 2: 0})
        self.step = kwargs.pop('step', 0)
        self.max_steps = kwargs.pop('max_steps', settings.MAX_GAME_STEPS)
        self.goal = kwargs.pop('goal', 0)
        self.__dict__.update(kwargs)
        ###############################################
        self.ballControl = 1 #l'equipe qui shoot le ballon à l'instant même


    def __str__(self):
        return ("Step: %d, %s " %(self.step,str(self.ball)))+\
               " ".join("(%d,%d):%s" %(k[0],k[1],str(p)) for k,p in sorted(self.states.items()))+\
               (" score : %d-%d" %(self.score_team1,self.score_team2))+\
               (", ballControl : %s" %(self.ballControl))
    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return dict(states=dict_to_json(self.states),
                strategies=dict_to_json( self.strategies),
                ball=self.ball,score=dict_to_json(self.score),step=self.step,
                max_steps=self.max_steps,goal=self.goal,ballControl = self.ballControl)
    def player_state(self, id_team, id_player):
        """ renvoie la configuration du joueur
        :param id_team: numero de la team du joueur
        :param id_player: numero du joueur
        :return:
        """
        return self.states[(id_team, id_player)]

    @property
    def players(self):
        """ renvoie la liste des cles des joueurs (idteam,idplayer)
        :return: liste des cles
        """
        return sorted(self.states.keys())

    def nb_players(self, team):
        """ nombre de joueurs de la team team
        :param team: 1 ou 2
        :return:
        """
        return len([x for x in self.states.keys() if x[0] == team])

    def get_score_team(self, idx):
        """ score de la team idx : 1 ou 2
        :param idx: numero de la team
        :return:
        """
        return self.score[idx]

    @property
    def score_team1(self):
        return self.get_score_team(1)

    @property
    def score_team2(self):
        return self.get_score_team(2)

    def copy(self):
        return deepcopy(self)

    def apply_actions(self, actions=None,strategies=None):
        if strategies: self.strategies.update(strategies)
        shoots = []
        playersAgility = 0
        playersStrength = 0
        playersAgilityIndex = -1
        playerTeam = None
        self.goal = 0
        if actions:
            #print("########################################################")
            for k, c in self.states.items():
                if k in actions:
                    #print("********************************************************")
                    #print(k, actions[k][1]["agility"])
                    #print(c)
                    shoots.append(c.next(self.ball, actions[k][0], actions[k][1]["speed"]))
                    if((playersAgility < actions[k][1]["agility"] or (playersAgility == actions[k][1]["agility"] and self.ballControl != k[0])) and (shoots[-1].x != 0.0 or shoots[-1].y != 0.0)):
                    #    print("CHANGEMENT", actions[k][1]["agility"])
                        playersAgility = actions[k][1]["agility"]
                        playersStrength = actions[k][1]["strength"]
                        playersAgilityIndex = len(shoots)-1
                        playerTeam = k[0]
                    #    print(k)
                    #print(shoots)
                    #print(actions[k])
                    #print(self.player_state(k[0],k[1]))
        #print("########################################################")
        if(playerTeam):
            self.ballControl = playerTeam
        self.ball.next(shoots[playersAgilityIndex].scale(playersStrength))
        self.step += 1
        if self.ball.inside_goal():
            self._do_goal(2 if self.ball.position.x <= 0 else 1)
            return
        if self.ball.position.x < 0:
            self.ball.position.x = -self.ball.position.x
            self.ball.vitesse.x = -self.ball.vitesse.x
        if self.ball.position.y < 0:
            self.ball.position.y = -self.ball.position.y
            self.ball.vitesse.y = -self.ball.vitesse.y
        if self.ball.position.x > settings.GAME_WIDTH:
            self.ball.position.x = 2 * settings.GAME_WIDTH - self.ball.position.x
            self.ball.vitesse.x = -self.ball.vitesse.x
        if self.ball.position.y > settings.GAME_HEIGHT:
            self.ball.position.y = 2 * settings.GAME_HEIGHT - self.ball.position.y
            self.ball.vitesse.y = -self.ball.vitesse.y

    def _do_goal(self, idx):
        self.score[idx]+=1
        self.goal = idx

    @classmethod
    def create_initial_state(cls, nb_players_1=0, nb_players_2=0, team = 1):
        """ Creer un etat initial avec le nombre de joueurs indique
        :param nb_players_1: nombre de joueur de la team 1
        :param nb_players_2: nombre de joueur de la teamp 2
        :return:
        """
        state = cls()
        state.reset_state(nb_players_1=nb_players_1,nb_players_2= nb_players_2, team = team)
        return state

    @classmethod
    def createMutatedState(cls, nb_players_1=0,nb_players_2=0, mutationValue = 0.1):
        state = cls()
        dataHandler = csvHandler(1,[nb_players_1,nb_players_2])
        dataLowDensity = dataHandler.findLowdensityState(nbState=1)[0]
        randomData = np.random.random_sample(len(dataLowDensity)) * np.tile(np.array([150,90]),int(len(dataLowDensity)/2))
        dataLowDensity = dataLowDensity*(1-mutationValue)+randomData*mutationValue
        if((nb_players_1 + nb_players_2)*2 != len(dataLowDensity) - 4):
            raise AttributeError
        if nb_players_1 == 4:
            state.states[1, 0] = PlayerState(position=Vector2D(dataLowDensity[0], dataLowDensity[1]))
            state.states[1, 1] = PlayerState(position=Vector2D(dataLowDensity[2], dataLowDensity[3]))
            state.states[1, 2] = PlayerState(position=Vector2D(dataLowDensity[4], dataLowDensity[5]))
            state.states[1, 3] = PlayerState(position=Vector2D(dataLowDensity[6], dataLowDensity[7]))
        if nb_players_2 == 4:
            state.states[2, 0] = PlayerState(position=Vector2D(dataLowDensity[8], dataLowDensity[9]))
            state.states[2, 1] = PlayerState(position=Vector2D(dataLowDensity[10], dataLowDensity[11]))
            state.states[2, 2] = PlayerState(position=Vector2D(dataLowDensity[12], dataLowDensity[13]))
            state.states[2, 3] = PlayerState(position=Vector2D(dataLowDensity[14], dataLowDensity[15]))
        state.ball = Ball(Vector2D(dataLowDensity[-4],dataLowDensity[-3]),Vector2D())
        state.goal = 0
        return state

    @classmethod
    def createInterpolateState(cls, nb_players_1=0,nb_players_2=0):
        state = cls()
        dataHandler = csvHandler(1, [nb_players_1, nb_players_2])
        dataLowDensity = dataHandler.findLowdensityState(nbState=2)
        #Parcours des possibles interpolations et selection de la meilleure
        bestInterpolationValue = -1
        bestEvaluation = 0
        for interpolationValue in range(1,10):
            currentInterpolationValue = interpolationValue/10
            #print(currentInterpolationValue, " : ", end="")
            currentDataLowDensity = dataLowDensity[0] * currentInterpolationValue + dataLowDensity[1] * (1-currentInterpolationValue)
            currentEvaluation = dataHandler.evaluateDensity(currentDataLowDensity)
            #print(currentEvaluation[0],currentEvaluation[1])
            if(currentEvaluation[0]+currentEvaluation[1] > bestEvaluation):
                bestInterpolationValue = currentInterpolationValue
                bestEvaluation = currentEvaluation[0]+currentEvaluation[1]
        #print("Result : ", bestInterpolationValue, bestEvaluation)
        dataLowDensity = dataLowDensity[0] * bestInterpolationValue + dataLowDensity[1] * (1-bestInterpolationValue)
        if ((nb_players_1 + nb_players_2) * 2 != len(dataLowDensity) - 4):
            raise AttributeError
        if nb_players_1 == 4:
            state.states[1, 0] = PlayerState(position=Vector2D(dataLowDensity[0], dataLowDensity[1]))
            state.states[1, 1] = PlayerState(position=Vector2D(dataLowDensity[2], dataLowDensity[3]))
            state.states[1, 2] = PlayerState(position=Vector2D(dataLowDensity[4], dataLowDensity[5]))
            state.states[1, 3] = PlayerState(position=Vector2D(dataLowDensity[6], dataLowDensity[7]))
        if nb_players_2 == 4:
            state.states[2, 0] = PlayerState(position=Vector2D(dataLowDensity[8], dataLowDensity[9]))
            state.states[2, 1] = PlayerState(position=Vector2D(dataLowDensity[10], dataLowDensity[11]))
            state.states[2, 2] = PlayerState(position=Vector2D(dataLowDensity[12], dataLowDensity[13]))
            state.states[2, 3] = PlayerState(position=Vector2D(dataLowDensity[14], dataLowDensity[15]))
        state.ball = Ball(Vector2D(dataLowDensity[-4], dataLowDensity[-3]), Vector2D())
        state.goal = 0
        return state

    def reset_state(self, nb_players_1=0, nb_players_2=0, team = 1):
        def InversePosition(vector, team = team):
            if(team == 2):
                return Vector2D(settings.GAME_WIDTH - vector.x,vector.y)
            return vector
        def InverseTeam(teamJoueur, team = team):
            if(team == 2):
                return int(-teamJoueur+3)
            return teamJoueur
        def getNbPlayers(team):
            if(team == 1):
                return nb_players_1
            else:
                return  nb_players_2

        if nb_players_1 == 0 and self.nb_players(1) > 0:
            nb_players_1 = self.nb_players(1)
        if nb_players_2 == 0 and self.nb_players(2) > 0:
            nb_players_2 = self.nb_players(2)
        quarters = [i * settings.GAME_HEIGHT / 4. for i in range(1, 4)]
        rows = [settings.GAME_WIDTH * 0.1, settings.GAME_WIDTH * 0.35, settings.GAME_WIDTH * (1 - 0.35),
                settings.GAME_WIDTH * (1 - 0.1)]
        if getNbPlayers(InverseTeam(1)) == 1:
            self.states[(InverseTeam(1), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*0.9, quarters[1])))
        if getNbPlayers(InverseTeam(2)) == 1:
            self.states[(InverseTeam(2), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*1.5, quarters[1])))
        if getNbPlayers(InverseTeam(1)) == 2:
            self.states[(InverseTeam(1), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*0.9, quarters[1])))
            self.states[(InverseTeam(1), 1)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.2, quarters[1])))
        if getNbPlayers(InverseTeam(2)) == 2:
            self.states[(InverseTeam(2), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*1.3, quarters[1])))
            self.states[(InverseTeam(2), 1)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.9, quarters[1])))
        if getNbPlayers(InverseTeam(1)) == 3:
            self.states[(InverseTeam(1), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*0.9, quarters[1])))
            self.states[(InverseTeam(1), 1)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.30, quarters[0])))
            self.states[(InverseTeam(1), 2)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.30, quarters[2])))
        if getNbPlayers(InverseTeam(2)) == 3:
            self.states[(InverseTeam(2), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*1.3, quarters[1])))
            self.states[(InverseTeam(2), 1)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.85, quarters[0])))
            self.states[(InverseTeam(2), 2)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.85, quarters[2])))
        if getNbPlayers(InverseTeam(1)) == 4:
            self.states[(InverseTeam(1), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*0.9, quarters[1])))
            self.states[(InverseTeam(1), 1)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.30-5, quarters[0])))
            self.states[(InverseTeam(1), 2)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.30+5, quarters[2])))
            self.states[(InverseTeam(1), 3)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.15, quarters[1])))
        if getNbPlayers(InverseTeam(2)) == 4:
            self.states[(InverseTeam(2), 0)] = PlayerState(position=InversePosition(Vector2D((settings.GAME_WIDTH/2)*1.3, quarters[1])))
            self.states[(InverseTeam(2), 1)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.8-5, quarters[0])))
            self.states[(InverseTeam(2), 2)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.8+5, quarters[2])))
            self.states[(InverseTeam(2), 3)] = PlayerState(position=InversePosition(Vector2D(settings.GAME_WIDTH*0.9, quarters[1])))
        self.ball = Ball(Vector2D(settings.GAME_WIDTH / 2, settings.GAME_HEIGHT / 2),Vector2D())
        self.goal = 0
        return self



###############################################################################
# SoccerTeam
###############################################################################

class Player(object):
    def __init__(self,name=None,strategy=None, type="agility", simu=None):
        """
        :param name:
        :param strategy:
        :param type: Trois types de joueurs pour l'instant : valeur possible sont : "agility", "speed", "strength". Les valeurs sont dans settings.py
        :param simu: la simulation entiere
        """
        self.name = name or ""
        self.strategy = strategy
        self.type = type
        if(type=="agility"):
            self.characs = settings.joueurAgile
        elif(type=="speed"):
            self.characs = settings.joueurRapide
        elif(type=="strength"):
            self.characs = settings.joueurFort
    def to_dict(self):
        return dict(name=self.name)
    def __str__(self):
        return "%s (%s)" %(self.name,str(self.strategy))
    def __repr__(self):
        return self.__str__()
    def to_dict(self):
        return {"name":self.name,"strategy":self.strategy.__repr__(),"type":self.type}

class SoccerTeam(object):
    """ Equipe de foot. Comporte une  liste ordonnee de  Player.
    """

    def __init__(self, name=None, players=None, login=None, simu = None, entraineur = None):
        """
        :param name: nom de l'equipe
        :param players: liste de joueur Player(name,strategy)
        :return:
        """
        self.name, self.players, self.login = name or "", players or [], login or ""
        self.entraineur = entraineur
    def to_dict(self):
        return {"name":self.name,"players":self.players,"login":self.login}
    def __iter__(self):
        return iter(self.players)

    def __str__(self):
        return str(self.name)+"("+self.login+")"+": "+" ".join(str(p) for p in self.players)
    def __repr__(self):
        return self.__str__()


    def add(self,name,strategy,type = "agility"):
        self.players.append(Player(name,strategy,type))
        if(self.entraineur != None):
            strats = self.entraineur.getOrderStrategies()
            strats[len(self.players)-1]=strategy
            self.entraineur.setOrderStrategies(strats)
        return self
    @property
    def players_name(self):
        """
        :return: liste des noms des joueurs de l'equipe
        """
        return [x.name for x in self.players]
    def player_name(self, idx):
        """
        :param idx: numero du joueur
        :return: nom du joueur
        """
        return self.players[idx].name
    #------------------------------------------------------------------------------------------------
    #------------------------------------------------------------------------------------------------
    def players_type(self):
        """ retourne listes des types des joueurs de l'equipe"""
        return [x.type for x in self.players]
    def player_type(self, idx):
        """ retourne type du joueur de numero idx"""
        return self.players[idx].type
    #------------------------------------------------------------------------------------------------
    #------------------------------------------------------------------------------------------------

    @property
    def strategies(self):
        """
        :return: liste des strategies des joueurs
        """
        return [x.strategy for x in self.players]
    def strategy(self, idx):
        """
        :param idx: numero du joueur
        :return: strategie du joueur
        """
        return self.players[idx].strategy
    def compute_strategies(self, state, id_team):
        """ calcule les actions de tous les joueurs
        :param state: etat courant
        :param id_team: numero de l'equipe
        :return: dictionnaire action et caracteristique des joueurs
        """
        if(self.entraineur != None):
            if(hasattr(self.entraineur, 'setCurrentState')):
                self.entraineur.setCurrentState(state)
            self.entraineur.giveOrders()
        return dict([((id_team, i), (x.strategy.compute_strategy(state.copy(), id_team, i),x.characs)) for i, x in
                     enumerate(self.players) if  hasattr( x.strategy,"compute_strategy")])

    # ------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------
    def giveOrder(self, idx,order):
        """
        :param idx: numero du joueur
        """
        self.players[idx].strategy.addOrder(order)

    def resetOrder(self, idx):
        self.players[idx].strategy.resetOrders()

    def resetOrders(self):
        for player in self.players:
            player.strategy.resetOrders()
    # ------------------------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------------------------

    @property
    def nb_players(self):
        """
        :return: nombre de joueurs
        """
        return len(self.players)
    def copy(self):
        return deepcopy(self)



###############################################################################
# Simulation
###############################################################################


class Simulation(object):
    ETAT = None

    def __init__(self,team1=None,team2=None, shouldSaveData = True, max_steps = settings.MAX_GAME_STEPS,initial_state=None,getMoreData = False, isPlayable = False,**kwargs):
        self.team1, self.team2 = team1 or SoccerTeam(),team2 or SoccerTeam()
        #######################################################
        if(hasattr(self.team1.entraineur, 'setter')):
            self.team1.entraineur.setter(1,[len(self.team1.players),len(self.team2.players)])
        if (hasattr(self.team2.entraineur, 'setter')):
            self.team2.entraineur.setter(2,[len(self.team1.players),len(self.team2.players)])
        self.shouldSaveData = shouldSaveData
        self.initial_state = initial_state or  SoccerState.create_initial_state(self.team1.nb_players,self.team2.nb_players)
        self.initial_state2 = SoccerState.create_initial_state(self.team1.nb_players,self.team2.nb_players,2)
        if(getMoreData):
            if(settings.shouldDoMutation):
                self.unseenState = SoccerState.createMutatedState(self.team1.nb_players,self.team2.nb_players)
            else:
                self.unseenState = SoccerState.createInterpolateState(self.team1.nb_players,self.team2.nb_players)
        else:
            self.unseenState = None
        self.isPlayable = isPlayable
        self.ignoredPlayer = None
        #######################################################
        self.state = self.initial_state.copy()
        Simulation.ETAT = self.state.copy()
        self.max_steps = max_steps
        self.state.max_steps = self.initial_state.max_steps =  max_steps
        self.listeners = SoccerEvents()
        self._thread = None
        self._on_going = False
        self._thread = None
        self._kill = False
        self.states = []
        self.error = False
        try:
            self.replay = type(self.team1.strategy(0))==str or type(self.team1.strategy(0)) == unicode
        except NameError:
            self.replay = type(self.team1.strategy(0))==str
        for s in self.team1.strategies + self.team2.strategies:
            self.listeners += s
        self.__dict__.update(kwargs)

    def reset(self):
        try:
            self.replay = type(self.team1.strategy(0))==str or type(self.team1.strategy(0)) == unicode
        except NameError:
            self.replay = type(self.team1.strategy(0))==str
        self._thread = None
        self._kill = False
        self._on_going = False
        if self.replay:
            return
        self.states = []
        self.state = self.get_initial_state()
        self.error = False
    def to_dict(self):
        return dict(team1=self.team1,team2=self.team2,state=self.state,max_steps=self.max_steps,states=self.states,initial_state=self.initial_state)
    def get_initial_state(self, team = 1):
        if(self.unseenState):
            return self.unseenState
        if(team == 2):
            return self.initial_state2.copy()
        return self.initial_state.copy()
    def start_thread(self):
        if not self._thread or not self._thread.isAlive():
            self._kill = False
            self._thread = threading.Thread(target=self.start)
            self._thread.start()
    def kill(self):
        self._kill = True
    def set_state(self,state):
        state.score = self.state.score
        self.state = state
        self.state.max_steps = self.max_steps
        self.state.step = len(self.states)
    def start(self):
        if self._on_going:
            return
        if self.replay:
            self.state = self.states[0]
        self.begin_match()
        while not self.stop():
            self.next_step()
        self.end_match()
        self._on_going = False
        return self
    @property
    def step(self):
        return self.state.step

    def get_score_team(self,i):
        return self.state.get_score_team(i)
    def next_step(self):
        if self.stop():
            return
        if self.replay:
            self.state = self.states[self.state.step+1]
        else:
            actions=dict()
            strategies=dict()
            for i,t in enumerate([self.team1,self.team2]):
                try:
                    actions.update(t.compute_strategies(self.state, i+1))
                    strategies.update(dict([((i,j),s.name) for j,s in enumerate(t.strategies)]))
                except Exception as e:
                    time.sleep(0.0001)
                    logger.debug("%s" % (traceback.format_exc(),))
                    logger.warning("%s" %(e,))
                    self.state.step=self.max_steps
                    self.state.score[2-i]=100
                    self.error = True
                    logger.warning("Error for team %d -- loose match" % ((i+1),))
                    self.states.append(self.state.copy())
                    return
            #print(actions)
            self.state.apply_actions(actions,strategies)
            Simulation.ETAT = self.state.copy()
            self.states.append(self.state.copy())
        self.update_round()
    def get_team(self,idx):
        if idx==1:
            return self.team1
        if idx == 2:
            return self.team2
    def setIgnoredPlayer(self, ignoredPlayer):
        self.ignoredPlayer = ignoredPlayer
        if(ignoredPlayer[0] == 1):
            self.team1.entraineur.ignoredPlayer = ignoredPlayer[1]
            self.team2.entraineur.ignoredPlayer = None
        else:
            self.team2.entraineur.ignoredPlayer = ignoredPlayer[1]
            self.team1.entraineur.ignoredPlayer = None
    def stop(self):
        return self._kill or self.state.step >= self.max_steps or (self.replay and self.step+1>=len(self.states))
    def update_round(self):
        self.listeners.update_round(self.team1,self.team2,self.state.copy())
        if self.state.goal > 0:
            self.end_round()
    def begin_round(self):
        if not self.replay:
            self.score=dict(self.state.score)
            self.set_state(self.get_initial_state(int(-self.state.goal+3)))
            self.team1.resetOrders()
            self.team2.resetOrders()
            self.listeners.begin_round(self.team1,self.team2,self.state.copy())
            self.states.append(self.state.copy())
        self.listeners.begin_round(self.team1,self.team2,self.state.copy())
    def end_round(self):
        self.listeners.end_round(self.team1, self.team2, self.state.copy())
        if not self.stop():
            self.begin_round()
    def begin_match(self):
        self._on_going = True
        self._kill = False
        self.listeners.begin_match(self.team1,self.team2,self.state.copy())
        self.begin_round()
    def end_match(self):
        self._kill = True
        self.listeners.end_match(self.team1,self.team2,self.state.copy())
        self.replay = True
    def send_strategy(self,key):
        self.listeners.send_strategy(key)
