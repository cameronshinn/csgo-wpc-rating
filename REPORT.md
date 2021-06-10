# Report

This project aims to implement the methods described in the paper [Valuing Actions in Counter-Strike: Global Offensive](https://arxiv.org/pdf/2011.01324.pdf), attempting to reproduce the results while exploring some additions to the existing work.

This paper uses different classifiers to predict the win probability of a team a various points in a round of Counter-Strike. By looking at win probability predictions over time, the changes in win probability can be attributed to the actions of different players. Player performances can be determined using collective sum of win probability changes that a player is responsible for. Compared to the current player rating systems, this method makes it trivial to determine the impact of different events on the outcome of a round, but accurately attributing those events to player actions is challenging.

[Short presentation](https://docs.google.com/presentation/d/1j1cH6fV361hLiMzej3Ih6blSx6KYijBdEzcwsoV5yic/edit?usp=sharing)

## Scraping a Dataset

The original paper uses a dataset comprised of 4800 game demos all scraped from [HLTV.org](https://www.hltv.org/). Since this dataset is not available, the first task is to collect a dataset. Like the paper<sup>[1]</sup>, I decided to scrape my data from HLTV since they have extensive amounts of records on professional matches and would prove useful in the future if me or others wanted to scrape demos off of that site.

There were no existing libraries that could fetch all the information I wanted off of HLTV, but I made things easier by starting with a [reputable HLTV scraper](https://github.com/SocksPls/hltv-api/blob/master/main.py) and modifying from there. There were 3 main modifications I made to adapt the script to my uses:
1. Accept a date range input to scrape data from all matches within that date range.
2. Collect stats from element of each page containing the scoreboard stats of each game (importantly the closed-source HLTV 2.0 ratings for possible comparison).
3. The download URL for the demo files, which contain the detailed match data that will make up the dataset.

With the necessary details for each match scraped from the website, I then used a script to download and parse all of the demo replay files (.dem). The original paper<sup>[1]</sup> had an accompanying [parser](https://github.com/pnxenopoulos/csgo) for these demo files which made reproducing their results much more possible.

The demos for each game were bundled into zip files for each match, so in order to parse one demo I had to download all the demos for the match and then keep the demo files for the other games around for when the script reached them. The script downloads the demo, parses it and then deletes the demo before moving onto the next one so avoid storing them all simultaneously. The 2800 demo files I did download were about 400GB in total size. After parsing out all the data I used another script to merge the data from each game into a single group of dataframes, but that could have easily been combined with the parsing.

## Data Munging and Feature Extraction

The data munging and feature extraction took the most effort of any component. The CSVs that come out of the demo parser area list of events, whether it be damage, kills, planting the bomb, etc., which needs to be used to extract new features. The new features are a series of game states at various points in the round. This is a combination of player health numbers, numnber of players alive, player positions and many more. For each event that takes place, we have a row for the correspondingly updated game state. Every type of event usually will only update a few features of the overall game state, so features of the game state that are unchanged are kept from the previous game state.

The feature I have contained within a game state are such:

* `RoundTick`: Number of ticks (128 per second) that have passed since the start of the round.
* `TAlive`: Number of Terrorists alive.
* `CTAlive`: Number of Counter-Terrorists alive.
* `TTotalHp`: Collective amount of HP between all Terrorists.
* `CTTotalHp`: Collective amount of HP between all Terrorists.
* `BombPlantedA`: If the bomb is currently planted at the A bombsite.
* `BombPlantedB`: If the bomb is currently planted at the B bombsite.
* `ClosestDistToA`: The shortest distance of any player to the A bombsite (one column for each team).
* `ClosestDistToB`: The shortest distance of any player to the B bombsite (one column for each team).
* `ChangeClosestDistToA`: Lagged feature indicating the change in closest distance to A from the last game state divided by the number of ticks since the last game state (one column for each team).
* `ChangeClosestDistToB`: Lagged feature indicating the change in closest distance to A from the last game state divided by the number of ticks since the last game state (one column for each team).
* `Map`: The map on which the game is taking place.
* `BuyType`: Strength of the weapons and equipment the team has (categorical), extrapolated from the total equipment value (one column for each team).

## Fitting Models

The models used in [1] are logistic regression, CatBoost and XGBoost. For this project I also fit these three models and do a simple hyperparameter search on CatBoost and XGBoost. I used an 80/20 train/test split and fit data standardizers on only the test set and applied them to both sets to avoid leaking my training data into the test data. The hyperparameters I played with for CatBoost are learning rate, depth and L2 regularization. For XGBoost I looked at max depth, column samples per tree, learning rate and minimum child weight. I performed a grid search for a set of values for each of the hyperparameters and evaulated them using the log loss, selecting the hyperparameters that gave the lowest log loss.

## Results

My results performing cross-validation are:
| Model | Log Loss | Brier Score | AUC |
| ----- | -------- | ----------- | --- |
| Logistic Regression | 0.4706 | 0.1578 | 0.8495 |
| CatBoost | 0.4522 | 0.1513 | 0.8617 |
| XGBoost | **0.4511** | **0.1510** | **0.8620** |

The results from [1] are:

| Model | Log Loss | Brier Score | AUC |
| ----- | -------- | ----------- | --- |
| Logistic Regression | 0.5539 | 0.1912 | 0.7743 |
| CatBoost | 0.5443 | 0.1875 | 0.7851 |
| XGBoost | **0.5353** | **0.1842** | **0.7913** |

In both of our results, XGBoost looks to be the best model for this task, with my results being only barely better than CatBoost. Notably my models performed better on my data than theirs did on their data, despite having ~4x more. I will not claim that my methods were better because I haven't examined the validity of my results, but if that is the case then I suspect that the `Map` feature not present had a significant impact. The only other features I had that were not present in their models was the distance change metrics (`ChangeClosestDistToA`, `ChangeClosestDistToB`). Given more time, I'd like to asses how much of the variance of my models' predictions can be explained by these two features.

An example of predictions on a single round can be found in [example_round.csv](example_round.csv) and a corresponding plot in [example.html](example.html). The models I trained can be found in the [models folder](models/).

## Challenges

Scraping a dataset and feature engineering were both very challenging and took up the majority of time spent on this project. Since I was dealing with a high volume of data, I tested everything out on small amounts of data to verify that the pipeline was working. However once that was successful I ran into more issues when running the full dataset through the pipeline.

The first issue was that my computer ran out of memory and couldn't run ~2800 matches-worth of data. I ended up froping this down to 1400 to get my models trained and it was still plenty of data.

Even once I was able to process the data, there were a handful of new issues that came up in the preprocessing which were non-existent when working on the smaller test run. Since I assumed that everything would work I left myself no time to fix these issues, which makes me question the validity of my results. I will probably come back to this in the future and examine the problems and make the whole pipeline easier and cleaner.

## Reference

[1] Xenopoulos, Peter, et al. "[Valuing Actions in Counter-Strike: Global Offensive](https://arxiv.org/pdf/2011.01324.pdf)." 2020 IEEE International Conference on Big Data (Big Data). IEEE, 2020.
