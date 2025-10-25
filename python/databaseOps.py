import sqlite3
import json

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
