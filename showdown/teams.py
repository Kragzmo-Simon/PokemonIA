from enum import Enum

class Team:
    """
    A team is composed of 6 pokemons and a player
    """
    def __init__(self, player):
        self.player = player # either p1 or p2
        self.pokemons = [None] * 6

        # This index tracks the next index of self.pokemons that should be added
        # If it is equal to 6, then the team is full
        self.pokemon_index_to_add = 0

    def add_pokemon(self, pokemon):
        self.pokemons[self.pokemon_index_to_add] = pokemon
        self.pokemon_index_to_add += 1

    def self_print(self):
        for pokemon in self.pokemons:
            if pokemon is not None:
                pokemon.self_print()

    def print_active_pokemon(self):
        for pokemon in self.pokemons:
            if pokemon.is_active():
                pokemon.self_print()

    def get_active_pokemon_possible_moves(self):
        for pokemon in self.pokemons:
            #pokemon.self_print()
            if pokemon is not None and pokemon.is_active():
                return pokemon.get_possible_moves()

    def update_moves_with_smogon(self, smogon_move):
        for pokemon in self.pokemons:
            pokemon.update_move_data_with_smogon(smogon_move)

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
        self.smogon_id = smogon_id + 1

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

        # item
        self.item = item

        # ability
        self.ability = ability
        self.base_ability = base_ability

        # moves
        self.moves_names = [move1,move2,move3,move4]
        self.complete_moves = []

        # active if the pokemon that is currently fighting
        self.active = active

        # stats modifiers
        # self.crit_level = 0
        # condition and statuses

        """
        self.base_hp = 0
        self.base_attack = 0
        self.base_defense = 0
        self.base_special_attack = 0
        self.base_special_defense = 0
        self.base_special_defense = 0
        """

        # Status and condition
        #self.status = 0
        #self.condition = 0

    def update_moves(self, moves):
        self.complete_moves = moves

    def is_active(self):
        return self.active

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
                if len(self.complete_moves) >= (index+1):
                    pok_move = self.complete_moves[index]
                    pok_move.update_smogon_data(smogon_move_type, 
                                                smogon_move_category, 
                                                smogon_move_power, 
                                                smogon_move_accuracy, 
                                                smogon_move_description)
                else:
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

                print("Updating ", move_name, " (", self.name,")")

    def self_print(self):
        print("\n", self.smogon_id, " - ", self.name, " (level", self.level,",", self.gender,") - active : ", self.active)
        print("    hps - ", self.current_hp, "/", self.max_hp)
        print("    stats - ", self.attack, "/", self.defense, "/", self.special_attack, 
                "/", self.special_defense, "/", self.speed)
        print("    moves - ", self.moves_names[0], "/", self.moves_names[1], "/", self.moves_names[2], "/", self.moves_names[3])
        print("    abilities - ", self.ability, "(originally ", self.base_ability, ")")
        print("    item - ", self.item)

        print("    moves details : ")
        for move in self.complete_moves:
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

