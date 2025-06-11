# ShelfLife Savers: Intelligent Inventory & Logistics System

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.2.2-blue)
![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.1.2-orange)
![License](https://img.shields.io/badge/license-MIT-green.svg)

An integrated system designed to help retail stores reduce waste and optimize operations through intelligent demand forecasting, dynamic inventory management, and efficient route planning.

---

## 核心功能 (Core Features)

This project combines several key components into a single, powerful tool for retail management:

*   🔮 Demand Forecasting: Utilizes a Random Forest model trained on historical sales, weather patterns, and promotional events to accurately predict future product demand[3].
*   📦 Dynamic Inventory Management: Generates daily reports on items that need reordering, are about to expire, and suggests actions like markdowns to minimize waste[4].
*   🚚 Optimized Delivery Routing: Uses Google OR-Tools to calculate the most efficient delivery routes for customer orders, considering vehicle capacity, delivery urgency, and real-time factors like traffic[6].
*   🖥️ Interactive Web Dashboard: A user-friendly frontend built with Flask, HTML, and JavaScript allows for easy interaction with the system's core features without needing to use the command line[1].

## System Architecture

The system is designed with a modular architecture that separates concerns, making it scalable and easy to maintain.
+-------------------+ +---------------------+ +---------------------+
| Data Sources |----->| ShelfLife Savers |----->| Outputs |
| (Generated CSVs) | | (Python Backend) | | |
+-------------------+ +---------------------+ +---------------------+
| - sales_history | | 1. Demand Predictor | | - JSON via API |
| - weather_data | | 2. Inventory Manager| | - CSV Reports |
| - events_data | | 3. Route Optimizer | | - Web Dashboard |
| - stores_data | | 4. Flask API Server | | |
+-------------------+ +---------------------+ +---------------------+



## Tech Stack

*   Backend: Python, Flask[1]
*   Machine Learning: Scikit-learn, Pandas, NumPy[3]
*   Optimization: Google OR-Tools[6]
*   Frontend: HTML, CSS, Vanilla JavaScript
*   Data Handling: Joblib, Geopy

## Getting Started

Follow these steps to set up and run the project on your local machine.

### Prerequisites

*   Python 3.10 or newer
*   `pip` and `venv`

### Installation & Setup

1.  Clone the repository:
    ```
    git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
    cd YOUR_REPOSITORY_NAME
    ```

2.  Create and activate a virtual environment:
    ```
    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate

    # For Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  Install the required dependencies:
    *(Note: A `requirements.txt` file is recommended. You can create one with the command `pip freeze > requirements.txt` after installing the packages below.)*
    ```
    pip install flask pandas numpy scikit-learn joblib geopy ortools
    ```

4.  Run the initial system setup:
    This one-time command will create the necessary directories (`data/`, `models/`, `reports/`), generate all dummy data, and train the demand prediction model[5].
    ```
    python src/main.py setup
    ```
    You should see output confirming that data was generated and the model was trained successfully.

## Usage

You can interact with the ShelfLife Savers system in three ways:

### 1. Web Dashboard (Recommended)

The most user-friendly way to use the application.

1.  Start the Flask API server:
    ```
    python src/api.py
    ```
2.  Open your web browser and navigate to:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

You can now use the dashboard to predict demand and run daily operations for any store.

### 2. Command-Line Interface (CLI)

The `main.py` script provides several commands for direct interaction from your terminal[5].

*   Run a full demo for multiple stores:
    ```
    python src/main.py demo
    ```

*   Run daily operations for a single store:
    ```
    python src/main.py operations Store_B
    ```

*   Predict demand for a specific product:
    ```
    python src/main.py predict Store_A Milk 7
    ```

### 3. API Endpoints

The Flask API exposes several endpoints for programmatic access[1].

| Method | Endpoint                    | Description                                         |
| :----- | :-------------------------- | :-------------------------------------------------- |
| `GET`  | `/`                         | Serves the main web dashboard.                      |
| `POST` | `/predict`                  | Predicts demand for a given product and store.      |
| `GET`  | `/operations/<store_id>`    | Runs full daily operations for the specified store. |
| `GET`  | `/inventory/<store_id>`     | Returns a detailed inventory report for the store.  |
| `GET`  | `/routes/<store_id>`        | Returns an optimized delivery route plan.           |

Example using `curl`:
curl -X POST
-H "Content-Type: application/json"
-d '{"store_id": "Store_A", "product": "Bread"}'
http://127.0.0.1:5000/predict


## Project Structure

The project is organized to separate concerns, with all source code located in the `src/` directory.

.
├── .gitignore # Files to be ignored by Git
├── README.md # This file
└── src/
├── main.py # Main entry point for CLI and orchestration
├── api.py # Flask web server and API endpoints
├── data_generator.py # Generates all required dummy data
├── demand_predictor.py # Handles model training and prediction
├── inventory_manager.py # Manages stock levels and reordering
├── route_optimizer.py # Optimizes delivery routes
├── static/ # CSS and JavaScript for the frontend
│ ├── css/style.css
│ └── js/script.js
└── templates/ # HTML templates for the frontend
└── index.html


*   `data/`: (Generated) Contains all raw data CSVs.
*   `models/`: (Generated) Stores the trained machine learning model (`.pkl`) files.
*   `reports/`: (Generated) Stores all output CSVs from inventory and route reports.

## Future Improvements

*   User Authentication: Secure the API and dashboard with user login.
*   Database Integration: Replace CSV files with a robust database (e.g., PostgreSQL) for better data management.
*   Real-Time Data: Integrate with real-time weather and traffic APIs for more accurate predictions and routing.
*   CI/CD Pipeline: Implement a CI/CD pipeline using GitHub Actions to automate testing and deployment.
