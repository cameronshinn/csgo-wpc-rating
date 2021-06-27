import numpy as np
import pandas as pd
from typing import List

class Game:
    """
    Match
    Map
    Teams
    Rounds
    """

    def __init__(self, match: str, map: str, teams: list[str], rounds: list[Round]) -> Game:
        pass

class Round:
    """
    Start Tick
    Freeze Time End Tick
    Outcome Decided Tick
    End Tick
    Winner
    End Reason
    Game States
    ?Different Types of Events?
    """
    def __init__(self, **kwargs):
        for name, val in kwargs.items():
            setattr(self, val, name)


class RoundStates(pd.DataFrame):
    @staticmethod
    def _localize_ticks(df: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
        df = df[(df['Tick'] >= start) & (df['Tick'] <= end)]
        df['RoundTick'] = df['Tick'] - start
        return df

    @staticmethod
    def _preprocess_plants(plants: pd.DataFrame) -> pd.DataFrame:
        plants = _localize_ticks(plants)

        for site in ['A', 'B']:
            plants['BombPlanted' + site] = (plants['BombSite'] == site) & (plants['BombAction'] == 'plant')

        plants['AttackerSide'] = plants['BombAction'].map({'plant': 'T', 'defuse': 'CT'})
        plants['VictimSide'] = plants['BombAction'].map({'plant': 'CT', 'defuse': 'T'})
        plants['AttackerSteamId'] = plants['PlayerSteamId']
        plants_features = ['RoundTick', 'BombPlantedA', 'BombPlantedB', 'AttackerSide', 'VictimSide', 'AttackerSteamId']
        plants = plants[plants_features]

        return plants

    # This definitely needs to get tested and checked
    @staticmethod
    def _preprocess_playerframes(playerframes: pd.DataFrame) -> pd.DataFrame:
        playerframes = _localize_ticks(playerframes)

        sides = ['T', 'CT']
        side_frames = []

        for side in sides:
            aggs = ['min', 'max', 'mean']:
            sub_features = ['RoundTick', 'DistToBombsiteA', 'DistToBombsiteA']
            agg_dict = {'DistToBombsiteA': aggs, 'DistToBombsiteA': aggs}

            if side == 'CT':  # Add feature for total number of defuse kits on CT side
                sub_features.append('Has Defuse')
                agg_dict['Has Defuse'] = ['sum']

            reduced = playerframes[(playerframes.Side == side) & playerframes['Is Alive']][sub_features]

            side_frames.append(reduced.groupby('RoundTick', as_index=False).aggregate(agg_dict))

        playerframes = pd.merge(side_frames, how='outer', suffixes=sides, validate='one_to_one')
        # TODO: Also get player distances to teammates (average distance, shortest distance, largest distance)

        return playerframes

    @staticmethod
    def _preprocess_damages(damages: pd.DataFrame) -> pd.DataFrame:
        damages = _localize_ticks(damages)
        damages = damages[damages.Weapon != 'C4']  # Drop C4 damage since those happen when the round ends
        damages = damages[damages_features]
        damages_features = ['RoundTick', 'HpDamageTaken', 'AttackerSteamId', 'AttackerSide', 'VictimSteamId', 'VictimSide']
        group_on = damages_features.remove('HpDamageTaken')
        damages = damages.groupby(group_on, as_index=False).sum()  # Merge damages that happen on the same tick (shotguns, grenades + bullets)

        return damages

    @staticmethod
    def _preprocess_kills(kills: pd.DataFrame) -> pd.DataFrame:
        kills = _localize_ticks(kills)
        kills = kills[kills.Weapon != 'C4']  # Drop C4 kills since those happen when the round ends
        kills_features = ['RoundTick', 'AttackerSteamId', 'AttackerSide', 'VictimSteamId', 'VictimSide']
        kills = kills[kills_features]

        return kills

    @classmethod
    def from_events(cls, round: Round, **event_types) -> RoundStates:
        plants = cls._preprocess_plants(event_types['plants'])
        playerframes = cls._preprocess_playerframes(event_types['playerframes'])
        damages = cls._preprocess_damages(event_types['damages'])
        kills = cls._preprocess_kills(event_types['kills'])

        # Merge kills and damage into the same dataframe
        kills['IsKill'] = True
        merge_on = ['RoundTick', 'AttackerSteamId', 'AttackerSide', 'VictimSteamId', 'VictimSide']
        damages_kills = pd.merge(damages, kills, on=merge_on, validate='one_to_one')
        damages_kills['IsKill'] = damages_kills.IsKill.fillna(False)


"""
1. Convert different sets of events to a single set of game states
2. Predict win probability at each game state
3. Assign responsibility for changing game states and average changes for each player
4. Develop methods for comparing player rating models
    a. Comparing different methods for assigning responsibility
    b. Compare different win probability models
    c. Compare to classic player rating metrics
"""

"""

"""

def main():
    for

if __name__ == '__main__':
    main()
