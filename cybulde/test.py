import pandas as pd

dev_df = pd.read_parquet("./data/processed/dev.parquet")

print(dev_df.head())
print(dev_df.shape)
