
from .teams import *
import re

def parse_own_team_state(socket_input):
    # Team construction
    side = re.findall(r"name.*pokemon.*\[.*}\]", socket_input)[0]
    pokemons = re.findall(r"{.*?}.*?}", side)

    new_team = Team("p2")

    for pokemon in pokemons:
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

        '''
        print("\nName : ", name)
        print("Current HP : ", current_hp)
        print("Base HP : ", max_hp)
        print("Active : ", active)
        print("Attack : ", attack)
        print("Defense : ", defense)
        print("SpAttack : ", spAttack)
        print("SpDefense : ", spDefense)
        print("Speed : ", speed)
        print("Move 1 :", move1)
        print("Move 2 : ", move2)
        print("Move 3 : ", move3)
        print("Move 4 : ", move4)
        print("Ability : ", ability)
        print("BaseAbility : ", base_ability)
        print("Item : ", item)
        '''

        new_pokemon = Pokemon(name,level,gender,current_hp,max_hp,
                        attack,defense,spAttack,spDefense,speed,
                        move1,move2,move3,move4,
                        ability,base_ability,item, active)
        new_team.add_pokemon(new_pokemon)

    # Active pokemon information

    active_pokemon_moves = re.findall(r"moves.*canDynamax.*maxMoves.*}}", socket_input)

    # dissociate normal moves info from maxmoves info
    categories = re.findall(r"\[.*?\]", active_pokemon_moves[0])

    # Normal moves
    normal_moves = re.findall(r"{.*?}", categories[0])
    for normal_move in normal_moves:
        move_informations = normal_move.split(",")

        name = move_informations[1].split(":")[-1].replace("\\\"","").strip()
        current_pp = move_informations[2].split(":")[-1].strip()
        max_pp = move_informations[3].split(":")[-1].strip()
        target = move_informations[4].split(":")[-1].replace("\\\"","").strip()
        disabled = True if move_informations[5].split(":")[-1].replace("}","").strip() == "true"  else False

        new_move = Move(name, target, disabled, current_pp, max_pp)

    # Maxmoves
    maxmoves = re.findall(r"{.*?}", categories[1])
    for maxmove in maxmoves:
        maxmove_lines = re.split(r",",maxmove)
        maxmove_name = maxmove_lines[0].split(r":")[-1].replace("\\\"","").strip()
        maxmove_target = maxmove_lines[1].split(r":")[-1].replace("}","").replace("\\\"","").strip()

    return new_team



