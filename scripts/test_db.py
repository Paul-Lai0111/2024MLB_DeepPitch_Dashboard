# Run this in your terminal to verify db.py works
# python -c "
from src.db import PitchDB
import pandas as pd

db = PitchDB()

# Create a small test DataFrame
test_df = pd.DataFrame({
    'pitcher': ['Yamamoto', 'Glasnow', 'Buehler'],
    'pitch_type': ['FF', 'FF', 'SL'],
    'release_speed': [95.2, 97.1, 88.4]
})

db.save_dataframe(test_df, 'test_table', mode='replace')
print(db.list_tables())
print(db.query_to_df('SELECT * FROM test_table'))
