# -*- coding: utf-8 -*-
"""Module for Room and Battle objects"""

import math
import time
from collections import deque
from . import utils, user
import random
import re
from .teams import *

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
            active_pokemon_moves = re.findall(r"moves.*canDynamax.*maxMoves.*}}", socket_input)

            # dissociate normal moves info from maxmoves info
            categories = re.findall(r"\[.*?\]", active_pokemon_moves[0])

            # Normal moves
            normal_moves = re.findall(r"{.*?}", categories[0])
            active_pokemon_moves = []
            for smogon_id, normal_move in enumerate(normal_moves):
                move_informations = normal_move.split(",")

                name = move_informations[1].split(":")[-1].replace("\\\"","").strip()
                current_pp = move_informations[2].split(":")[-1].strip()
                max_pp = move_informations[3].split(":")[-1].strip()
                target = move_informations[4].split(":")[-1].replace("\\\"","").strip()
                disabled = True if move_informations[5].split(":")[-1].replace("}","").strip() == "true"  else False

                new_move = Move(name, smogon_id, target, disabled, current_pp, max_pp)
                #new_move.self_print()
                active_pokemon_moves.append(new_move)

            # Team construction
            side = re.findall(r"name.*pokemon.*\[.*}\]", socket_input)[0]
            pokemons = re.findall(r"{.*?}.*?}", side)

            self.own_team = Team("p2")

            # arrays containing the moves and the pokemons names that have to be asked to smogon
            moves_to_ask_smogon = []
            pokemons_to_ask_smogon = []
                    
            for smogon_id,pokemon in enumerate(pokemons):
                stats = re.split(r",", pokemon)

                hp_stats = stats[-15].split(r":")[-1].replace("\\\"","").strip().split(r"/")
                activity = stats[-14].split(r":")[-1].strip()

                name = stats[1].split(r":")[-1].replace("\\\"","").strip()
                level = stats[2].replace("\\\"","").replace("L","").strip()
                current_hp = hp_stats[0]
                max_hp = hp_stats[1]
                active = True if activity == "true" else False
                attack = stats[-13].split(r":")[-1].strip()
                defense = stats[-12].split(r":")[-1].strip()
                spAttack = stats[-11].split(r":")[-1].strip()
                spDefense = stats[-10].split(r":")[-1].strip()
                speed = stats[-9].split(r":")[-1].replace("}","").strip()
                move1 = stats[-8].split(r":")[-1].replace("\\\"","").replace("[","").strip()
                move2 = stats[-7].replace("\\\"","").strip()
                move3 = stats[-6].replace("\\\"","").strip()
                move4 = stats[-5].replace("\\\"","").replace("]","").strip()
                ability = stats[-1].split(r":")[-1].replace("\\\"","").replace("}","").strip()
                base_ability = stats[-4].split(r":")[-1].replace("\\\"","").replace("}","").strip()
                item = stats[-3].split(r":")[-1].replace("\\\"","").replace("}","").strip()

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
                    new_pokemon.update_moves(active_pokemon_moves)
                self.own_team.add_pokemon(new_pokemon)
        
            # TODO METTRE UN COUNT DES ATTAQUES / MOVES A RECUP POUR SLEEP LE BOT LE TEMPS DE LES RECUP

            #print("collection moves : ", len(self.moves_name_collection))
            #print("collection pokemons : ", len(self.pokemon_names_collection))

            # Send smogon the commands to retrieve the moves and pokemons data
            for pokemon in pokemons_to_ask_smogon:
                await self.get_M_or_P_data(pokemon)
                self.pokemon_names_collection.append(pokemon)
            for move in moves_to_ask_smogon:
                await self.get_M_or_P_data(move)
                self.moves_name_collection.append(move)

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
        pokemon_name = re.findall(r">.*?<", pokemon_link[-1])[0].replace(">","").replace("<","").replace(" ","").strip().lower()

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
        move_name = re.findall(r">.*?<", move_link[-1])[0].replace(">","").replace("<","").replace(" ","").strip().lower()

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
        
        new_move = Move(move_name)
        new_move.update_smogon_data(move_type, move_category, move_power, move_accuracy, move_description)

        if new_move not in self.moves_collection:
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
    async def make_decicion(self, client=None,
        delay=0, lifespan=math.inf):
        """
        Selects a random move among the moves that can be executed.
        """
        print("Making a decision...")

        #self.own_team.print_active_pokemon()

        possible_moves = self.own_team.get_active_pokemon_possible_moves()

        #for move in possible_moves:
        #    print("dat id : ", move.get_smogon_id())

        # 1/4 chance of switching (switch_or_move=0) and 3/4 chance of moving (switch_or_move=1,2 or 3)
        switch_or_move = random.randint(1,4)
        if switch_or_move and len(possible_moves) > 0:
            # will be used more effectively than just a randomint when the intelligent logic will be called
            randomly_generated_move_id = random.randint(1,len(possible_moves))
            move_id = possible_moves[randomly_generated_move_id-1].get_smogon_id() + 1
            await self.move(move_id,1)
        else:
            switch_id = random.randint(2,6)
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