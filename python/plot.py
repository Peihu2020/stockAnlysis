import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set Chinese font for matplotlib (if needed for labels)
plt.rcParams['font.sans-serif'] = ['SimHei']  # For Chinese characters on Windows
plt.rcParams['axes.unicode_minus'] = False    # Fix minus sign display

import plotly.graph_objects as go
from datetime import datetime

import plotly.graph_objects as go
from datetime import datetime

def plot_kpi_trend(results_by_time, kpi_type='综合KPI', selected_codes=None, output_file='output/index.html'):
    """
    使用 Plotly 绘制 KPI 趋势图并保存为 HTML文件，支持鼠标悬停提示和图例点击隐藏
    :param results_by_time: dict, 格式为 {datetime_str: {stock_code: {...}}}
    :param kpi_type: 要绘制的KPI类型 ('短线KPI', '长线KPI', '综合KPI')
    :param selected_codes: 可选，指定要显示的股票代码列表
    :param output_file: 输出的 HTML 文件名
    """
    timestamps = sorted(results_by_time.keys())
    datetime_objects = [datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps]

    all_codes = set(code for snapshot in results_by_time.values() for code in snapshot.keys())
    stock_codes = selected_codes if selected_codes else sorted(all_codes)

    fig = go.Figure()

    for code in stock_codes:
        kpi_values = []
        for ts in timestamps:
            snapshot = results_by_time[ts]
            value = snapshot.get(code, {}).get(kpi_type, None)
            kpi_values.append(value if value is not None else None)

        fig.add_trace(go.Scatter(
            x=datetime_objects,
            y=kpi_values,
            mode='lines+markers',
            name=code,
            hovertemplate=f"<b>{code}</b><br>%{{x|%Y-%m-%d %H:%M:%S}}<br>{kpi_type}: %{{y:.2f}}<extra></extra>"
        ))

    fig.update_layout(
        title=f"{kpi_type} 趋势图",
        xaxis_title="分析时间",
        yaxis_title="KPI值",
        hovermode="x unified",
        template="plotly_white",
        legend_title_text="股票代码"
    )

    # 保存为 HTML 文件
    fig.write_html(output_file, include_plotlyjs='cdn')
    print(f"图表已保存为 {output_file}")



# 绘制KPI比较图
def plot_kpi_comparison(results, current_datetime):
    stock_codes = list(results.keys())
    short_term_kpis = [results[code]['短线KPI'] for code in stock_codes]
    long_term_kpis = [results[code]['长线KPI'] for code in stock_codes]
    comprehensive_kpis = [results[code]['综合KPI'] for code in stock_codes]
    
    x = np.arange(len(stock_codes))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width, short_term_kpis, width, label='短线KPI', color='skyblue')
    bars2 = ax.bar(x, long_term_kpis, width, label='长线KPI', color='lightgreen')
    bars3 = ax.bar(x + width, comprehensive_kpis, width, label='综合KPI', color='orange')
    
    ax.set_xlabel('股票代码')
    ax.set_ylabel('KPI值')
    ax.set_title(f'股票KPI比较 ({current_datetime})')
    ax.set_xticks(x)
    ax.set_xticklabels(stock_codes)
    ax.legend()
    
    # 在柱状图上添加数值标签
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# 绘制价格变化百分比热力图
def plot_percentage_change_heatmap(results, current_datetime):
    stock_codes = list(results.keys())
    periods = ['10', '50', '100']
    
    # 创建数据矩阵
    data = []
    for code in stock_codes:
        row = [results[code]['percentage_changes'].get(period, 0) for period in periods]
        data.append(row)
    
    df = pd.DataFrame(data, index=stock_codes, columns=[f'{period}天' for period in periods])
    
    plt.figure(figsize=(10, 6))
    sns.heatmap(df, annot=True, cmap='RdYlGn', center=0, fmt='.2f', 
                linewidths=0.5, cbar_kws={'label': '变化百分比 (%)'})
    plt.title(f'股票价格变化百分比热力图 ({current_datetime})')
    plt.tight_layout()
    plt.show()

