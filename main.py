import summoner as Summ
import datetime
import utils
import alerts
import riot_api
import time
import configs

class mamieBot():

    def __init__(self, puuid_list = configs.PUUID_LIST[10:], timeout = 10, queue_type = "RANKED_SOLO_5x5"):
        self.puuid_list = puuid_list
        self.timeout = timeout
        self.queue_type = queue_type
        self.queue_id = configs.QUEUE_TYPE_TO_ID[queue_type]
        self.summoners = set(Summ.Summoner(puuid = puuid) for puuid in puuid_list)
        self.summoners_ingame = {} # {summoner: region_gameId} dictionary
        self.summoners_lastgame = {summoner.puuid: None for summoner in self.summoners} # {summoner: gameId} dictionary
        self.summoners_rank = {summoner.puuid: summoner.get_rank(self.queue_id) for summoner in self.summoners} # {summoner: {leaguePoints: LP, wins: w, losses: l, ...}} dictionary
        self.summoners_that_have_dodged = {} # {summoner: [dodge_timestamps]} dictionary
        self.message_logs = []

    def run(self):
        while(True):
            try:
                for summoner in self.summoners:
                    # Scout for summoners that just dodged a game # TODO: dodged a promo # TODO: or decayed
                    past_rank = self.summoners_rank[summoner.puuid]
                    new_rank = summoner.get_rank(self.queue_id)
                    comparison = utils.compare(past_rank, new_rank)
                    dodge = comparison["result"] == "DODGE"
                    decay = comparison["result"] == "DECAY"
                    extra_message = comparison["description"]
                    if dodge:
                        # If this is their first dodge, build the dodge timestamps list with the dodge's timestamp                
                        if summoner.puuid not in self.summoners_that_have_dodged:
                            self.summoners_that_have_dodged[summoner.puuid] = [datetime.datetime.now()]
                        else:
                        # If they had already dodged (the dodge tiers go down by 1 every 12 hours)
                            self.summoners_that_have_dodged[summoner.puuid].append(datetime.datetime.now())
                            self.summoners_that_have_dodged[summoner.puuid] = [ts for ts in self.summoners_that_have_dodged[summoner.puuid] if (datetime.datetime.now() - ts).seconds <= 12*3600]
                        self.summoners_rank[summoner.puuid] = new_rank
                        message_log = alerts.dodge_info(summoner.summoner_name, self.summoners_that_have_dodged[summoner.puuid], extra_message = extra_message)
                        self.message_logs.append(message_log)

                    # Scout for summoners that just got in game
                    if summoner.puuid not in self.summoners_ingame:
                        current_game = summoner.get_current_game()
                        if current_game is not None:
                            game_id = current_game["gameId"]
                            # The call summoner.get_current_game() lingers after the game ends so we check if it's a different game
                            if game_id != self.summoners_lastgame[summoner.puuid]:
                                self.summoners_lastgame[summoner.puuid] = game_id
                                self.summoners_ingame[summoner.puuid] = f"{configs.REGION.upper()}_{game_id}"
                                message_log = alerts.got_in_a_game(past_rank, current_game)
                                self.message_logs.append(message_log)

                    # Scout for summoners that just got out of a game
                    else:
                        current_game = summoner.get_current_game() 

                        # If they are no longer in game, get the game result
                        if current_game is None:    
                            game_id = self.summoners_ingame[summoner.puuid]
                            ended_game = riot_api.get_ended_game_info(game_id)
                            if ended_game is not None:      
                                game_info = ended_game["info"]                                
                                past_rank = self.summoners_rank[summoner.puuid]
                                new_rank = summoner.get_rank(self.queue_id)
                                self.summoners_rank[summoner.puuid] = new_rank
                                del self.summoners_ingame[summoner.puuid]
                                message_log = alerts.got_out_of_game(game_info, past_rank, new_rank)
                                self.message_logs.append(message_log)

            except Exception as e:
                print("ERROR in main.py", e)
                #self.message_logs.append({"exception": e, "discord": False})
                
            # Empty the messages already printed to Discord
            self.message_logs = [message_log for message_log in self.message_logs if not message_log["discord"]]

            # Timeout
            time.sleep(self.timeout)             
                    

def test():
    m = mamieBot()
    m.run()

    for puuid in puuid_list:
        try:
            Summ.Summoner(puuid = configs.PUUID_LIST[2]).summoner_name
            y= x.puuid
        except:
            print(puuid)

