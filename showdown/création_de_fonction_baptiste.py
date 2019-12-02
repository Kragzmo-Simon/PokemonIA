# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 02:38:32 2019

@author: admin
"""


from enum import Enum
from random import randint

class Team:
    """
    A team is composed of 6 pokemons and a player
    """
    def __init__(self, player):
        self.player = player # either p1 or p2
        #self.pokemons = [None] * 6
        self.pokemons = []
        self.buffs = Side_Buffs()

        # This index tracks the next index of self.pokemons that should be added
        # If it is equal to 6, then the team is full
        #self.pokemon_index_to_add = 0

    def raise_stat(self, stat_name, levels):
        print("Applying Buff : ", stat_name, " +", levels," (", self.player, ")")
        self.buffs.raise_stat(stat_name, levels)

    def lower_stat(self, stat_name, levels):
        print("Applying Debuff : ", stat_name, " -", levels," (", self.player, ")")
        self.buffs.lower_stat(stat_name, levels)

    def reset_buffs(self):
        self.buffs.reset()

    def set_all_pokemons_to_inactive(self):
        for pokemon in self.pokemons:
            pokemon.make_inactive()

    def make_pokemon_active(self, pokemon_name):
        for pokemon in self.pokemons:
            if pokemon.has_name(pokemon_name):
                pokemon.make_active()

    def get_pokemon(self, pokemon_name):
        for pokemon in self.pokemons:
            if pokemon.has_name(pokemon_name):
                return pokemon

    def add_pokemon(self, pokemon):
        if len(self.pokemons) <= 5:
            self.pokemons.append(pokemon)
        """
        if self.pokemon_index_to_add < 6:
            self.pokemons[self.pokemon_index_to_add] = pokemon
            self.pokemon_index_to_add += 1
        """

    def self_print(self):
        for pokemon in self.pokemons:
            if pokemon is not None:
                pokemon.self_print()

    def print_active_pokemon(self):
        for pokemon in self.pokemons:
            if pokemon.is_active():
                pokemon.self_print()

    def get_player(self):
        return self.player

    def get_pokemon_names(self):
        pokemon_names = []
        for pokemon in self.pokemons:
            pokemon_names.append(pokemon.get_name())
        return pokemon_names

    def get_possible_pokemon_switch(self):
        possible_switch_names = []
        for pokemon in self.pokemons:
            if (pokemon.get_current_hp() != 0) and (not pokemon.is_active()):
                possible_switch_names.append(pokemon.get_name())
        return possible_switch_names

    def get_active_pokemon_possible_moves(self):
        for pokemon in self.pokemons:
            if pokemon is not None and pokemon.is_active():
                return pokemon.get_possible_moves()

    def check_smogon_data_update(self):
        # checks if all the smogon data has been updated on pokemons and moves
        # returns False if data has not been updated and True if it has been updated
        for pokemon in self.pokemons:
            if pokemon is not None:
                #print("Checking : ", pokemon.get_name())
                smogon_update, moves_or_pok_to_resend = pokemon.has_been_updated_with_smogon()
                if not smogon_update:
                    return False, moves_or_pok_to_resend
                #print("Pokemon correctly updated : ", pokemon.get_name())
            else:
                print("A pokemon is NONE")
                return False, []
        print("The team was correctly updated")
        return True, []

    def update_moves_with_smogon(self, smogon_move):
        for pokemon in self.pokemons:
            pokemon.update_move_data_with_smogon(smogon_move)

    def update_pokemons_with_smogon(self, smogon_pokemon):
        for pokemon in self.pokemons:
            if smogon_pokemon.has_name(pokemon.get_name()):
                #print("Updating this pokemon : ", pokemon.get_name())
                types_collection = smogon_pokemon.get_types()
                abilities_collection = smogon_pokemon.get_abilities_collection()
                base_hp = smogon_pokemon.get_base_hp()
                base_attack = smogon_pokemon.get_base_attack()
                base_defense = smogon_pokemon.get_base_defense()
                base_special_attack = smogon_pokemon.get_base_special_attack()
                base_special_defense = smogon_pokemon.get_base_special_defense()
                base_speed = smogon_pokemon.get_base_speed()
 
                pokemon.update_smogon_data(types_collection, 
                                        abilities_collection,
                                        base_hp,
                                        base_attack,
                                        base_defense,
                                        base_special_attack,
                                        base_special_defense,
                                        base_speed)

class Pokemon:

    def __init__(self,  name,
                        smogon_id,
                        level,
                        gender,
                        current_hp,
                        max_hp,
                        attack,
                        defense,
                        special_attack,
                        special_defense,
                        speed,
                        move1,
                        move2,
                        move3,
                        move4,
                        ability,
                        base_ability,
                        item,
                        active):
        # Name
        self.name = name

        # Id of smogon
        if smogon_id is not None:
            self.smogon_id = int(smogon_id) + 1
        else:
            self.smogon_id = None

        # Level
        self.level = level

        # Gender
        self.gender = gender

        # Stats
        self.current_hp = current_hp
        self.max_hp = max_hp
        self.attack = attack
        self.defense = defense
        self.special_attack = special_attack
        self.special_defense = special_defense
        self.speed = speed

        # Base stats
        self.base_hp = None
        self.base_attack = None
        self.base_defense = None
        self.base_special_attack = None
        self.base_special_defense = None
        self.base_speed = None

        # item
        self.item = item

        # ability
        self.ability = ability
        self.base_ability = base_ability
        self.abilities_collection = []

        # moves
        self.moves_names = [move1,move2,move3,move4]
        self.complete_moves = []

        # active if the pokemon that is currently fighting
        self.active = active

        # type
        self.types_collection = []

        # boolean to check if the smogon data has been retrieved and used
        self.smogon_data_has_been_retrieved = False

        # stats modifiers
        # self.crit_level = 0
        # condition and statuses

        # Status and condition
        #self.status = 0
        #self.condition = 0

    def update_smogon_data(self, 
                            types_collection, 
                            abilities_collection,
                            base_hp,
                            base_attack,
                            base_defense,
                            base_special_attack,
                            base_special_defense,
                            base_speed):
        self.types_collection = types_collection
        self.abilities_collection = abilities_collection
        self.base_hp = base_hp
        self.base_attack = base_attack
        self.base_defense = base_defense
        self.base_special_attack = base_special_attack
        self.base_special_defense = base_special_defense
        self.base_speed = base_speed
        self.smogon_data_has_been_retrieved = True

    def update_moves(self, moves):
        self.complete_moves = moves

    def has_name(self, pokemon_name):
        if self.name.lower() == pokemon_name.lower():
            return True
        else:
            return False

    def make_active(self):
        print("Pokemon ", self.name, " is now active")
        self.active = True

    def make_inactive(self):
        print("Pokemon ", self.name, " is now inactive")
        self.active = False

    def is_active(self):
        return self.active

    def get_name(self):
        return self.name

    def get_types(self):
        return self.types_collection

    def get_abilities_collection(self):
        return self.abilities_collection

    def get_base_hp(self):
        return self.base_hp
    
    def get_max_hp(self):
        return self.max_hp
    
    def set_max_hp(self,new_max_hp):
        self.max_hp=str(new_max_hp)

    def get_base_attack(self):
        return self.base_attack
        
    def get_base_defense(self):
        return self.base_defense

    def get_base_special_attack(self):
        return self.base_special_attack

    def get_base_special_defense(self):
        return self.base_special_defense

    def get_base_speed(self):
        return self.base_speed

    def get_move(self, move_name):
        for move in self.complete_moves:
            if move.has_name(move_name):
                return move
        return None
     
    def get_level(self):
        return self.level
    
    def get_current_hp(self):
        return self.current_hp
    
    def get_attack(self):
        return self.attack
    
    def set_attack(self,new_attack):
        self.attack=new_attack
    
    def get_defense(self):
        return self.defense
    
    def set_defense(self,new_defense):
        self.defense=new_defense

    def get_special_attack(self):
        return self.special_attack
        
    def set_special_attack(self,new_special_attack):
        self.special_attack=new_special_attack
        
    def get_special_defense(self):
        return self.special_defense
    
    def set_special_defense(self,new_special_defense):
        self.special_defense=new_special_defense
    
    def get_speed(self):
        return self.speed
    
    def set_special_speed(self,new_special_speed):
        self.speed=new_special_speed
    

    def has_been_updated_with_smogon(self):
        # check that the pokemon moves have been loaded
        if len(self.complete_moves) != len(self.moves_names):
            print("Moveset not yet fully loaded (", self.name,")")

            # get the moves that have not been updated correctly to send the data commands
            #self.self_print()

            # moves the current pokemon actually knows
            known_moves = []
            for move in self.complete_moves:
                known_moves.append(move.get_name())

            # compare with the moves the pokemon is supposed to know
            moves_names_to_resend = []
            for move_name in self.moves_names:
                if move_name not in known_moves:
                    print("\nMove ", move_name, " not known")
                    print("known moves : ", known_moves)
                    print("supposedly known moves : ", self.moves_names, "\n")
                    moves_names_to_resend.append(move_name)
            return False, moves_names_to_resend

        # check if each one of the moves has not been updated
        for move in self.complete_moves:
            #print("Checking ", move.get_name())
            if move is not None and not move.has_been_updated_with_smogon():
                print("Move has not been updated : ", move.get_name())
                return False, [move.get_name()]
            #else:
            #    print("Move correctly updated : ", move.get_name())
        
        # check if the pokemon has been updated
        if not self.smogon_data_has_been_retrieved:
            #print("Pokemon has not been updated : ", self.name)
            return False, [self.name]
        return True, []

    def get_possible_moves(self):
        # moves that are not disabled and that still have remaining pp
        possible_moves = []
        for move in self.complete_moves:
            if move.is_castable():
                possible_moves.append(move)
        return possible_moves

    def update_move_data_with_smogon(self, smogon_move):
        for index,move_name in enumerate(self.moves_names):
            if smogon_move.has_name(move_name):
                smogon_move_type = smogon_move.get_move_type()
                smogon_move_category = smogon_move.get_category()
                smogon_move_power = smogon_move.get_power()
                smogon_move_accuracy = smogon_move.get_accuracy()
                smogon_move_description = smogon_move.get_description()

                # if the pokemon is active, its moves should already be defined and should be
                # updated. if the pokemon is not active, its moves are not defined and should
                # be created
                pok_is_using_trapping_move = False
                if self.active:
                    # if the pokemon is active, its moves are already instanciated
                    pok_move = self.get_move(move_name)
                    if pok_move is not None:
                        pok_move.update_smogon_data(smogon_move_type, 
                                                    smogon_move_category, 
                                                    smogon_move_power, 
                                                    smogon_move_accuracy, 
                                                    smogon_move_description)
                    else:
                        # pokemon active just fainted
                        # or is using outrage (other moves have not been loaded)
                        print("ERREUR MOVE NONE : ", move_name)
                        pok_is_using_trapping_move = True
                if (not self.active) or pok_is_using_trapping_move:
                    # if the pokemon is not active
                    new_move = Move(move_name)
                    new_move.update_smogon_data(smogon_move_type, 
                                                smogon_move_category, 
                                                smogon_move_power, 
                                                smogon_move_accuracy, 
                                                smogon_move_description)
                    
                    # add the move in the pokemon moveset
                    new_move_set = self.complete_moves
                    new_move_set.append(new_move)
                    self.update_moves(new_move_set)

                #print("Updating ", move_name, " (", self.name,")")

    def self_print(self):
        print("\n", self.smogon_id, " - ", self.name, " (level", self.level,",", self.gender,") - active : ", self.active)
        print("    hps - ", self.current_hp, "/", self.max_hp)
        print("    stats - ", self.attack, "/", self.defense, "/", self.special_attack, 
                "/", self.special_defense, "/", self.speed)
        print("    moves - ", self.moves_names[0], "/", self.moves_names[1], "/", self.moves_names[2], "/", self.moves_names[3])
        print("    abilities - ", self.ability, "(originally ", self.base_ability, ")")
        print("    item - ", self.item)

        if len(self.types_collection) == 2:
            print("    types - ", self.types_collection[0], " / ", self.types_collection[1])
        if len(self.types_collection) == 1:
            print("    type - ", self.types_collection[0])
        
        abilities_string = ""
        for ability in self.abilities_collection:
            abilities_string += (ability + ", ")
        print("    possible abilities : ", abilities_string)

        print("    moves details : ")
        for move in self.complete_moves:
            if move is not None:
                move.self_print()

class Move:

    def __init__(self,  name,
                        smogon_id = None,
                        target = None,
                        disabled = None,
                        current_pp = None,
                        max_pp = None):
        self.name = name

        # this id specifies the place of the pokemon in the team
        self.smogon_id = smogon_id
        
        # the target specifies "self", "allAdjacentFoes" or "Normal"
        self.target = target
        self.disabled = disabled
        self.current_pp = current_pp
        self.max_pp = max_pp

        # Information below will be updated when the data is retrieved from smogon
        self.types = None
        self.power = 9000
        self.accuracy = 9000
        self.description = None
        self.category = None

        # boolean to check if the smogon data has been retrieved and used
        self.smogon_data_has_been_retrieved = False

        # self.gigamax = mettre toutes les infos du maxmove directement dans le move plutot que
        # de creer un second move

    def update_smogon_data(self, move_type, category, power, accuracy, description):
        self.types = move_type
        self.power = power
        self.accuracy = accuracy
        self.description = description
        self.category = category
        self.smogon_data_has_been_retrieved = True

    def is_castable(self):
        if not self.disabled and int(self.current_pp) > 0:
            return True
        else:
            return False

    def has_name(self, move_name):
        if self.name == move_name:
            return True
        else:
            return False

    def get_name(self):
        return self.name

    def get_smogon_id(self):
        return self.smogon_id

    def get_move_type(self):
        return self.types

    def get_category(self):
        return self.category

    def get_power(self):
        return self.power

    def get_accuracy(self):
        return self.accuracy

    def get_description(self):
        return  self.description

    def has_been_updated_with_smogon(self):
        return self.smogon_data_has_been_retrieved

    def self_print(self):
        print("\n", self.name, " (id : ", self.smogon_id, ", target : ", self.target, ", disabled : ", self.disabled,")")
        print("    pp : ", self.current_pp, "/", self.max_pp)
        print("    types - ", self.types, " (", self.category,")")
        print("    power - ", self.power," / accuracy - ", self.accuracy)

class Side_Buffs:
    def __init__(self):
        self.attack = 0
        self.defense = 0
        self.special_attack = 0
        self.special_defense = 0
        self.speed = 0

    def raise_stat(self, stat_name, levels):
        if stat_name == "atk":
            self.attack += int(levels)
        if stat_name == "def":
            self.defense += int(levels)
        if stat_name == "spa":
            self.special_attack += int(levels)
        if stat_name == "spd":
            self.special_defense += int(levels)
        if stat_name == "spe":
            self.speed += int(levels)

    def lower_stat(self, stat_name, levels):
        if stat_name == "atk":
            self.attack -= int(levels)
        if stat_name == "def":
            self.defense -= int(levels)
        if stat_name == "spa":
            self.special_attack -= int(levels)
        if stat_name == "spd":
            self.special_defense -= int(levels)
        if stat_name == "spe":
            self.speed -= int(levels)

    def reset(self):
        self.attack = 0
        self.defense = 0
        self.special_attack = 0
        self.special_defense = 0
        self.speed = 0
    
    def self_print(self):
        print("\natk : ", self.attack)
        print("def : ", self.defense)
        print("spa : ", self.special_attack)
        print("spd : ", self.special_defense)
        print("spe : ", self.speed, "\n")

class Condition(Enum):
    """
    Special Status that has no display element in the game (such as love and confusion).
    """
    LOVE = 0
    CONFUSION = 1

class Status(Enum):
    """
    Status of the pokemon (appears in the game with a small rectangle beside the HP bar).
    """
    POISON = 0
    STRONG_POISON = 1
    SLEEP = 2
    BURN = 3
    PARALYSIS = 4
    FREEZE = 5


class Move:

    def __init__(self,  name,
                        smogon_id = None,
                        target = None,
                        disabled = None,
                        current_pp = None,
                        max_pp = None):
        self.name = name

        # this id specifies the place of the pokemon in the team
        self.smogon_id = smogon_id
        
        # the target specifies "self", "allAdjacentFoes" or "Normal"
        self.target = target
        self.disabled = disabled
        self.current_pp = current_pp
        self.max_pp = max_pp

        # Information below will be updated when the data is retrieved from smogon
        self.types = None
        self.power = 9000
        self.accuracy = 9000
        self.description = None
        self.category = None

        # boolean to check if the smogon data has been retrieved and used
        self.smogon_data_has_been_retrieved = False

        # self.gigamax = mettre toutes les infos du maxmove directement dans le move plutot que
        # de creer un second move

    def update_smogon_data(self, move_type, category, power, accuracy, description):
        self.types = move_type
        self.power = power
        self.accuracy = accuracy
        self.description = description
        self.category = category
        self.smogon_data_has_been_retrieved = True

    def is_castable(self):
        if not self.disabled and int(self.current_pp) > 0:
            return True
        else:
            return False

    def has_name(self, move_name):
        if self.name == move_name:
            return True
        else:
            return False

    def get_name(self):
        return self.name

    def get_smogon_id(self):
        return self.smogon_id

    def get_move_type(self):
        return self.types

    def get_category(self):
        return self.category

    def get_power(self):
        return self.power

    def get_accuracy(self):
        return self.accuracy

    def get_description(self):
        return  self.description

    def has_been_updated_with_smogon(self):
        return self.smogon_data_has_been_retrieved

    def self_print(self):
        print("\n", self.name, " (id : ", self.smogon_id, ", target : ", self.target, ", disabled : ", self.disabled,")")
        print("    pp : ", self.current_pp, "/", self.max_pp)
        print("    types - ", self.types, " (", self.category,")")
        print("    power - ", self.power," / accuracy - ", self.accuracy)

class Condition(Enum):
    """
    Special Status that has no display element in the game (such as love and confusion).
    """
    LOVE = 0
    CONFUSION = 1

class Status(Enum):
    """
    Status of the pokemon (appears in the game with a small rectangle beside the HP bar).
    """
    POISON = 0
    STRONG_POISON = 1
    SLEEP = 2
    BURN = 3
    PARALYSIS = 4
    FREEZE = 5



new_attack=Move('Flamethrower',None,None,False,10,None)
new_attack.update_smogon_data('Fire','Special','90','100','The target is scorched with an intense blast of fire. This may also leave the target with a burn. ')
print(Move.get_name(new_attack))
new_attack2=Move('Earthquake',None,None,False,10,None)
new_attack2.update_smogon_data('Ground','Physical','100','100','Damage doubles if the target is using Dig. Z-Move Base Power: 180')
print(Move.get_name(new_attack))
new_attack3=Move('Dragon Claw',None,None,False,10,None)
new_attack3.update_smogon_data('Dragon','Physical','80','100','No additional effect. Z-Move Base Power: 160')
print(Move.get_name(new_attack))
new_attack4=Move('Flare Blitz',None,None,False,10,None)
new_attack4.update_smogon_data('Fire','Physical','120','100','Has a 10% chance to burn the target. If the target lost HP, the user takes recoil damage equal to 33% the HP lost by the target, rounded half up, but not less than 1 HP. Z-Move Base Power: 190')
print(Move.get_name(new_attack))

new_pokemon=Pokemon('Charizard','6','100','male','360','360','293','280','348','295','328',new_attack,new_attack2,new_attack3,new_attack4,'Solar Power','Jolly','Charizardite X','active')
new_pokemon.update_smogon_data(['Fire','FLying'],['Blaze','Solar Power'],'78','84','79','109','85','100')
print(Move.is_castable(new_attack))

new_pokemon2=Pokemon('Venusaur','3','100','male','364','364','263','365','299','299','259','ddd','aaa','bbb','ccc','Chlorophyll','Bold','Venusaurite','active')
new_pokemon2.update_smogon_data(['Grass','Poison'],['Chlorophyll','Overgrow'],'80','82','83','100','100','80')

#retourne la table des types
def type_table():
    tab=[]
    tab2=[]
    fichier = open("E:/admin/Desktop/projetia/PokemonIA/data/pokemon_type.txt",'r')
    
    for ligne in fichier:
        if (not('Fairy,1' in ligne)):
            tab+=[ligne[0:len(ligne)-1]]
        else:
            tab+=[ligne]
    fichier.close()
    for i in tab:
        tab2+=[i.split(',')]
    return (tab2)

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
            

#calcul les dégats de l'attaque faite par le pokémon 1 sur le pokémon 2
def damage_calcul(pokemon1,pokemon2,attack):
    Att=0
    Def=0
    Stab=1
    if (Move.get_category(attack) =='Special'):
        Att=int(Pokemon.get_special_attack(pokemon1))
        Def=int(Pokemon.get_special_defense(pokemon2))
    if (Move.get_category(attack) =='Physical'):
        Att=int(Pokemon.get_attack(pokemon1))
        Def=int(Pokemon.get_defense(pokemon2))
    pokemon_type=Pokemon.get_types(pokemon1)
    for type_pokemon in pokemon_type:
        if (type_pokemon==Move.get_move_type(attack)):
            Stab=1.5
    lvl=int(Pokemon.get_level(pokemon1))
    Pui=int(Move.get_power(attack))
    CM=randint(100,100)/100*Stab*type_multipplicator(attack,pokemon2)
    print(CM)
    damage=int(int((((lvl*0.4+2)*Att*Pui)/(Def*50))+2)*CM)
    return damage


#fonction qui choisi quelle move du pokémon il est préférable de choisir pour l'attaque d'un pokemon 1 sur un pokemon 2
def select_move(pokemon1,pokemon2,move1,move2,move3,move4):
    moves=Pokemon.get_possible_moves(pokemon1)
    print("les moves sont")
    print(moves)
    move_selected="aucune attaque n'est sélectionné"
    max_damage=0
    print(damage_calcul(pokemon1,pokemon2,move1))
    if(damage_calcul(pokemon1,pokemon2,move1)>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,move1)
        move_selected=move1.get_name()
    if(damage_calcul(pokemon1,pokemon2,move2)>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,move2)
        move_selected=move2.get_name()
    if(damage_calcul(pokemon1,pokemon2,move3)>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,move3)
        move_selected=move3.get_name()
    if(damage_calcul(pokemon1,pokemon2,move4)>max_damage):
        max_damage=damage_calcul(pokemon1,pokemon2,move4)
        move_selected=move4.get_name()
    return move_selected,max_damage

select_move(new_pokemon,new_pokemon2,new_attack,new_attack2,new_attack3,new_attack4)


new_pokemon3=Pokemon('Venusaur','3',"82",'male','364','364','263','265','299','299','259','ddd','aaa','bbb','ccc','Chlorophyll','Bold','Venusaurite','active')
new_pokemon3.update_smogon_data(['Grass','Poison'],['Chlorophyll','Overgrow'],'80','82','83','100','100','80')

def set_stats_ennemi_pokemon(pokemon):
    iv=31
    hp=int(Pokemon.get_base_hp(pokemon))
    attack=int(Pokemon.get_base_attack(pokemon))
    defense=int(Pokemon.get_base_defense(pokemon))
    special_attack=int(Pokemon.get_base_special_attack(pokemon))
    special_defense=int(Pokemon.get_base_special_defense(pokemon))
    spd=int(Pokemon.get_base_speed(pokemon))
    lvl=int(Pokemon.get_level(pokemon))
    new_hp=int(((2*hp+iv)*lvl)/100+lvl+10)+17
    new_attack=int(((2*attack+iv)*lvl)/100+5)+17
    new_defense=int(((2*defense+iv)*lvl)/100+5)+17
    new_special_attack=int(((2*special_attack+iv)*lvl)/100+5)+17
    new_special_defense=int(((2*special_defense+iv)*lvl)/100+5)+17
    new_spd=int(((2*spd+iv)*lvl)/100+5)+17
    pokemon.set_max_hp(new_hp)
    pokemon.set_attack(str(new_attack))
    pokemon.set_defense(str(new_defense))
    pokemon.set_special_attack(str(new_special_attack))
    pokemon.set_special_defense(str(new_special_defense))
    pokemon.set_special_speed(str(new_spd))
    

#def calcul_ennemie_potentiel_damage(pokemon):
    
set_stats_ennemi_pokemon(new_pokemon3)
print("les stats du pokémon sont")
print(Pokemon.get_max_hp(new_pokemon3))
print(Pokemon.get_attack(new_pokemon3))
print(Pokemon.get_defense(new_pokemon3))
print(Pokemon.get_special_attack(new_pokemon3))
print(Pokemon.get_special_defense(new_pokemon3))
print(Pokemon.get_speed(new_pokemon3))

def assert_opponent_pokemon_threat(pokemon1,pokemon2):
    pokemon_type=Pokemon.get_types(pokemon2)
    max_damage=0
    for type_pokemon in pokemon_type:
        attackphy=Move(type_pokemon+'phy',None,None,False,10,None)
        attackphy.update_smogon_data(type_pokemon,'Physical','100','100','stabed attack')
        attackspe=Move(type_pokemon+'phy',None,None,False,10,None)
        attackspe.update_smogon_data(type_pokemon,'Special','100','100','stabed attack')
        print(Move.get_move_type(attack_spe))
        phy_damage=damage_calcul(pokemon2,pokemon1,attackphy)
        spe_damage=damage_calcul(pokemon2,pokemon1,attackspe)
        if (max_damage>phy_damage):
            max_damage=phy_damage
        if (max_damage>spe_damage):
            max_damage=spe_damage
    return max_damage

assert_opponent_pokemon_threat(new_pokemon2,new_pokemon)
            
            
damage_calcul(new_pokemon,new_pokemon2,new_attack)















