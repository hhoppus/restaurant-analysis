import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any
import logging
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import os
from dotenv import load_dotenv
from pathlib import Path

# Get parent directory (where .env is located)
parent_dir = Path(__file__).resolve().parent.parent

# Load environment variables from parent directory
load_dotenv(parent_dir / '.env')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_connection() -> Engine:
    """
    Create database connection using environment variables
    """
    db_params = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME')
    }
    
    # Validate all required parameters are present
    missing_params = [k for k, v in db_params.items() if v is None]
    if missing_params:
        raise ValueError(f"Missing required environment variables: {missing_params}")
    
    # Create connection string
    connection_string = (
        f"postgresql://{db_params['user']}:{db_params['password']}"
        f"@{db_params['host']}:{db_params['port']}/{db_params['database']}"
    )
    
    return create_engine(connection_string)

def load_pos_data_from_db(query: str) -> pd.DataFrame:
    """Load POS data from database using SQL query"""
    engine = get_database_connection()
    return pd.read_sql(query, engine, parse_dates=['timestamp'])

def load_pos_data_from_file(file_path: str) -> pd.DataFrame:
    """Load POS data from CSV file"""
    return pd.read_csv(file_path, parse_dates=['timestamp'])

def load_pos_data(source: str, from_database: bool = False) -> pd.DataFrame:
    """
    Load POS data from either a CSV file or database
    
    Parameters:
    -----------
    source : str
        Either file path or SQL query
    from_database : bool
        If True, execute SQL query; if False, load from CSV file
    """
    try:
        if from_database:
            df = load_pos_data_from_db(source)
        else:
            df = load_pos_data_from_file(source)
            
        # Validate required columns
        required_columns = [
            'timestamp', 'location', 'server_id', 'table_number',
            'item_name', 'item_category', 'price', 'payment_type'
        ]
        
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
        logger.info(f"Successfully loaded {len(df)} records")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise

