from soccersimulator import SoccerTeam, Simulation, show_simu,KeyboardStrategy,DTreeStrategy,load_jsonz,dump_jsonz
from soccersimulator import apprend_arbre, build_apprentissage, genere_dot
from ProfIA import FonceurStrategy,DefenseurStrategy,SuperState
import sklearn
import numpy as np
import pickle

assert sklearn.__version__ >= "0.18.1","Updater sklearn !! (pip install -U sklearn --user )"



### Transformation d'un etat en features : state,idt,idp -> R^d

def my_get_features(state,idt,idp):
    """ extraction du vecteur de features d'un etat, ici distance a la balle, distance au but, distance balle but """
    state = SuperState(state,idt,idp)
    f1 = state.distance(state.ball_p)
    f2 = state.distance(state.my_goal)
    f3 = state.ball_p.distance(state.my_goal)
    return [f1,f2,f3]

my_get_features.names = ["dball","dbut","dballbut"]


def entrainer(fname):
    #Creation d'une partie
    kb_strat = KeyboardStrategy()
    kb_strat.add("a",FonceurStrategy())
    kb_strat.add("z",DefenseurStrategy())
    
    team1 = SoccerTeam(name="Contol Team")
    team2 = SoccerTeam(name="Sparing")
    team1.add("ControlPlayer",kb_strat)
    team2.add("Player",FonceurStrategy()) 
    simu = Simulation(team1,team2)
    #Jouer, afficher et controler la partie
    show_simu(simu)
    print("Nombre d'exemples : "+str(len(kb_strat.states)))
    # Sauvegarde des etats dans un fichier
    dump_jsonz(kb_strat.states,fname)

def apprendre(exemples, get_features,fname=None):
    #genere l'ensemble d'apprentissage
    data_train, data_labels = build_apprentissage(exemples,get_features)
    ## Apprentissage de l'arbre
    dt = apprend_arbre(data_train,data_labels,depth=10,feature_names=get_features.names)
    ##Sauvegarde de l'arbre
    if fname is not None:
        with open(fname,"wb") as f:
            pickle.dump(dt,f)
    return dt

if __name__=="__main__":

    entrainer("test_kb_strat.jz")

    dic_strategy = {FonceurStrategy().name:FonceurStrategy(),DefenseurStrategy().name:DefenseurStrategy()}

    states_tuple = load_jsonz("test_kb_strat.jz")
    apprendre(states_tuple,my_get_features,"tree_test.pkl")
    with open("tree_test.pkl","rb") as f:
        dt = pickle.load(f)
    # Visualisation de l'arbre
    genere_dot(dt,"test_arbre.dot")
    #Utilisation de l'arbre : arbre de decision, dico strategy, fonction de transformation etat->variables
    treeStrat1 = DTreeStrategy(dt,dic_strategy,my_get_features)
    treeteam = SoccerTeam("Arbre Team")
    team2 = SoccerTeam(name="Sparing")
    treeteam.add("Joueur 1",treeStrat1)
    treeteam.add("Joueur 2",treeStrat1)
    team2.add("Joueur 1", FonceurStrategy())
    team2.add("Joueur 2",DefenseurStrategy())
    simu = Simulation(treeteam,team2)
    show_simu(simu)

