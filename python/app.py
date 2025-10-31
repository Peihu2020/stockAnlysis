from datetime import datetime, timedelta
from plot import *
from databaseOps import *
from stockOps import *
import time, os
import logging
import concurrent.futures
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_hkt_within_market_hours():
    # Convert current UTC time to HKT (UTC+8)
    utc_now = datetime.utcnow()
    hkt_now = utc_now + timedelta(hours=8)
    logger.info(f"UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"HKT time: {hkt_now.strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if it's a weekday (Monday=0, Sunday=6)
    weekday = hkt_now.weekday()
    logger.info(f"HKT weekday: {weekday} ({hkt_now.strftime('%A')})")
    if weekday >= 5:  # 5 = Saturday, 6 = Sunday
        logger.info("Market is closed: weekend")
        return False

    # Check if time is within 9:00 to 16:59
    hkt_hour = hkt_now.hour
    hkt_minute = hkt_now.minute
    logger.info(f"HKT hour: {hkt_hour}, minute: {hkt_minute}")
    if 9 <= hkt_hour < 17:
        logger.info("Market is open")
        return True
    else:
        logger.info("Market is closed: outside trading hours")
        return False

def analyze_single_stock(code: str, hsi_current_price: float, hsi_prices: List[float], current_datetime: str) -> Dict[str, Any]:
    """分析单只股票的独立函数，用于并行处理"""
    try:
        logger.info(f"开始分析股票: {code}")
        historical_prices = fetch_stock_data(code)
        if not historical_prices:
            logger.warning(f"获取股票数据失败: {code}, 可能已退市或代码错误")
            return None
        if len(historical_prices) < 100:
            logger.warning(f"获取股票数据少于100天: {code}，跳过")
            return None
            
        current_price = round(historical_prices[-1], 2)
        percentage_changes = calculate_percentage_change(current_price, historical_prices)
        hsi_comparison = calculate_hsi_comparison(hsi_current_price, hsi_prices)

        short_term_kpi = calculate_short_term_kpi(percentage_changes, hsi_comparison)
        long_term_kpi = calculate_long_term_kpi(percentage_changes, hsi_comparison)
        comprehensive_kpi = calculate_comprehensive_kpi(short_term_kpi, long_term_kpi)
        
        logger.info(f"完成分析股票: {code} - 价格: {current_price}, 综合KPI: {comprehensive_kpi}")
        
        return {
            'code': code,
            'current_price': current_price,
            'percentage_changes': percentage_changes,
            'hsi_comparison': hsi_comparison,
            '短线KPI': short_term_kpi,
            '长线KPI': long_term_kpi,
            '综合KPI': comprehensive_kpi,
            'analysis_datetime': current_datetime
        }
    except Exception as e:
        logger.error(f"执行计算失败 {code}: {e}")
        return None

def main_parallel(config_file: str, max_workers: int = None) -> None:
    """并行版本的主函数"""
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"分析时间: {current_datetime}")
    
    stock_codes = read_stock_codes(config_file)
    hsi_prices = fetch_hsi_data()

    if not hsi_prices:
        logger.error("获取恒生指数数据失败，程序终止。")
        return

    hsi_current_price = hsi_prices[-1]
    result = {}

    logger.info(f"开始并行分析 {len(stock_codes)} 只股票...")
    
    # 使用线程池并行处理（适合I/O密集型任务）
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_code = {
            executor.submit(analyze_single_stock, code, hsi_current_price, hsi_prices, current_datetime): code 
            for code in stock_codes
        }
        
        # 收集结果
        completed_count = 0
        for future in concurrent.futures.as_completed(future_to_code):
            code = future_to_code[future]
            try:
                stock_result = future.result()
                if stock_result:
                    result[code] = stock_result
                    completed_count += 1
                    logger.info(f"进度: {completed_count}/{len(stock_codes)} - 完成分析: {code}")
                else:
                    logger.warning(f"进度: {completed_count}/{len(stock_codes)} - 跳过分析: {code}")
            except Exception as e:
                logger.error(f"分析股票 {code} 时发生错误: {e}")
                completed_count += 1  # 即使失败也计数，避免进度显示错误

    # 保存结果
    if result:
        logger.info("开始保存结果到数据库...")
        save_results_to_influxdb(result)
        save_results_to_db(result)
        logger.info(f"\n=== 股票分析完成 ({current_datetime}) ===")
        logger.info(f"成功分析 {len(result)}/{len(stock_codes)} 只股票")
        
        # 读取并绘制结果
        # results = read_results_from_db()
        # plot_kpi_trend(results)
    else:
        logger.warning("没有成功分析任何股票")

def main_sequential(config_file: str) -> None:
    """顺序版本的主函数（保持原有逻辑）"""
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
        try:
            historical_prices = fetch_stock_data(code)
            if not historical_prices:
                print(f"获取股票数据失败: {code}, 可能已退市或代码错误")
                continue
            if len(historical_prices) < 100:
                print(f"获取股票数据少于100天: {code}，跳过 ")
                continue
            current_price = round(historical_prices[-1], 2)
            percentage_changes = calculate_percentage_change(current_price, historical_prices)
            hsi_comparison = calculate_hsi_comparison(hsi_current_price, hsi_prices)
    
            short_term_kpi = calculate_short_term_kpi(percentage_changes, hsi_comparison)
            long_term_kpi = calculate_long_term_kpi(percentage_changes, hsi_comparison)
            comprehensive_kpi = calculate_comprehensive_kpi(short_term_kpi, long_term_kpi)
        except Exception as e:
            print(f"执行计算失败: {e}")
            continue
            
        result[code] = {
            'current_price': current_price,
            'percentage_changes': percentage_changes,
            'hsi_comparison': hsi_comparison,
            '短线KPI': short_term_kpi,
            '长线KPI': long_term_kpi,
            '综合KPI': comprehensive_kpi,
            'analysis_datetime': current_datetime
        }

    save_results_to_influxdb(result)
    save_results_to_db(result)
    print(f"\n=== 股票分析结果 ({current_datetime}) ===")

def main(config_file: str, parallel: bool = True, max_workers: int = None) -> None:
    """主函数，可选择并行或顺序执行"""
    if parallel:
        main_parallel(config_file, max_workers)
    else:
        main_sequential(config_file)

if __name__ == "__main__":
    sleep_seconds = int(os.getenv("SLEEP_SECONDS", "300"))  # default: 5 minutes
    debug = os.getenv("DEBUG", "false").lower() == "true"
    use_parallel = "true"
    max_workers = 10
    
    logger.info(f"配置参数: SLEEP_SECONDS={sleep_seconds}, DEBUG={debug}, USE_PARALLEL={use_parallel}, MAX_WORKERS={max_workers}")
    
    while True:
        if is_hkt_within_market_hours() or debug:
            try:
                main('config.ini', parallel=use_parallel, max_workers=max_workers)
            except Exception as e:
                logger.error(f"执行失败: {e}")
        else:
            logger.info("当前时间不在香港市场开放时间内，跳过执行。")
        logger.info(f"等待 {sleep_seconds} 秒后再次检查...")
        time.sleep(sleep_seconds)
