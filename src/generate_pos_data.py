import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_pos_data(start_date='2024-01-01', days=90):
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Create basic menu items with realistic prices and costs
    menu_items = {
        'Burger': {'price': 12.99, 'category': 'Main'},
        'Cheeseburger': {'price': 14.99, 'category': 'Main'},
        'Veggie Burger': {'price': 13.99, 'category': 'Main'},
        'French Fries': {'price': 4.99, 'category': 'Side'},
        'Sweet Potato Fries': {'price': 5.99, 'category': 'Side'},
        'Garden Salad': {'price': 8.99, 'category': 'Side'},
        'Chicken Wings': {'price': 11.99, 'category': 'Appetizer'},
        'Mozzarella Sticks': {'price': 7.99, 'category': 'Appetizer'},
        'Soda': {'price': 2.99, 'category': 'Beverage'},
        'Iced Tea': {'price': 2.99, 'category': 'Beverage'},
        'Beer': {'price': 5.99, 'category': 'Alcohol'},
        'Wine': {'price': 7.99, 'category': 'Alcohol'}
    }

    # Restaurant locations
    locations = ['Downtown', 'Suburb West', 'Suburb East', 'Airport', 'Mall']
    
    # Generate server IDs (some servers work at multiple locations)
    servers = [f'S{i:03d}' for i in range(1, 31)]

    # Initialize empty list for records
    records = []
    
    # Generate data for each day
    start = datetime.strptime(start_date, '%Y-%m-%d')
    for day in range(days):
        current_date = start + timedelta(days=day)
        
        # Different number of orders based on day of week
        num_orders = int(np.random.normal(
            loc=300 if current_date.weekday() < 5 else 400,
            scale=30
        ))
        
        for _ in range(max(0, num_orders)):  # Ensure non-negative number of orders
            # Randomly select location
            location = np.random.choice(locations)
            
            # Generate timestamp with realistic patterns
            # Now we have 12 hours (11 AM to 10 PM) and 12 corresponding probabilities
            hours = np.arange(11, 23)  # 11 AM to 10 PM
            hour_probs = np.array([
                0.05,  # 11 AM
                0.10,  # 12 PM
                0.15,  # 1 PM
                0.10,  # 2 PM
                0.05,  # 3 PM
                0.10,  # 4 PM
                0.15,  # 5 PM
                0.15,  # 6 PM
                0.08,  # 7 PM
                0.04,  # 8 PM
                0.02,  # 9 PM
                0.01   # 10 PM
            ])
            
            hour = np.random.choice(hours, p=hour_probs)
            minute = np.random.randint(0, 60)
            timestamp = current_date.replace(hour=hour, minute=minute)
            
            # Generate order details
            num_items = np.random.randint(1, 6)
            items = np.random.choice(list(menu_items.keys()), size=num_items)
            
            # Some orders have missing or incorrect data
            server = np.random.choice(servers) if np.random.random() > 0.05 else None
            table = f"T{np.random.randint(1, 21)}" if np.random.random() > 0.03 else None
            
            # Generate individual item records with occasional price errors
            for item in items:
                price = menu_items[item]['price']
                # Introduce occasional price errors
                if np.random.random() < 0.02:
                    price = price * np.random.choice([0.1, 10])  # Obviously wrong prices
                
                record = {
                    'timestamp': timestamp,
                    'location': location,
                    'server_id': server,
                    'table_number': table,
                    'item_name': item,
                    'item_category': menu_items[item]['category'],
                    'price': price,
                    'payment_type': np.random.choice(['CASH', 'CREDIT', 'DEBIT', None], p=[0.2, 0.6, 0.15, 0.05])
                }
                records.append(record)
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    # Add some duplicate records (common POS issue)
    duplicate_idx = np.random.choice(len(df), size=int(len(df) * 0.01), replace=False)
    duplicates = df.iloc[duplicate_idx].copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df

# Generate the data
pos_data = generate_pos_data()

# Show some example records
print("\nFirst few records:")
print(pos_data.head())

# Show basic statistics
print("\nBasic statistics:")
print(pos_data.describe())

# Show data quality issues
print("\nMissing values:")
print(pos_data.isnull().sum())

# Save to CSV
pos_data.to_csv('restaurant_pos_data.csv', index=False)