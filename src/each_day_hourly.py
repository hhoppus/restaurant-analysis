import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from utils import load_pos_data

def analyze_daily_hourly_patterns(df):
    """
    Analyze and visualize average hourly order volumes for each day of the week
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing POS data with timestamp column
    """
    # Add day of week and hour
    df['day_of_week'] = df['timestamp'].dt.day_name()
    df['hour'] = df['timestamp'].dt.hour
    df['date'] = df['timestamp'].dt.date
    
    # Calculate number of each weekday in the dataset
    days_count = df.groupby('day_of_week')['date'].nunique()
    
    # Calculate total orders for each day-hour combination
    hourly_volume = df.groupby(['day_of_week', 'hour']).size().reset_index(name='order_count')
    
    # Calculate average orders by dividing by number of that weekday
    hourly_volume['avg_orders'] = hourly_volume.apply(
        lambda row: row['order_count'] / days_count[row['day_of_week']], 
        axis=1
    ).round(1)
    
    # Define colors for each day
    colors = {
        'Monday': '#FF9999',    # Soft red
        'Tuesday': '#66B2FF',   # Soft blue
        'Wednesday': '#99FF99', # Soft green
        'Thursday': '#FFCC99',  # Soft orange
        'Friday': '#FF99FF',    # Soft purple
        'Saturday': '#FFE680',  # Soft yellow
        'Sunday': '#B2B2B2'     # Soft gray
    }
    
    # Create the plot
    plt.figure(figsize=(15, 8))
    
    # Plot each day's line
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day in days_order:
        day_data = hourly_volume[hourly_volume['day_of_week'] == day]
        plt.plot(day_data['hour'], day_data['avg_orders'], 
                'o-', label=f"{day} (avg: {day_data['avg_orders'].mean():.1f})", 
                color=colors[day], linewidth=2, markersize=6)
    
    plt.title('Average Hourly Order Volume by Day of Week', pad=20, fontsize=14)
    plt.xlabel('Hour of Day', fontsize=12)
    plt.ylabel('Average Number of Orders', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(title='Day of Week', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(range(11, 23))  # Restaurant hours 11 AM to 10 PM
    
    # Print validation statistics
    print("\nValidation Statistics:")
    print("-" * 50)
    for day in days_order:
        day_count = days_count[day]
        day_orders = df[df['day_of_week'] == day].shape[0]
        print(f"{day}:")
        print(f"  Total orders: {day_orders:,}")
        print(f"  Number of {day}s in dataset: {day_count}")
        print(f"  Average orders per {day}: {day_orders/day_count:.1f}")
    
    plt.tight_layout()
    return plt.gcf()

def main():
    try:
        # Load the data from SQL database
        query = "SELECT * FROM cleaned_pos_data_full_v2"
        df = load_pos_data(query, from_database=True)
        
        # Create visualization
        fig = analyze_daily_hourly_patterns(df)
        plt.show()
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()