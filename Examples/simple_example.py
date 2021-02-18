from soccersimulator import SoccerTeam, Simulation, show_simu
from ProfIA import FonceurStrategy,FonceurTestStrategy,DefenseurStrategy,get_team, RandomStrategy


## Creation d'une equipe
pyteam = SoccerTeam(name="RealTeam")

#pyteam.add("Mouna",DefenseurStrategy(), "strength")
pyteam.add("Neila",FonceurStrategy(), "strength")
#pyteam.add("Emmanuelle",FonceurStrategy(),"strength")

team2 = SoccerTeam(name="SubstantialTeam")
#team2.add("Guillaume",DefenseurStrategy(),"strength")
#team2.add("Guillaume2",DefenseurStrategy(),"speed")
team2.add("Hannah",FonceurStrategy(),"strength")
team2.add("Hannah",FonceurStrategy(),"agility")



#Creation d'une partie
simu = Simulation(pyteam,team2)
#Jouer et afficher la partie
show_simu(simu)
