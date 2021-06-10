# Report

This project aims to implement the methods described in the paper [Valuing Actions in Counter-Strike: Global Offensive](https://arxiv.org/pdf/2011.01324.pdf), attempting to reproduce the results while exploring some additions to the existing work.

**EXPLAIN THE IDEAS OF THE PAPER HERE**

## Scraping a Dataset

The original paper uses a dataset comprised of 4800 game demos all scraped from [HLTV.org](https://www.hltv.org/). Since this dataset is not available, the first task is to collect a dataset. Like the paper<sup>[1]</sup>, I decided to scrape my data from HLTV since they have extensive amounts of records on professional matches and would prove useful in the future if me or others wanted to scrape demos off of that site.

There were no existing libraries that could fetch all the information I wanted off of HLTV, but I made things easier by starting with a [reputable HLTV scraper](https://github.com/SocksPls/hltv-api/blob/master/main.py) and modifying from there. There were 3 main modifications I made to adapt the script to my uses:
1. Accept a date range input to scrape data from all matches within that date range.
2. Collect stats from element of each page containing the scoreboard stats of each game (importantly the closed-source HLTV 2.0 ratings for possible comparison).
3. The download URL for the demo files, which contain the detailed match data that will make up the dataset.

With the necessary details for each match scraped from the website, I then used a script to download and parse all of the demo replay files (.dem). The original paper<sup>[1]</sup> had an accompanying [parser](https://github.com/pnxenopoulos/csgo) for these demo files which made reproducing their results much more possible.

The demos for each game were bundled into zip files for each match, so in order to parse one demo I had to download all the demos for the match and then keep the demo files for the other games around for when the script reached them. The script downloads the demo, parses it and then deletes the demo before moving onto the next one so avoid storing them all simultaneously. The 2800 demo files I did download were about 400GB in total size. After parsing out all the data I used another script to merge the data from each game into a single group of dataframes, but that could have easily been combined with the parsing.

## Data Munging and Feature Extraction

The data munging and feature extraction took the most effort of any component

## Fitting Models

## Results

## Challenges and Caveats

## Reference

[1] Xenopoulos, Peter, et al. "[Valuing Actions in Counter-Strike: Global Offensive](https://arxiv.org/pdf/2011.01324.pdf)." 2020 IEEE International Conference on Big Data (Big Data). IEEE, 2020.
