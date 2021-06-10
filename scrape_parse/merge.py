import json
import os
import pandas as pd
import sys

CSV_DIR = 'csvs'

CSV_TYPES = ['BombEvents', 'Damages', 'Flashes', 'Frames', 'Kills', 'PlayerFrames', 'Rounds']

def main(results_json, redirects_json):
    with open(results_json) as f:
        results = json.load(f)

    with open(redirects_json) as f:
        redirects = json.load(f)

    for csv_type in CSV_TYPES:
        print(f'\nCreating {csv_type}.csv\n')
        combined_csv = csv_type + '.csv'

        first = True
        num_rows_processed = 0

        for i, result in results.items():
            print(i)
            demo_link = result['demo_link']

            try:
                rar_filename = redirects[demo_link]
            except KeyError:
                continue

            rar_basename = rar_filename.split('.')[0]
            map = result['map'].lower()
            match_id = rar_basename if rar_basename.endswith(map) else f'{rar_basename}-{map}'
            match_data_dir = os.path.join(CSV_DIR, match_id)
            match_csv = os.path.join(match_data_dir, f'{match_id}_{csv_type}.csv')

            if not os.path.exists(match_data_dir) or os.listdir(match_data_dir) == []:
                continue

            # Make sure all types of CSVs are in the directory
            missing = False
            for t in CSV_TYPES:
                dir_has_type = False
                for file in os.listdir(match_data_dir):
                    if file.endswith(t + '.csv'):
                        dir_has_type = True

                if not dir_has_type:
                    missing = True
                    break

            if missing:
                print(match_data_dir, 'is missing CSV types!')
                continue


            # match_df = pd.read_csv(match_csv, index_col=0, dtype={'AttackerSteamId': int, 'VictimSteamId': int})
            match_df = pd.read_csv(match_csv, index_col=0)

            if csv_type == 'Frames':
                match_df['MatchId'] = match_id

                name_conversions = {
                    'Cache': 'de_cache',
                    'Cobblestone': 'de_cbble',
                    'Dust2': 'de_dust2',
                    'Inferno': 'de_inferno',
                    'Mirage': 'de_mirage',
                    'Nuke': 'de_nuke',
                    'Overpass': 'de_overpass',
                    'Train': 'de_train',
                    'Vertigo': 'de_vertigo'
                }

                match_df['MapName'] = name_conversions[result['map']]

            # Reset indexing and rearrange columns
            match_df.reset_index(drop=True, inplace=True)
            match_df.index += num_rows_processed
            match_cols = list(match_df)

            for colname in reversed(['MatchId', 'MapName', 'RoundNum', 'Tick']):
                if colname not in match_cols:
                    continue

                match_cols.insert(0, match_cols.pop(match_cols.index(colname)))

            match_df = match_df.loc[:, match_cols]

            if first:
                match_df.to_csv(combined_csv)
                first = False
            else:
                match_df.to_csv(combined_csv, mode='a', header=False)

            num_rows_processed += match_df.shape[0]

        # All CSVs need MatchId, MapName, RoundNum, Tick as first 4 columns
        # Frames needs RoundNum,MatchId,MapName

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
