# -*- coding: utf-8 -*-
"""
An example client that challenges a player to 
a random battle when PM'd, or accepts any
random battle challenge.
"""
import showdown
import logging
import asyncio
from pprint import pprint

logging.basicConfig(level=logging.INFO)
with open('data/login.txt', 'rt') as f,\
     open('data/mono-ghost.txt', 'rt') as team:
    ghost_team = team.read()
    username, password = f.read().strip().splitlines()
    print("My name : ", username)
    print("My pwd : ", password)

class ChallengeClient(showdown.Client):
    battle_current_turn = 1 # current turn

    async def on_private_message(self, pm):
        if pm.recipient == self:
            await self.cancel_challenge()
            await pm.author.challenge('', 'gen7randombattle')

    async def on_challenge_update(self, challenge_data):
        incoming = challenge_data.get('challengesFrom', {})
        for user, tier in incoming.items():
            if 'random' in tier:
                await self.accept_challenge(user, 'null')
            if 'gen7monotype' in tier:
                await self.accept_challenge(user, ghost_team)

    async def on_room_init(self, room_obj):
        if room_obj.id.startswith('battle-'):
            await asyncio.sleep(3)
            
            battle_continue = True
            while battle_continue:
                await asyncio.sleep(1)
                if len(self.rooms) == 1:
                    for key in self.rooms:
                        current_battle = self.rooms.get(key)
                        if self.battle_current_turn == current_battle.current_turn:
                            self.battle_current_turn += 1

                            # Do the move
                            await room_obj.move(1,1)

                            if self.battle_current_turn >= 10:
                                battle_continue = False

            # Choisir un switch
            #await room_obj.switch(2,2)

            # Forfeit
            await room_obj.say('Oh my, look at the time! Gotta go, gg.')
            await room_obj.forfeit()
            await room_obj.leave()

ChallengeClient(name=username, password=password).start()

