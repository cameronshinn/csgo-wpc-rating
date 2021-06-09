# Adapted from SocksPls/hltv-api https://github.com/SocksPls/hltv-api/blob/master/main.py

import json
import requests
import sys
import traceback
from bs4 import BeautifulSoup
from time import sleep

WEBSITE = "https://www.hltv.org"

def get_parsed_page(url, sleep_time=1):
    # This fixes a blocked by cloudflare error i've encountered
    headers = {
        "referer": "https://www.hltv.org/stats",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    sleep(sleep_time)  # Sleep to prevent getting rate limited
    return BeautifulSoup(requests.get(url, headers=headers).text, "lxml")

def get_demo_link(match_page_url):
    match_page = get_parsed_page(match_page_url)
    demo_url = WEBSITE + match_page.find("a", attrs={"class": "flexbox left-right-padding"})["href"]
    return demo_url

def get_stats(game_page_url):
    game = get_parsed_page(game_page_url)
    match_page_url = WEBSITE + game.find("a", attrs={"class": "match-page-link button"})["href"]
    demo_link = get_demo_link(match_page_url)

    all_stats = {}

    for team_stats in game.find_all(attrs={"class": "stats-table"}):
        header_row = True
        for player in team_stats.find_all("tr"):
            if header_row:  # first <tr> isn't for a player
                team_name = player.find("th", attrs={"class": "st-teamname text-ellipsis"}).text
                all_stats[team_name] = {}
                header_row = False
                continue

            name = player.find("td", {"class": "st-player"}).text.strip()
            kills = player.find("td", {"class": "st-kills"}).text.split()[0]  # Second value in parentheses is headshots
            assists = player.find("td", {"class": "st-assists"}).text.split()[0]  # Second value in parentheses is flash assists
            deaths = player.find("td", {"class": "st-deaths"}).text
            kd_ratio = player.find("td", {"class": "st-kdratio"}).text.replace('%', '')
            adr = player.find("td", {"class": "st-adr"}).text
            rating = player.find("td", {"class": "st-rating"}).text

            for suffix in [" won", "", " lost"]:
                kd_diff_found = player.find("td", {"class": "st-kddiff" + suffix})
                if kd_diff_found:
                    kd_diff = kd_diff_found.text

                fk_diff_found = player.find("td", {"class": "st-fkdiff" + suffix})
                if fk_diff_found:
                    fk_diff = fk_diff_found.text

            all_stats[team_name][name] = {
                "kills": int(kills),
                "assists": int(assists),
                "deaths": int(deaths),
                "kd_ratio": float(kd_ratio),
                "kd_diff": int(kd_diff),
                "adr": float(adr),
                "fk_diff": int(fk_diff),
                "hltv_2_rating": float(rating)
            }

    num_players = len(list(all_stats.values())[0]) + len(list(all_stats.values())[1])

    if num_players != 10:
        raise ValueError(f"Found {num_players} players for match stats")

    return all_stats, demo_link

def get_results_by_date(start_date, end_date):
    # Dates like yyyy-mm-dd  (iso)
    results_dict = {}
    offset = 0
    count = 0
    # Loop through all stats pages
    while True:
        url = "https://www.hltv.org/stats/matches?startDate="+start_date+"&endDate="+end_date+"&offset="+str(offset)

        results = get_parsed_page(url)

        # Total amount of results of the query
        amount = int(results.find("span", attrs={"class": "pagination-data"}).text.split("of")[1].strip())

        # All rows (<tr>s) of the match table
        pastresults = results.find("tbody").find_all("tr")

        # Parse each <tr> element to a result dictionary
        for result in pastresults:
            try:
                team_cols = result.find_all("td", {"class": "team-col"})
                t1 = team_cols[0].find("a").text
                t2 = team_cols[1].find("a").text
                t1_score = int(team_cols[0].find_all(attrs={"class": "score"})[0].text.strip()[1:-1])
                t2_score = int(team_cols[1].find_all(attrs={"class": "score"})[0].text.strip()[1:-1])
                map = result.find(attrs={"class": "statsDetail"}).find(attrs={"class": "dynamic-map-name-full"}).text
                event = result.find(attrs={"class": "event-col"}).text
                date = result.find(attrs={"class": "date-col"}).find("a").find("div").text
                print(f"({count+1}/{amount}) Parsing result {t1} vs. {t2}")

                # Get player match stats
                game_page_url = WEBSITE + result.find(attrs={"class": "date-col"}).find("a", href=True)["href"]
                all_stats, demo_link = get_stats(game_page_url)

                result_dict = {
                    "team1": t1,
                    "team2": t2,
                    "team1score": t1_score,
                    "team2score": t2_score,
                    "team1stats": all_stats[t1],
                    "team2stats": all_stats[t2],
                    "date": date,
                    "map": map,
                    "event": event,
                    "demo_link": demo_link
                }

            except KeyboardInterrupt:
                raise
            except Exception:
                print(traceback.format_exc())
                print('Skipping...')
                continue

            # Add this pages results to the result list
            results_dict[count] = result_dict
            count += 1

        # Get the next 50 results (next page) or break
        if offset < amount:
            offset += 50
        else:
            break

    return results_dict

if __name__ == '__main__':
    start_date = sys.argv[1]  # '2021-05-03'
    end_date = sys.argv[2]  # '2021-05-04'
    results = get_results_by_date(start_date, end_date)

    with open(f"results_{start_date}_to_{end_date}.json", "w+") as f:
        json.dump(results, f)
