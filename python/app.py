from datetime import datetime, timedelta
from plot import *
from databaseOps import *
from stockOps import *
import time, os

def is_hkt_within_market_hours():
    # Convert current UTC time to HKT (UTC+8)
    utc_now = datetime.utcnow()
    hkt_now = utc_now + timedelta(hours=8)

    # Check if it's a weekday (Monday=0, Sunday=6)
    if hkt_now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False

    # Check if time is within 9:00 to 16:59
    hkt_hour = hkt_now.hour
    return 9 <= hkt_hour < 17

def main(config_file):
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"分析时间: {current_datetime}")
    
    stock_codes = read_stock_codes(config_file)
    hsi_prices = fetch_hsi_data()

    if not hsi_prices:
        print("获取恒生指数数据失败，程序终止。")
        return

    hsi_current_price = hsi_prices[-1]
    result = {}

    for code in stock_codes:
        historical_prices = fetch_stock_data(code)
        if not historical_prices:
            print(f"获取股票数据失败: {code}, 可能已退市或代码错误")
            continue

        current_price = round(historical_prices[-1], 2)
        percentage_changes = calculate_percentage_change(current_price, historical_prices)
        hsi_comparison = calculate_hsi_comparison(hsi_current_price, hsi_prices)

        short_term_kpi = calculate_short_term_kpi(percentage_changes, hsi_comparison)
        long_term_kpi = calculate_long_term_kpi(percentage_changes, hsi_comparison)
        comprehensive_kpi = calculate_comprehensive_kpi(short_term_kpi, long_term_kpi)

        result[code] = {
            'current_price': current_price,
            'percentage_changes': percentage_changes,
            'hsi_comparison': hsi_comparison,
            '短线KPI': short_term_kpi,
            '长线KPI': long_term_kpi,
            '综合KPI': comprehensive_kpi,
            'analysis_datetime': current_datetime
        }

    save_results_to_db(result)
    print(f"\n=== 股票分析结果 ({current_datetime}) ===")
    results = read_results_from_db()
    plot_kpi_trend(results)

if __name__ == "__main__":
    sleep_seconds = int(os.getenv("SLEEP_SECONDS", "300"))  # default: 5 minutes
    while True:
        if is_hkt_within_market_hours():
            try:
                main('config.ini')
            except Exception as e:
                print(f"执行失败: {e}")
        else:
            print("当前时间不在香港市场开放时间内，跳过执行。")
        print(f"等待 {sleep_seconds} 秒后再次检查...")
        time.sleep(sleep_seconds)
