import sqlite3

import os
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB config from environment
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "stock_kpi")

def save_results_to_influxdb(results):
    print("🔧 Connecting to InfluxDB...")
    print(f"  ➤ URL: {INFLUX_URL}")
    print(f"  ➤ Org: {INFLUX_ORG}")
    print(f"  ➤ Bucket: {INFLUX_BUCKET}")
    print(f"  ➤ Token: {'SET' if INFLUX_TOKEN else 'NOT SET'}")

    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    health = client.health()
    print(f"✅ InfluxDB health check: {health.status}")

    for code, data in results.items():
        print(f"\n📊 Writing data for stock: {code}")
        print(f"  ➤ Analysis time: {data['analysis_datetime']}")
        print(f"  ➤ Current price: {data['current_price']}")
        print(f"  ➤ 短线KPI: {data['短线KPI']}, 长线KPI: {data['长线KPI']}, 综合KPI: {data['综合KPI']}")
        print(f"  ➤ Percentage changes: {json.dumps(data['percentage_changes'], ensure_ascii=False)}")
        print(f"  ➤ HSI comparison: {json.dumps(data['hsi_comparison'], ensure_ascii=False)}")

        try:
            point = (
                Point("kpi_result")
                .tag("stock_code", code)
                .field("current_price", data["current_price"])
                .field("kpi_short", data["短线KPI"])
                .field("kpi_long", data["长线KPI"])
                .field("kpi_comprehensive", data["综合KPI"])
                .field("percentage_changes", json.dumps(data["percentage_changes"], ensure_ascii=False))
                .field("hsi_comparison", json.dumps(data["hsi_comparison"], ensure_ascii=False))
                .time(data["analysis_datetime"], WritePrecision.S)
            )
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            print("✅ Write successful")
        except Exception as e:
            print(f"❌ Write failed for {code}: {e}")

    client.close()
    print("\n🔒 InfluxDB connection closed.")



def read_results_from_db():
    conn = sqlite3.connect('output/stock_kpi.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT analysis_time, stock_code, current_price,
               percentage_changes, hsi_comparison,
               kpi_short, kpi_long, kpi_comprehensive
        FROM kpi_results
        ORDER BY analysis_time DESC, stock_code ASC
    ''')

    rows = cursor.fetchall()
    conn.close()

    results = {}
    for row in rows:
        analysis_time, stock_code, current_price, pct_json, hsi_json, kpi_short, kpi_long, kpi_comp = row
        results.setdefault(analysis_time, {})[stock_code] = {
            'current_price': current_price,
            'percentage_changes': json.loads(pct_json),
            'hsi_comparison': json.loads(hsi_json),
            '短线KPI': kpi_short,
            '长线KPI': kpi_long,
            '综合KPI': kpi_comp
        }

    return results

def save_results_to_db(results):
    conn = sqlite3.connect('output/stock_kpi.db')
    cursor = conn.cursor()

    # Create table with JSON fields for nested data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kpi_results (
            analysis_time TEXT,
            stock_code TEXT,
            current_price REAL,
            percentage_changes TEXT,
            hsi_comparison TEXT,
            kpi_short REAL,
            kpi_long REAL,
            kpi_comprehensive REAL,
            PRIMARY KEY (analysis_time, stock_code)
        )
    ''')

    for code, data in results.items():
        cursor.execute('''
            INSERT OR REPLACE INTO kpi_results VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['analysis_datetime'],
            code,
            data['current_price'],
            json.dumps(data['percentage_changes'], ensure_ascii=False),
            json.dumps(data['hsi_comparison'], ensure_ascii=False),
            data['短线KPI'],
            data['长线KPI'],
            data['综合KPI']
        ))

    conn.commit()
    conn.close()
