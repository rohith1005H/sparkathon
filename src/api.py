from flask import Flask, jsonify, request, render_template
from main import ShelfLifeSavers
from datetime import datetime, timedelta
import json

app = Flask(__name__, template_folder='templates', static_folder='static')
shelf_life_system = ShelfLifeSavers()

# Load model on startup
try:
    shelf_life_system.demand_predictor.load_model()
    print("Model loaded successfully!")
except Exception as e:
    print(f"Could not load model. Please run setup first. Error: {e}")

# This route now serves your HTML dashboard
@app.route('/')
def home():
    """Serves the main dashboard page."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict_demand():
    """Predict demand for a specific product."""
    try:
        data = request.json
        store_id = data.get('store_id', 'Store_A')
        product = data.get('product', 'Milk')
        # Predict for tomorrow by default
        target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        prediction = shelf_life_system.demand_predictor.predict_demand(store_id, product, target_date)
        
        return jsonify({
            "store_id": store_id,
            "product": product,
            "date": target_date,
            "predicted_demand": prediction,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# CORRECTED ROUTE: Added <store_id> parameter
@app.route('/inventory/<store_id>')
def get_inventory_report(store_id):
    """Get inventory report for a store."""
    try:
        report = shelf_life_system.inventory_manager.generate_inventory_report(store_id)
        result = {
            "store_id": store_id,
            "summary": report['summary'],
            "reorder_suggestions": report['reorder_suggestions'].to_dict('records'),
            "expiring_items": report['expiring_items'].to_dict('records'),
            "report_timestamp": report['report_date']
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# CORRECTED ROUTE: Added <store_id> parameter
@app.route('/routes/<store_id>')
def get_route_optimization(store_id):
    """Get route optimization for a store."""
    try:
        report = shelf_life_system.route_optimizer.generate_route_report(store_id)
        if report:
            # Convert DataFrames in the report to JSON serializable format if any
            if 'delivery_schedule' in report and isinstance(report['delivery_schedule'], pd.DataFrame):
                report['delivery_schedule'] = report['delivery_schedule'].to_dict('records')
            return jsonify(report)
        else:
            return jsonify({"error": "Could not generate route optimization"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# CORRECTED ROUTE: Added <store_id> parameter
@app.route('/operations/<store_id>')
def run_daily_operations(store_id):
    """Run complete daily operations for a store."""
    try:
        result = shelf_life_system.run_daily_operations(store_id)
        response = {
            "store_id": store_id,
            "timestamp": result['timestamp'],
            "inventory_summary": result['inventory_report']['summary'],
            "route_summary": result['route_report']['summary'] if result['route_report'] else None,
            "status": "completed"
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
