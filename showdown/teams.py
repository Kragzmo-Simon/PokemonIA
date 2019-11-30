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

class Pokemon:

    def __init__(self,  name,
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
        self.moves = [move1,move2,move3,move4]

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

    def self_print(self):
        print("\n", self.name, " (level", self.level,",", self.gender,") - active : ", self.active)
        print("    hps - ", self.current_hp, "/", self.max_hp)
        print("    stats - ", self.attack, "/", self.defense, "/", self.special_attack, 
                "/", self.special_defense, "/", self.speed)
        print("    moves - ", self.moves[0], "/", self.moves[1], "/", self.moves[2], "/", self.moves[3])
        print("    abilities - ", self.ability, "(originally ", self.base_ability, ")")
        print("    item - ", self.item)

class Move:

    def __init__(self,  name,
                        target,
                        disabled,
                        current_pp,
                        max_pp):
        self.name = name
        self.target = target
        self.disabled = disabled
        self.current_pp = current_pp
        self.max_pp = max_pp

        # Information below will be updated later on update call
        self.types = [None] * 2
        self.power = 9000
        self.accuracy = 9000

        # self.gigamax = mettre toutes les infos du maxmove directement dans le move plutot que
        # de creer un second move

    def self_print(self):
        print("\n", self.name, " (", self.target, ", ", self.disabled,")")
        print("    pp : ", self.current_pp, "/", self.max_pp)
        print("    types - ", self.types[0], " - ", self.types[1])
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

