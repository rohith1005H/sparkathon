import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import os
from datetime import datetime, timedelta

class DemandPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.encoders = {}
        self.is_trained = False
        
    def load_data(self):
        """Load all necessary data for prediction"""
        sales_df = pd.read_csv('data/sales_history.csv')
        weather_df = pd.read_csv('data/weather_data.csv')
        events_df = pd.read_csv('data/events_data.csv')
        
        # Merge data
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        weather_df['date'] = pd.to_datetime(weather_df['date'])
        events_df['date'] = pd.to_datetime(events_df['date'])
        
        # Merge sales with weather
        merged_df = pd.merge(sales_df, weather_df, on='date', how='left')
        
        # Create events impact column
        merged_df['event_impact'] = 1.0
        for _, event in events_df.iterrows():
            mask = merged_df['date'] == event['date']
            merged_df.loc[mask, 'event_impact'] = event['impact']
        
        return merged_df
    
    def create_features(self, df):
        """Create features for machine learning"""
        df = df.copy()
        
        # Date features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Lag features (previous sales)
        df = df.sort_values(['store_id', 'product', 'date'])
        df['sales_lag_1'] = df.groupby(['store_id', 'product'])['quantity_sold'].shift(1)
        df['sales_lag_7'] = df.groupby(['store_id', 'product'])['quantity_sold'].shift(7)
        df['sales_rolling_7'] = df.groupby(['store_id', 'product'])['quantity_sold'].rolling(7).mean().reset_index(level=['store_id', 'product'], drop=True)
        
        # Fill NaN values
        df['sales_lag_1'].fillna(df.groupby(['store_id', 'product'])['quantity_sold'].transform('mean'), inplace=True)
        df['sales_lag_7'].fillna(df.groupby(['store_id', 'product'])['quantity_sold'].transform('mean'), inplace=True)
        df['sales_rolling_7'].fillna(df.groupby(['store_id', 'product'])['quantity_sold'].transform('mean'), inplace=True)
        
        return df
    
    def encode_categorical_features(self, df, fit=True):
        """Encode categorical features"""
        categorical_cols = ['store_id', 'product', 'weather_condition']
        
        for col in categorical_cols:
            if fit:
                if col not in self.encoders:
                    self.encoders[col] = LabelEncoder()
                df[col + '_encoded'] = self.encoders[col].fit_transform(df[col])
            else:
                df[col + '_encoded'] = self.encoders[col].transform(df[col])
        
        return df
    
    def prepare_features(self, df, fit=True):
        """Prepare features for training/prediction"""
        df = self.create_features(df)
        df = self.encode_categorical_features(df, fit=fit)
        
        feature_columns = [
            'year', 'month', 'day', 'day_of_week', 'is_weekend',
            'temperature', 'humidity', 'precipitation',
            'event_impact', 'sales_lag_1', 'sales_lag_7', 'sales_rolling_7',
            'store_id_encoded', 'product_encoded', 'weather_condition_encoded'
        ]
        
        return df[feature_columns], df['quantity_sold'] if 'quantity_sold' in df.columns else None
    
    def train_model(self):
        """Train the demand prediction model"""
        print("Loading training data...")
        df = self.load_data()
        
        print("Preparing features...")
        X, y = self.prepare_features(df, fit=True)
        
        # Remove rows with NaN values
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask]
        y = y[mask]
        
        print(f"Training on {len(X)} samples...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        
        print(f"Model Performance:")
        print(f"MAE: {mae:.2f}")
        print(f"RMSE: {np.sqrt(mse):.2f}")
        
        # Save model
        os.makedirs('models', exist_ok=True)
        joblib.dump(self.model, 'models/demand_model.pkl')
        joblib.dump(self.encoders, 'models/encoders.pkl')
        
        self.is_trained = True
        print("Model trained and saved successfully!")
        
        return {'mae': mae, 'rmse': np.sqrt(mse)}
    
    def load_model(self):
        """Load pre-trained model"""
        if os.path.exists('models/demand_model.pkl'):
            self.model = joblib.load('models/demand_model.pkl')
            self.encoders = joblib.load('models/encoders.pkl')
            self.is_trained = True
            print("Model loaded successfully!")
            return True
        return False
    
    def predict_demand(self, store_id, product, target_date, weather_forecast=None):
        """Predict demand for specific product at specific store"""
        if not self.is_trained:
            if not self.load_model():
                raise ValueError("Model not trained. Please train the model first.")
        
        # Create prediction data
        pred_data = {
            'date': [pd.to_datetime(target_date)],
            'store_id': [store_id],
            'product': [product],
            'temperature': [weather_forecast.get('temperature', 20) if weather_forecast else 20],
            'humidity': [weather_forecast.get('humidity', 60) if weather_forecast else 60],
            'precipitation': [weather_forecast.get('precipitation', 0) if weather_forecast else 0],
            'weather_condition': [weather_forecast.get('condition', 'Sunny') if weather_forecast else 'Sunny'],
        }
        
        pred_df = pd.DataFrame(pred_data)
        
        # Add historical data for lag features
        historical_df = self.load_data()
        combined_df = pd.concat([historical_df, pred_df], ignore_index=True)
        combined_df['event_impact'] = 1.0  # Default no event impact
        
        # Prepare features
        X, _ = self.prepare_features(combined_df, fit=False)
        
        # Get the last row (our prediction row)
        X_pred = X.iloc[-1:].fillna(method='ffill').fillna(0)
        
        # Make prediction
        prediction = self.model.predict(X_pred)[0]
        
        return max(0, int(prediction))
    
    def predict_multiple(self, predictions_list):
        """Predict demand for multiple items"""
        results = []
        for pred in predictions_list:
            try:
                demand = self.predict_demand(
                    pred['store_id'], 
                    pred['product'], 
                    pred['date'],
                    pred.get('weather_forecast')
                )
                results.append({
                    'store_id': pred['store_id'],
                    'product': pred['product'],
                    'date': pred['date'],
                    'predicted_demand': demand
                })
            except Exception as e:
                print(f"Error predicting for {pred}: {e}")
                results.append({
                    'store_id': pred['store_id'],
                    'product': pred['product'],
                    'date': pred['date'],
                    'predicted_demand': 0,
                    'error': str(e)
                })
        
        return results

if __name__ == "__main__":
    predictor = DemandPredictor()
    predictor.train_model()
    
    # Test prediction
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    prediction = predictor.predict_demand('Store_A', 'Milk', tomorrow)
    print(f"Predicted demand for Milk at Store_A tomorrow: {prediction}")