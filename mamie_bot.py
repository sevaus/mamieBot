import alerts
import configs
from dodge import Dodge
from game import Game
from change import Change
from summoner import Summoner
import utils

import json
import traceback


class mamieBot():

    def __init__(self, queue_ids = ("420", "1100")):
        self.queue_ids = queue_ids
        self.message_logs = []

        # Load the summoners from the local puuid list
        with open(configs.PUUID_PATH, encoding = "utf-8") as json_data:
            data = json.load(json_data)
            self.puuids = set(data.keys())         
        self.summoners = {puuid: Summoner(puuid = puuid) for puuid in self.puuids} # {puuid: summoner} dictionary
        self.summoners_to_dodges = {puuid: Dodge(summoner = self.summoners[puuid]) for puuid in self.puuids}
        self.summoners_to_change = {puuid: Change(self.summoners[puuid], self.queue_ids) for puuid in self.puuids}
        self.summoners_to_games = {}
        self.summoners_about_to_decay = {} # {puuid: [last_alert]} dictionary
        self.game_ids_handled = [] # We keep track of the games that have ended and been handled to avoid duplicates


    # TODO: decay + decayed
    def update(self):
        """Sends new message logs."""

        # Update the summoners list
        with open(configs.PUUID_PATH, encoding = "utf-8") as json_data:
            data = json.load(json_data)
            past_puuids, self.puuids = self.puuids, set(data.keys())        
        additions = [puuid for puuid in self.puuids if puuid not in past_puuids]
        deletions = [puuid for puuid in past_puuids if puuid not in self.puuids]
        if additions:
            self.summoners.update({puuid: Summoner(puuid = puuid) for puuid in additions})
            self.summoners_to_dodges.update({puuid: Dodge(self.summoners[puuid]) for puuid in additions})
            self.summoners_to_change.update({puuid: Change(self.summoners[puuid], self.queue_ids) for puuid in additions})
        if deletions:
            for attr in ["summoners", "summoners_to_dodges", "summoners_to_games", "summoners_to_change", "summoners_about_to_decay"]:
                setattr(self, attr, {puuid: value for (puuid, value) in getattr(self, attr).items() if puuid not in deletions})

        # Run for each summoner
        for (puuid, summoner) in self.summoners.items():
            try:
                # If the summoner is not in an active game, we check for decay, dodge or new game
                if self.summoners_to_games.get(puuid, []) == []:                    
                    # Compare past and new entries
                    past_entries = self.summoners_to_change[puuid].entries
                    changes = self.summoners_to_change[puuid].check_for_change() # TODO: refactor class Change() to be DecayChecker() and have it check for inactivity - add the dodge check to Dodge() class

                    for (queue_id, change) in changes.items():
                            
                            # TEMPPPP
                            if queue_id == "1100" and puuid != "rrwLNzHXrKOZMWs4f601NEhMy54SQZ2iZa2SEbQXkxGzyOUg9cuyEmKIJXaTQLEUgZP_qS_TJl0l1w":
                                continue


                            past_entry = past_entries[queue_id]

                            # Scout for summoners that just dodged a game
                            if change == "DODGE":
                                self.summoners_to_dodges[puuid].add_a_dodge(utils.now())
                                message_log = self.summoners_to_dodges[puuid].dodge_message_log(past_entry)
                                self.message_logs.append(message_log)

                                # Update the counter for lp_update.py
                                with open(configs.LP_UPDATE_PATH, encoding = "utf-8") as json_data:
                                    summary = json.load(json_data)
                                past = summary.get(puuid, {})
                                past_dodges = past.get("dodges", 0)                        
                                past.update({"dodges": past_dodges + 1})
                                summary[puuid] = past
                                with open(configs.LP_UPDATE_PATH, "w", encoding = "utf-8") as json_data:
                                    json.dump(summary, json_data)

                            # Finally, scout for summoners that just got in game
                            else:
                                game_data = summoner.get_current_game(queue_id = queue_id)
                                if game_data is not None:
                                    game = Game(game_data, summoner)
                                    if game.game_id not in self.game_ids_handled: # The call summoner.get_current_game() lingers after the game ends so we check if it's a different game
                                        tft = queue_id in configs.TFT_QUEUE_IDS
                                        message_log = game.in_game_message_log() if not tft else game.tft_in_game_message_log()
                                        self.message_logs.append(message_log)
                                        self.summoners_to_games[puuid] = [game]

                # Otherwise, we check if the game has ended (special case for TFT games as a summoner can get into another one while the previous one hasn't ended)
                else:
                    games = self.summoners_to_games[puuid]
                    for game in games:
                        tft = game.tft
                        if game.has_ended():
                            message_log = game.out_of_game_message_log() if not tft else game.tft_out_of_game_message_log()
                            self.message_logs.append(message_log)
                            self.game_ids_handled.append(game.game_id)
                        elif tft:
                            for queue_id in self.queue_ids:
                                game_data = summoner.get_current_game(queue_id = queue_id)
                                if game_data is not None:
                                    game = Game(game_data, summoner)
                                    if (game.game_id not in self.game_ids_handled) and (game.game_id not in [game.game_id for game in games]):
                                        message_log = game.tft_in_game_message_log()
                                        self.message_logs.append(message_log)
                                        games.append(game)
                    self.summoners_to_games[puuid] = [game for game in games if game.game_id not in self.game_ids_handled]

                # Flush out old dodges
                self.summoners_to_dodges[puuid].refresh_dodge_list()

            except Exception as e:
                field_exception = {"name": "Exception", "value": (str(e))[:1000], "inline": True}
                fields_traceback = {"name": "Description", "value": (traceback.format_exc())[:1000], "inline": True}
                fields = [field_exception, fields_traceback]                                    
                embed = {"title": f"mamie_bot.py failed for summoner {summoner.riot_name}", "fields": fields, "color": configs.YELLOW}
                ts = utils.now().strftime(configs.DMYHMS_FORMAT)
                message_log = {"embed": embed, "footer": ts, "done_with": False, "bugged": True}
                self.message_logs.append(message_log)

        # Empty the messages already handled
        self.message_logs = [message_log for message_log in self.message_logs if not message_log["done_with"]]