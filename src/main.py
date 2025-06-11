import os
import sys
from datetime import datetime, timedelta
from data_generator import DataGenerator
from demand_predictor import DemandPredictor
from inventory_manager import InventoryManager
from route_optimizer import RouteOptimizer

class ShelfLifeSavers:
    def __init__(self):
        self.data_generator = DataGenerator()
        self.demand_predictor = DemandPredictor()
        self.inventory_manager = InventoryManager()
        self.route_optimizer = RouteOptimizer()
        
    def setup_system(self):
        """Initial setup of the system"""
        print("🚀 Setting up ShelfLife Savers System...")
        
        # Create directories
        os.makedirs('data', exist_ok=True)
        os.makedirs('models', exist_ok=True)
        os.makedirs('reports', exist_ok=True)
        
        # Generate initial data
        print("📊 Generating dummy data...")
        self.data_generator.generate_all_data()
        
        # Train demand prediction model
        print("🧠 Training demand prediction model...")
        self.demand_predictor.train_model()
        
        print("✅ System setup complete!")
    
    def run_daily_operations(self, store_id='Store_A'):
        """Run daily operations for a specific store"""
        print(f"\n🏪 Running daily operations for {store_id}")
        print("=" * 50)
        
        # 1. Generate inventory report
        print("📦 Generating inventory report...")
        inventory_report = self.inventory_manager.generate_inventory_report(store_id)
        
        print(f"Inventory Summary for {store_id}:")
        print(f"  - Total products: {inventory_report['summary']['total_products']}")
        print(f"  - Items expiring soon: {inventory_report['summary']['items_expiring_soon']}")
        print(f"  - Reorder recommendations: {inventory_report['summary']['reorder_recommendations']}")
        
        # Show reorder suggestions
        reorder_df = inventory_report['reorder_suggestions']
        urgent_reorders = reorder_df[reorder_df['recommended_order'] > 0]
        
        if len(urgent_reorders) > 0:
            print(f"\n📋 Urgent Reorder Recommendations:")
            for _, row in urgent_reorders.iterrows():
                print(f"  - {row['product']}: Order {row['recommended_order']} units")
                print(f"    Current stock: {row['current_stock']}, Predicted demand (7d): {row['predicted_demand_7d']}")
        
        # Show expiring items
        expiring_items = inventory_report['expiring_items']
        if len(expiring_items) > 0:
            print(f"\n⚠️  Items Expiring Soon:")
            for _, row in expiring_items.iterrows():
                print(f"  - {row['product']} (Batch: {row['batch_id']}): {row['quantity']} units")
                print(f"    Days until expiry: {row['days_until_expiry']}, Action: {row['recommended_action']}")
                if row['recommended_action'] == 'MARKDOWN':
                    print(f"    Suggested markdown: {row['suggested_markdown']}%")
        
        # 2. Optimize delivery routes
        print(f"\n🚛 Optimizing delivery routes...")
        route_report = self.route_optimizer.generate_route_report(store_id)
        
        if route_report:
            print(f"Route Optimization Summary:")
            print(f"  - Total routes: {route_report['summary']['total_routes']}")
            print(f"  - Total distance: {route_report['summary']['total_distance_km']} km")
            print(f"  - Estimated time: {route_report['summary']['total_estimated_time_hours']} hours")
            print(f"  - Traffic conditions: {route_report['summary']['traffic_conditions']}")
            
            # Show route details
            for i, route in enumerate(route_report['optimized_routes']['routes']):
                print(f"\n  Route {i+1} (Vehicle {route['vehicle_id']}):")
                print(f"    - Deliveries: {route['route_load']}")
                print(f"    - Distance: {route['route_distance_km']:.1f} km")
                print(f"    - Estimated time: {route['adjusted_time_minutes']:.0f} minutes")
                if route['traffic_delay_minutes'] > 0:
                    print(f"    - Traffic delay: {route['traffic_delay_minutes']} minutes")
        
        # 3. Save reports
        print(f"\n💾 Saving reports...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save inventory reports
        self.inventory_manager.save_report_to_csv(inventory_report, f"reports/inventory_report")
        
        # Save route reports
        if route_report:
            self.route_optimizer.save_routes_to_csv(route_report, f"reports/routes")
        
        print(f"Reports saved with timestamp: {timestamp}")
        
        return {
            'inventory_report': inventory_report,
            'route_report': route_report,
            'timestamp': timestamp
        }
    
    def predict_future_demand(self, store_id, product, days_ahead=7):
        """Predict demand for specific product for next N days"""
        print(f"\n🔮 Predicting demand for {product} at {store_id} for next {days_ahead} days:")
        
        predictions = []
        for day in range(1, days_ahead + 1):
            future_date = (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d')
            predicted_demand = self.demand_predictor.predict_demand(store_id, product, future_date)
            predictions.append({
                'date': future_date,
                'predicted_demand': predicted_demand
            })
            print(f"  {future_date}: {predicted_demand} units")
        
        total_demand = sum([p['predicted_demand'] for p in predictions])
        print(f"  Total predicted demand: {total_demand} units")
        
        return predictions
    
    def run_demo(self):
        """Run a complete demo of the system"""
        print("🎬 Running ShelfLife Savers Demo")
        print("=" * 60)
        
        # Setup if needed
        if not os.path.exists('data/sales_history.csv'):
            self.setup_system()
        else:
            # Load existing model
            self.demand_predictor.load_model()
        
        # Run operations for all stores
        stores = ['Store_A', 'Store_B', 'Store_C']
        
        for store in stores:
            operations_result = self.run_daily_operations(store)
            
            # Show demand prediction for a random product
            import random
            random_product = random.choice(['Milk', 'Bread', 'Bananas', 'Apples'])
            self.predict_future_demand(store, random_product, 3)
            
            print("\n" + "-" * 60)
        
        print("\n🎉 Demo completed successfully!")
        print("Check the 'reports' folder for detailed CSV reports.")

def main():
    """Main entry point"""
    app = ShelfLifeSavers()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'setup':
            app.setup_system()
        elif command == 'demo':
            app.run_demo()
        elif command == 'operations':
            store_id = sys.argv[2] if len(sys.argv) > 2 else 'Store_A'
            app.run_daily_operations(store_id)
        elif command == 'predict':
            store_id = sys.argv[2] if len(sys.argv) > 2 else 'Store_A'
            product = sys.argv[3] if len(sys.argv) > 3 else 'Milk'
            days = int(sys.argv[4]) if len(sys.argv) > 4 else 7
            app.predict_future_demand(store_id, product, days)
        else:
            print("Available commands: setup, demo, operations [store_id], predict [store_id] [product] [days]")
    else:
        # Run demo by default
        app.run_demo()

if __name__ == "__main__":
    main()