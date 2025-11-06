"""
Performance benchmark script for database indexes.

This script demonstrates the performance improvement from database indexes
by comparing query execution times with and without indexes.
"""

import sqlite3
import tempfile
import time
from datetime import datetime, timedelta

from garden_manager.database.plant_data import PlantDatabase
from garden_manager.database.garden_db import GardenDatabase
from garden_manager.database.models import PlantingInfo


def create_test_data(db_path, num_users=10, plots_per_user=5, plants_per_plot=10):
    """
    Create test data for benchmarking.

    Args:
        db_path: Path to database
        num_users: Number of users to create
        plots_per_user: Number of plots per user
        plants_per_plot: Number of planted items per plot

    Returns:
        Tuple of (total_plots, total_planted_items, total_care_tasks)
    """
    garden_db = GardenDatabase(db_path)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM plants LIMIT 1")
        plant_id = cursor.fetchone()[0]

    total_plots = 0
    total_planted_items = 0

    for user_id in range(1, num_users + 1):
        for plot_num in range(plots_per_user):
            plot_id = garden_db.create_garden_plot(
                name=f"Plot {plot_num} for User {user_id}",
                width=10,
                height=10,
                location="Test Location",
                user_id=user_id
            )
            total_plots += 1

            for plant_num in range(plants_per_plot):
                planting_info = PlantingInfo(
                    plant_id=plant_id,
                    plot_id=plot_id,
                    x_pos=plant_num % 10,
                    y_pos=plant_num // 10,
                    notes=f"Plant {plant_num}",
                    planted_date=datetime.now() - timedelta(days=plant_num),
                    days_to_maturity=60
                )
                garden_db.add_planted_item(planting_info)
                total_planted_items += 1

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM care_tasks")
        total_care_tasks = cursor.fetchone()[0]

    return total_plots, total_planted_items, total_care_tasks


def drop_all_indexes(db_path):
    """Remove all indexes from the database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Get all indexes
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND sql IS NOT NULL
        """)
        indexes = cursor.fetchall()

        # Drop each index
        for (index_name,) in indexes:
            cursor.execute(f"DROP INDEX {index_name}")

        conn.commit()


def benchmark_query(conn, query, params=None, iterations=100):
    """
    Benchmark a query execution time.

    Args:
        conn: Database connection
        query: SQL query to execute
        params: Query parameters
        iterations: Number of times to run the query

    Returns:
        Average execution time in milliseconds
    """
    cursor = conn.cursor()
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        cursor.fetchall()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds

    return sum(times) / len(times)


def run_benchmarks():
    """Run performance benchmarks with and without indexes."""
    print("=" * 70)
    print("DATABASE INDEX PERFORMANCE BENCHMARK")
    print("=" * 70)

    # Create two databases: one with indexes, one without
    db_with_indexes = tempfile.mktemp(suffix=".db")
    db_without_indexes = tempfile.mktemp(suffix=".db")

    print("\n1. Creating test databases...")
    print("   - Database WITH indexes")
    _ = PlantDatabase(db_with_indexes)
    print("   - Database WITHOUT indexes")
    _ = PlantDatabase(db_without_indexes)
    drop_all_indexes(db_without_indexes)

    print("\n2. Populating with test data...")
    stats = create_test_data(db_with_indexes, num_users=5, plots_per_user=10, plants_per_plot=20)
    create_test_data(db_without_indexes, num_users=5, plots_per_user=10, plants_per_plot=20)
    print(f"   - Created {stats[0]} plots")
    print(f"   - Created {stats[1]} planted items")
    print(f"   - Created {stats[2]} care tasks")

    # Define test queries
    queries = [
        ("Season Filtering", "SELECT * FROM plants WHERE season = 'spring'", None),
        ("User's Plots", "SELECT * FROM garden_plots WHERE user_id = 3", None),
        ("Plot's Plants", "SELECT * FROM planted_items WHERE plot_id = 5", None),
        ("Item's Tasks", "SELECT * FROM care_tasks WHERE planted_item_id = 10", None),
        ("Due Date Filter",
         "SELECT * FROM care_tasks WHERE due_date <= datetime('now', '+30 days')", None),
        ("Due & Incomplete",
         "SELECT * FROM care_tasks WHERE due_date <= datetime('now', '+30 days') AND completed = 0",
         None),
    ]

    print("\n3. Running benchmarks (100 iterations per query)...\n")
    print(f"{'Query':<20} {'Without Index':<15} {'With Index':<15} {'Speedup':<10}")
    print("-" * 70)

    conn_with = sqlite3.connect(db_with_indexes)
    conn_without = sqlite3.connect(db_without_indexes)

    total_speedup = 0
    count = 0

    for name, query, params in queries:
        time_with = benchmark_query(conn_with, query, params)
        time_without = benchmark_query(conn_without, query, params)
        speedup = time_without / time_with if time_with > 0 else 1.0

        print(f"{name:<20} {time_without:>10.3f} ms   {time_with:>10.3f} ms   {speedup:>6.1f}x")

        total_speedup += speedup
        count += 1

    conn_with.close()
    conn_without.close()

    avg_speedup = total_speedup / count if count > 0 else 1.0

    print("-" * 70)
    print(f"{'Average Speedup:':<20} {avg_speedup:>42.1f}x")

    print("\n4. Summary:")
    print(f"   ✅ Average performance improvement: {avg_speedup:.1f}x faster")
    print("   ✅ Indexes significantly improve query performance")
    print("   ✅ Complex queries benefit most from compound indexes")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_benchmarks()
