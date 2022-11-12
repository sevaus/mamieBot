import datetime
import utils
import configs 
import community_dragon as cdragon
import requests
import numpy as np
from PIL import Image

# TODO: infer role and add vs ennemy?
#@utils.add_time
def got_in_a_game(summoner_rank, game):
    """Creates the message displayed when a summoner gets in a game."""

    # Retrieve game information 
    summoner_id = summoner_rank["summonerId"]
    for participant in game["participants"]:
        if participant["summonerId"] == summoner_id:
            sum1_id = participant["spell1Id"]
            sum2_id = participant["spell2Id"]
            champ_id = participant["championId"]
            summoner_name = participant["summonerName"]
    game_start_timer = utils.convert_epoch_to_datetime(game["gameStartTime"]/1000).strftime(configs.DMYHMS_FORMAT) # This take a few minutes to be updated by Riot - defaults to 1st Jan 1970
    sum1 = cdragon.SUMMONER_SPELLS_ID_TO_PATH_AND_NAME[sum1_id]
    sum2 = cdragon.SUMMONER_SPELLS_ID_TO_PATH_AND_NAME[sum2_id]
    champ = cdragon.CHAMPION_ID_TO_PATH_AND_NAME[champ_id]

    # Create the embed
    title =  f"{summoner_name} just got into a game!"
    description = "They are playing {champ} with {sum1} and {sum2}.".format(champ = champ["name"], sum1 = sum1["name"], sum2 = sum2["name"])
    colour = configs.ORANGE
    embed = {"title": title, "description": description, "color": colour}

    # The image is the champion's icon | the summoner spells
    sum1_icon = cdragon.get_content_at_path(sum1["path"])
    sum2_icon = cdragon.get_content_at_path(sum2["path"])
    sums = utils.stack_images(sum1_icon, sum2_icon, how = "vertically")
    champ_icon = cdragon.get_content_at_path(champ["path"])
    image = utils.stack_images(champ_icon, sums, how = "horizontally")

    # The fields are rank | type of game (demotion, promotion, placement or normal) | TODO: good ban (True/False)
    rank = utils.format_rank(summoner_rank)
    game_type = utils.get_ingame_rank_message(summoner_rank)
    field_rank = {"name": "Rank", "value": rank, "inline": True}
    field_game_type = {"name": "Game type", "value": game_type, "inline": True}
    field_good_ban = {"name": "Good ban", "value": False, "inline": True}
    fields = [field_rank, field_game_type]

    # The footer is the timestamp
    ts = datetime.datetime.now().strftime(configs.DMYHMS_FORMAT)

    # Create the message log
    message_log = {"embed": embed, "image": image, "fields": fields, "footer": ts, "discord": False}
    print(ts + ": " + title + " " + description)
    return message_log

