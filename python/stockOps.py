import yfinance as yf
import configparser
from plot import *
from databaseOps import *

# 读取配置文件中的股票代码
def read_stock_codes(config_file):
    config = configparser.ConfigParser()
    with open(config_file, 'r', encoding='utf-8') as f:
        config.read_file(f)
    return config['Stocks']['codes'].split(',')

# 从Yahoo Finance获取股票价格数据
def fetch_stock_data(stock_code):
    stock = yf.Ticker(stock_code)
    historical_data = stock.history(period="max")  # 获取最大历史数据
    return historical_data['Close'].tolist()  # 返回收盘价列表

# 计算价格变化百分比
def calculate_percentage_change(current_price, historical_prices):
    changes = {}
    for days in [10, 50, 100]:
        past_price = historical_prices[-days] if len(historical_prices) >= days else None
        if past_price:
            changes[days] = round(((current_price - past_price) / past_price) * 100, 2)  # 四舍五入到小数点后两位
    return changes

# 计算与HSI的百分比变化
def calculate_hsi_comparison(hsi_current_price, hsi_prices):
    hsi_changes = {}
    for days in [10, 50, 100]:
        past_hsi_price = hsi_prices[-days] if len(hsi_prices) >= days else None
        if past_hsi_price:
            hsi_changes[days] = round(((hsi_current_price - past_hsi_price) / past_hsi_price) * 100, 2)  # 四舍五入到小数点后两位
    return hsi_changes

# 获取恒生指数数据
def fetch_hsi_data():
    hsi = yf.Ticker("^HSI")  # 恒生指数的Yahoo Finance代码
    hsi_data = hsi.history(period="max")
    return hsi_data['Close'].tolist()  # 返回收盘价列表

# 计算短线KPI
def calculate_short_term_kpi(percentage_changes, hsi_changes):
    # 计算短线KPI
    short_term_kpi = (percentage_changes[10] + percentage_changes[50]) - (hsi_changes[10] + hsi_changes[50])
    return round(short_term_kpi, 2)  # 四舍五入到小数点后两位

# 计算长线KPI
def calculate_long_term_kpi(percentage_changes, hsi_changes):
    # 计算长线KPI
    long_term_kpi = (percentage_changes[50] + percentage_changes[100]) - (hsi_changes[50] + hsi_changes[100])
    return round(long_term_kpi, 2)  # 四舍五入到小数点后两位

# 计算综合KPI
def calculate_comprehensive_kpi(short_term_kpi, long_term_kpi):
    # 计算综合KPI
    comprehensive_kpi = (short_term_kpi + long_term_kpi) / 2
    return round(comprehensive_kpi, 2)  # 四舍五入到小数点后两位
