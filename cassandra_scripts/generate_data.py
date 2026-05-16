import uuid
import random
from datetime import datetime, timedelta

def generate_cql():
    users = []
    products = []
    
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
    states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"]
    categories = ["Electronics", "Clothing", "Home & Garden", "Books", "Toys", "Sports"]
    statuses = ["PENDING", "SHIPPED", "DELIVERED", "CANCELLED"]

    cql_lines = ["USE ecommerce_demo;"]

    # Generate Users
    for i in range(100):
        u_id = uuid.uuid4()
        users.append(u_id)
        first = f"User{i}"
        last = f"Lastname{i}"
        email = f"user{i}@example.com"
        city_idx = random.randint(0, 9)
        cql_lines.append(f"INSERT INTO users (user_id, first_name, last_name, email, city, state, created_at) VALUES ({u_id}, '{first}', '{last}', '{email}', '{cities[city_idx]}', '{states[city_idx]}', toTimestamp(now()));")

    # Generate Products
    for i in range(50):
        p_id = uuid.uuid4()
        products.append(p_id)
        name = f"Product {i}"
        cat = random.choice(categories)
        price = round(random.uniform(10.0, 500.0), 2)
        stock = random.randint(0, 1000)
        cql_lines.append(f"INSERT INTO products (product_id, name, category, price, stock_quantity, created_at) VALUES ({p_id}, '{name}', '{cat}', {price}, {stock}, toTimestamp(now()));")

    # Generate Orders
    for i in range(200):
        u_id = random.choice(users)
        o_id = uuid.uuid4()
        date = datetime.now() - timedelta(days=random.randint(0, 30))
        date_str = date.strftime('%Y-%m-%d %H:%M:%S')
        amount = round(random.uniform(20.0, 1000.0), 2)
        status = random.choice(statuses)
        cql_lines.append(f"INSERT INTO orders_by_user (user_id, order_id, order_date, total_amount, status) VALUES ({u_id}, {o_id}, '{date_str}', {amount}, '{status}');")

    # Generate Inventory Log
    for p_id in products:
        for _ in range(5):
            change = random.randint(-10, 50)
            reason = "Restock" if change > 0 else "Sale"
            cql_lines.append(f"INSERT INTO inventory_log (product_id, movement_id, change_amount, reason, timestamp) VALUES ({p_id}, now(), {change}, '{reason}', toTimestamp(now()));")

    with open('insert_data.cql', 'w') as f:
        f.write('\n'.join(cql_lines))

if __name__ == "__main__":
    generate_cql()
