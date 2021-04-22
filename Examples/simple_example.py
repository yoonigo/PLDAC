from soccersimulator import SoccerTeam, Simulation, show_simu
from ProfIA import FonceurStrategy,FonceurStrategyWithOrder,FonceurTestStrategy,DefenseurStrategy,get_team, RandomStrategy, EntraineurSVM, EntraineurRandom, EntraineurKNN, EntraineurDistribueAbs, EntraineurDistribueRel


## Creation d'une equipe
#pyteam = SoccerTeam(name="RealTeam")
pyteam = SoccerTeam(name="RealTeam", entraineur=EntraineurDistribueRel(True))
#pyteam = SoccerTeam(name="RealTeam", knn=True)

#pyteam.add("Mouna",DefenseurStrategy(), "strength")
pyteam.add("Mouna",FonceurStrategyWithOrder(), "speed")
pyteam.add("Neila",FonceurStrategyWithOrder(), "strength")
pyteam.add("Felix",FonceurStrategyWithOrder(), "strength")
pyteam.add("Manu",FonceurStrategyWithOrder(),"agility")

#team2 = SoccerTeam(name="SubstantialTeam")
#team2 = SoccerTeam(name="SubstantialTeam", entraineur=EntraineurRandom(["tire vers","se deplace vers","dribble vers"],["Balle","CornerTopLeft","CornerTopRight","CornerBottomLeft","CornerBottomRight","MiddleTop","Middle","MiddleBottom"]))
team2 = SoccerTeam(name="SubstantialTeam", entraineur=EntraineurDistribueRel(True))

#team2.add("Guillaume",DefenseurStrategy(),"strength")
#team2.add("Guillaume2",DefenseurStrategy(),"speed")

team2.add("Hannah",FonceurStrategyWithOrder(),"speed")
team2.add("Vincent",FonceurStrategyWithOrder(), "strength")
team2.add("Nicolas",FonceurStrategyWithOrder(), "strength")
team2.add("Guillaume",FonceurStrategyWithOrder(),"agility")




#Creation d'une partie
simu = Simulation(pyteam,team2,getMoreData=False)
#Jouer et afficher la partie
show_simu(simu)
