import datetime
import configs
from PIL import Image
from io import BytesIO


def add_time(f):
    """Decorator to add the time to a function f outputting a string."""
    def aux(*args, **kwargs):
        return "{dt}: {s}".format(dt = datetime.datetime.now().strftime(configs.DMYHMS_FORMAT), s = f(*args, **kwargs))
    return aux


def convert_datetime_to_epoch(dt):
    """Converts given datetime to an epoch timestamp in seconds (ie to the number of seconds between 1st Jan 1970 0:00 and dt)."""
    return int(dt.timestamp())


def convert_epoch_to_datetime(epoch):
    """Converts given epoch timestamp in seconds to datetime."""
    return datetime.datetime.fromtimestamp(epoch)


def convert_seconds_to_hms(n):
    """Converts a number of seconds to hour/minute/seconds."""
    h = int(n/3600)
    n -= 3600*h
    m = int(n/60)
    n -= 60*m
    s = n if n > 9 else "0{}".format(n)
    return "{h}:{m}:{s}".format(h = h, m = m, s = s) if h > 0 else "{m}:{s}".format(m = m, s = s)


def format_progress(progress):
    """Formats the progress string (eg "WLNNN") into Discord emojis."""
    res = ""
    for c in progress:
        if c == "W":
            res += configs.GREEN_CHECKMARK
        elif c == "L":
            res += configs.RED_CROSS
        elif c == "N":
            res += configs.WHITE_SQUARE
        elif c == "D":
            res += configs.BLACK_CIRCLE
        else:
            res += c
    return res


def compare(past_rank, new_rank):
    """Compares the two ranks to get the LP lost/gained and to spot dodges."""

    # Get the rank info
    past_tier = past_rank["tier"].capitalize()
    past_division = past_rank["rank"].capitalize()
    past_lp = past_rank["leaguePoints"] 
    past_wins = past_rank["wins"]
    past_losses = past_rank["losses"]

    new_tier = new_rank["tier"].capitalize()
    new_division = new_rank["rank"].capitalize()
    new_lp = new_rank["leaguePoints"]
    new_wins = new_rank["wins"]
    new_losses = new_rank["losses"]    

    was_in_promos = "miniSeries" in past_rank
    if was_in_promos:
        past_progress = past_rank["miniSeries"]["progress"]
    is_in_promos = "miniSeries" in new_rank
    if is_in_promos:
        new_progress = past_rank["miniSeries"]["progress"]   

    was_unranked = past_tier == "UNRANKED"
    if was_unranked:
        past_progress = past_rank["placements"]["progress"]
    is_unranked = new_tier == "UNRANKED"
    if is_unranked:
        new_progress = past_rank["placements"]["progress"]   

    is_inactive = new_rank["inactive"]

    # The result is a dictionary with (at least) the keys "result" and "description"
    res = {"result": None, "description": None}

    # If the number of games stays constant, it is either dodge, decay (it could also be a remake but we handle that in alerts.py's got_out_of_game)
    if (past_wins + past_losses) == (new_wins + new_losses):
        if not ((past_tier == new_tier) and (past_division == new_division) and (past_lp == new_lp)):
            if is_inactive:
                res["result"] = "DECAY"
                res["description"] = f"They decayed from {format_rank(past_rank)} to {format_rank(new_rank)}"
            else:
                res["result"] = "DODGE"
                if was_in_promos:
                    progress = past_progress[:-1] + "D"
                    if is_in_promos:
                        res["description"] = f"They dodged a game in their promotion ({format_progress(progress)})."
                    else:
                        res["description"] = f"They ended their promotion on a dodge ({format_progress(progress)})."
                else:
                    res["description"] = None # None because this is fed in alerts.dodge_info's extra_message

    # Otherwise, we check for wins (including promotions) and losses (including demotions)
    elif (past_wins + past_losses) != (new_wins + new_losses):
        # TODO: find out if a remake counts as a win or loss or None and account for it
        if new_wins == past_wins + 1:
            if past_tier != new_tier:
                res["result"] = "PROMOTION (TIER)"
                progress = past_progress[:-1] + "W" # Don't take the last character as it is an "N" that we now know is a win
                res["description"] = f" They got promoted to {new_tier} {new_lp} LP ({format_progress(progress)})!"
            elif past_division != new_division:
                res["result"] = "PROMOTION (DIVISION)"
                res["description"] = f"They got promoted to {new_division} {new_lp} LP!"
            elif was_in_promos:
                res["result"] = "WIN (SERIES)"
                res["description"] = f"They won a promotion game ({format_progress(new_progress)})!"
            elif was_unranked:
                if is_unranked:
                    res["result"] = "WIN (PLACEMENTS)"
                    res["description"] = f"They won a placement game ({format_progress(new_progress)})!"
                else:
                    res["result"] = "WIN (COMPLETE PLACEMENTS)"
                    progress = past_progress[:-1] + "W"
                    res["description"] = f"They won their last placement game and placed {format_rank(new_rank)} ({format_progress(progress)})!"
            else:
                res["result"] = "WIN"
                res["description"] = f"They won {new_lp - past_lp} LP!"                               
        elif new_losses == past_losses + 1:
            if past_tier != new_tier:
                res["result"] = "DEMOTION (TIER)"
                res["description"] = f"They got demoted to {new_tier} {new_lp} LP."
            elif past_division != new_division:
                res["result"] = "DEMOTION (DIVISION)"
                res["description"] = f"They got demoted to {new_division} {new_lp} LP."
            elif was_in_promos:
                if is_in_promos:
                    res["result"] = "LOSE (SERIES)"
                    res["description"] = f"They lost a promotion game ({format_progress(new_progress)})."
                else:
                    res["result"] = "LOSE (COMPLETE SERIES)"
                    progress = past_progress[:-1] + "L"
                    res["description"] = f"They lost their series ({format_progress(progress)})."
            elif was_unranked:
                if is_unranked:
                    res["result"] = "LOSE (PLACEMENTS)"
                    res["description"] = f"They lost a placement game ({format_progress(new_progress)})."
                else:
                    res["result"] = "LOSE (COMPLETE PLACEMENTS)"
                    progress = past_progress[:-1] + "L"
                    res["description"] = f"They lost their last placement game and placed {format_rank(new_rank)} ({format_progress(progress)})."  
            else:
                res["result"] = "LOSE"
                res["description"] = f"They lost {past_lp - new_lp} LP."

    else:
        res["result"] = configs.DEBUG_MESSAGE
        res["description"] = configs.DEBUG_MESSAGE
        res["debug"] = {"past_rank": past_rank, "new_rank": new_rank}

    return res

