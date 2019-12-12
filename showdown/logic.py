
from .teams import *
#from teams import *
from random import randint
import re

def determince_speed_tie(pokemon1, pokemon2):
    if int(pokemon1.get_speed()) >= int(pokemon2.get_speed()):
        return True
    return False

#retourne la table des types
def type_table():
    weakness_lines=[]
    weakness_table=[]
    weakness_file = open("./data/pokemon_type.txt",'r')
    #weakness_file = open("../data/pokemon_type.txt",'r')
    
    for weakness_line in weakness_file:
        if (not('fairy,1' in weakness_line)):
            # remove \n when not last line
            weakness_lines+=[weakness_line[0:len(weakness_line)-1]]
        else:
            weakness_lines+=[weakness_line]
    weakness_file.close()
    for i in weakness_lines:
        weakness_table+=[i.split(',')]
    return (weakness_table)

#retourne le coefficient multiplicateur CM entre l'attaque et lle pokémon qui subbit l'attaque 
def type_multipplicator(attack,pokemon):
    table_type=type_table()
    type_pokemon=Pokemon.get_types(pokemon)
    type_attack=Move.get_move_type(attack)
    attack_type_indice=0
    for indice in range(0,len(table_type)):
        if(type_attack==table_type[indice][0]):
            attack_type_indice=indice
    CM=1
    for pokemon_type in type_pokemon:
        pokemon_type_indice=0
        for indice in range(0,len(table_type)):
            if(pokemon_type==table_type[0][indice]):
                pokemon_type_indice=indice
        CM=CM*float(table_type[attack_type_indice][pokemon_type_indice])
    return CM

def damage_calcul(pokemon1,pokemon2,attack):
    Att=0
    Def=1
    Stab=1
    Pui=0
    damage=0
    current_hp=int(Pokemon.get_current_hp(pokemon2))
    # TODO temporary fix to remove status from hp bar
    max_hp_statusless = re.findall(r"[0-9]+",Pokemon.get_max_hp(pokemon2))
    max_hp=int(max_hp_statusless[0])
    current_hp=max_hp*(current_hp/100)

    if (Move.get_category(attack) =='special'):
        Att=int(Pokemon.get_special_attack(pokemon1))
        Def=int(Pokemon.get_special_defense(pokemon2))
    if (Move.get_category(attack) =='physical'):
        Att=int(Pokemon.get_attack(pokemon1))
        Def=int(Pokemon.get_defense(pokemon2))
    pokemon_type=Pokemon.get_types(pokemon1)
    for type_pokemon in pokemon_type:
        if (type_pokemon==Move.get_move_type(attack)):
            Stab=1.5
    lvl=int(Pokemon.get_level(pokemon1))
    if (not(Move.get_category(attack)=='status')) and Move.get_power(attack) is not None:
        Pui=int(Move.get_power(attack))
        CM=randint(100,100)/100*Stab*type_multipplicator(attack,pokemon2)
        damage=int(int((((lvl*0.4+2)*Att*Pui)/(Def*50))+2)*CM)
    percentage_hp=int((damage/current_hp)*100)
    return percentage_hp

#fonction qui choisi quelle move du pokémon il est préférable de choisir pour l'attaque d'un pokemon 1 sur un pokemon 2
def select_move(pokemon1,pokemon2):
    moves=Pokemon.get_possible_moves(pokemon1)
    moveset = [None,None,None,None]
    for move_index,move in enumerate(moves):
        moveset[move_index] = move
    move_selected=None
    max_damage=0
    if moveset[0] is not None and (damage_calcul(pokemon1,pokemon2,moveset[0])>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,moveset[0])
        move_selected=moveset[0].get_name()
    if moveset[1] is not None and (damage_calcul(pokemon1,pokemon2,moveset[1])>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,moveset[1])
        move_selected=moveset[1].get_name()
    if moveset[2] is not None and (damage_calcul(pokemon1,pokemon2,moveset[2])>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,moveset[2])
        move_selected=moveset[2].get_name()
    if moveset[3] is not None and (damage_calcul(pokemon1,pokemon2,moveset[3])>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,moveset[3])
        move_selected=moveset[3].get_name()
    return move_selected,max_damage

def assert_opponent_pokemon_threat(pokemon1,pokemon2):
    pokemon_type=Pokemon.get_types(pokemon2)
    max_damage=0
    for type_pokemon in pokemon_type:
        attackphy=Move(type_pokemon+'phy',None,None,False,10,None)
        attackphy.update_smogon_data(type_pokemon,'physical','100','100','stabed attack')
        attackspe=Move(type_pokemon+'phy',None,None,False,10,None)
        attackspe.update_smogon_data(type_pokemon,'special','100','100','stabed attack')
        phy_damage=damage_calcul(pokemon2,pokemon1,attackphy)
        spe_damage=damage_calcul(pokemon2,pokemon1,attackspe)
        if (max_damage<phy_damage):
            max_damage=phy_damage
        if (max_damage<spe_damage):
            max_damage=spe_damage
    return max_damage
