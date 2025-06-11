document.addEventListener('DOMContentLoaded', () => {
    // --- Populate Product Dropdown ---
    const products = [
        'Milk', 'Bread', 'Eggs', 'Bananas', 'Apples', 'Lettuce',
        'Tomatoes', 'Chicken', 'Yogurt', 'Cheese', 'Carrots', 'Potatoes'
    ];
    const productDropdown = document.getElementById('predict-product');
    products.forEach(product => {
        const option = document.createElement('option');
        option.value = product;
        option.textContent = product;
        productDropdown.appendChild(option);
    });

    // --- DOM Elements ---
    const predictForm = document.getElementById('predict-form');
    const operationsForm = document.getElementById('operations-form');
    const predictionResultDiv = document.getElementById('prediction-result');
    const operationsResultDiv = document.getElementById('operations-result');

    // --- Event Listener for Prediction Form ---
    predictForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const storeId = document.getElementById('predict-store').value;
        const product = document.getElementById('predict-product').value;
        
        predictionResultDiv.innerHTML = '<p>Loading prediction...</p>';

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ store_id: storeId, product: product })
            });
            const data = await response.json();

            if (response.ok) {
                predictionResultDiv.innerHTML = `
                    <h3>Prediction Result</h3>
                    <p><strong>Store:</strong> ${data.store_id}</p>
                    <p><strong>Product:</strong> ${data.product}</p>
                    <p><strong>Date:</strong> ${data.date}</p>
                    <p><strong>Predicted Demand:</strong> ${data.predicted_demand} units</p>
                `;
            } else {
                throw new Error(data.error || 'Prediction failed.');
            }
        } catch (error) {
            predictionResultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        }
    });

    // --- Event Listener for Operations Form ---
    operationsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const storeId = document.getElementById('operations-store').value;
        
        operationsResultDiv.innerHTML = '<p>Running operations, please wait...</p>';

        try {
            const response = await fetch(`/operations/${storeId}`);
            const data = await response.json();

            if (response.ok) {
                operationsResultDiv.innerHTML = `
                    <h3>Operations Summary for ${data.store_id}</h3>
                    <p><strong>Status:</strong> ${data.status}</p>
                    <p><strong>Inventory Summary:</strong></p>
                    <ul>
                        <li>Total Products: ${data.inventory_summary.total_products}</li>
                        <li>Items Expiring Soon: ${data.inventory_summary.items_expiring_soon}</li>
                        <li>Reorder Recommendations: ${data.inventory_summary.reorder_recommendations}</li>
                    </ul>
                    <p><strong>Route Summary:</strong></p>
                    <ul>
                        <li>Total Routes: ${data.route_summary ? data.route_summary.total_routes : 'N/A'}</li>
                        <li>Total Distance: ${data.route_summary ? data.route_summary.total_distance_km : 'N/A'} km</li>
                    </ul>
                `;
            } else {
                throw new Error(data.error || 'Operation failed.');
            }
        } catch (error) {
            operationsResultDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        }
    });
});
