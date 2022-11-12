import requests
import utils
import configs

# TODO: try except the r.status_code != 200, handle rate limiting

def get_summoner(puuid = None, summoner_name = None, account_id = None, summoner_id = None):
    """Returns a dictionary {id, accountId, puuid, name, profileIconId, revisionDate, summonerLevel}."""
    if puuid is not None:
        r = requests.get(url = configs.SUMMONER_BY_PUUID.format(puuid = puuid))
        if r.status_code == 200:
            summoner = r.json()
            return summoner
        else:
            print(f"Error {r.status_code} while fetching get_summoner for {puuid}")

    elif summoner_name is not None:
        r  = requests.get(url = configs.SUMMONER_BY_NAME.format(name = summoner_name))
        if r.status_code == 200:
            summoner = r.json()
            return summoner
        else:
            print(f"Error {r.status_code} while fetching get_summoner")

    elif account_id is not None:
        r  = requests.get(url = configs.SUMMONER_BY_ACCOUNT_ID.format(account_id = account_id))
        if r.status_code == 200:
            summoner = r.json()
            return summoner
        else:
            print(f"Error {r.status_code} while fetching get_summoner")            
    elif summoner_id is not None:
        r  = requests.get(url = configs.SUMMONER_BY_SUMMONER_ID.format(summoner_id = summoner_id))
        if r.status_code == 200:
            summoner = r.json()
            return summoner
        else:
            print(f"Error {r.status_code} while fetching get_summoner")            
    else:
        return None


def get_summoner_ranks(summoner_id):
    """Returns a dictionary of dictionaries {queue_type: dictionary about this queue_type}."""
    r = requests.get(url = configs.RANK_BY_SUMMONER_ID.format(summoner_id = summoner_id))
    if r.status_code == 200:
        queue_list = r.json() # This is a list (each entry corresponds to a queue)
        ranks = {}
        for queue in queue_list:
            queue_type = queue["queueType"]
            ranks[queue_type] = queue
        return ranks
    else:
        print(f"Error {r.status_code} while fetching summoner_ranks") 
        return None
        

def get_played_games(puuid, queue_id, start):
    """Return a list of match_ids corresponding to the (finished) games played by puuid between start and now (the beginning of the list is the most recent game)."""
    epoch_start = utils.convert_datetime_to_epoch(start)
    r = requests.get(url = configs.MATCHES_BY_PUUID.format(puuid = puuid, epoch_start = epoch_start, queue_id = queue_id))
    if r.status_code == 200:
        games = r.json()
        return games
    else:
        print(f"Error {r.status_code} while fetching get_played_games") 
        return None


def get_ended_game_info(match_id):
    """Returns information about the ended game - the fields are detailled at https://developer.riotgames.com/apis#match-v5/GET_getMatch."""
    r = requests.get(url = configs.MATCHES_BY_MATCH_ID.format(match_id = match_id))
    if r.status_code == 200:
        game = r.json()
        return game
    else: 
        print(f"Error {r.status_code} while fetching get_ended_game_info") 
        return None


def get_current_game(summoner_id):
    """Returns information about the current game."""
    r = requests.get(url = configs.CURRENT_MATCH_BY_SUMMONER_ID.format(summoner_id = summoner_id))
    if r.status_code == 200:
        game = r.json()  
        return game
    # Avoid printing 404 errors (which usually indicate that the summoner is not in game)
    elif r.status_code != 404:
        print(f"Error {r.status_code} while fetching get_current_game") 
        return None