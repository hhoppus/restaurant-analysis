import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from utils import POSDataAnalyzer, load_pos_data

def create_location_hour_heatmap(analyzer, figsize=(12, 8)):
    """
    Create a heatmap showing average orders per hour by location with corrected averaging
    """
    # Calculate total days in dataset for each location
    location_days = analyzer.df.groupby('location')['date'].nunique()
    
    # Calculate total orders for each location-hour combination
    hourly_totals = (analyzer.df.groupby(['location', 'hour'])
                    .size()
                    .reset_index(name='total_orders'))
    
    # Create the hour range we expect (11-22 based on restaurant hours)
    expected_hours = range(11, 23)
    
    # Ensure we have all location-hour combinations, filling missing with 0
    all_combinations = pd.MultiIndex.from_product(
        [location_days.index, expected_hours],
        names=['location', 'hour']
    )
    
    # Reindex to include all hours, filling missing with 0
    hourly_totals = (hourly_totals
                    .set_index(['location', 'hour'])
                    .reindex(all_combinations, fill_value=0)
                    .reset_index())
    
    # Calculate true average by dividing by total days for that location
    hourly_totals['avg_orders'] = (
        hourly_totals.apply(
            lambda row: row['total_orders'] / location_days[row['location']], 
            axis=1
        )
    ).round(1)
    
    # Create heatmap data
    heatmap_data = hourly_totals.pivot(
        index='location',
        columns='hour',
        values='avg_orders'
    )
    
    # Create the plot
    plt.figure(figsize=figsize)
    sns.heatmap(heatmap_data, 
                annot=True,
                fmt='.1f',
                cmap='YlOrRd',
                cbar_kws={'label': 'Average Orders per Hour'})
    
    plt.title('Average Orders per Hour by Location')
    plt.xlabel('Hour of Day')
    plt.ylabel('Location')
    plt.xticks(rotation=0)
    plt.tight_layout()
    
    # Validation print
    for location in heatmap_data.index:
        total = heatmap_data.loc[location].sum()
        print(f"{location} - Sum of hourly averages: {total:.1f}")
    
    return plt.gcf()

# Load the data and create analyzer
df = load_pos_data("cleaned_pos_data_full_v2", from_database=True)
analyzer = POSDataAnalyzer(df)

# Create and show the heatmap
heatmap = create_location_hour_heatmap(analyzer)
plt.show()