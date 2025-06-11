import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from geopy.distance import geodesic
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

class RouteOptimizer:
    def __init__(self):
        self.stores_data = pd.read_csv('data/stores_data.csv')
        
        # Delivery urgency levels based on product type
        self.urgency_levels = {
            'URGENT': 1,    # Ice cream, frozen items
            'HIGH': 2,      # Dairy, meat
            'MEDIUM': 3,    # Fresh produce
            'LOW': 4        # Non-perishables
        }
        
        # Product categories
        self.product_urgency = {
            'Milk': 'HIGH', 'Eggs': 'HIGH', 'Yogurt': 'HIGH', 'Cheese': 'HIGH',
            'Chicken': 'URGENT', 'Lettuce': 'MEDIUM', 'Tomatoes': 'MEDIUM',
            'Bananas': 'MEDIUM', 'Apples': 'MEDIUM', 'Carrots': 'MEDIUM',
            'Bread': 'LOW', 'Potatoes': 'LOW'
        }
    
    def generate_delivery_orders(self, store_id, num_orders=20):
        """Generate sample delivery orders"""
        orders = []
        
        # Customer locations around the store
        store_location = self.stores_data[self.stores_data['store_id'] == store_id].iloc[0]
        store_lat, store_lon = store_location['lat'], store_location['lon']
        
        for i in range(num_orders):
            # Random customer location within 10km radius
            lat_offset = random.uniform(-0.1, 0.1)
            lon_offset = random.uniform(-0.1, 0.1)
            customer_lat = store_lat + lat_offset
            customer_lon = store_lon + lon_offset
            
            # Random order details
            num_items = random.randint(1, 5)
            order_items = random.sample(list(self.product_urgency.keys()), num_items)
            
            # Calculate order urgency (highest urgency item determines order urgency)
            order_urgency = min([self.urgency_levels[self.product_urgency[item]] for item in order_items])
            urgency_label = [k for k, v in self.urgency_levels.items() if v == order_urgency][0]
            
            # Order time - some orders are older (higher priority)
            order_time = datetime.now() - timedelta(hours=random.randint(0, 6))
            
            orders.append({
                'order_id': f"ORD_{store_id}_{i:03d}",
                'store_id': store_id,
                'customer_lat': customer_lat,
                'customer_lon': customer_lon,
                'items': order_items,
                'urgency_level': urgency_label,
                'urgency_score': order_urgency,
                'order_time': order_time,
                'estimated_prep_time': random.randint(5, 15),  # minutes
                'delivery_window': random.choice(['ASAP', '2-hour', '4-hour'])
            })
        
        return pd.DataFrame(orders)
    
    def calculate_distance_matrix(self, locations):
        """Calculate distance matrix between all locations"""
        n = len(locations)
        distance_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance = geodesic(
                        (locations[i]['lat'], locations[i]['lon']),
                        (locations[j]['lat'], locations[j]['lon'])
                    ).kilometers
                    distance_matrix[i][j] = distance * 1000  # Convert to meters
        
        return distance_matrix.astype(int)
    
    def optimize_routes(self, store_id, max_vehicles=3, vehicle_capacity=20):
        """Optimize delivery routes using Google OR-Tools"""
        print(f"Optimizing routes for {store_id}...")
        
        # Generate orders
        orders_df = self.generate_delivery_orders(store_id)
        
        # Filter urgent orders first
        urgent_orders = orders_df[orders_df['urgency_level'].isin(['URGENT', 'HIGH'])].copy()
        
        if len(urgent_orders) == 0:
            urgent_orders = orders_df.head(10)  # Take first 10 if no urgent orders
        
        # Prepare locations (store + customer locations)
        store_location = self.stores_data[self.stores_data['store_id'] == store_id].iloc[0]
        locations = [{'lat': store_location['lat'], 'lon': store_location['lon'], 'type': 'depot'}]
        
        for _, order in urgent_orders.iterrows():
            locations.append({
                'lat': order['customer_lat'],
                'lon': order['customer_lon'],
                'type': 'customer',
                'order_id': order['order_id'],
                'urgency_score': order['urgency_score']
            })
        
        # Calculate distance matrix
        distance_matrix = self.calculate_distance_matrix(locations)
        
        # Create routing model
        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix), max_vehicles, 0  # depot index is 0
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # Distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add capacity constraint
        demands = [0]  # depot has no demand
        for i in range(1, len(locations)):
            demands.append(1)  # each customer has demand of 1
        
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [vehicle_capacity] * max_vehicles,  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )
        
        # Add urgency constraint (priority)
        def urgency_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == 0:  # depot
                return 0
            return locations[from_node].get('urgency_score', 4)
        
        urgency_callback_index = routing.RegisterUnaryTransitCallback(urgency_callback)
        routing.AddDimension(
            urgency_callback_index,
            0,  # no slack
            10,  # maximum urgency
            True,  # start cumul to zero
            'Urgency'
        )
        
        # Setting first solution heuristic
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(10)
        
        # Solve
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            return self.extract_routes(manager, routing, solution, locations, urgent_orders)
        else:
            print("No solution found!")
            return None
    
    def extract_routes(self, manager, routing, solution, locations, orders_df):
        """Extract optimized routes from solution"""
        routes = []
        total_distance = 0
        
        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_load = 0
            route_locations = []
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route_load += 1 if node_index > 0 else 0
                
                location_info = {
                    'location_index': node_index,
                    'lat': locations[node_index]['lat'],
                    'lon': locations[node_index]['lon'],
                    'type': locations[node_index]['type']
                }
                
                if node_index > 0:  # Not depot
                    location_info['order_id'] = locations[node_index]['order_id']
                    location_info['urgency_score'] = locations[node_index]['urgency_score']
                
                route_locations.append(location_info)
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
            
            # Add final depot
            route_locations.append({
                'location_index': manager.IndexToNode(index),
                'lat': locations[0]['lat'],
                'lon': locations[0]['lon'],
                'type': 'depot_return'
            })
            
            if route_load > 0:  # Only include routes with deliveries
                routes.append({
                    'vehicle_id': vehicle_id,
                    'route_distance_km': route_distance / 1000,
                    'route_load': route_load,
                    'locations': route_locations,
                    'estimated_time_minutes': (route_distance / 1000) * 2.5 + route_load * 5  # 2.5 min/km + 5 min per stop
                })
            
            total_distance += route_distance
        
        return {
            'routes': routes,
            'total_distance_km': total_distance / 1000,
            'total_vehicles_used': len(routes),
            'optimization_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def add_real_time_constraints(self, routes, traffic_factor=1.2, weather_impact=1.0):
        """Add real-time constraints like traffic and weather"""
        adjusted_routes = []
        
        for route in routes['routes']:
            adjusted_route = route.copy()
            
            # Adjust time based on traffic and weather
            base_time = route['estimated_time_minutes']
            adjusted_time = base_time * traffic_factor * weather_impact
            
            # Add traffic delays
            traffic_delay = random.randint(5, 20) if traffic_factor > 1.1 else 0
            
            adjusted_route.update({
                'base_time_minutes': base_time,
                'adjusted_time_minutes': adjusted_time + traffic_delay,
                'traffic_delay_minutes': traffic_delay,
                'traffic_factor': traffic_factor,
                'weather_impact': weather_impact,
                'recommended_departure': datetime.now() + timedelta(minutes=10)
            })
            
            adjusted_routes.append(adjusted_route)
        
        return {
            'routes': adjusted_routes,
            'total_distance_km': routes['total_distance_km'],
            'total_vehicles_used': routes['total_vehicles_used'],
            'optimization_timestamp': routes['optimization_timestamp'],
            'real_time_adjustment': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def generate_delivery_schedule(self, optimized_routes):
        """Generate detailed delivery schedule with time windows"""
        schedule = []
        
        for route in optimized_routes['routes']:
            current_time = datetime.now()
            departure_time = current_time + timedelta(minutes=10)  # 10 min prep time
            
            for i, location in enumerate(route['locations']):
                if location['type'] == 'depot':
                    schedule.append({
                        'vehicle_id': route['vehicle_id'],
                        'stop_number': i,
                        'location_type': 'depot_start',
                        'scheduled_time': departure_time.strftime('%H:%M'),
                        'activity': 'Load vehicle and depart',
                        'duration_minutes': 10
                    })
                    current_time = departure_time + timedelta(minutes=10)
                    
                elif location['type'] == 'customer':
                    # Travel time to customer (simplified calculation)
                    travel_time = 15  # Average 15 minutes between stops
                    arrival_time = current_time + timedelta(minutes=travel_time)
                    
                    # Service time at customer
                    service_time = random.randint(3, 8)  # 3-8 minutes per delivery
                    
                    schedule.append({
                        'vehicle_id': route['vehicle_id'],
                        'stop_number': i,
                        'location_type': 'customer',
                        'order_id': location.get('order_id', ''),
                        'scheduled_arrival': arrival_time.strftime('%H:%M'),
                        'scheduled_departure': (arrival_time + timedelta(minutes=service_time)).strftime('%H:%M'),
                        'activity': 'Deliver order',
                        'duration_minutes': service_time,
                        'urgency_score': location.get('urgency_score', 4)
                    })
                    
                    current_time = arrival_time + timedelta(minutes=service_time)
                    
                elif location['type'] == 'depot_return':
                    return_time = current_time + timedelta(minutes=15)  # Return to depot
                    schedule.append({
                        'vehicle_id': route['vehicle_id'],
                        'stop_number': i,
                        'location_type': 'depot_return',
                        'scheduled_time': return_time.strftime('%H:%M'),
                        'activity': 'Return to depot',
                        'duration_minutes': 5
                    })
        
        return pd.DataFrame(schedule)
    
    def generate_route_report(self, store_id):
        """Generate comprehensive route optimization report"""
        print(f"Generating route optimization report for {store_id}...")
        
        # Optimize routes
        optimized_routes = self.optimize_routes(store_id)
        
        if not optimized_routes:
            return None
        
        # Add real-time constraints
        current_hour = datetime.now().hour
        traffic_factor = 1.3 if 7 <= current_hour <= 9 or 17 <= current_hour <= 19 else 1.0
        weather_impact = random.choice([1.0, 1.1, 1.2])  # Simulate weather conditions
        
        final_routes = self.add_real_time_constraints(
            optimized_routes, traffic_factor, weather_impact
        )
        
        # Generate delivery schedule
        delivery_schedule = self.generate_delivery_schedule(final_routes)
        
        # Generate summary
        summary = {
            'store_id': store_id,
            'total_routes': len(final_routes['routes']),
            'total_distance_km': round(final_routes['total_distance_km'], 2),
            'total_estimated_time_hours': round(
                sum([route['adjusted_time_minutes'] for route in final_routes['routes']]) / 60, 2
            ),
            'average_deliveries_per_route': round(
                sum([route['route_load'] for route in final_routes['routes']]) / len(final_routes['routes']), 1
            ) if final_routes['routes'] else 0,
            'traffic_conditions': 'Heavy' if traffic_factor > 1.2 else 'Moderate' if traffic_factor > 1.0 else 'Light',
            'weather_impact': 'High' if weather_impact > 1.15 else 'Moderate' if weather_impact > 1.05 else 'Low',
            'earliest_departure': min([route['recommended_departure'] for route in final_routes['routes']]).strftime('%H:%M') if final_routes['routes'] else 'N/A',
            'latest_return': 'N/A'  # Would calculate from delivery schedule
        }
        
        return {
            'summary': summary,
            'optimized_routes': final_routes,
            'delivery_schedule': delivery_schedule,
            'report_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def calculate_route_efficiency(self, route_report):
        """Calculate route efficiency metrics"""
        if not route_report:
            return None
        
        routes = route_report['optimized_routes']['routes']
        
        # Calculate efficiency metrics
        total_distance = sum([route['route_distance_km'] for route in routes])
        total_deliveries = sum([route['route_load'] for route in routes])
        total_time = sum([route['adjusted_time_minutes'] for route in routes])
        
        efficiency_metrics = {
            'distance_per_delivery': round(total_distance / total_deliveries, 2) if total_deliveries > 0 else 0,
            'time_per_delivery': round(total_time / total_deliveries, 2) if total_deliveries > 0 else 0,
            'vehicle_utilization': round((total_deliveries / (len(routes) * 20)) * 100, 1),  # Assuming 20 capacity
            'route_compactness': 'High' if total_distance / len(routes) < 15 else 'Medium' if total_distance / len(routes) < 25 else 'Low'
        }
        
        return efficiency_metrics
    
    def save_routes_to_csv(self, route_report, filename_prefix="routes"):
        """Save route optimization results to CSV"""
        if not route_report:
            return
        
        store_id = route_report['summary']['store_id']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Prepare route details for CSV
        route_details = []
        for route in route_report['optimized_routes']['routes']:
            for i, location in enumerate(route['locations']):
                route_details.append({
                    'vehicle_id': route['vehicle_id'],
                    'stop_sequence': i,
                    'location_type': location['type'],
                    'lat': location['lat'],
                    'lon': location['lon'],
                    'order_id': location.get('order_id', ''),
                    'urgency_score': location.get('urgency_score', ''),
                    'route_distance_km': route['route_distance_km'],
                    'estimated_time_minutes': route['adjusted_time_minutes'],
                    'traffic_delay_minutes': route['traffic_delay_minutes']
                })
        
        # Save to CSV
        routes_df = pd.DataFrame(route_details)
        routes_df.to_csv(f"{filename_prefix}_{store_id}_{timestamp}.csv", index=False)
        
        # Save summary
        summary_df = pd.DataFrame([route_report['summary']])
        summary_df.to_csv(f"{filename_prefix}_summary_{store_id}_{timestamp}.csv", index=False)
        
        # Save delivery schedule
        if 'delivery_schedule' in route_report:
            route_report['delivery_schedule'].to_csv(f"{filename_prefix}_schedule_{store_id}_{timestamp}.csv", index=False)
        
        print(f"Route optimization results saved for {store_id}")
    
    def simulate_real_time_updates(self, route_report):
        """Simulate real-time route updates"""
        if not route_report:
            return None
        
        print("Simulating real-time route updates...")
        
        updates = []
        for route in route_report['optimized_routes']['routes']:
            # Simulate random events
            event_type = random.choice(['traffic_delay', 'delivery_completed', 'customer_unavailable', 'no_change'])
            
            if event_type == 'traffic_delay':
                delay_minutes = random.randint(10, 30)
                updates.append({
                    'vehicle_id': route['vehicle_id'],
                    'event_type': 'traffic_delay',
                    'delay_minutes': delay_minutes,
                    'new_eta': (datetime.now() + timedelta(minutes=route['adjusted_time_minutes'] + delay_minutes)).strftime('%H:%M'),
                    'recommended_action': 'Notify customers of delay'
                })
            
            elif event_type == 'customer_unavailable':
                updates.append({
                    'vehicle_id': route['vehicle_id'],
                    'event_type': 'customer_unavailable',
                    'recommended_action': 'Reschedule delivery or leave at safe location'
                })
            
            elif event_type == 'delivery_completed':
                updates.append({
                    'vehicle_id': route['vehicle_id'],
                    'event_type': 'delivery_completed',
                    'recommended_action': 'Proceed to next stop'
                })
        
        return updates

if __name__ == "__main__":
    optimizer = RouteOptimizer()
    
    # Generate route report for Store_A
    report = optimizer.generate_route_report('Store_A')
    
    if report:
        print("Route Optimization Summary:")
        print(f"- Total routes: {report['summary']['total_routes']}")
        print(f"- Total distance: {report['summary']['total_distance_km']} km")
        print(f"- Total estimated time: {report['summary']['total_estimated_time_hours']} hours")
        print(f"- Traffic conditions: {report['summary']['traffic_conditions']}")
        print(f"- Weather impact: {report['summary']['weather_impact']}")
        print(f"- Earliest departure: {report['summary']['earliest_departure']}")
        
        # Show route details
        for i, route in enumerate(report['optimized_routes']['routes']):
            print(f"\nRoute {i+1} (Vehicle {route['vehicle_id']}):")
            print(f"  - Deliveries: {route['route_load']}")
            print(f"  - Distance: {route['route_distance_km']:.1f} km")
            print(f"  - Estimated time: {route['adjusted_time_minutes']:.0f} minutes")
            if route['traffic_delay_minutes'] > 0:
                print(f"  - Traffic delay: {route['traffic_delay_minutes']} minutes")
        
        # Calculate efficiency metrics
        efficiency = optimizer.calculate_route_efficiency(report)
        if efficiency:
            print(f"\nEfficiency Metrics:")
            print(f"  - Distance per delivery: {efficiency['distance_per_delivery']} km")
            print(f"  - Time per delivery: {efficiency['time_per_delivery']} minutes")
            print(f"  - Vehicle utilization: {efficiency['vehicle_utilization']}%")
            print(f"  - Route compactness: {efficiency['route_compactness']}")
        
        # Save results
        optimizer.save_routes_to_csv(report)
        
        # Simulate real-time updates
        real_time_updates = optimizer.simulate_real_time_updates(report)
        if real_time_updates:
            print(f"\nReal-time Updates:")
            for update in real_time_updates:
                print(f"  - Vehicle {update['vehicle_id']}: {update['event_type']}")
                print(f"    Action: {update['recommended_action']}")
                if 'delay_minutes' in update:
                    print(f"    Delay: {update['delay_minutes']} minutes")
                if 'new_eta' in update:
                    print(f"    New ETA: {update['new_eta']}")
    else:
        print("Could not generate route optimization report.")