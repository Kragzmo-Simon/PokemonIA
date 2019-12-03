# -*- coding: utf-8 -*-
"""Module for Room and Battle objects"""

import math
import time
from collections import deque
from . import utils, user
import random
import re
import asyncio
from .teams import *
from .logic import *

class Room:
    """
    Class representing a room on showdown. Tracks messages sent into the room,
    userlists, and includes utility methods to be used in conjunction with
    a client.

    Args:
        room_id (:obj:`str`) : The room's id. Ex: 'lobby', 'healthfitness'
        client (:obj:`showdown.client.Client`, optional) : The client to be
            used with the Room object's utility functions. Defaults to None.
        max_logs (:obj:`int`) : The maximum number of logs to be included in
            the Room object. Logs include chat messages, room intros, tour.
            updates, etc...

    Attributes:
        id (:obj:`str`) : The room's id.
        logs (:obj:`collections.deque`) : Queue containing all of the logs
            associated with the room.
        userlist (:obj:`dict`) : Dictionary with entries of {user_id : User}
            containing all the room's current users.
        client (:obj:`showdown.client.Client`) : The client to be
            used with the Room object's utility functions. Defaults to None.
        title (:obj:`str`) : The room's title. Ex: 'Lobby', 'Monotype'
    """
    def __init__(self, room_id, client=None, max_logs=5000):
        self.id = room_id
        self.logs = deque(maxlen=max_logs)
        self.userlist = {}
        self.client = client
        self.title = None
        self.init_time = time.time()

    def __eq__(self, other):
        return isinstance(other, Room) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return '<{} `{}`>'.format(self.__class__.__name__, self.title)

    def add_content(self, content):
        """
        Adds content to the Room object's logs attribute. Content is also
        parsed and used to update the Room's state through the update method.
        """
        self.logs.append(content)
        inp_type, params = utils.parse_text_input(content)
        self.update(inp_type, *params)

    def _add_user(self, user_str):
        """
        Adds a user object built from user_str to the Room's roomlist
        """
        new_user = user.User(user_str, client=self.client)
        self.userlist[new_user.id] = new_user

    def _remove_user(self, user_id):
        """
        Removes a user object built from user_str from the Room's roomlist
        """
        self.userlist.pop(user_id, None)

    def update(self, inp_type, *params):
        """
        Updates the Room's state from input. This his method isn't intended to
        be called directly, but rather through a client's receiver method.
        """

        #Title set
        if inp_type == 'title':
            self.title = params[0]

        #Userlist init
        if inp_type == 'users':
            user_strs = params[0].split(',')[1:]
            for user_str in user_strs:
                self._add_user(user_str)

        #User name change
        elif inp_type == 'n':
            user_str, old_id = params
            self._remove_user(old_id)
            self._add_user(user_str)

        #User leave
        elif inp_type == 'l':
            user_id = utils.name_to_id(params[0])
            self._remove_user(user_id)

        #User join
        elif inp_type == 'j':
            user_str = params[0]
            self._add_user(user_str)

    @utils.require_client
    async def request_auth(self, client=None, delay=0, lifespan=math.inf):
        """
        Request room auth using the specified client or the Room's client
        attribute. The actual info will be sent to the clienet with inp_type
        of 'popup'.
        """
        await client.use_command(self.id, 'roomauth',
            delay=delay, lifespan=lifespan)

    @utils.require_client
    async def say(self, content, client=None, delay=0, lifespan=math.inf):
        """
        Send a message to the room using the specified client or the Room's
        client attribute.
        """
        await client.say(self.id, content, delay=delay, lifespan=lifespan)

    @utils.require_client
    async def join(self, client=None, delay=0, lifespan=math.inf):
        """
        Join the room using the specified client or the room's client
        attribute.
        """
        await client.join(self.id, delay=0, lifespan=lifespan)

    @utils.require_client
    async def leave(self, client=None, delay=0, lifespan=math.inf):
        """
        Leave the room using the specified client or the room's client
        attribute.
        """
        await client.leave(self.id, delay=delay, lifespan=lifespan)

