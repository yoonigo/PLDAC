from .strategies import DefenseurStrategy,FonceurStrategy,RandomStrategy, FonceurTestStrategy
from .optimization import ParamSearch
from soccersimulator import SoccerTeam
from .tools import SuperState

def get_team(nb_players):
	myteam = SoccerTeam(name="ProfTeam")
	if nb_players == 1:
		myteam.add("Joueur " ,FonceurStrategy())
	if nb_players == 2:
		myteam.add("Joueur 1", FonceurStrategy())
		myteam.add("Joueur 2", DefenseurStrategy())
	if nb_players == 4:
		myteam.add("Joueur 1",RandomStrategy())
		myteam.add("Joueur 2",RandomStrategy())
		myteam.add("Joueur 3",RandomStrategy())
		myteam.add("Joueur 4",RandomStrategy())
	return myteam	

def get_team_challenge(num):
	myteam = SoccerTeam(name="MaTeamChallenge")
	if num == 1:
		myteam.add("Joueur Chal "+str(num),FonceurStrategy())
	return myteam
