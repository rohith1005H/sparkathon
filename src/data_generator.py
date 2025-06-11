import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class DataGenerator:
    def __init__(self):
        self.products = [
            'Milk', 'Bread', 'Eggs', 'Bananas', 'Apples', 'Lettuce', 
            'Tomatoes', 'Chicken', 'Yogurt', 'Cheese', 'Carrots', 'Potatoes'
        ]
        self.stores = ['Store_A', 'Store_B', 'Store_C', 'Store_D', 'Store_E']
        
    def generate_sales_history(self, days=365):
        """Generate historical sales data"""
        data = []
        start_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            day_of_week = current_date.weekday()
            
            for store in self.stores:
                for product in self.products:
                    # Base demand with seasonal and weekly patterns
                    base_demand = random.randint(20, 100)
                    
                    # Weekend boost
                    weekend_multiplier = 1.3 if day_of_week >= 5 else 1.0
                    
                    # Seasonal patterns
                    month = current_date.month
                    seasonal_multiplier = 1.2 if month in [6, 7, 8] else 1.0
                    
                    # Product-specific patterns
                    if product == 'Milk':
                        base_demand *= 1.5
                    elif product in ['Bananas', 'Apples']:
                        base_demand *= 1.2
                    
                    final_demand = int(base_demand * weekend_multiplier * seasonal_multiplier)
                    final_demand += random.randint(-10, 10)  # Random noise
                    final_demand = max(0, final_demand)
                    
                    data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'store_id': store,
                        'product': product,
                        'quantity_sold': final_demand,
                        'day_of_week': day_of_week,
                        'month': month
                    })
        
        df = pd.DataFrame(data)
        df.to_csv('data/sales_history.csv', index=False)
        return df
    
    def generate_weather_data(self, days=365):
        """Generate weather data"""
        data = []
        start_date = datetime.now() - timedelta(days=days)
        
        for day in range(days + 7):  # Include future days
            current_date = start_date + timedelta(days=day)
            
            # Seasonal temperature patterns
            month = current_date.month
            if month in [12, 1, 2]:  # Winter
                temp = random.randint(-5, 10)
            elif month in [3, 4, 5]:  # Spring
                temp = random.randint(10, 25)
            elif month in [6, 7, 8]:  # Summer
                temp = random.randint(20, 35)
            else:  # Fall
                temp = random.randint(5, 20)
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'temperature': temp,
                'humidity': random.randint(30, 90),
                'precipitation': random.choice([0, 0, 0, 0, 1, 2, 5]),  # Mostly no rain
                'weather_condition': random.choice(['Sunny', 'Cloudy', 'Rainy', 'Sunny', 'Sunny'])
            })
        
        df = pd.DataFrame(data)
        df.to_csv('data/weather_data.csv', index=False)
        return df
    
    def generate_events_data(self):
        """Generate local events data"""
        events = [
            {'date': '2024-07-04', 'event': 'Independence Day', 'impact': 1.5},
            {'date': '2024-11-28', 'event': 'Thanksgiving', 'impact': 2.0},
            {'date': '2024-12-25', 'event': 'Christmas', 'impact': 1.8},
            {'date': '2024-01-01', 'event': 'New Year', 'impact': 1.3},
            {'date': '2024-02-14', 'event': 'Valentine Day', 'impact': 1.2},
            {'date': '2024-10-31', 'event': 'Halloween', 'impact': 1.4},
        ]
        
        df = pd.DataFrame(events)
        df.to_csv('data/events_data.csv', index=False)
        return df
    
    def generate_stores_data(self):
        """Generate store location and capacity data"""
        store_data = [
            {'store_id': 'Store_A', 'lat': 40.7128, 'lon': -74.0060, 'capacity': 500},
            {'store_id': 'Store_B', 'lat': 40.7589, 'lon': -73.9851, 'capacity': 300},
            {'store_id': 'Store_C', 'lat': 40.6782, 'lon': -73.9442, 'capacity': 400},
            {'store_id': 'Store_D', 'lat': 40.7831, 'lon': -73.9712, 'capacity': 600},
            {'store_id': 'Store_E', 'lat': 40.6892, 'lon': -74.0445, 'capacity': 350},
        ]
        
        df = pd.DataFrame(store_data)
        df.to_csv('data/stores_data.csv', index=False)
        return df
    
    def generate_all_data(self):
        """Generate all dummy data"""
        print("Generating sales history...")
        self.generate_sales_history()
        print("Generating weather data...")
        self.generate_weather_data()
        print("Generating events data...")
        self.generate_events_data()
        print("Generating stores data...")
        self.generate_stores_data()
        print("All data generated successfully!")

if __name__ == "__main__":
    generator = DataGenerator()
    generator.generate_all_data()