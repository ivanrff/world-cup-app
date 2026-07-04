import os
from dotenv import load_dotenv
import kagglehub

# load_dotenv()
# KAGGLE_API_TOKEN = os.getenv("KAGGLE_API_TOKEN")

files = ['matches.csv', 'teams.csv']

for file in files:
    kagglehub.dataset_download(
        'mominullptr/fifa-world-cup-2026-dataset',
        path=file,
        output_dir='data/kaggle',
        force_download=True)