# plot training data numbers

import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the Excel file
file_path = '../../data/trainingdata.xlsx'
data = pd.read_excel(file_path)

# Adjust the 'Types' column by merging 'sequential?' into 'sequential'
#data['Types'] = data['Types'].replace('sequential?', 'sequential')

# Recount the occurrences of each type in the 'Types' column after the adjustment
adjusted_type_counts = data['Types'].value_counts()

# Plotting the adjusted bar chart with count labels on each bar
plt.figure(figsize=(10, 6))
bars = plt.bar(adjusted_type_counts.index, adjusted_type_counts.values, color='skyblue')

# Adding count labels above each bar
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')

plt.xlabel('Types')
plt.ylabel('Counts')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('../../data/trainingdata.png')
plt.show()
