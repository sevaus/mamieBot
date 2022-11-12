####################
# MISC
####################

POSITION_TO_ROLE = {"TOP": "Top", "JUNGLE": "Jungle", "MIDDLE": "Mid", "BOTTOM": "Bot", "UTILITY": "Support"} # TODO: add None (ie when the api doesn't know where the player played)
BEGINNING_OF_SEASON = "2022-01-07"
APEX_TIERS = ["MASTER", "GRANDMASTER", "CHALLENGER"]
DEBUG_MESSAGE = "UNKNOWN"

####################
# API KEY
####################

API_KEY = None # Regenerated at https://developer.riotgames.com/


####################
# DISCORD AND CLIENT
####################

DISCORD_CHANNEL_ID = None # Integer!
DISCORD_TOKEN = None
SERVER_PORT = "12345"
SERVER_HOST = "localhost"
GREEN_CHECKMARK = ":white_check_mark:"
RED_CROSS = ":x:"
WHITE_SQUARE = ":white_medium_square:"
BLACK_CIRCLE = ":black_circle:"

####################
# MISC
####################

DMYHMS_FORMAT = "%d/%m/%Y, %H:%M:%S"

CACHE_PATH = "test.json"

PUUID_LIST = None

QUEUE_TYPE_TO_ID = {"RANKED_SOLO_5x5": "420", "RANKED_FLEX_SR": "440", "DRAFT_5x5": "400", "BLIND_5x5": "430"} # TODO: find real queue_types for 400 and 430
QUEUE_ID_TO_TYPE = {v: k for (k, v) in QUEUE_TYPE_TO_ID.items()}

####################
# COLOURS INT VALUE AND HEX CODE (from https://gist.github.com/thomasbnt/b6f455e2c7d743b796917fa3c205f812)
####################

ORANGE = 15105570 # #E67E22
GREEN = 5763719 # #57F287
RED = 15548997 # #ED4245
YELLOW = 16776960 # #FFFF00
LIGHT_GREY = 12370112 # #BCC0C0
BLACK = 2303786 # #23272A

####################
# API ENTRY POINTS
####################

REGION = "euw1"
BASE_URL = "https://{region}.api.riotgames.com/lol".format(region = REGION)

SUMMONER_BY_PUUID = "{base}/summoner/v4/summoners/by-puuid/{{puuid}}?api_key={key}".format(base = BASE_URL, key = API_KEY)
SUMMONER_BY_NAME = "{base}/summoner/v4/summoners/by-name/{{name}}?api_key={key}".format(base = BASE_URL, key = API_KEY) 
SUMMONER_BY_ACCOUNT_ID = "{base}/summoner/v4/summoners/by-account/{{account_id}}?api_key={key}".format(base = BASE_URL, key = API_KEY)
SUMMONER_BY_SUMMONER_ID = "{base}/summoner/v4/summoners/{{summoner_id}}?api_key={key}".format(base = BASE_URL, key = API_KEY)
RANK_BY_SUMMONER_ID = "{base}/league/v4/entries/by-summoner/{{summoner_id}}?api_key={key}".format(base = BASE_URL, key = API_KEY)

BASE_URL_MATCH = "https://{region}.api.riotgames.com/lol".format(region = "europe")
MATCHES_BY_PUUID = "{base}/match/v5/matches/by-puuid/{{puuid}}/ids?startTime={{epoch_start}}&queue={{queue_id}}&start=0&count=100&api_key={key}".format(base = BASE_URL_MATCH, key = API_KEY) 
MATCHES_BY_MATCH_ID = "{base}/match/v5/matches/{{match_id}}?api_key={key}".format(base = BASE_URL_MATCH, key = API_KEY)
CURRENT_MATCH_BY_SUMMONER_ID = "{base}/spectator/v4/active-games/by-summoner/{{summoner_id}}?api_key={key}".format(base = BASE_URL, key = API_KEY)

####################
# RANKS
####################

TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND", "MASTER", "GRANDMASTER", "CHALLENGER"]
RANKS = ["IV", "III", "II", "I"]