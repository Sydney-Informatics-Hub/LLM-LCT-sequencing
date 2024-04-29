# plot training data numbers

import pandas as pd
import matplotlib.pyplot as plt

file_path = '../../data/trainingdata.xlsx'

data = pd.read_excel(file_path)

# Convert all values in the 'Types' column to lowercase
data['Types'] = data['Types'].str.lower()
# remove leading and trailing whitespaces
data['Types'] = data['Types'].str.strip()

if 'Origin' not in data.columns:
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


else:
    pivot_data = data.pivot_table(index='Types', columns='Origin', aggfunc='size', fill_value=0)

    # order the rows in the pivot table according to total counts
    pivot_data['Total'] = pivot_data.sum(axis=1)
    pivot_data.sort_values(by='Total', ascending=False, inplace=True)
    total_counts = pivot_data['Total']
    # drop the 'Total' column
    pivot_data.drop(columns='Total', inplace=True)


    # Plotting the stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    pivot_data.plot(kind='bar', stacked=True, color=['skyblue', 'lightgreen', 'salmon'], ax=ax)

    # Adding count labels above each bar
    for i, (idx, row) in enumerate(pivot_data.iterrows()):
        cum_height = 0
        for col in pivot_data.columns:
            label = row[col]
            if label > 0:  # Only add label if there's a count
                ax.text(i, cum_height + label/2, int(label), ha='center', va='center')
                cum_height += label
        # Add totoal count label at the top of each bar
        ax.text(i, cum_height, int(total_counts[idx]), ha='center', va='bottom')

    plt.xlabel('Types')
    plt.ylabel('Counts')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Type')
    plt.tight_layout()
    plt.savefig('../../data/trainingdata_stacked.png')
    plt.show()
