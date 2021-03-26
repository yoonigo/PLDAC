# -*- coding: utf-8 -*-
import pyglet
import csv
import os
# pyglet.options["debug_gl"]=True
# pyglet.options["debug_trace"]=True
# pyglet.options["debug_gl_trace"]=True

from pyglet import gl
import time
import traceback
from . import settings
from .guiutils import *
import logging
from .guisettings import *
from .settings import GAME_HEIGHT, GAME_WIDTH
from .database import csvHandler

#patate = csvHandler()
#patate.duplicateData('../soccersimulator/etats.csv','../soccersimulator/ordres.csv','../soccersimulator/etatsSym.csv','../soccersimulator/ordresSym.csv',True)

FPS = 50.
FPS_MOD = 5.
logger = logging.getLogger("soccersimulator.gui")



class SimuGUI(pyglet.window.Window):
    AUTO = 0
    MANUAL = 1
    NOWAIT = -1
    key_handlers = {
        pyglet.window.key.ESCAPE: lambda w: w.exit(),
        pyglet.window.key.P: lambda w: w.play(),
        pyglet.window.key.PLUS: lambda w: w._increase_fps(),
        pyglet.window.key.MINUS: lambda w: w._decrease_fps(),
        pyglet.window.key.NUM_0: lambda w: w._switch_hud_names(),
        pyglet.window.key._0: lambda w: w._switch_hud_names(),
        pyglet.window.key.NUM_ADD: lambda w: w._increase_fps(),
        pyglet.window.key.NUM_SUBTRACT: lambda w: w._decrease_fps(),
        pyglet.window.key.BACKSPACE: lambda w: w._switch_manual_step_flag(),
        pyglet.window.key.SPACE: lambda w: w._switch_manual_step(),
        ####
        pyglet.window.key.A: lambda w: w.selectAction(),
        pyglet.window.key.T: lambda w: w.selectTargeting(),
        pyglet.window.key.R: lambda w: w.changeTarget(),
        pyglet.window.key.Z: lambda w: w.lowerTargetingMixage(),
        pyglet.window.key.E: lambda w: w.upperTargetingMixage()
        ####
    }

    def __init__(self,simu=None,width=1500,height=800):
        pyglet.window.Window.__init__(self, width=width, height=height, resizable=True)
        self.set_size(width, height)
        self.focus()
        self.clear()
        self._fps = FPS
        self._sprites = dict()
        self._background = BackgroundSprite()
        self._state = None
        self._mode_next = self.AUTO
        self._waiting_key = False
        self._hud_names = True
        self.hud = Hud()
        ###################################################################################
        self.orders_hud = Orders_hud()
        self.csvHandler = csvHandler()
        self.lastPlayersSelectedRecently = []  # TEMPORAIRE IL FAUT DECIDER D'OU LE METTRE
        self.selectedPlayer = [(1, 0), None]
        self.lastTargetsSelectedRecently = []  # TEMPORAIRE IL FAUT DECIDER D'OU LE METTRE
        self.selectedTarget = "SaCage"
        self.selectedTarget2 = "SaCage"
        self.enregistrer = True
        self.lastStateSaved = None
        ###################################################################################
        ###
        pyglet.clock.schedule_interval(self.update, 1. / 25)
        self.set(simu)
        if simu:
            self.play()

    @property
    def state(self):
        return self.get_state()

    def update(self, dt=None):
        self.draw()

    def _wait_next(self):
        if self._mode_next == self.NOWAIT:
            return
        if self._mode_next == self.AUTO:
            time.sleep(1. / self._fps)
        if self._mode_next == self.MANUAL:
            self._waiting_key = True
            while self._waiting_key:
                time.sleep(0.0001)

    def _switch_manual_step_flag(self):
        self._waiting_key = False

    def _switch_manual_step(self):
        if self._mode_next == self.MANUAL:
            self._mode_next = self.AUTO
            self._waiting_key = False
        else:
             self._mode_next = self.MANUAL






    def playerToName(self,player):
        return self.get_team(player[0]).player_name(player[1])

    def selectAction(self):
        self.orders_hud.change_action()

    def selectTargeting(self):
        self.orders_hud.change_targeting()

    def changeTarget(self):
        self.orders_hud.change_target()

    def lowerTargetingMixage(self):
        self.orders_hud.change_mixage_target_value(-1)

    def upperTargetingMixage(self):
        self.orders_hud.change_mixage_target_value(1)

    def resetOrderGUI(self):
        self.lastPlayersSelectedRecently = []  # TEMPORAIRE IL FAUT DECIDER D'OU LE METTRE
        self.selectedPlayer = [(1, 0), None]
        self.lastTargetsSelectedRecently = []  # TEMPORAIRE IL FAUT DECIDER D'OU LE METTRE
        self.selectedTarget = "SaCage"
        self.selectedTarget2 = "SaCage"

    def orderToString(self, order):
        if(order == None):
            return "Fonceur"
        if(len(order)>2):
            action = ""
            actionTmp = order[0].split(" ")
            for word in actionTmp[:-1]:
                action+=word + " "
            action += "entre "
            if (type(order[1]) == tuple):
                cible1 = self.playerToName(order[1])
            else:
                cible1 = order[1]
            if (type(order[2]) == tuple):
                cible2 = self.playerToName(order[2])
            else:
                cible2 = order[2]
            return action + cible1 + " et " + cible2
        else:
            action = order[0] + " "
            if (type(order[1]) == tuple):
                cible = self.playerToName(order[1])
            else:
                cible = order[1]
            return action + cible

    def doOrder(self):
        order = self.orders_hud.get_order()
        team = self.get_team(self.selectedPlayer[0][0])
        for t in [1,2]:
            for i in range(self.get_team(t).nb_players):
                if(self.playerToName((t,i)) == order[1]):
                    order[1] = (t,i)
                if(len(order) == 4):
                    if(self.playerToName((t,i)) == order[2]):
                        order[2] = (t,i)
        team.giveOrder(self.selectedPlayer[0][1],order)
        self.selectedPlayer[1] = order

    def getStateForCSVs(self):
        posBall = self.state.ball.position
        ballNextLikelyPosition = self.state.ball.nextLikelyPosition
        ballTeam = self.state.ballControl
        players = {}
        players[1] = {}
        players[2] = {}
        for k, v in self.state.players:
            players[k][v] = (self.state.player_state(k, v).position, self.get_team(k).player_type(v))
        team1pos = ''
        team2pos = ''
        team1type = ''
        team2type = ''
        for k in players:
            if k == 1:
                for p in players[k]:
                    if team1pos == '':
                        team1pos += str(players[k][p][0])
                    else:
                        team1pos += '/' + str(players[k][p][0])
                    if team1type == '':
                        team1type += players[k][p][1]
                    else:
                        team1type += '/' + players[k][p][1]
            else:
                for p in players[k]:
                    if team2pos == '':
                        team2pos += str(players[k][p][0])
                    else:
                        team2pos += '/' + str(players[k][p][0])
                    if team2type == '':
                        team2type += players[k][p][1]
                    else:
                        team2type += '/' + players[k][p][1]

        return [posBall, ballNextLikelyPosition, team1pos, team1type, team2pos, team2type, ballTeam]

    def on_mouse_press(self,x,y,button,modifiers):
        lengthWindow, heightWindow = self.get_size() #Taille de l'interface en pixel
        x_n, y_n = (x * (settings.GAME_WIDTH + ORDERS_HUD_WIDTH) / lengthWindow, y * (settings.GAME_HEIGHT + HUD_HEIGHT) / heightWindow)

        if(x_n >= settings.GAME_WIDTH): #Selection dans Order_Hud
            if (x_n >= settings.GAME_WIDTH + 12 and x_n <= settings.GAME_WIDTH + 33.3) and ((y_n >= settings.GAME_HEIGHT - 57) and (y_n <= settings.GAME_HEIGHT - 50.5)):
                self.doOrder()
                ### écrire les données de l'état (matrice X)
                if(self.simu.shouldSaveData):
                    self.csvHandler.addDataToCSVs([self.selectedPlayer[0]]+ self.selectedPlayer[1], self.getStateForCSVs())
            elif(x_n >= settings.GAME_WIDTH + 37 and x_n <= settings.GAME_WIDTH + 53) and ((y_n >= settings.GAME_HEIGHT - 57) and (y_n <= settings.GAME_HEIGHT - 50.5)):
                #self.selectedPlayer[1] = None
                team = self.get_team(self.selectedPlayer[0][0])
                team.resetOrder(self.selectedPlayer[0][1])
        else: #Selection sur le terrain
            if(button == 1):
                nearestPlayers = [] #Liste des joueurs proches de la souris
                for k, v in self.state.players:
                    newValue = self.state.player_state(k,v).position.distance(Vector2D(x_n, y_n))
                    if(newValue <= DISTANCEMAXALASOURIS): #Si le joueur dépasse la distance maximale fixée, on ne le considère pas
                        if(not nearestPlayers): #Si la liste est vide, le premier joueur est le plus proche
                            nearestPlayers.append([(k,v),newValue])
                        else: #La liste sera ordonnée et completée incrémentalement (indice 0 = le plus proche)
                            index = 0
                            isNearest = False
                            while(index<len(nearestPlayers) and not isNearest):
                                if(newValue < nearestPlayers[index][1]):
                                    isNearest = True
                                    nearestPlayers.insert(index,[(k,v),newValue])
                                else:
                                    index+=1
                            if(not isNearest):
                                nearestPlayers.append([(k,v),newValue])
                if(nearestPlayers): #Si au moins un joueur est suffisament proche
                    if(len(nearestPlayers) == 1): #S'il n'y a qu'un joueur proche
                        self.lastPlayersSelectedRecently = [] #Plus besoin de garder en mémoire les joueurs
                        selectedPlayer = nearestPlayers[0][0]
                    else:
                        alreadySelected = True
                        index = 0
                        while alreadySelected and index<len(nearestPlayers): #Sinon on parcours tous les joueurs, on choisit le premier qu'on a jamais vu
                            joueur = nearestPlayers[index][0]
                            if(joueur in self.lastPlayersSelectedRecently):
                                index+=1
                            else:
                                self.lastPlayersSelectedRecently.append(joueur) #On sélectionne ce joueur et on considère qu'il a déjà été vu
                                selectedPlayer = joueur
                                alreadySelected = False
                        if(alreadySelected): #Tous les joueurs proches ont déjà été sélectionnés ! On recommence le parcours des joueurs !
                            self.lastPlayersSelectedRecently = [nearestPlayers[0][0]]
                            selectedPlayer = nearestPlayers[0][0]
                    self.selectedPlayer = [selectedPlayer,self.get_team(selectedPlayer[0]).strategy(selectedPlayer[1]).getCurrentOrder()]
            elif(button == 4 or button == 2):
                nearestTargets = []  # Liste des cibles proches de la souris
                for k, v in self.state.players:
                    newValue = self.state.player_state(k, v).position.distance(Vector2D(x_n, y_n))
                    if (newValue <= DISTANCEMAXALASOURIS):  # Si le joueur dépasse la distance maximale fixée, on ne le considère pas
                        if (not nearestTargets):  # Si la liste est vide, le premier joueur est le plus proche
                            nearestTargets.append([(k, v), newValue])
                        else:  # La liste sera ordonnée et completée incrémentalement (indice 0 = le plus proche)
                            index = 0
                            isNearest = False
                            while (index < len(nearestTargets) and not isNearest):
                                if (newValue < nearestTargets[index][1]):
                                    isNearest = True
                                    nearestTargets.insert(index, [(k, v), newValue])
                                else:
                                    index += 1
                            if (not isNearest):
                                nearestTargets.append([(k, v), newValue])
                otherTargets = [("Balle",self.state.ball.position.distance(Vector2D(x_n, y_n)))]
                otherTargets.append(("BalleProchaine",self.state.ball.position.distance(Vector2D(x_n, y_n))))
                otherTargets.append(("CornerTopLeft",Vector2D(0,GAME_HEIGHT).distance(Vector2D(x_n, y_n))))
                otherTargets.append(("CornerTopRight", Vector2D(GAME_WIDTH,GAME_HEIGHT).distance(Vector2D(x_n, y_n))))
                otherTargets.append(("CornerBottomLeft", Vector2D(0, 0).distance(Vector2D(x_n, y_n))))
                otherTargets.append(("CornerBottomRight", Vector2D(GAME_WIDTH, 0).distance(Vector2D(x_n, y_n))))
                otherTargets.append(("MiddleTop", Vector2D(GAME_WIDTH/2, GAME_HEIGHT).distance(Vector2D(x_n, y_n))))
                otherTargets.append(("MiddleBottom", Vector2D(GAME_WIDTH/2, 0).distance(Vector2D(x_n, y_n))))
                otherTargets.append(("Middle", Vector2D(GAME_WIDTH/2, GAME_HEIGHT/2).distance(Vector2D(x_n, y_n))))
                if(self.selectedPlayer[0][0] == 1):
                    otherTargets.append(("SaCage", Vector2D(0, GAME_HEIGHT/2).distance(Vector2D(x_n, y_n))))
                    otherTargets.append(("CageAdverse", Vector2D(GAME_WIDTH, GAME_HEIGHT/2).distance(Vector2D(x_n, y_n))))
                else:
                    otherTargets.append(("SaCage", Vector2D(GAME_WIDTH, GAME_HEIGHT/2).distance(Vector2D(x_n, y_n))))
                    otherTargets.append(("CageAdverse", Vector2D(0, GAME_HEIGHT/2).distance(Vector2D(x_n, y_n))))

                for target in otherTargets:
                    if (target[1] <= DISTANCEMAXALASOURIS):  # Si la cible dépasse la distance maximale fixée, on ne la considère pas
                        if (not nearestTargets):  # Si la liste est vide, la premiere cible est la plus proche
                            nearestTargets.append([target[0], target[1]])
                        else:  # La liste sera ordonnée et completée incrémentalement (indice 0 = le plus proche)
                            index = 0
                            isNearest = False
                            while (index < len(nearestTargets) and not isNearest):
                                if (target[1] < nearestTargets[index][1]):
                                    isNearest = True
                                    nearestTargets.insert(index, [target[0], target[1]])
                                else:
                                    index += 1
                            if (not isNearest):
                                nearestTargets.append([target[0], target[1]])

                if (nearestTargets):  # Si au moins une cible est suffisament proche
                    if (len(nearestTargets) == 1):  # S'il n'y a qu'un joueur proche
                        self.lastTargetsSelectedRecently = []  # Plus besoin de garder en mémoire les joueurs
                        selectedTarget = nearestTargets[0][0]
                    else:
                        alreadySelected = True
                        index = 0
                        while alreadySelected and index < len(nearestTargets):  # Sinon on parcours tous les joueurs, on choisit le premier qu'on a jamais vu
                            joueur = nearestTargets[index][0]
                            if (joueur in self.lastTargetsSelectedRecently):
                                index += 1
                            else:
                                self.lastTargetsSelectedRecently.append(joueur)  # On sélectionne ce joueur et on considère qu'il a déjà été vu
                                selectedTarget = joueur
                                alreadySelected = False
                        if (alreadySelected):  # Tous les joueurs proches ont déjà été sélectionnés ! On recommence le parcours des joueurs !
                            self.lastTargetsSelectedRecently = [nearestTargets[0][0]]
                            selectedTarget = nearestTargets[0][0]
                    if(button == 4 and not self.orders_hud.currentTarget=="B"):
                        self.selectedTarget = selectedTarget
                    elif(button == 2 or (button == 4 and self.orders_hud.currentTarget=="B")):
                        self.selectedTarget2 = selectedTarget


    def _switch_hud_names(self):
        self._hud_names = not self._hud_names

    def create_drawable_objects(self):
        if not self.state:
            return
        self._sprites = dict()
        self._sprites["ball"] = BallSprite()
        for k, v in self.state.players:
            if not self.get_team(k):
                name_p = '%d %d|' % (k, v)
                #################################
                type="agility"
                ################################
            else:
                name_p = self.get_team(k).player_name(v)
                #################################################
                type  = self.get_team(k).player_type(v)
                ###############################################
            color=TEAM1_COLOR if k == 1 else TEAM2_COLOR
            self._sprites[(k, v)] = PlayerSprite(name_p, color, type)
        if hasattr(self.state,"zones_1"):
            for i,z in enumerate(self.state.zones_1):
                self._sprites[(i,"z1")]=RectSprite(z.l, GREEN_COLOR if self.state.zones_1_bool[i] else RED_COLOR)
        if hasattr(self.state,"zones_2"):
            for i,z in enumerate(self.state.zones_2):
                self._sprites[(i,"z2")]=RectSprite(z.l, GREEN_COLOR if self.state.zones_2_bool[i] else RED2_COLOR)
    def _update_sprites(self):
        team1 = team2 = ongoing = ""
        if not self.state:
            return
        if len(self._sprites) ==0:
            self.create_drawable_objects()
        if self.get_team(1):
            team1 = "%s %s - %s" % (self.get_team(1).name,self.get_team(1).login, self.get_score(1))
        if self.get_team(2):
            team2 = "%s %s - %s" % (self.get_team(2).name, self.get_team(2).login, self.get_score(2))
        ongoing = "Round : %d/%d" % (self.state.step, self.get_max_steps())
        self.hud.set_val(team1=team1, team2=team2, ongoing=ongoing)
        ######################
        #targets = ["Balle","CageAdverse","SaCage","CornerTopLeft","CornerTopRight","CornerBottomLeft","CornerBottomRight","MiddleTop","MiddleBottom","Middle"]
        #for k, v in self.state.players:
        #    name_p = self.get_team(k).player_name(v)
        #    targets.append(name_p)
        currentAction = self.orderToString(self.get_team(self.selectedPlayer[0][0]).strategy(self.selectedPlayer[0][1]).getCurrentOrder())
        if(type(self.selectedTarget) == tuple):
            target = self.playerToName(self.selectedTarget)
        else:
            target = self.selectedTarget
        if (type(self.selectedTarget2) == tuple):
            target2 = self.playerToName(self.selectedTarget2)
        else:
            target2 = self.selectedTarget2
        self.orders_hud.set_val(player=self.playerToName(self.selectedPlayer[0]), ongoing_order=currentAction, target=target, target2 = target2)
        ######################
        for k in self.state.players:
            self._sprites[k].position = self.state.player_state(k[0], k[1]).position
            self._sprites[k].vitesse= self.state.player_state(k[0], k[1]).vitesse
        if hasattr(self.state,"zones_1"):
            for i,z in enumerate(self.state.zones_1):
                self._sprites[(i,"z1")].position=z.position
                self._sprites[(i,"z1")].set_color( GREEN_COLOR if self.state.zones_1_bool[i] else RED_COLOR)
        if hasattr(self.state,"zones_2"):
            for i,z in enumerate(self.state.zones_2):
                self._sprites[(i,"z2")].position=z.position
                self._sprites[(i,"z2")].set_color( GREEN_COLOR if self.state.zones_2_bool[i] else RED2_COLOR)
        self._sprites["ball"].position = self.state.ball.position
        self._sprites["ball"].vitesse = self.state.ball.vitesse

    def reset(self):
        self._state = None
        self._sprites = dict()
        self._background = BackgroundSprite()
        self.hud = Hud()
        self.orders_hud = Orders_hud()
        try:
            self.simu.listeners -= self
        except Exception:
            pass
        self.simu = None

    def draw(self):
        try:
            if self.state:
                self._update_sprites()
                gl.glClear(gl.GL_COLOR_BUFFER_BIT)
                self._background.draw()
                for d in self._sprites.values():
                    d.draw()
                self.hud.draw()
                self.orders_hud.draw()
        except Exception as e:
            time.sleep(0.0001)
            logger.error("%s\n\t%s" %(e, traceback.format_exc()))
            raise e

    def _increase_fps(self):
        self._fps = min(self._fps + FPS_MOD, 200)
    def _decrease_fps(self):
        self._fps = max(self._fps - FPS_MOD, 1)
    def on_draw(self):
        self.draw()

    def on_key_press(self, symbol, modifiers):
        if symbol in self.key_handlers:
            handler = self.key_handlers.get(symbol, lambda w: None)
            handler(self)
            return pyglet.event.EVENT_HANDLED
        k=pyglet.window.key.symbol_string(symbol)
        if modifiers & pyglet.window.key.MOD_SHIFT:
                k=k.capitalize()
        else:
                k=k.lower()
        try:
            self.simu.send_strategy(k)
        except  Exception:
            pass
        return pyglet.event.EVENT_HANDLED

    def on_resize(self, width, height):
        pyglet.window.Window.on_resize(self, width, height)
        self.focus()
        return pyglet.event.EVENT_HANDLED

    def focus(self):
        try:
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            gl.gluOrtho2D(0, settings.GAME_WIDTH + ORDERS_HUD_WIDTH, 0, settings.GAME_HEIGHT + HUD_HEIGHT)
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glLoadIdentity()
        except Exception as e:
            time.sleep(0.0001)
            logger.error("%s\n\t%s"  %(e, traceback.format_exc()))

    def on_close(self):
        pyglet.window.Window.on_close(self)
        return pyglet.event.EVENT_HANDLED

    def exit(self):
        if hasattr(self.simu, "kill"):
            self.simu.kill()
        self.simu.listeners -= self
        pyglet.clock.unschedule(self.update)
        self.close()
        pyg_stop()
        return pyglet.event.EVENT_HANDLED

    def change_state(self, state):
        self._state = state.copy()

    def set(self, simu):
        self.simu = simu
        try:
            self.simu.listeners += self
        except Exception:
            pass
    def show(self,state):
        self._state = state
        self.update()
    def play(self):
        try:
            self.simu.start_thread()
        except Exception as e:
            pass

    def get_state(self):
        try:
            return self._state
        except Exception:
            return None
    def get_team(self, i):
        try:
            return self.simu.get_team(i)
        except Exception:
            return None
    #####################################
    #def get_players_type(self, i):
#        team = self.get_team(i)
        #return team.players_type()

    #####################################
    def get_score(self,i):
        try:
            return self.state.get_score_team(i)
        except Exception:
            return 0

    def get_max_steps(self):
        try:
            return self.max_steps
        except Exception:
            pass
        try:
            return self.state.max_steps
        except Exception:
            pass
        return settings.MAX_GAME_STEPS

    def update_round(self, team1, team2, state):
        self.change_state(state)
        self._wait_next()

    def begin_match(self, team1, team2, state):
        pass

    def begin_round(self, team1, team2, state):
        self.change_state(state)

    def end_round(self, team1, team2, state):
        self.change_state(state)
        self.resetOrderGUI()
        pass

    def end_match(self, team1, team2, state):
        pass


def show_simu(simu):
    gui = SimuGUI(simu)
    pyg_start()

def show_state(state):
    gui = SimuGUI()
    gui.show(state)
    pyg_start()

def pyg_start():
    pyglet.app.run()

def pyg_stop():
    pyglet.app.exit()