def find_index(x, l):
    """Returns the index of the first ocurrence of x in l."""
    for i in range(0, len(l)):
        if l[i] == x:
            return i
    return -1


def get_adjacent_rank(tier, rank, get_next = True):
    """Gets the next/previous possible rank (ie Gold 3 -> Gold 2)."""
    offset = 1 if get_next else -1
    next_tier = configs.TIERS[find_index(tier, configs.TIERS) + offset]
    next_rank = configs.RANKS[find_index(rank, configs.TIERS) + offset]
    return format_rank({"tier": next_tier, "rank": next_rank, "leaguePoints": 1})


def get_ingame_rank_message(summoner_rank):
    """Gets the message regarding rank displayes when a summoner gets in game (demotion, promotion, placement or normal)."""
    tier = summoner_rank["tier"] # eg: Gold
    rank = summoner_rank["rank"] # eg: II
    lp = summoner_rank["leaguePoints"]

    # If they are unranked, display their W/L
    if "placements" in summoner_rank:
        progress = summoner_rank["placements"]["progress"]
        game_type = f"Placements ({format_progress(progress)})"
    else: 
        next_rank = get_adjacent_rank(tier, rank, get_next = True)
        # If they are in series, display their W/L
        if "miniSeries" in summoner_rank:
            progress = summoner_rank["miniSeries"]["progress"]
            game_type = f"Promotion game to {next_rank} ({format_progress(progress)})"
        # If they are about to move a division within a tier (eg diamond 2 to diamond 1)
        elif lp == 100:
            game_type = f"Promotion game to {next_rank}"
        # If they are about to demote (from within a division - demoting from tiers is not handled)
        elif (lp == 0) and (rank != "IV") :
            previous_rank = get_adjacent_rank(tier, rank, get_next = False)
            if tier not in configs.APEX_TIERS:
                game_type = f"Demotion game to {previous_rank}"
            # The demotion in Master tier can only happen after the first three games (source https://support-leagueoflegends.riotgames.com/hc/en-us/articles/4405776545427)
            elif tier == configs.APEX_TIERS[0]:
                fresh_blood = summoner_rank["freshBlood"] # This means that they are still new to the tier and thus benefit from demotion shield
                if fresh_blood:
                    game_type = f"Demotion shielded game - When you first enter Master, you’re protected from losses and cannot be removed for your first three games)"
                else:
                    game_type = f"Demotion game to {previous_rank}"
        else:
            game_type = "Regular"

    return game_type


def format_rank(summoner_rank):
    """Formats the rank (tier + rank + lp)."""
    tier = summoner_rank["tier"] # eg: Gold
    rank = summoner_rank["rank"] # eg: II
    tier_division = tier.capitalize() + ((" " + rank) if tier not in configs.APEX_TIERS else "") # "Master" instead of "Master I"
    lp = summoner_rank["leaguePoints"]
    if tier.upper() == "UNRANKED":
        rank = "Unranked"
    else:
        rank = f"{tier_division} {lp} LP"      
    return rank
                

def stack_images(first_image, second_image, how):
    """Returns an PIL.Image that is the horizontal (left-right) or vertical concatenation (top-bot) of given same-width and same-height images."""

    img1 = first_image if type(first_image) == Image.Image else Image.open(BytesIO(first_image))
    img2 = second_image if type(second_image) == Image.Image else Image.open(BytesIO(second_image))

    if how == "horizontally":
        res = Image.new("RGB", (img1.width + img2.width, img2.height))
        res.paste(img1, (0, 0)) # Pastes img1 at the bottom left
        res.paste(img2, (img1.width, 0)) # Pastes img2 at the bottom right

    elif how == "vertically":
        res = Image.new("RGB", (img2.width, img2.height + img1.height))
        res.paste(img2, (0, img1.height)) # Pastes img1 at the top left
        res.paste(img1, (0, 0)) # Pastes img2 at bottom top left
        
    return res