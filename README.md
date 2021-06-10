# CS:GO WPC Rating

This CS:GO player rating system performs win probability prediction using machine learning and win probabilty change attribution to rate players based on how their actions change their team's chances of winning. Detalis of the system are explained in the [`REPORT.md`](REPORT.md) file.

## Setup

1. Get all the python packages used in the codebase, run `pip install -r requirements.txt`.
2. If you wish to use demo parser to create a dataset from demo files, get the submodules when cloning this repositoriy using `--recurse-submodules` flag. Follow the setup instructions in their [`README.md`](https://github.com/pnxenopoulos/csgo/blob/master/README.md) file.

## Running Components

### Dataset Collection

#### Demo Link Scaper [`scrape.py`](scrape_parse/scrape.py)

`python scrape.py [start date] [end date]`

This script takes in a date range as two command line arguments (start and end date) in the form of yyyy-mm-dd. It then searches [HLTV.org](https://www.hltv.org/) for all matches that took place within that date range and collects the scoreboard data and download link for the demo zip file. This data gets output into a JSON file.

#### Downloader-Parser [`download_parse.py`](scrape_parse/download_parse.py)

`python download_parse.py [path to scraper results]`

This script takes a command line argument of the path to a JSON file of the format output by the demo link  scraper. Using the download links in the JSON, it downloads the demos for each match and then parses them using the demo parser outputting a collection of CSV files for each game that gets downloaded and parsed. It also outputs a file `redirects.json` containing the resolved URL of the download links (so we can see the info contained in the file name before downloading it).

#### Data Merger [`merge.py`](scrape_parse/merge.py)

`python merge.py [path to scraper results] [path to redirects json]`

This script takes two command line arguments, the results JSON file output by the demo link scraper and the `redirects.json` file that the downloader-parser outputs. It merges all of the CSV files output by the downloader-parser by what type of CSV it is. For example, all the CSVs with damage events from each match get combined into a single CSV file, `Damages.csv`.

### Model Fitting

#### Dataset Preprocessing [`create_game_states.ipynb`](create_game_states.ipynb)

This notebook performs the data munging and feature extraction from the dataset. It uses `Damages.csv`, `Kills.csv`, `BombEvents.csv`, `PlayerFrames.csv`, `Rounds.csv`. Most of this data is event-based (rows for each event) and so this script uses these events assemble a game state every time any event occurs. It outputs a CSV file `game_states.csv`.

#### Model Fitting and Hyperparameter Search [`models.ipynb`](models.ipynb)

This script does the preprocssing on the game states dataframe and then fits models to that dataset. The preprocessing is just scaling/standardization and encoding dummies for categorical variables. The models get fit are linear regression, CatBoost and XGBoost. A hyperparameter search is performed when fitting the models, comparing different sets of hyperparameters via the log loss on the validation set. The final models get saved as files.
