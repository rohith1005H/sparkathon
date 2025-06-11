import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from demand_predictor import DemandPredictor

class InventoryManager:
    def __init__(self):
        self.predictor = DemandPredictor()
        self.predictor.load_model()
        
        # Product shelf life in days
        self.shelf_life = {
            'Milk': 7, 'Bread': 3, 'Eggs': 21, 'Bananas': 5, 'Apples': 14,
            'Lettuce': 7, 'Tomatoes': 7, 'Chicken': 3, 'Yogurt': 14,
            'Cheese': 21, 'Carrots': 14, 'Potatoes': 30
        }
        
        # Minimum stock levels
        self.min_stock = {
            'Milk': 50, 'Bread': 30, 'Eggs': 40, 'Bananas': 25, 'Apples': 35,
            'Lettuce': 20, 'Tomatoes': 25, 'Chicken': 30, 'Yogurt': 25,
            'Cheese': 20, 'Carrots': 15, 'Potatoes': 40
        }
    
    def generate_current_inventory(self, store_id):
        """Generate current inventory status for a store"""
        inventory = []
        
        for product in self.shelf_life.keys():
            # Generate multiple batches with different expiry dates
            num_batches = np.random.randint(2, 5)
            
            for batch in range(num_batches):
                days_until_expiry = np.random.randint(1, self.shelf_life[product])
                expiry_date = datetime.now() + timedelta(days=days_until_expiry)
                quantity = np.random.randint(10, 100)
                
                inventory.append({
                    'store_id': store_id,
                    'product': product,
                    'batch_id': f"{product}_{batch}_{store_id}",
                    'quantity': quantity,
                    'expiry_date': expiry_date,
                    'days_until_expiry': days_until_expiry,
                    'received_date': datetime.now() - timedelta(days=self.shelf_life[product] - days_until_expiry)
                })
        
        return pd.DataFrame(inventory)
    
    def calculate_reorder_suggestions(self, store_id, days_ahead=7):
        """Calculate reorder suggestions based on predicted demand"""
        print(f"Calculating reorder suggestions for {store_id}...")
        
        current_inventory = self.generate_current_inventory(store_id)
        suggestions = []
        
        for product in self.shelf_life.keys():
            # Get current stock
            product_inventory = current_inventory[current_inventory['product'] == product]
            current_stock = product_inventory['quantity'].sum()
            
            # Predict demand for next week
            total_predicted_demand = 0
            for day in range(1, days_ahead + 1):
                future_date = (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d')
                daily_demand = self.predictor.predict_demand(store_id, product, future_date)
                total_predicted_demand += daily_demand
            
            # Calculate stock that will expire
            expiring_stock = product_inventory[
                product_inventory['days_until_expiry'] <= days_ahead
            ]['quantity'].sum()
            
            # Available stock after accounting for expiry
            available_stock = current_stock - expiring_stock
            
            # Calculate reorder quantity
            safety_stock = self.min_stock[product]
            needed_stock = total_predicted_demand + safety_stock
            reorder_quantity = max(0, needed_stock - available_stock)
            
            suggestions.append({
                'store_id': store_id,
                'product': product,
                'current_stock': current_stock,
                'predicted_demand_7d': total_predicted_demand,
                'expiring_stock_7d': expiring_stock,
                'available_stock': available_stock,
                'recommended_order': reorder_quantity,
                'priority': 'HIGH' if reorder_quantity > 0 else 'LOW'
            })
        
        return pd.DataFrame(suggestions)
    
    def identify_expiring_items(self, store_id, warning_days=2):
        """Identify items that are about to expire"""
        current_inventory = self.generate_current_inventory(store_id)
        
        expiring_items = current_inventory[
            current_inventory['days_until_expiry'] <= warning_days
        ].copy()
        
        # Calculate suggested markdown percentage
        expiring_items['suggested_markdown'] = expiring_items['days_until_expiry'].apply(
            lambda x: min(50, max(10, (warning_days - x + 1) * 20))
        )
        
        # Determine action
        expiring_items['recommended_action'] = expiring_items['days_until_expiry'].apply(
            lambda x: 'DONATE' if x <= 0 else 'MARKDOWN' if x <= 1 else 'MONITOR'
        )
        
        return expiring_items[['store_id', 'product', 'batch_id', 'quantity', 
                              'days_until_expiry', 'suggested_markdown', 'recommended_action']]
    
    def optimize_stock_rotation(self, store_id):
        """Provide stock rotation recommendations"""
        current_inventory = self.generate_current_inventory(store_id)
        
        rotation_plan = []
        
        for product in current_inventory['product'].unique():
            product_inventory = current_inventory[
                current_inventory['product'] == product
            ].sort_values('days_until_expiry')
            
            for idx, row in product_inventory.iterrows():
                priority = 'URGENT' if row['days_until_expiry'] <= 1 else \
                          'HIGH' if row['days_until_expiry'] <= 3 else 'NORMAL'
                
                rotation_plan.append({
                    'store_id': store_id,
                    'product': product,
                    'batch_id': row['batch_id'],
                    'quantity': row['quantity'],
                    'days_until_expiry': row['days_until_expiry'],
                    'rotation_priority': priority,
                    'position': 'FRONT' if priority in ['URGENT', 'HIGH'] else 'BACK'
                })
        
        return pd.DataFrame(rotation_plan)
    
    def generate_inventory_report(self, store_id):
        """Generate comprehensive inventory report"""
        print(f"Generating inventory report for {store_id}...")
        
        current_inventory = self.generate_current_inventory(store_id)
        reorder_suggestions = self.calculate_reorder_suggestions(store_id)
        expiring_items = self.identify_expiring_items(store_id)
        rotation_plan = self.optimize_stock_rotation(store_id)
        
        report = {
            'store_id': store_id,
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_products': len(current_inventory['product'].unique()),
                'total_stock_value': len(current_inventory),  # Simplified
                'items_expiring_soon': len(expiring_items),
                'reorder_recommendations': len(reorder_suggestions[reorder_suggestions['recommended_order'] > 0])
            },
            'current_inventory': current_inventory,
            'reorder_suggestions': reorder_suggestions,
            'expiring_items': expiring_items,
            'rotation_plan': rotation_plan
        }
        
        return report
    
    def save_report_to_csv(self, report, filename_prefix="inventory_report"):
        """Save inventory report to CSV files"""
        store_id = report['store_id']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save each component
        report['current_inventory'].to_csv(f"{filename_prefix}_{store_id}_inventory_{timestamp}.csv", index=False)
        report['reorder_suggestions'].to_csv(f"{filename_prefix}_{store_id}_reorder_{timestamp}.csv", index=False)
        report['expiring_items'].to_csv(f"{filename_prefix}_{store_id}_expiring_{timestamp}.csv", index=False)
        report['rotation_plan'].to_csv(f"{filename_prefix}_{store_id}_rotation_{timestamp}.csv", index=False)
        
        print(f"Reports saved for {store_id}")

if __name__ == "__main__":
    manager = InventoryManager()
    
    # Generate report for Store_A
    report = manager.generate_inventory_report('Store_A')
    
    print("Inventory Summary:")
    print(f"- Total products: {report['summary']['total_products']}")
    print(f"- Items expiring soon: {report['summary']['items_expiring_soon']}")
    print(f"- Reorder recommendations: {report['summary']['reorder_recommendations']}")
    
    print("\nReorder Suggestions:")
    print(report['reorder_suggestions'][report['reorder_suggestions']['recommended_order'] > 0])
    
    print("\nExpiring Items:")
    print(report['expiring_items'])