# 绘制与HSI比较的雷达图
def plot_hsi_comparison_radar(results, current_datetime):
    stock_codes = list(results.keys())
    periods = [10, 50, 100]
    
    fig = plt.figure(figsize=(10, 8))
    fig.suptitle(f'股票与HSI比较雷达图 ({current_datetime})', fontsize=16)
    
    for i, code in enumerate(stock_codes):
        ax = fig.add_subplot(2, (len(stock_codes)+1)//2, i+1, polar=True)
        
        # 计算与HSI的差异
        differences = []
        for period in periods:
            stock_change = results[code]['percentage_changes'].get(period, 0)
            hsi_change = results[code]['hsi_comparison'].get(period, 0)
            differences.append(stock_change - hsi_change)
        
        # 完成雷达图的闭合
        angles = np.linspace(0, 2*np.pi, len(periods), endpoint=False).tolist()
        angles += angles[:1]  # 闭合图形
        differences += differences[:1]  # 闭合图形
        
        ax.plot(angles, differences, 'o-', linewidth=2, label=code)
        ax.fill(angles, differences, alpha=0.25)
        ax.set_thetagrids(np.degrees(angles[:-1]), [f'{period}天' for period in periods])
        ax.set_title(f'{code} vs HSI')
        ax.grid(True)
    
    plt.tight_layout()
    plt.show()

# 绘制当前价格条形图
def plot_current_prices(results, current_datetime):
    stock_codes = list(results.keys())
    prices = [results[code]['current_price'] for code in stock_codes]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(stock_codes, prices, color='lightblue', edgecolor='darkblue')
    
    plt.xlabel('股票代码')
    plt.ylabel('当前价格')
    plt.title(f'股票当前价格比较 ({current_datetime})')
    
    # 在柱状图上添加价格标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

# 绘制综合KPI排名
def plot_comprehensive_kpi_ranking(results, current_datetime):
    # 创建DataFrame用于排序
    df_data = []
    for code, data in results.items():
        df_data.append({
            'Stock': code,
            '综合KPI': data['综合KPI'],
            '短线KPI': data['短线KPI'],
            '长线KPI': data['长线KPI']
        })
    
    df = pd.DataFrame(df_data)
    df = df.sort_values('综合KPI', ascending=False)
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(df['Stock'], df['综合KPI'], 
                   color=plt.cm.RdYlGn(np.linspace(0, 1, len(df))))
    
    plt.xlabel('股票代码')
    plt.ylabel('综合KPI')
    plt.title(f'股票综合KPI排名 ({current_datetime})')
    
    # 在柱状图上添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()

# 绘制所有股票的详细比较图
def plot_detailed_comparison(results, current_datetime):
    stock_codes = list(results.keys())
    
    # 创建子图
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle(f'股票分析详细报告 ({current_datetime})', fontsize=16)
    
    # 1. 价格变化百分比比较
    periods = ['10', '50', '100']
    x = np.arange(len(periods))
    width = 0.8 / len(stock_codes)
    
    for i, code in enumerate(stock_codes):
        changes = [results[code]['percentage_changes'].get(period, 0) for period in periods]
        ax1.bar(x + i * width, changes, width, label=code)
    
    ax1.set_xlabel('时间周期')
    ax1.set_ylabel('变化百分比 (%)')
    ax1.set_title('价格变化百分比比较')
    ax1.set_xticks(x + width * (len(stock_codes) - 1) / 2)
    ax1.set_xticklabels([f'{period}天' for period in periods])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. 与HSI比较的差异
    for i, code in enumerate(stock_codes):
        differences = []
        for period in periods:
            stock_change = results[code]['percentage_changes'].get(period, 0)
            hsi_change = results[code]['hsi_comparison'].get(period, 0)
            differences.append(stock_change - hsi_change)
        ax2.bar(x + i * width, differences, width, label=code)
    
    ax2.set_xlabel('时间周期')
    ax2.set_ylabel('与HSI差异 (%)')
    ax2.set_title('与HSI表现差异')
    ax2.set_xticks(x + width * (len(stock_codes) - 1) / 2)
    ax2.set_xticklabels([f'{period}天' for period in periods])
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. 三种KPI比较
    kpi_types = ['短线KPI', '长线KPI', '综合KPI']
    x_kpi = np.arange(len(kpi_types))
    
    for i, code in enumerate(stock_codes):
        kpis = [results[code]['短线KPI'], results[code]['长线KPI'], results[code]['综合KPI']]
        ax3.bar(x_kpi + i * width, kpis, width, label=code)
    
    ax3.set_xlabel('KPI类型')
    ax3.set_ylabel('KPI值')
    ax3.set_title('KPI类型比较')
    ax3.set_xticks(x_kpi + width * (len(stock_codes) - 1) / 2)
    ax3.set_xticklabels(kpi_types)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 4. 当前价格
    prices = [results[code]['current_price'] for code in stock_codes]
    bars = ax4.bar(stock_codes, prices, color='lightcoral')
    ax4.set_xlabel('股票代码')
    ax4.set_ylabel('当前价格')
    ax4.set_title('当前价格')
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(axis='y', alpha=0.3)
    
    # 在价格柱状图上添加标签
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()

# 保存结果到CSV文件
def save_results_to_csv(results, current_datetime):
    data_for_csv = []
    for code, data in results.items():
        row = {
            '股票代码': code,
            '当前价格': data['current_price'],
            '分析时间': data['analysis_datetime'],
            '10天变化百分比': data['percentage_changes'].get(10, 0),
            '50天变化百分比': data['percentage_changes'].get(50, 0),
            '100天变化百分比': data['percentage_changes'].get(100, 0),
            '10天HSI变化': data['hsi_comparison'].get(10, 0),
            '50天HSI变化': data['hsi_comparison'].get(50, 0),
            '100天HSI变化': data['hsi_comparison'].get(100, 0),
            '短线KPI': data['短线KPI'],
            '长线KPI': data['长线KPI'],
            '综合KPI': data['综合KPI']
        }
        data_for_csv.append(row)
    
    df = pd.DataFrame(data_for_csv)
    filename = f"stock_analysis_{current_datetime.replace(':', '').replace(' ', '_')}.csv"
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"结果已保存到: {filename}")
