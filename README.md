# 🚕 Employee Cab Pooling & Smart Pickup Routing

A Flask + MySQL based employee transportation system that groups employees into shared cabs and generates smart pickup routes while respecting **cab capacity, maximum ride time, and night safety constraints**.

Live Demo: [Employee Cab Pooling](https://employee-cab-pooling.up.railway.app/)

## ✨ Features

- Employee registration and login
- Admin authentication
- Employee cab booking and cancellation
- Geographic employee pooling
- Grid-based location grouping
- Cab capacity enforcement
- Nearest-neighbour pickup routing
- Pickup ETA calculation
- Maximum ride-time validation
- Night safety validation
- Automatic night-route reordering
- Guard/escort fallback for unsafe routes
- Late booking placement into existing cabs
- Automatic route re-planning
- Duplicate booking protection
- Unit tests for pooling and routing

## 🛠️ Tech Stack

- **Python**
- **Flask**
- **MySQL**
- **Jinja2**
- **mysql-connector-python**
- **unittest**

## 📁 Project Structure

```text
Cab-Pooling-System/
│
├── app.py
├── config.py
├── database.py
├── create_admin.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── routes/
│   ├── admin.py
│   ├── auth.py
│   ├── booking.py
│   ├── employee.py
│   └── pooling.py
│
├── services/
│   ├── pooling.py
│   └── routing.py
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── employee_dashboard.html
│   ├── admin_dashboard.html
│   ├── book_cab.html
│   ├── my_bookings.html
│   ├── generate_pool.html
│   ├── cab_pools.html
│   └── route.html
│
├── tests/
│   ├── test_pooling.py
│   └── test_routing.py
│
└── sql/
    └── database.sql
````

## ⚙️ Setup

### 1. Create Virtual Environment

```powershell
python -m venv venv
```

### 2. Activate Environment

```powershell
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure MySQL

Create the database using:

```text
sql/database.sql
```

Or from MySQL command line:

```bash
mysql -u root -p < sql/database.sql
```

### 5. Create `.env`

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=cab_pooling
SECRET_KEY=your_secret_key
```

> Do not commit `.env` to GitHub.

### 6. Create Admin

```powershell
python create_admin.py
```

### 7. Start Application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## 🗺️ Routing Algorithm

The system uses a **nearest-neighbour heuristic** instead of solving the full Vehicle Routing Problem.

1. Employees are grouped based on geographic proximity.
2. The employee farthest from the office is selected as the first pickup.
3. The nearest unvisited employee is selected next.
4. The process continues until all employees are included.
5. The resulting route is validated against the maximum ride-time limit.

For `k` employees, nearest-neighbour routing takes approximately:

```text
O(k²)
```

An exact approach could require:

```text
O(k!)
```

possible pickup sequences, so the heuristic provides better performance for practical cab sizes such as 4 or 6 employees.

## 📍 Geographic Pooling

Employees are mapped into geographic grid cells.

Nearby cells are searched when creating cab groups, reducing unnecessary comparisons compared with checking every employee against every other employee.

Approximate complexity:

```text
O(n + candidate comparisons)
```

Distance is calculated using the **Haversine formula**.

> Haversine provides straight-line distance. A production version could use Google Maps, Mapbox, OSRM, or another road-routing service for real road distances.

## 🌙 Night Safety

Night shifts are defined as:

```text
22:00 - 06:00
```

The system checks whether a single female employee becomes the **first pickup or final drop**.

If the route is unsafe:

1. Alternative pickup orders are tested.
2. A safe route is selected when possible.
3. If no safe route exists, a guard/escort requirement is triggered.

Worst-case night-route search:

```text
O(k!)
```

This is practical because cab capacity is small.

## 🔄 Dynamic Booking & Re-planning

### Late Booking

A late booking:

* Finds active cabs for the same shift/date.
* Checks available capacity.
* Temporarily adds the employee.
* Validates the new route.
* Checks maximum ride time.
* Assigns the booking only if valid.
* Recalculates the affected cab.

Unrelated cabs are not rebuilt.

### Cancellation

When an employee cancels:

```text
Booking → CANCELLED
        ↓
Remove from Cab
        ↓
Recalculate Route
```

Only the affected cab is re-planned.

## 🛡️ Duplicate Booking Protection

The database prevents a booking from being assigned to multiple cabs using a unique constraint on:

```text
cab_members.booking_id
```

## 🧪 Testing

Run all tests:

```powershell
python -m unittest discover
```

For detailed output:

```powershell
python -m unittest discover -v
```

Tests cover:

* Geographic grid calculation
* Haversine distance
* Cab capacity
* Employee assignment
* Route generation
* Route distance
* Maximum ride-time validation
* Night-route validation
* Empty/invalid inputs
* Invalid route rejection

## 🎬 Demo Flow

For demonstration:

```text
Admin Login
    ↓
View Employee Bookings
    ↓
Generate Cab Pools
    ↓
Open Cab Route
    ↓
Show Pickup Sequence + ETA
    ↓
Show Maximum Ride-Time Validation
    ↓
Demonstrate Night Safety
    ↓
Cancel Employee
    ↓
Show Route Re-planning
    ↓
Create Late Booking
    ↓
Show Booking Added to Existing Cab
```

## 🚀 Future Improvements

* Real road-network routing
* Google Maps / Mapbox / OSRM integration
* Redis caching
* Geohash/spatial indexing
* Real-time GPS tracking
* Automatic driver assignment
* Push/SMS notifications
* Background route optimization
* Monitoring and analytics dashboards

## 📌 Complexity Summary

| Component                 |                     Complexity |
| ------------------------- | -----------------------------: |
| Geographic Pooling        | `O(n + candidate comparisons)` |
| Nearest-Neighbour Routing |                        `O(k²)` |
| Ride-Time Validation      |                        `O(k²)` |
| Night Safety              |             `O(k!)` worst case |
| Space Complexity          |                         `O(n)` |

## 🏁 Conclusion

This project demonstrates a practical backend solution for **employee cab pooling, geographic grouping, pickup route generation, safety validation, maximum ride-time enforcement, and dynamic route re-planning**.

It combines simple and efficient heuristics with database constraints to provide predictable behaviour for small-capacity employee transportation systems.