class Battle(Room):
    current_turn = 0    # Attribute turn for the main check
    """
    Subclass of Room representing a battle room on Showdown. Has additional
    attributes and utility methods.

    Args:
        room_id (:obj:`str`) : The room's id. Ex: 'lobby', 'healthfitness'
        client (:obj:`showdown.client.Client`, optional) : The client to be
            used with the Room object's utility functions. Defaults to None.
        max_logs (:obj:`int`) : The maximum number of logs to be included in
            the Room object. Logs include chat messages, room intros, tour.
            updates, etc...


    Inherited attributes:
        id (:obj:`str`) : The room's id.
        logs (:obj:`collections.deque`) : Queue containing all of the logs
            associated wcurrith the room.
        userlist (:obj:`dict`) : Dictionary with entries of {user_id : User}
            containing all the room's current users.
        client (:obj:`showdown.client.Client`) : The client to be
            used with the Room object's utility functions. Defaults to None.
        title (:obj:`str`) : The room's title. Ex: 'Zarel vs. Aegisium Z'

    Attributes:
        rules (:obj:`list`) : A list of strings describing the match's rules
        p1 (:obj:`showdown.user.User`) : User object representing player one in
            the match
        p1 (:obj:`showdown.user.User`) : User object representing player two in
            the match
        rated (:obj:`bool`) : True if the match is rated (on ladder), else False
        tier (:obj:`str`) : String representing the matches tier.
            Ex: 'gen7monotype', 'gen7ou'
        winner (:obj:`showdown.user.User`) : User object representing the winner
            of the battle. Defaults to None if the match has not ended yet.
        winner_id (:obj:`str`) : String representing the match id of the
            battle's winner. Ex: 'p1', 'p2'
        loser (:obj:`showdown.user.User`) : User object representing the loser
            of the battle. Defaults to None if the match has not ended yet.
        loser_id (:obj:`str`) : String representing the match id of the
            battle's loser. Ex: 'p1', 'p2'
        ended (:obj:`bool`) : True if a player has won the match, else False
    """
    def __init__(self, room_id, client=None, max_logs=5000):
        Room.__init__(self, room_id, client=client, max_logs=max_logs)
        self.rules = []
        self.p1, self.p2 = None, None
        self.rated = False
        self.ended = False
        self.tier = None
        self.winner, self.loser = None, None
        self.winner_id, self.loser_id = None, None

        # teams
        self.own_team = None
        self.opponent_team = None

        # pokemon and moves collections
        self.pokemon_collection = []
        self.pokemon_names_collection = []
        self.moves_collection = []
        self.moves_name_collection = []

    def add_turn(self):
        self.current_turn += 1

    async def update_own_team(self, socket_input):
        try:
            # Active pokemon information
            active_pokemon_moves = re.findall(r"moves.*?side", socket_input)
            active_pokemon_moves_to_add = []

            # if the state is a forceswitch state
            force_Switch_needed = False
            if len(active_pokemon_moves) == 0:
                check_force_switch = re.findall(r"forceSwitch.*?side", socket_input)
                needs_a_force_switch = re.findall(r"\[.*?\]", check_force_switch[0])[0].replace("[","").replace("]","").strip()
                force_Switch_needed = True
                if needs_a_force_switch == "true":
                    print("Force switch received")
            else:
                pokemon_is_trapped = re.findall(r"trapped.*?:.*?}", active_pokemon_moves[0])
                if len(pokemon_is_trapped) != 0 and "trapped" in pokemon_is_trapped[0]:
                    print("He's trapped")
                    # TODO : make all other moves disabled

                # dissociate normal moves info from maxmoves info
                categories = re.findall(r"\[.*?\]", active_pokemon_moves[0])

                # Normal moves
                normal_moves = re.findall(r"{.*?}", categories[0])
                for smogon_id, normal_move in enumerate(normal_moves):
                    move_informations = normal_move.split(",")

                    name = move_informations[1].split(":")[-1].replace("\\\"","").replace("}","").strip() #

                    if len(move_informations) == 6:
                        current_pp = move_informations[2].split(":")[-1].strip()
                        max_pp = move_informations[3].split(":")[-1].strip()
                        target = move_informations[4].split(":")[-1].replace("\\\"","").strip()
                        disabled = True if move_informations[5].split(":")[-1].replace("}","").strip() == "true"  else False
                    else:
                        current_pp = None
                        max_pp = None
                        target = None
                        disabled = None
                        
                    new_move = Move(name, smogon_id, target, disabled, current_pp, max_pp)
                    #new_move.self_print()
                    active_pokemon_moves_to_add.append(new_move)

            # player name
            player_name = "p3"
            player_information = re.findall(r"name.*?\,.*?\,.*?pokemon", socket_input)
            if len(player_information) == 1:
                player_attributes = re.split(r",",player_information[0])
                if len(player_attributes) >= 2:
                    player_name = re.split(r":", player_attributes[1])[1].replace("\\\"","").strip()
                    
            if player_name == "p3":
                print("Erreur lors de la lecture du player : ", socket_input)

            # Team construction
            side = re.findall(r"name.*pokemon.*\[.*}\]", socket_input)[0]
            pokemons = re.findall(r"{.*?}.*?}", side)

            self.own_team = Team(player_name)

            # arrays containing the moves and the pokemons names that have to be asked to smogon
            moves_to_ask_smogon = []
            pokemons_to_ask_smogon = []
                    
            for smogon_id,pokemon in enumerate(pokemons):
                stats = re.split(r",", pokemon)

                hp_stats = re.findall(r"condition.*?,", pokemon)[0].split(r":")[-1].replace("\\\"","").replace(",","").strip().split(r"/")
                activity = re.findall(r"active.*?,", pokemon)[0].split(r":")[-1].replace(",","").strip()
                pokemon_general_stats = re.findall(r"stats.*?}", pokemon)[0].split(r",")
                pokemon_moveset = re.findall(r"\[.*?\]", pokemon)[0].split(r",")

                if len(re.findall(r"details.*?,", pokemon)[0].split(r":")) == 2:
                    name = re.findall(r"details.*?,", pokemon)[0].split(r":")[1].replace("\\\"","").replace(",","").replace("-","").replace(".","").replace(" ","").replace("'","").strip()
                else:
                    # Type:Null pokemon
                    name_decomposed = re.findall(r"details.*?,", pokemon)[0].split(r":")
                    name = name_decomposed[1] + name_decomposed[2]
                    name = name.replace("\\\"","").replace(",","").replace("-","").replace(".","").replace(" ","").replace("'","").strip()
                    #name = "TypeNull"
                level = stats[2].replace("\\\"","").replace("L","").strip()
                if len(hp_stats) == 2:
                    current_hp = hp_stats[0]
                    max_hp = hp_stats[1]
                elif hp_stats[0] == "0 fnt":
                    current_hp = 0
                    max_hp = 0
                else:
                    # This should never happen
                    current_hp = None
                    max_hp = None
                active = True if activity == "true" else False
                attack = pokemon_general_stats[0].split(r":")[-1].strip()
                defense = pokemon_general_stats[1].split(r":")[-1].strip()
                spAttack = pokemon_general_stats[2].split(r":")[-1].strip()
                spDefense = pokemon_general_stats[3].split(r":")[-1].strip()
                speed = pokemon_general_stats[4].split(r":")[-1].replace("}","").strip()
                ability = re.findall(r"ability.*?}", pokemon)[0].split(r":")[1].replace("\\\"","").replace("}","").strip()
                base_ability = re.findall(r"baseAbility.*?,", pokemon)[0].split(r":")[1].replace(",","").replace("\\\"","").replace("}","").strip()
                item = re.findall(r"item.*?,", pokemon)[0].split(r":")[1].replace("\\\"","").replace("}","").replace(",","").strip()

                pokemon_full_moveset = [None, None, None, None]
                for move_index,pokemon_move_line in enumerate(pokemon_moveset):
                    pokemon_full_moveset[move_index] = pokemon_move_line.replace("\\\"","").replace("[","").replace("]","").strip()

                move1 = pokemon_full_moveset[0]
                move2 = pokemon_full_moveset[1]
                move3 = pokemon_full_moveset[2]
                move4 = pokemon_full_moveset[3]

                """
                # For Debug concerns
                if name == "Null" or name == "null" or name == "Type" or name == "type":
                    print("Pokemon Null : ", socket_input)
                    name = "type:null"
                """

                if len(stats) == 19:
                    gender = stats[3].replace("\\\"","").strip()
                else:
                    gender = None
                
                new_pokemon = Pokemon(name,smogon_id,level,gender,current_hp,max_hp,
                                attack,defense,spAttack,spDefense,speed,
                                move1,move2,move3,move4,
                                ability,base_ability,item, active)

                if move1 not in moves_to_ask_smogon and move1 not in self.moves_name_collection:
                    moves_to_ask_smogon.append(move1)
                if move2 not in moves_to_ask_smogon and move2 not in self.moves_name_collection:
                    moves_to_ask_smogon.append(move2)
                if move3 not in moves_to_ask_smogon and move3 not in self.moves_name_collection:
                    moves_to_ask_smogon.append(move3)
                if move4 not in moves_to_ask_smogon and move4 not in self.moves_name_collection:
                    moves_to_ask_smogon.append(move4)

                if name not in self.pokemon_names_collection:
                    pokemons_to_ask_smogon.append(name)

                if active:
                    new_pokemon.update_moves(active_pokemon_moves_to_add)
                self.own_team.add_pokemon(new_pokemon)
        

            # Update the team with the moves and pokemon stored in collections
            for already_known_move in self.moves_collection:
                self.own_team.update_moves_with_smogon(already_known_move)
            for already_known_pokemon in self.pokemon_collection:
                self.own_team.update_pokemons_with_smogon(already_known_pokemon)
            

            # Send smogon the commands to retrieve the moves and pokemons data
            for pokemon in pokemons_to_ask_smogon:
                await self.get_M_or_P_data(pokemon)
                self.pokemon_names_collection.append(pokemon)
            for move in moves_to_ask_smogon:
                await self.get_M_or_P_data(move)
                self.moves_name_collection.append(move)

            # Send a switch if forceswitch was received
            if force_Switch_needed:
                await self.make_switch()

            # these moves are the ones we already data from smogon
            # (here, the real ones are supposed to be more or less empty
            # but the names ones should be full)
            """
            #Code to debug moveset, is currently useless 
            real_collection_moves_names = []
            for move in self.moves_collection:
                real_collection_moves_names.append(move.get_name())
            print("collection moves : ", len(self.moves_name_collection))
            print("collection moves real: ", len(self.moves_collection))
            print("collection pokemons : ", len(self.pokemon_names_collection))
            print("collection pokemons real : ", len(self.pokemon_collection))
            """

            """
            # Maxmoves
            maxmoves = re.findall(r"{.*?}", categories[1])
            for maxmove in maxmoves:
                maxmove_lines = re.split(r",",maxmove)
                maxmove_name = maxmove_lines[0].split(r":")[-1].replace("\\\"","").strip()
                maxmove_target = maxmove_lines[1].split(r":")[-1].replace("}","").replace("\\\"","").strip()
            """
        except IndexError as err:
            print(".................. Erreur : ", err)
            print("L'input faible : ", socket_input)

    def update_smogon_data_pokemon(self, socket_input):
        # move name
        pokemon_link = re.findall(r"<a.*href.*?</a>", socket_input)
        pokemon_name = re.findall(r">.*?<", pokemon_link[-1])[0].replace(">","").replace("<","").replace(" ","").replace(".","").replace("'","").strip().lower()

        # types
        pokemon_types_collection = []
        pokemon_types = re.findall(r"alt=\\\".*?\\\"", socket_input)
        for pok_type in pokemon_types:
            pokemon_type = pok_type.replace("alt=\\\"","").replace("\\\"","").strip().lower()
            pokemon_types_collection.append(pokemon_type)

        # abilities
        pokemon_abilities_collection = []
        pokemon_abilities = re.findall(r"abilitycol.*?</span", socket_input)
        for pok_ability in pokemon_abilities:
            pokemon_abilities_names = re.findall(r">[a-zA-Z].*?<", pok_ability)
            for pokemon_ability in pokemon_abilities_names:
                pokemon_ability_name = pokemon_ability.replace(">","").replace("<","").replace(" ","").strip().lower()
                pokemon_abilities_collection.append(pokemon_ability_name)

        # stats
        pokemon_stats = re.findall(r"/>[0-9]+</span>", socket_input)
        pokemon_hp = re.findall(r">.*?<", pokemon_stats[0])[-1].replace(">","").replace("<","").replace(" ","").strip().lower()
        pokemon_atk = re.findall(r">.*?<", pokemon_stats[1])[-1].replace(">","").replace("<","").replace(" ","").strip().lower()
        pokemon_def = re.findall(r">.*?<", pokemon_stats[2])[-1].replace(">","").replace("<","").replace(" ","").strip().lower()
        pokemon_speA = re.findall(r">.*?<", pokemon_stats[3])[-1].replace(">","").replace("<","").replace(" ","").strip().lower()
        pokemon_speD = re.findall(r">.*?<", pokemon_stats[4])[-1].replace(">","").replace("<","").replace(" ","").strip().lower()
        pokemon_spe = re.findall(r">.*?<", pokemon_stats[5])[-1].replace(">","").replace("<","").replace(" ","").strip().lower()
        
        new_pokemon = Pokemon(pokemon_name,None,None,None,None,pokemon_hp,
                                None,None,None,None,None,
                                None,None,None,None,
                                None,None,None, False)
        
        new_pokemon.update_smogon_data(pokemon_types_collection, 
                                        pokemon_abilities_collection,
                                        pokemon_hp,
                                        pokemon_atk,
                                        pokemon_def,
                                        pokemon_speA,
                                        pokemon_speD,
                                        pokemon_spe)

        if new_pokemon not in self.pokemon_collection:
            self.pokemon_collection.append(new_pokemon)

        self.opponent_team.update_pokemons_with_smogon(new_pokemon)

        # update on allied pokemons
        self.own_team.update_pokemons_with_smogon(new_pokemon)

        # Display
        """
        print("\nname : " ,pokemon_name)
        for pok_type in pokemon_types_collection:
            print("type : ", pok_type)
        for ability in pokemon_abilities_collection:
            print("ability : ", ability)
        print("hp : ", pokemon_hp)
        print("atk : ", pokemon_atk)
        print("def : ", pokemon_def)
        print("speA : ", pokemon_speA)
        print("speD : ", pokemon_speD)
        print("spe : ", pokemon_spe)
        """

    def update_smogon_data_move(self, socket_input):
        # move name
        move_link = re.findall(r"<a.*href.*?</a>", socket_input)
        move_name = re.findall(r">.*?<", move_link[-1])[0].replace(">","").replace("<","").replace(" ","").replace("-","").strip().lower()

        # type and phys/spe
        attributes = re.findall(r"alt=\\\".*?\\\"", socket_input)
        move_type = attributes[-2].replace("alt=","").replace("\\\"","").strip().lower()
        move_category = attributes[-1].replace("alt=","").replace("\\\"","").strip().lower()

        # power and accuracy
        caracteristics = re.findall(r"<br.*?</span>", socket_input)
        move_power = None
        if len(caracteristics) == 3:
            move_power = caracteristics[-3].replace("<br>","").replace("</span>","").strip()
            move_accuracy = caracteristics[-2].replace("<br>","").replace("</span>","").replace("%","").strip()
        else:
            move_accuracy = caracteristics[0].replace("<br>","").replace("</span>","").replace("%","").strip()
            # if move_accuracy is_number

        # additional info
        description = re.findall(r"movedesccol.*?</span>", socket_input)
        move_description = description[-1].replace("</span>","").replace("movedesccol\\\">","").strip().lower()
        
        new_move = Move(move_name, None, None, False, 8, None)
        new_move.update_smogon_data(move_type, move_category, move_power, move_accuracy, move_description)

        moves_collection_names = []
        for collection_move in self.moves_collection:
            moves_collection_names.append(collection_move.get_name())

        if new_move.get_name() not in moves_collection_names:
            self.moves_collection.append(new_move)

        # check if a pokemon in the team has the move in which case, the move is updated
        self.own_team.update_moves_with_smogon(new_move)

        # TODO add verification for enemy team
        #new_move.self_print()
        """
        print("\nmove : " ,move_name)
        print("type : ", move_type)
        print("category : ", move_category)
        print("power : ", move_power)
        print("accuracy : ", move_accuracy)
        print("description : ", move_description)
        """

    async def update_turn(self, socket_input):
        # create opponent team
        if self.opponent_team is None:
            if self.own_team is None:
                print("IMPOSSIBLE DE CREER LA TEAM ADVERSE")
            else:
                if self.own_team.get_player() == "p2":
                    opponent_player_name = "p1"
                else:
                    opponent_player_name = "p2"
                self.opponent_team = Team(opponent_player_name)
        
        # turn parsing
        damage_event_player, damage_event_pokemon, damage_event_current_hp, damage_event_max_hp = None,None,None,None
        damage_event_type = "-"
        boost_events_collection = []
        unboost_events_collection = []
        switch_events_collection = []
        lines = socket_input.split("\\n")
        for line in lines:
            # damage events
            damages_events = re.findall(r"-damage.*$",line)
            for damage_event in damages_events:
                damage_infos = damage_event.split("|")
                damage_event_pokemon_and_player = damage_infos[1].split(r":")
                damage_event_hp_bar = damage_infos[2].split("/")

                damaged_pokemon_owner = damage_event_pokemon_and_player[0].replace("a","").strip()
                if damaged_pokemon_owner == self.opponent_team.get_player():
                    damage_event_player = damaged_pokemon_owner
                    damage_event_pokemon = damage_event_pokemon_and_player[1].replace(" ","").replace(".","").strip().lower()
                    damage_event_current_hp = damage_event_hp_bar[0].replace("\\n","").replace("fnt","").strip()
                    damage_event_max_hp = 100
                    damage_event_type = "damage"

                if damaged_pokemon_owner == self.own_team.get_player():
                    if damage_event_current_hp == "0":
                        self.own_team.reset_buffs()
        
            # heal events
            heals_events = re.findall(r"-heal.*$",line)
            for heal_event in heals_events:
                heal_infos = heal_event.split("|")
                heal_event_pokemon_and_player = heal_infos[1].split(r":")
                heal_event_hp_bar = heal_infos[2].split("/")

                healed_pokemon_owner = heal_event_pokemon_and_player[0].replace("a","").strip()
                if healed_pokemon_owner == self.opponent_team.get_player():
                    damage_event_player = healed_pokemon_owner
                    damage_event_pokemon = heal_event_pokemon_and_player[1].strip().lower()
                    damage_event_current_hp = heal_event_hp_bar[0].replace("\\n","").replace("fnt","").strip()
                    damage_event_max_hp = 100
                    damage_event_type = "heal"

            # boost events
            boosts_events = re.findall(r"-boost.*$", line)
            for boost_event in boosts_events:
                boost_infos = boost_event.split("|")
                boost_event_pokemon_and_player = boost_infos[1].split(r":")

                boost_event_player = boost_event_pokemon_and_player[0].replace("a","").strip()
                boost_event_pokemon = boost_event_pokemon_and_player[1].strip().lower()
                boost_event_stat = boost_infos[2].strip().lower()
                boost_event_level = boost_infos[3].replace("\\n","").strip()
                
                pokemon_boost = [boost_event_player,
                                    boost_event_pokemon,
                                    boost_event_stat,
                                    boost_event_level]
                boost_events_collection.append(pokemon_boost)

            # unboost events
            unboosts_events = re.findall(r"-unboost.*$", line)
            for unboost_event in unboosts_events:
                unboost_infos = unboost_event.split("|")
                unboost_event_pokemon_and_player = unboost_infos[1].split(r":")

                unboost_event_player = unboost_event_pokemon_and_player[0].replace("a","").strip()
                unboost_event_pokemon = unboost_event_pokemon_and_player[1].strip().lower()
                unboost_event_stat = unboost_infos[2].strip().lower()
                unboost_event_level = unboost_infos[3].replace("\\n","").strip()

                pokemon_unboost = [unboost_event_player,
                                    unboost_event_pokemon,
                                    unboost_event_stat,
                                    unboost_event_level]
                unboost_events_collection.append(pokemon_unboost)

            switch_events = re.findall(r"switch.*$", line)
            for switch_event in switch_events:
                switch_infos = switch_event.split("|")
                switch_event_pokemon_and_player = switch_infos[1].split(r":")

                switch_event_player = switch_event_pokemon_and_player[0].replace("a","").strip()
                switch_event_pokemon = switch_event_pokemon_and_player[1].strip().lower()
                switch_event_pokemon_level = switch_infos[2].split(",")[1].replace("L","").strip()
                switch_event_pokemon_current_hp = switch_infos[3].split("/")[0]
                switch_event_pokemon_max_hp = 100

                pokemon_switch = [switch_event_player,
                                    switch_event_pokemon,
                                    switch_event_pokemon_level,
                                    switch_event_pokemon_current_hp,
                                    switch_event_pokemon_max_hp]
                switch_events_collection.append(pokemon_switch)

                # remove boosts and unboosts of the current side
                new_boost_collection = []
                for boost in boost_events_collection:
                    if boost[0] != switch_event_player:
                        new_boost_collection.append(boost)
                boost_events_collection = new_boost_collection

                new_unboost_collection = []
                for unboost in unboost_events_collection:
                    if unboost[0] != switch_event_player:
                        new_unboost_collection.append(boost)
                unboost_events_collection = new_unboost_collection

                if self.opponent_team.get_player() == switch_event_player:
                    self.opponent_team.reset_buffs()
                if self.own_team.get_player() == switch_event_player:
                    self.own_team.reset_buffs()

        # Résumé du tour
        #print(damage_event_player, " / ", damage_event_pokemon, " => ", damage_event_current_hp, " / ", 
        #            damage_event_max_hp, "(", damage_event_type,")")
        
        for boost in boost_events_collection:
            #print(boost[0], " / ", boost[1], " => ", boost[2], " +", boost[3])
            if boost[0] == self.opponent_team.get_player():
                self.opponent_team.raise_stat(boost[2],boost[3])
            if boost[0] == self.own_team.get_player():
                self.own_team.raise_stat(boost[2],boost[3])
        for unboost in unboost_events_collection:
            #print(unboost[0], " / ", unboost[1], " => ", unboost[2], " -", unboost[3])
            if unboost[0] == self.opponent_team.get_player():
                self.opponent_team.lower_stat(unboost[2],unboost[3])
            if unboost[0] == self.own_team.get_player():
                self.own_team.lower_stat(unboost[2],unboost[3])            
        for switch in switch_events_collection:
            #print("switch : ", switch[0], " - ", switch[1], " (", switch[2], ")", switch[3], " / ", switch[4])
            if switch[0] == self.opponent_team.get_player():
                pokemon_names = self.opponent_team.get_pokemon_names()

                # create the opponent pokemon if needed and set it to be the only active pokemon
                if switch[1] not in pokemon_names:
                    self.opponent_team.set_all_pokemons_to_inactive()
                    # switch[2] contains the pokemon level
                    new_pokemon = Pokemon(switch[1],None,switch[2],None,100,None,
                                None,None,None,None,None,
                                None,None,None,None,
                                None,None,None, True)
                    new_pokemon.update_moves([None,None,None,None])
                    self.opponent_team.add_pokemon(new_pokemon)

                    # send showdown data command
                    await self.get_M_or_P_data(switch[1])
                else:
                    self.opponent_team.set_all_pokemons_to_inactive()
                    self.opponent_team.make_pokemon_active(switch[1])

                    #current_pokemon = self.opponent_team.get_pokemon(switch[1])
                    #current_pokemon.self_print()
        # If damage kills opponent pokemon, make all opponent's pokemons inactive
        if damage_event_player == self.opponent_team.get_player():
            if damage_event_current_hp == "0" and damage_event_type == "damage":
                self.opponent_team.set_all_pokemons_to_inactive()
                self.opponent_team.reset_buffs()
            
            if damage_event_max_hp is not None and damage_event_current_hp is not None and damage_event_pokemon is not None:
                # if the pokemon is not killed, update its hp status
                opponent_active_pokemon = self.opponent_team.get_pokemon(damage_event_pokemon)
                opponent_active_pokemon.set_current_hp(damage_event_current_hp)

    def print_own_team(self):
        if self.own_team is not None:
            self.own_team.self_print()

    def update(self, inp_type, *params): #TODO: Fix this up
        """
        Updates the Room's state from input. This his method isn't intended to
        be called directly, but rather through a client's receiver method.
        """
        Room.update(self, inp_type, *params)
        if inp_type == 'player':
            player_id, name = params[0], params[1]
            if not name or player_id not in ('p1', 'p2'):
                return
            setattr(self, player_id, user.User(name, client=self.client))
        elif inp_type == 'rated':
            self.rated = True
        elif inp_type == 'tier':
            self.tier = utils.name_to_id(params[0])
        elif inp_type == 'rule':
            self.rules.append(params[0])
        elif inp_type == 'win':
            winner_name = params[0]
            if self.p1.name_matches(winner_name):
                self.winner, self.winner_id = self.p1, 'p1'
                self.loser, self.loser_id = self.p2, 'p2'
            elif self.p2.name_matches(winner_name):
                self.winner, self.winner_id = self.p2, 'p2'
                self.loser, self.loser_id = self.p1, 'p1'
            self.ended = True

    @utils.require_client
    async def save_replay(self, client=None, delay=0, lifespan=math.inf):
        """
        |coro|

        Uses the specified client or the object's client attribute to save a
        replay of the battle. The battle must be ended before for this method
        to work. 
        """
        await client.save_replay(self.id, delay=delay, lifespan=lifespan)

    @utils.require_client
    async def forfeit(self, client=None, delay=0, lifespan=math.inf):
        """
        |coro|

        Uses the specified client or the object's client attribute to forfeit
        the battle. The client must be one of the players in the battle for this
        to work.
        """
        await client.forfeit(self.id, delay=delay, lifespan=lifespan)

    #TODO: Test everything below here

    @utils.require_client
    async def set_timer_on(self, client=None, delay=0, lifespan=math.inf):
        """
        |coro|

        Uses the specified client or the object's client attribute to turn on
        the battle timer. The client must be one of the players in the battle 
        for this to work.
        """
        await self.client.use_command(self.id, 'timer', 'on',
            delay=delay, lifespan=lifespan)

    @utils.require_client
    async def set_timer_off(self, client=None, delay=0, lifespan=math.inf):
        """
        |coro|

        Uses the specified client or the object's client attribute to turn off
        the battle timer. The client must be one of the players in the battle 
        for this to work.
        """
        await self.client.use_command(self.id, 'timer', 'off',
            delay=delay, lifespan=lifespan)

    @utils.require_client
    async def switch(self, switch_id, turn_num, client=None, 
        delay=0, lifespan=math.inf):
        """
        |coro|

        Uses the specified client or the object's client to switch into a
        different pokemon. The client must be one of the players in the battle 
        for this to work.
        """
        await self.client.use_command(self.id, 'switch', '{}'.format(switch_id),
            delay=delay, lifespan=lifespan)

    @utils.require_client
    async def move(self, move_id, turn_num, mega=False, client=None,
        delay=0, lifespan=math.inf):
        """
        |coro|

        Uses the specified client or the object's client attribute to turn on
        the battle timer. The client must be one of the players in the battle 
        for this to work.
        """
        await self.client.use_command(self.id, 'choose', 'move {}'
            .format(move_id),
            delay=delay, lifespan=lifespan)

    @utils.require_client
    async def get_M_or_P_data(self, move_name, mega=False, client=None,
        delay=0, lifespan=math.inf):
        """
        |coro|

        Uses the specified client or the object's client attribute to get data
        of one pokemon. The client must be one of the players in the battle 
        for this to work.
        """
        await self.client.use_command(self.id, 'data', '{}'
            .format(move_name),
            delay=delay, lifespan=lifespan)

    @utils.require_client
    async def make_decision(self, client=None,
        delay=0, lifespan=math.inf):
        """
        Selects a random move among the moves that can be executed.
        """

        # size tracking variables that helps resending the data if some has not been updated
        old_moves_name_collection_size = -1
        old_moves_collection_size = -1

        # Wait for the data to be updated
        smogon_data_has_not_been_updated = True
        while smogon_data_has_not_been_updated:

            current_moves_name_collection_size = len(self.moves_name_collection)
            current_moves_collection_size = len(self.moves_collection)
            # resend data command
            if current_moves_name_collection_size != current_moves_collection_size:
                if old_moves_name_collection_size == current_moves_name_collection_size:
                    if old_moves_collection_size == current_moves_collection_size:
                        # This part checks all moves present in the collection and then sends data for
                        # each move that should be in it but is not (move information has not been received)
                        print("RESENDING DATA : ", 
                                current_moves_collection_size, " / ",
                                current_moves_name_collection_size)
                        # get the missing moves names
                        current_moves_real_collection_names = []
                        for collection_move in self.moves_collection:
                            current_moves_real_collection_names.append(collection_move.get_name())

                        print("current collection : ", current_moves_real_collection_names)
                        print("supposed collection : ", self.moves_name_collection)

                        # resend the command data to smogon
                        for move_name in self.moves_name_collection:
                            if move_name not in current_moves_real_collection_names:
                                print("Resending : ", move_name)
                                await self.get_M_or_P_data(move_name)

                old_moves_name_collection_size = current_moves_name_collection_size
                old_moves_collection_size = current_moves_collection_size

            # check if the data has been updated
            if  current_moves_collection_size == current_moves_name_collection_size:

                data_commands_names_to_resend = []
                # smogon_data_has_not_been_updated becomes false once all the data has been correctly updated in all pokemons
                smogon_update, data_commands_names_to_resend1 = self.own_team.check_smogon_data_update()
                smogon_update2, data_commands_names_to_resend2 = self.opponent_team.check_smogon_data_update()
                
                if smogon_update and smogon_update2:
                    # TODO mettre le check sur la team adverse
                    smogon_data_has_not_been_updated = False
                else:
                    for data_command in data_commands_names_to_resend1:
                        data_commands_names_to_resend.append(data_command)
                    for data_command in data_commands_names_to_resend2:
                        data_commands_names_to_resend.append(data_command)

                # resend data commands if need be
                if smogon_data_has_not_been_updated:
                    for data_command_name in data_commands_names_to_resend:
                        print("Resending 2 : ", data_command_name)
                        await self.get_M_or_P_data(data_command_name)

                #print("Checking smogon data update...................... : ", smogon_data_has_not_been_updated)
            await asyncio.sleep(2)

        #self.opponent_team.print_active_pokemon()
        #self.own_team.print_active_pokemon()


        print("Making a decision")
        #possible_moves = self.own_team.get_active_pokemon_possible_moves()

        await self.select_best_decision()

        #for move in possible_moves:
        #    print("dat id : ", move.get_smogon_id())

        # 1/4 chance of switching (switch_or_move=0) and 3/4 chance of moving (switch_or_move=1,2 or 3)
        """
        switch_or_move = random.randint(0,4)
        if switch_or_move and len(possible_moves) > 0:
            # will be used more effectively than just a randomint when the intelligent logic will be called
            randomly_generated_move_id = random.randint(1,len(possible_moves))
            move_id = possible_moves[randomly_generated_move_id-1].get_smogon_id() + 1
            await self.move(move_id,1)
        else:
            await self.make_switch()
        """

    # fonction qui renvoie le meilleur switch ou move à effectuer
    @utils.require_client
    async def select_best_decision(self, client=None,
        delay=0, lifespan=math.inf):

        print("Retrieving data...")
        # get both active pokemons and other switchs
        pokemon1 = self.own_team.get_active_pokemon()
        print("pokemon1 retrieved")
        pokemon2 = self.opponent_team.get_active_pokemon()
        print("pokemon2 retrieved")
        pokemon2.set_stats_enemy_pokemon()
        print("stats update done")
        possible_switchs = self.own_team.get_possible_pokemon_switch()
        print("switch options retrieved")

        print("Calculating active pokemon options")

        # heuristics for the active pokemon (considering a direct move)
        active_pokemon_move_selected = None
        active_pokemon_max_dmg = 0
        active_pokemon_speed_tie_won = False
        active_pokemon_tanking_capacity = 0
        if pokemon1 is not None and pokemon2 is not None:
            print("selecting a move")
            active_pokemon_move_selected, active_pokemon_max_dmg = select_move(pokemon1,pokemon2)
            print("determining speed tie")
            active_pokemon_speed_tie_won = determince_speed_tie(pokemon1, pokemon2)
            print("determing tanking capacity")
            active_pokemon_tanking_capacity = assert_opponent_pokemon_threat(pokemon1, pokemon2)
            print("active pokemon options calculation done")

            #print("checking : ", pokemon1.get_name(), " / ", pokemon2.get_name())
            #print("dat speed tie : ", active_pokemon_speed_tie_won)
            #print("_______________best move : ", active_pokemon_move_selected, " (", active_pokemon_max_dmg, ")")
            #print("tanking capacity : ", active_pokemon_tanking_capacity)
        else:
            print("Erreur : un des pokemons est None")

        active_pokemon_move_selected_should_be_used = False
        if active_pokemon_max_dmg >= 100 and active_pokemon_speed_tie_won:
            print("choose move (1) : ", active_pokemon_move_selected)
            active_pokemon_move_selected_should_be_used = True
        if active_pokemon_max_dmg >= active_pokemon_tanking_capacity and active_pokemon_speed_tie_won:
            print("choose move (2) : ", active_pokemon_move_selected)
            active_pokemon_move_selected_should_be_used = True
        if active_pokemon_max_dmg >= 100 and active_pokemon_tanking_capacity < 90:
            print("choose move (3) : ", active_pokemon_move_selected)
            active_pokemon_move_selected_should_be_used = True
        if active_pokemon_max_dmg >= 50 and active_pokemon_tanking_capacity < 45:
            print("choose move (4) : ", active_pokemon_move_selected)
            active_pokemon_move_selected_should_be_used = True

        if active_pokemon_move_selected_should_be_used:
            # TODO Send command for move
            print("Declaring a well calculated move : ", active_pokemon_move_selected)
            await self.move(active_pokemon_move_selected,1)
            return

        print("Calculating switch options")

        for switch in possible_switchs:
            print("Checking switch : ", switch)
            switch_pokemon = self.own_team.get_pokemon(switch)
            print("Pokemon ", switch, "retrieved")

            switch_pokemon_move_selected = None
            switch_pokemon_max_dmg = 0
            switch_pokemon_speed_tie_won = False
            switch_pokemon_tanking_capacity = 0
            if switch_pokemon is not None and pokemon2 is not None:
                print("selecting a move")
                switch_pokemon_move_selected, switch_pokemon_max_dmg = select_move(switch_pokemon,pokemon2)
                print("determining speed tie")
                switch_pokemon_speed_tie_won = determince_speed_tie(switch_pokemon, pokemon2)
                print("determing tanking capacity")
                switch_pokemon_tanking_capacity = assert_opponent_pokemon_threat(switch_pokemon, pokemon2)
                print("switch pokemon options calculation done")

                #print("----checking : ", switch_pokemon.get_name(), " / ", pokemon2.get_name())
                #print("----dat speed tie : ", switch_pokemon_speed_tie_won)
                #print("----best move : ", switch_pokemon_move_selected, " (", switch_pokemon_max_dmg, ")")
                #print("----tanking capacity : ", switch_pokemon_tanking_capacity)

            print("Determining switch reliability")
            switch_pokemon_should_be_used = False
            if switch_pokemon_speed_tie_won and switch_pokemon_max_dmg >= 100 and switch_pokemon_tanking_capacity < 90:
                print("choose switch (5) : ", switch_pokemon.get_name())
                switch_pokemon_should_be_used = True
            if switch_pokemon_tanking_capacity < 25 and switch_pokemon_max_dmg > (2 * switch_pokemon_tanking_capacity):
                print("choose switch (6) : ", switch_pokemon.get_name())
                switch_pokemon_should_be_used = True
            if switch_pokemon_max_dmg >= 100 and switch_pokemon_tanking_capacity < 45:
                print("choose switch (7) : ", switch_pokemon.get_name())
                switch_pokemon_should_be_used = True

            if switch_pokemon_should_be_used:
                # TODO send command for switch
                #print("I choose this switch : ", switch_pokemon.get_name())
                print("Declaring a well calculated switch : ", switch)
                await self.switch(switch_pokemon.get_name(),1)
                return

        # TODO Send a default move
        print("Using Default Move")
        possible_default_moves=pokemon1.get_possible_moves()
        print("Default moves retrieved")
        if len(possible_default_moves) != 0:
            default_command_to_send = possible_default_moves[0].get_name()
            print("Declaring a default move")
            await self.move(default_command_to_send,1)
            return
        else:
            print("Declaring a default switch")
            await self.make_switch()
            return



    @utils.require_client
    async def make_switch(self, client=None,
        delay=0, lifespan=math.inf):
        """
        Sends a command that performs a random switch.
        """
        possible_switchs = self.own_team.get_possible_pokemon_switch()

        if len(possible_switchs) == 0:
            print("Erreur : aucun switch possible")
        else:
            randomly_generated_switch_id = random.randint(0,len(possible_switchs)-1)
            switch_id = possible_switchs[randomly_generated_switch_id]

            await self.switch(switch_id,1)

    @utils.require_client
    async def undo(self, client=None, delay=0, lifespan=math.inf):
        """
        |coro|
        
        Uses the specified client or the object's client attribute to undo their
        last move or switch. The player must be on of the players in the battle
        for this to work.
        """
        await self.client.use_comand(self.id, 'undo',
            delay=delay, lifespan=lifespan)

class_map = {
    'chat': Room,
    'battle': Battle
}