import requests

####################
# COMMUNITY DRAGON ENTRY POINTS (see https://github.com/communitydragon/docs/blob/master/assets.md)
####################

BASE_URL_CDRAGON = "https://raw.communitydragon.org/latest"
CHAMPION_ICONS = "{base}/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/{{champ_id}}.png".format(base = BASE_URL_CDRAGON)
SUMMONER_SPELLS = "{base}/plugins/rcp-be-lol-game-data/global/default/data/spells/icons2d/{{summoner_name}}".format(base = BASE_URL_CDRAGON)

SUMMONER_SPELLS = f"{BASE_URL_CDRAGON}/plugins/rcp-be-lol-game-data/global/default/v1/summoner-spells.json"
CHAMPIONS = f"{BASE_URL_CDRAGON}/plugins/rcp-be-lol-game-data/global/default/v1/champion-summary.json"

####################
# MAPS
####################

SUMMONER_SPELLS_ID_TO_PATH_AND_NAME = {ss["id"] : {"path": ss["iconPath"].lower(), "name": ss["name"]} for ss in requests.get(url = SUMMONER_SPELLS).json()}
CHAMPION_ID_TO_PATH_AND_NAME = {champ["id"] : {"path": champ["squarePortraitPath"].lower(), "name": champ["name"]} for champ in requests.get(url = CHAMPIONS).json()}

####################
# FUNCTIONS
####################

def get_content_at_path(path):
    """Returns the content at path by sourcing the correct url - see https://github.com/CommunityDragon/Docs/blob/master/assets.md#mapping-paths-from-json-files"""
    real_path = path.split("assets/")[1]
    url = f"{BASE_URL_CDRAGON}/plugins/rcp-be-lol-game-data/global/default/{real_path}"
    r = requests.get(url = url)
    if r.status_code == 200:
        content = r.content
        return content
    else:
        print(f"Error {r.status_code} while fetching get_content_at_path for {path}")

    