import pandas as pd
from pathlib import Path

mapping_path = Path('Mapping VAS.xlsx')
df = pd.read_excel(mapping_path)

# Normalize first-level account codes
first_level_col = df['1st'].ffill()
df['first_level'] = first_level_col.astype(str).str.replace('.0', '', regex=False)

# Clean textual columns
for col in ['Leadsheet', 'Item on FSs', 'FSs code']:
    df[col] = df[col].astype(str).replace({'nan': ''})

summary = (
    df.dropna(subset=['1st'])
    .groupby('first_level')[['Leadsheet', 'Item on FSs', 'FSs code']]
    .agg(lambda x: sorted({v.strip() for v in x if v.strip()}))
)

print('Total first-level account groups:', len(summary))
print('\nSample mapping (first 15):')
print(summary.head(15).to_string())

# Identify multiple mappings per first-level
multi_leadsheet = summary[summary['Leadsheet'].apply(len) > 1]
print('\nAccounts with multiple leadsheets:', multi_leadsheet.shape[0])
print(multi_leadsheet.head().to_string())

multi_fs_item = summary[summary['Item on FSs'].apply(len) > 1]
print('\nAccounts with multiple FS items:', multi_fs_item.shape[0])
print(multi_fs_item.head().to_string())
