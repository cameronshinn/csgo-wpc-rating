import contextlib
import json
import os
import rarfile
import requests
from shutil import rmtree
import sys
from time import sleep
from tqdm import tqdm

from csgo.parser import DemoParser

DEMO_DIR = 'demos'
CSV_DIR = 'csvs'
PROGRESS_JSON = 'redirects.json'
SKIP_JSON = 'skip.json'


@contextlib.contextmanager
def chdir(dir_name=None):
  of_dir = os.getcwd()

  try:
    if dir_name is not None:
      os.chdir(dir_name)

    yield
  finally:
    os.chdir(of_dir)


def get_filename(url):
    headers = {
        "referer": "https://www.hltv.org/stats",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64)"
    }

    sleep(1)
    response = requests.head(url, headers=headers, allow_redirects=True)
    return os.path.split(response.url)[-1]


def download_file(url):
    print('Downloading ' + url)

    headers = {
        "referer": "https://www.hltv.org/stats",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64)"
    }

    response = requests.get(url, headers=headers, allow_redirects=True, stream=True)
    file_name = os.path.basename(response.url)
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)

    with open(file_name, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)

    progress_bar.close()

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")

    return file_name


def main(summary_json):
    with open(summary_json) as f:
        games_stats = json.load(f)

    if os.path.exists(PROGRESS_JSON):
        with open(PROGRESS_JSON) as f:
            download_redirects = json.load(f)
    else:
        download_redirects = {}

    if os.path.exists(SKIP_JSON):
        with open(SKIP_JSON) as f:
            skips = json.load(f)
    else:
        skips = {}

    if not os.path.exists(DEMO_DIR):
        os.mkdir(DEMO_DIR)

    n_games = len(games_stats)

    try:
        for i in range(n_games):
            if str(i) in skips:
                continue

            # Get game stats and demo link
            game_stats = games_stats[str(i)]
            map = game_stats['map'].lower()
            demo_url = game_stats['demo_link']  # Keys are strings ints

            if demo_url not in download_redirects:
                f = get_filename(demo_url)
                download_redirects[demo_url] = f

            expected_rar_filename = download_redirects[demo_url]
            match_demos_dir = os.path.join(DEMO_DIR, expected_rar_filename.split('.')[0])
            print('RAR:', expected_rar_filename)

            # Get potential demo save directory
            demo_id = os.path.basename(os.path.normpath(match_demos_dir))
            demo_map_id = demo_id if demo_id.endswith(map) else f'{demo_id}-{map}'  # BO1 matches have map name already at the end
            csv_dir = os.path.join(CSV_DIR, demo_map_id)

            # Download demos from match and unzip
            if not os.path.exists(csv_dir) or len(os.listdir(csv_dir)) == 0:
                print(f'\n({i + 1}/{n_games})')
                print('Not found:', csv_dir)
                print('Looking for demo in', match_demos_dir)

                if not os.path.exists(match_demos_dir) or len(list(filter(lambda x: x.endswith(map + '.dem'), os.listdir(match_demos_dir)))) == 0:
                    print('Not found')

                    try:
                        demos_rar = download_file(demo_url)
                        rarfile.RarFile(demos_rar).extractall(path=match_demos_dir)  # Unrar
                        # download_redirects[demo_url] = match_demos_dir  # URL -> folder of unzipped demos
                    finally:
                        os.remove(demos_rar)  # Remove RAR file after extraction or exception
                else:
                    print('Found')

                # Parse demo if not already parsed
                if not os.path.exists(csv_dir):
                    os.makedirs(csv_dir)

                try:
                    demo_file = next(filter(lambda x: x.endswith(map + '.dem'), os.listdir(match_demos_dir)))
                    demo_path = os.path.join(match_demos_dir, demo_file)
                    demo_parser = DemoParser(demofile=demo_path, demo_id=demo_id, parse_rate=128)
                    demo_data = demo_parser.parse(return_type='df')

                    # Save demo data as CSVs
                    for df in ['Rounds', 'Kills', 'Damages', 'Grenades', 'Flashes', 'BombEvents', 'Frames', 'PlayerFrames']:
                        demo_data[df].to_csv(os.path.join(csv_dir, f'{demo_map_id}_{df}.csv'))
                except TypeError as e:
                    if str(e) == "'NoneType' object is not iterable":  # Parser/demofile issue
                        print('Parser/demofile issue: Adding', i, 'to skip')
                        skips[str(i)] = None
                    else:
                        raise
                except FileNotFoundError as e:
                    if str(e).startswith('[Errno 2] No such file or directory'):
                        print('Parser/demofile issue: Adding', i, 'to skip')
                        skips[str(i)] = None
                    else:
                        raise
                except rarfile.NotRarFile:
                    print('Parser/demofile issue: Adding', i, 'to skip')
                    skips[str(i)] = None
                except StopIteration:
                    skips[str(i)] = None
                except OSError:
                    print("OUT OF SPACE?")
                    raise
                finally:
                    if os.path.exists(demo_path):
                        os.remove(demo_path)

                    if os.path.exists(demo_id + '.json'):
                        os.remove(demo_id + '.json')

    finally:
        with open(PROGRESS_JSON, 'w+') as f:
            json.dump(download_redirects, f)

        with open(SKIP_JSON, 'w+') as f:
            json.dump(skips, f)


if __name__ == '__main__':
    main(sys.argv[1])
