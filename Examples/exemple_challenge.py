from soccersimulator import ChallengeFonceurButeur, SoccerTeam,show_simu
from ProfIA import get_team_challenge

team = get_team_challenge(1)

challenge = ChallengeFonceurButeur(team,max_but=20)
show_simu(challenge)
print("temps moyen : ",challenge.stats_score, "\nliste des temps",challenge.resultats)