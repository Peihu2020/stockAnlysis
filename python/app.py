from datetime import datetime
from plot import *
from databaseOps import *
from stockOps import *
import time, os


# 主程序
def main(config_file):
    # 获取当前日期时间
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"分析时间: {current_datetime}")
    
    stock_codes = read_stock_codes(config_file)
    hsi_prices = fetch_hsi_data()

    # 检查hsi_prices是否为空
    if not hsi_prices:
        print("获取恒生指数数据失败，程序终止。")
        return  # 终止程序

    hsi_current_price = hsi_prices[-1]  # 假设最后一个数据是当前价格
    # single result per execution
    result = {}
    for code in stock_codes:
        historical_prices = fetch_stock_data(code)
        
        # 检查historical_prices是否为空
        if not historical_prices:
            print(f"获取股票数据失败: {code}, 可能已退市或代码错误")
            continue  # 跳过此股票代码

        current_price = round(historical_prices[-1], 2)  # 四舍五入到小数点后两位

        percentage_changes = calculate_percentage_change(current_price, historical_prices)
        hsi_comparison = calculate_hsi_comparison(hsi_current_price, hsi_prices)  # 使用HSI的当前价格

        # 计算KPI
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
            'analysis_datetime': current_datetime  # 添加分析时间到每个股票结果
        }

    # 输出结果
    save_results_to_db(result)
    print(f"\n=== 股票分析结果 ({current_datetime}) ===")
    results = read_results_from_db()

    # 绘制图表
    plot_kpi_trend(results)

if __name__ == "__main__":
    sleep_seconds = int(os.getenv("SLEEP_SECONDS", "86400"))  # default: 1 day
    while True:
        try:
            main('config.ini')
        except Exception as e:
            print(f"执行失败: {e}")
        print(f"等待 {sleep_seconds} 秒后再次执行...")
        time.sleep(sleep_seconds)
