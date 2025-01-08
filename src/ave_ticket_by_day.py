import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from utils import load_pos_data
import logging

def analyze_daily_average_tickets(df):
    """
    Analyze and visualize average ticket prices by day of week
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing POS data with timestamp and price columns
    """
    # Calculate daily averages
    daily_avg = (df.groupby(df['timestamp'].dt.day_name())
                  .agg({
                      'price': ['mean', 'count', 'sum']
                  })
                  .round(2))
    
    # Flatten column names
    daily_avg.columns = ['avg_ticket', 'num_orders', 'total_revenue']
    
    # Reset index to get day_of_week as a column
    daily_avg = daily_avg.reindex(['Monday', 'Tuesday', 'Wednesday', 
                                  'Thursday', 'Friday', 'Saturday', 'Sunday'])
    
    # Print the statistics
    print("\nDaily Average Ticket Analysis:")
    print("-" * 50)
    for day in daily_avg.index:
        stats = daily_avg.loc[day]
        print(f"{day}:")
        print(f"  Average Ticket: ${stats['avg_ticket']:.2f}")
        print(f"  Number of Orders: {stats['num_orders']:,}")
        print(f"  Total Revenue: ${stats['total_revenue']:,.2f}")
    
    # Create the visualization
    plt.figure(figsize=(12, 6))
    
    # Create bar chart
    bars = plt.bar(daily_avg.index, daily_avg['avg_ticket'], 
                   color=sns.color_palette("husl", 7))
    
    # Customize the plot
    plt.title('Average Ticket Price by Day of Week', pad=20, fontsize=14)
    plt.xlabel('Day of Week', fontsize=12)
    plt.ylabel('Average Ticket Price ($)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.2f}',
                ha='center', va='bottom')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    
    return plt.gcf()

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Load the data from SQL
        logger.info("Loading POS data from database...")
        query = "SELECT * FROM cleaned_pos_data_full_v2"
        df = load_pos_data(query, from_database=True)
        
        # Create visualization
        logger.info("Creating daily average ticket analysis...")
        fig = analyze_daily_average_tickets(df)
        
        # Save the figure
        output_path = Path('analysis_output')
        output_path.mkdir(exist_ok=True)
        fig.savefig(output_path / 'daily_average_tickets.png', dpi=300, bbox_inches='tight')
        logger.info("Analysis complete. Results saved to 'analysis_output/daily_average_tickets.png'")
        
        plt.close(fig)
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()