#@utils.add_time
def got_out_of_game(game_info, past_rank, new_rank):
    """Creates the message displayed when a summoner gets out of a game."""

    # Retrieve game information 
    summoner_id = past_rank["summonerId"]    
    participants = game_info["participants"]
    game_length = game_info["gameDuration"] # In seconds
    remake = False
    for participant in participants:
        remake = remake or participant["teamEarlySurrendered"] # teamEarlySurrendered will only be True for one of the two teams
        if participant["summonerId"] == summoner_id:
            sum1 = cdragon.SUMMONER_SPELLS_ID_TO_PATH_AND_NAME[participant["summoner1Id"]]
            sum2 = cdragon.SUMMONER_SPELLS_ID_TO_PATH_AND_NAME[participant["summoner2Id"]]
            champ = cdragon.CHAMPION_ID_TO_PATH_AND_NAME[participant["championId"]]
            summoner_name = participant["summonerName"]
            win = participant["win"]
            kills = participant["kills"]
            deaths = participant["deaths"]
            assists = participant["assists"]
            played_role = configs.POSITION_TO_ROLE[participant["teamPosition"]] # Use this over "individualPosition" or "lane"
            number_of_pings = participant["basicPings"]
            pentakills = participant["pentaKills"]
            cs = participant["totalMinionsKilled"]
            vision_score = participant["visionScore"]
            kp = int(round(100*participant["challenges"].get("killParticipation", 1), 0)) # killParticipation won't be present if the team scored 0 kills
            team_id = participant["teamId"]            
            kda = f"{kills}/{deaths}/{assists}"
            kda_num = round((kills + assists)/deaths, 2) if deaths != 0 else 69420            
            cspm = round(60*cs/(game_length - 90), 1) # 1mn30 of delay    
    winning_team_role_to_participant = {configs.POSITION_TO_ROLE[participant["teamPosition"]]: participant for participant in participants if participant["win"]}
    losing_team_role_to_participant = {configs.POSITION_TO_ROLE[participant["teamPosition"]]: participant for participant in participants if not participant["win"]}
    winning_team_role_to_summoner = {configs.POSITION_TO_ROLE[participant["teamPosition"]]: participant["summonerName"] for participant in participants if participant["win"]}
    losing_team_role_to_summoner = {configs.POSITION_TO_ROLE[participant["teamPosition"]]: participant["summonerName"] for participant in participants if not participant["win"]}

    # Find opponent 
    for ennemy_role in (losing_team_role_to_participant if win else winning_team_role_to_participant):
        if ennemy_role == played_role:
            participant = (losing_team_role_to_participant if win else winning_team_role_to_participant)[ennemy_role]
            ennemy_sum1 = cdragon.SUMMONER_SPELLS_ID_TO_PATH_AND_NAME[participant["summoner1Id"]]
            ennemy_sum2 = cdragon.SUMMONER_SPELLS_ID_TO_PATH_AND_NAME[participant["summoner2Id"]]
            ennemy_champ = cdragon.CHAMPION_ID_TO_PATH_AND_NAME[participant["championId"]]

    # Find if there was any role difference (defined as a 150 gold per minute gap)
    max_gold_per_minute_diff = 0
    for role in winning_team_role_to_participant:
        winning_gold_per_minute = winning_team_role_to_participant[role]["challenges"]["goldPerMinute"]
        losing_gold_per_minute = losing_team_role_to_participant[role]["challenges"]["goldPerMinute"]
        if (winning_gold_per_minute - losing_gold_per_minute) > max_gold_per_minute_diff:
            max_gold_per_minute_diff = winning_team_role_to_participant[role]["challenges"]["goldPerMinute"] - losing_team_role_to_participant[role]["challenges"]["goldPerMinute"]
            role_diff = role
            max_gold_diff = winning_team_role_to_participant[role]["goldEarned"] - losing_team_role_to_participant[role]["goldEarned"]

    # Create the embed
    title =  f"{summoner_name} just got out of a {utils.convert_seconds_to_hms(game_length)} game on {{champ}} {played_role}!".format(champ = champ["name"])
    if remake:
        remake_because_of_them = (new_rank["losses"] == past_rank["losses"] + 1)
        description = "The game was remade because of them." if  remake_because_of_them else "The game was remade."
    else:
        comparison = utils.compare(past_rank, new_rank)
        description = comparison["description"]
        if max_gold_per_minute_diff > 150:
            diff = f"The game was a {role_diff} difference ({max_gold_diff} gold difference in {utils.convert_seconds_to_hms(game_length)})."
            description = f"{description}\n{diff}"
    colour = configs.BLACK if remake else (configs.GREEN if win else configs.RED) 
    embed = {"title": title, "description": description, "color": colour}   

    # The image is the champion's icon | the summoner spells # TODO: vs ennemy champion's icon | ennemy summoner spells
    sum1_icon = cdragon.get_content_at_path(sum1["path"])
    sum2_icon = cdragon.get_content_at_path(sum2["path"])
    sums = utils.stack_images(sum1_icon, sum2_icon, how = "vertically")
    champ_icon = cdragon.get_content_at_path(champ["path"])
    image1 = utils.stack_images(champ_icon, sums, how = "horizontally")
    ennemy_sum1_icon = cdragon.get_content_at_path(ennemy_sum1["path"])
    ennemy_sum2_icon = cdragon.get_content_at_path(ennemy_sum2["path"])
    ennemy_sums = utils.stack_images(ennemy_sum1_icon, ennemy_sum2_icon, how = "vertically")
    ennemy_champ_icon = cdragon.get_content_at_path(ennemy_champ["path"])
    image2 = utils.stack_images(ennemy_champ_icon, ennemy_sums, how = "horizontally")
    image = utils.stack_images(image1, image2, how = "horizontally")

    # The fields are rank | kda & kp | cs/min & vision score
    rank = utils.format_rank(new_rank)
    field_rank = {"name": "Rank", "value": rank, "inline": True}
    field_kda_kp = {"name": "KDA & KP", "value": f"{kda} ({kda_num}) & {kp}%", "inline": True}
    field_csm_and_vision_score = {"name": "CS & vision score", "value": f"{cs} ({cspm}) & {vision_score}", "inline": True}
    fields = [field_rank, field_kda_kp, field_csm_and_vision_score]        

    # The footer is the timestamp
    ts = datetime.datetime.now().strftime(configs.DMYHMS_FORMAT)

    # Create the message log
    message_log = {"embed": embed, "image": image, "fields": fields, "footer": ts, "discord": False}
    print(ts + ": " + title + " " + description)
    return message_log

#@utils.add_time
def dodge_info(summoner_name, list_of_dodges, extra_message = None):
    """Creates the message displayed when a summoner dodges a game."""

    # Get the timestamp at whitch they can requeue next
    number_of_dodges = len(list_of_dodges)
    if number_of_dodges == 1:
        ts = list_of_dodges[0]
        next = ts + datetime.timedelta(seconds = 6*60)
    elif number_of_dodges == 2:
        tss = list_of_dodges[1]
        next = tss + datetime.timedelta(seconds = 30*60)
    elif number_of_dodges == 3:
        tsss = list_of_dodges[0]
        next = tsss + datetime.timedelta(seconds = 12*3600)
    else:
        next = configs.DEBUG_MESSAGE

    # Create the embed
    title = f"{summoner_name} just dodged a game!"
    description = f"They can requeue at {next}."
    if extra_message is not None:
        description = f"{extra_message}\n{description}"
    colour = configs.LIGHT_GREY
    embed = {"title": title, "description": description, "color": colour}    

    # The footer is the timestamp
    ts = datetime.datetime.now().strftime(configs.DMYHMS_FORMAT)

    # Create the message log
    message_log = {"embed": embed, "footer": ts, "discord": False}
    print(ts + ": " + title + " " + description)
    return message_log        


 