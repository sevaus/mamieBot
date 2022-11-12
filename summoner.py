import datetime
import utils
import json 
import riot_api
import configs

class Summoner:
    def __init__(self, puuid = None, summoner_name = None, account_id = None, summoner_id = None):
        summoner = riot_api.get_summoner(puuid, summoner_name, account_id, summoner_id)
        if summoner:
            self.puuid = summoner["puuid"]
            self.summoner_name = summoner["name"]
            self.account_id = summoner["accountId"]
            self.summoner_id = summoner["id"]
        else:
            self.puuid = None
            self.summoner_name = None
            self.account_id = None
            self.summoner_id = None


    def get_current_game(self, queue_id = "420"):
        """Returns None if the summoner is not in a queue_id game and otherwise return the current game."""
        current_game = riot_api.get_current_game(self.summoner_id)
        if current_game is not None:
            if str(current_game["gameQueueConfigId"]) == str(queue_id):
                return current_game
        return None


    def get_played_games(self, queue_id = "420", start = datetime.datetime.now() + datetime.timedelta(seconds = -3600*2)):
        """Returns a list of all the games_id played in the selected queue in [start, now]."""
        return riot_api.get_played_games(self.puuid, queue_id, start)

           
    def get_all_ranks(self):
        """Returns a dictionary {"tier": tier, "rank": rank, ...} about this queue_type."""
        return riot_api.get_summoner_ranks(self.summoner_id)
        

    def get_rank(self, queue_id = "420"):
        all_ranks = self.get_all_ranks()
        for queue_type in all_ranks:
            if configs.QUEUE_TYPE_TO_ID[queue_type] == queue_id:
                return all_ranks[queue_type]
        # If we reach this part it means the queue_type we want is not present in all_ranks: the summoner is unranked in that queue_type
        games = self.get_played_games(queue_id, start = datetime.datetime.fromisoformat(configs.BEGINNING_OF_SEASON))
        number_of_wins = 0
        progress = ""
        for game_id in games:
            game_info = riot_api.get_ended_game_info(game_id)["info"]
            for participant in game_info["participants"]:
                if participant["puuid"] == self.puuid:
                    progress += "W" if participant["win"] else "L"
                    number_of_wins += participant["win"]
        progress = f"{progress:N<10}" # Fill right end with "N"'s
        placements = {"target": 10, "wins": number_of_wins, "losses": len(games) - number_of_wins, "progress": progress}
                
        return {"leagueId": None, "queueType": configs.QUEUE_ID_TO_TYPE[queue_id], "tier": "UNRANKED", "rank": "UNRANKED", "summonerId": self.summoner_id, 
                "summonerName": self.summoner_name, "leaguePoints": "UNRANKED", "wins": number_of_wins, "losses": len(games) - number_of_wins, "veteran": None, 
                "inactive": None, "freshBlood": None, "hotStreak": None,"placements": placements}

        
    def cache_rank(self, queue_type = "RANKED_SOLO_5x5", path = configs.CACHE_PATH):
        rank = self.get_all_ranks()[queue_type]
        #useful_rank_info = {"summoner_id": rank["summonerId"], "queue_type": rank["queueType"], "Tier": rank["tier"], "Rank": rank["rank"], "LP": rank["leaguePoints"]}

        # First read the current rank(s)
        with open(path, "r") as f:
            try:
                ranks = json.load(f)
            except:
                ranks = {}

        # Now write the new rank
        with open(path, "w") as f:
            ranks[self.puuid] = rank
            json.dump(ranks, f)


    def get_cached_rank(self, queue_type = "RANKED_SOLO_5x5", path = configs.CACHE_PATH):
        with open(path, "r") as f:
            return json.load(f)
        

def test():
    while(True):
        try:
            summoner = Summoner(summoner_name = "shnks")
            summoner.puuid
            summoner = Summoner(summoner_name = "sevaus")
            summoner.get_rank()            
            game_id = summoner.get_played_games(queue_id = 420)[0]
            current_game = riot_api.get_ended_game_info(game_id)
            p = current_game["info"]["participants"][0]
            dd = current_game["info"]

            summoner.get_all_ranks()
            game = summoner.get_current_game()
            summoner_rank = summoner.get_rank("RANKED_SOLO_5x5")
            ["RANKED_SOLO_5x5"]
            import configs
            import time
            game_start_timer = utils.convert_epoch_to_datetime(game["gameStartTime"]/1000).strftime(configs.DMYHMS_FORMAT)
            
            print(datetime.datetime.now().strftime(configs.DMYHMS_FORMAT), game_start_timer)
            # z = summoner.get_played_games(start = datetime.datetime(2022, 1, 1))[0]
            # game_id = z
            # utils.get_ended_game_info("EUW1_{game_id}".format(game_id = game_id))
            # a = utils.get_ended_game_info(z)
            # b = a["info"]
        except:
            pass
        time.sleep(1)