class POSDataAnalyzer:
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the POS data analyzer with a DataFrame
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame containing POS data with columns:
            timestamp, location, server_id, table_number, item_name, 
            item_category, price, payment_type
        """
        self.df = df.copy()
        self._preprocess_data()
        
    def _preprocess_data(self) -> None:
        """Preprocess the data for analysis"""
        logger.info("Preprocessing data...")
        
        # Convert timestamp to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(self.df['timestamp']):
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        # Add derived time columns
        self.df['date'] = self.df['timestamp'].dt.date
        self.df['hour'] = self.df['timestamp'].dt.hour
        self.df['day_of_week'] = self.df['timestamp'].dt.day_name()
        
        # Handle missing values
        self.df['payment_type'] = self.df['payment_type'].fillna('UNKNOWN')
        
        # Flag potential price anomalies
        price_stats = self.df.groupby('item_name')['price'].agg(['mean', 'std']).reset_index()
        price_stats['upper_bound'] = price_stats['mean'] + 3 * price_stats['std']
        price_stats['lower_bound'] = price_stats['mean'] - 3 * price_stats['std']
        
        self.df = self.df.merge(price_stats[['item_name', 'upper_bound', 'lower_bound']], 
                               on='item_name', how='left')
        
        self.df['price_anomaly'] = (
            (self.df['price'] > self.df['upper_bound']) | 
            (self.df['price'] < self.df['lower_bound'])
        )
        
        logger.info("Preprocessing complete.")

    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the dataset"""
        return {
            'date_range': (self.df['date'].min(), self.df['date'].max()),
            'total_sales': self.df['price'].sum(),
            'total_transactions': len(self.df),
            'unique_locations': self.df['location'].nunique(),
            'unique_servers': self.df['server_id'].nunique(),
            'price_anomalies': self.df['price_anomaly'].sum()
        }

    def analyze_daily_trends(self) -> pd.DataFrame:
        """Analyze daily sales trends"""
        daily_stats = self.df.groupby('date').agg({
            'price': ['count', 'sum', 'mean'],
            'item_name': 'count',
            'server_id': 'nunique'
        }).round(2)
        
        daily_stats.columns = [
            'transaction_count', 'total_sales', 
            'avg_ticket', 'items_sold', 'active_servers'
        ]
        return daily_stats

    def analyze_hourly_patterns(self) -> pd.DataFrame:
        """Analyze hourly sales patterns"""
        return self.df.groupby('hour').agg({
            'price': ['count', 'sum', 'mean'],
            'item_name': 'count'
        }).round(2)

    def analyze_server_performance(self, min_transactions: int = 10) -> pd.DataFrame:
        """
        Analyze server performance metrics
        
        Parameters:
        -----------
        min_transactions : int
            Minimum number of transactions for a server to be included
        """
        server_metrics = self.df.groupby('server_id').agg({
            'price': ['count', 'sum', 'mean'],
            'item_name': 'count',
            'price_anomaly': 'sum'
        }).round(2)
        
        server_metrics.columns = [
            'transaction_count', 'total_sales', 'avg_ticket',
            'items_sold', 'price_anomalies'
        ]
        
        # Filter by minimum transactions
        server_metrics = server_metrics[
            server_metrics['transaction_count'] >= min_transactions
        ]
        
        # Add derived metrics
        server_metrics['items_per_transaction'] = (
            server_metrics['items_sold'] / 
            server_metrics['transaction_count']
        ).round(2)
        
        return server_metrics.sort_values('total_sales', ascending=False)

    def analyze_menu_performance(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze menu item and category performance"""
        # Item analysis
        item_metrics = self.df.groupby('item_name').agg({
            'price': ['count', 'sum', 'mean'],
            'price_anomaly': 'sum'
        }).round(2)
        
        item_metrics.columns = [
            'quantity_sold', 'total_revenue', 
            'avg_price', 'price_anomalies'
        ]
        
        # Category analysis
        category_metrics = self.df.groupby('item_category').agg({
            'price': ['count', 'sum', 'mean'],
            'item_name': 'nunique'
        }).round(2)
        
        category_metrics.columns = [
            'quantity_sold', 'total_revenue', 
            'avg_price', 'unique_items'
        ]
        
        return item_metrics, category_metrics

    def analyze_location_performance(self) -> pd.DataFrame:
        """Analyze performance by location"""
        return self.df.groupby('location').agg({
            'price': ['count', 'sum', 'mean'],
            'item_name': 'count',
            'server_id': 'nunique'
        }).round(2)

    def analyze_payment_types(self) -> pd.DataFrame:
        """Analyze payment type distribution"""
        payment_metrics = self.df.groupby('payment_type').agg({
            'price': ['count', 'sum', 'mean']
        }).round(2)
        
        payment_metrics.columns = [
            'transaction_count', 'total_sales', 'avg_ticket'
        ]
        
        payment_metrics['sales_percentage'] = (
            payment_metrics['total_sales'] / 
            payment_metrics['total_sales'].sum() * 100
        ).round(2)
        
        return payment_metrics

    def plot_daily_trends(self, figsize: Tuple[int, int] = (15, 6)) -> None:
        """Plot daily sales trends"""
        daily_stats = self.analyze_daily_trends()
        
        plt.figure(figsize=figsize)
        plt.plot(daily_stats.index, daily_stats['total_sales'], marker='o')
        plt.title('Daily Sales Trend')
        plt.xlabel('Date')
        plt.ylabel('Total Sales ($)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.grid(True)

    def plot_hourly_patterns(self, figsize: Tuple[int, int] = (12, 6)) -> None:
        """Plot hourly sales patterns"""
        hourly_stats = self.analyze_hourly_patterns()
        
        plt.figure(figsize=figsize)
        plt.plot(hourly_stats.index, 
                hourly_stats[('price', 'sum')], 
                marker='o')
        plt.title('Hourly Sales Pattern')
        plt.xlabel('Hour of Day')
        plt.ylabel('Total Sales ($)')
        plt.grid(True)
        plt.tight_layout()

    def generate_report(self, output_path: str = None) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report
        
        Parameters:
        -----------
        output_path : str, optional
            If provided, save the report to this path
        """
        report = {
            'basic_stats': self.get_basic_stats(),
            'daily_trends': self.analyze_daily_trends(),
            'hourly_patterns': self.analyze_hourly_patterns(),
            'server_performance': self.analyze_server_performance(),
            'menu_performance': self.analyze_menu_performance(),
            'location_performance': self.analyze_location_performance(),
            'payment_analysis': self.analyze_payment_types()
        }
        
        if output_path:
            # Save relevant parts of the report to CSV
            for name, data in report.items():
                if isinstance(data, pd.DataFrame):
                    data.to_csv(f"{output_path}/{name}.csv")
                    
        return report