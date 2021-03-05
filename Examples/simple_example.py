from soccersimulator import SoccerTeam, Simulation, show_simu
from ProfIA import FonceurStrategy,FonceurStrategyWithOrder,FonceurTestStrategy,DefenseurStrategy,get_team, RandomStrategy


## Creation d'une equipe
pyteam = SoccerTeam(name="RealTeam")

#pyteam.add("Mouna",DefenseurStrategy(), "strength")
pyteam.add("Mouna",FonceurStrategyWithOrder(), "speed")
pyteam.add("Neila",FonceurStrategyWithOrder(), "strength")
pyteam.add("Felix",FonceurStrategyWithOrder(), "strength")
pyteam.add("Emmanuelle",FonceurStrategyWithOrder(),"agility")
#pyteam.add("Emmanuelle",FonceurStrategy(),"strength")

team2 = SoccerTeam(name="SubstantialTeam")
#team2.add("Guillaume",DefenseurStrategy(),"strength")
#team2.add("Guillaume2",DefenseurStrategy(),"speed")
team2.add("Vincent",FonceurStrategyWithOrder(), "strength")
team2.add("Nicolas",FonceurStrategyWithOrder(), "strength")
team2.add("Guillaume",FonceurStrategyWithOrder(),"agility")
team2.add("Hannah",FonceurStrategyWithOrder(),"speed")



#Creation d'une partie
simu = Simulation(pyteam,team2)
#Jouer et afficher la partie
show_simu(simu)
