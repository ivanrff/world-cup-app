# 2026 World Cup Opta Predictions Analysis

<em>Explore the 2026 World Cup Predictions from Opta</em>

<!-- BADGES -->
<!-- local repository, no metadata badges. -->

<em>Built with the tools and technologies:</em>

<img src="https://img.shields.io/badge/Streamlit-FF4B4B.svg?style=default&logo=Streamlit&logoColor=white" alt="Streamlit">
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=default&logo=Python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/Plotly-3F4F75.svg?style=default&logo=Plotly&logoColor=white" alt="Plotly">
<img src="https://img.shields.io/badge/pandas-150458.svg?style=default&logo=pandas&logoColor=white" alt="pandas">

</div>
<br>

---

## Overview

This repository contains analyses on the Opta 2026 World Cup Predictions as the tournament progresses.

---

## Data Sources
- https://www.kaggle.com/datasets/mominullptr/fifa-world-cup-2026-dataset
- https://theanalyst.com/competition/fifa-world-cup/fixtures

---

## Project Structure

```sh
└── world-cup/
    ├── app.py
    ├── data
    │   ├── db
    │   ├── kaggle
    │   └── opta
    └── src
        ├── 1_get_kaggle_data.py
        ├── 2_opta_scrapper.py
        ├── 3_data_prep.py
        ├── 4_db_ingest.py
        ├── scrap_qualify_predictions.py
        └── utils
```
---

## Project Index

| Script Name | Description |
| - | - |
| app.py | This Streamlit application displays soccer match predictions from Opta Supercomputer<br>- It presents performance data through visualizations including model grades and Brier scores across selected World Cup matches<br>- Users can filter by snapshot date to view past or future games, with intuitive charts showing prediction accuracy trends over time for tournament stages like group matches and knockout rounds. |
| 2_opta_scrapper.py | This script fetches and processes football match win probability data from Optas API during live events, specifically for the FIFA World Cup tournament<br>- It collects new match IDs, filters out already played games, retrieves detailed statistics via individual API calls, and saves them to a JSON file while maintaining execution logs<br>- The code integrates with existing data pipelines by leveraging stored fixture IDs and ensuring no redundant requests are made. |
| 3_data_prep.py | This script processes tournament match data by merging team information from separate files<br>- It calculates key attributes like rank differences and identifies favorite teams based on pre-tournament rankings<br>- The resulting DataFrame structures this information for downstream analysis, providing insights into team matchups without detailing specific implementation steps. |
| 4_db_ingest.py | This script processes football match prediction data from JSON files<br>- It extracts key information such as dates, team codes, pre-match probabilities, and outcomes, standardizing columns and handling timezones<br>- The transformed data is loaded into a SQL database for efficient querying and analysis by downstream applications. |