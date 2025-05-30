#!/usr/bin/env python3
"""
Plotly图表转PDF工具

提供将Plotly图表直接转换为PDF的功能，不依赖于HTML渲染
"""

import os
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# 不再使用figure_factory
from pathlib import Path
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入kaleido（Plotly的静态导出引擎）
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    logger.warning("Kaleido not available. PDF export will be limited.")
    KALEIDO_AVAILABLE = False


def create_system_info_table(data):
    """
    创建系统信息表格
    
    Args:
        data: 监控数据字典
        
    Returns:
        表格图形对象
    """
    # 计算平均值、最大值和最小值
    system_info = []
    
    # 系统负载
    for load_key, load_name in [
        ('system_load_1', '1分钟负载'),
        ('system_load_5', '5分钟负载'),
        ('system_load_15', '15分钟负载')
    ]:
        if load_key in data:
            load_values = data[load_key]
            system_info.append([
                load_name,
                f"{np.mean(load_values):.2f}",
                f"{np.max(load_values):.2f}",
                f"{np.min(load_values):.2f}"
            ])
    
    # CPU使用率
    cpu_cols = [col for col in data.keys() if col.startswith('cpu_') and col.endswith('_percent')]
    if cpu_cols:
        cpu_values = []
        for col in cpu_cols:
            if col in data:
                cpu_values.extend(data[col])
        
        system_info.append([
            'CPU使用率 (%)',
            f"{np.mean(cpu_values):.2f}",
            f"{np.max(cpu_values):.2f}",
            f"{np.min(cpu_values):.2f}"
        ])
    
    # 创建表格
    fig = go.Figure(data=[go.Table(
        header=dict(values=['指标', '平均值', '最大值', '最小值'],
                   fill_color='paleturquoise',
                   align='left'),
        cells=dict(values=list(zip(*system_info)),
                  fill_color='lavender',
                  align='left')
    )])
    
    fig.update_layout(
        title="系统概览",
        margin=dict(l=10, r=10, t=30, b=10),
        height=150
    )
    
    return fig


def create_process_table(data):
    """
    创建进程信息表格
    
    Args:
        data: 监控数据字典
        
    Returns:
        表格图形对象
    """
    # 获取所有进程名称
    proc_names = set()
    for key in data.keys():
        if key.endswith('_cpu_percent') and not key.startswith('cpu_'):
            proc_name = key.split('_cpu_percent')[0]
            proc_names.add(proc_name)
    
    # 为每个进程计算统计信息
    proc_info = []
    for proc_name in proc_names:
        cpu_key = f"{proc_name}_cpu_percent"
        mem_key = f"{proc_name}_memory_rss"
        status_key = f"{proc_name}_status"
        
        # CPU使用率
        cpu_avg = "N/A"
        cpu_max = "N/A"
        if cpu_key in data:
            cpu_values = [v for v in data[cpu_key] if v is not None]
            if cpu_values:
                cpu_avg = f"{np.mean(cpu_values):.2f}%"
                cpu_max = f"{np.max(cpu_values):.2f}%"
        
        # 内存使用
        mem_avg = "N/A"
        mem_max = "N/A"
        if mem_key in data:
            mem_values = [v for v in data[mem_key] if v is not None]
            if mem_values:
                mem_avg = f"{np.mean(mem_values)/1024/1024:.2f} MB"
                mem_max = f"{np.max(mem_values)/1024/1024:.2f} MB"
        
        # 状态
        status = "N/A"
        if status_key in data:
            statuses = [s for s in data[status_key] if s is not None]
            if statuses:
                # 获取最后一个状态
                status = statuses[-1]
        
        proc_info.append([proc_name, cpu_avg, cpu_max, mem_avg, mem_max, status])
    
    # 创建表格
    fig = go.Figure(data=[go.Table(
        header=dict(values=['进程名', '平均CPU', '最大CPU', '平均内存', '最大内存', '最后状态'],
                   fill_color='palegreen',
                   align='left'),
        cells=dict(values=list(zip(*proc_info)) if proc_info else [[], [], [], [], [], []],
                  fill_color='lavender',
                  align='left')
    )])
    
    fig.update_layout(
        title="进程监控统计",
        margin=dict(l=10, r=10, t=30, b=10),
        height=150 + 30 * len(proc_info)  # 根据进程数量调整高度
    )
    
    return fig


def create_system_pdf(data, output_path):
    """
    直接从数据创建系统监控PDF报告
    
    Args:
        data: 监控数据字典
        output_path: 输出PDF文件路径
        
    Returns:
        生成的PDF文件路径，如果失败则返回None
    """
    if not KALEIDO_AVAILABLE:
        logger.error("Kaleido is required for PDF export. Please install with 'pip install kaleido'")
        return None
        
    try:
        # 创建报告标题和说明
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_title = f"系统和进程监控报告 - 生成时间: {current_time}"
        
        # 创建系统信息表格
        system_table = create_system_info_table(data)
        
        # 创建进程信息表格
        process_table = create_process_table(data)
        
        # 创建一个包含三个子图的图表
        fig = make_subplots(
            rows=5, 
            cols=1,
            subplot_titles=(
                "系统概览",
                "进程监控统计",
                "系统负载", 
                "进程CPU使用率", 
                "进程内存使用"
            ),
            vertical_spacing=0.05,
            row_heights=[0.1, 0.15, 0.25, 0.25, 0.25]
        )
        
        # 确保时间戳是datetime对象
        timestamps = data.get('timestamp', [])
        if timestamps and not isinstance(timestamps[0], pd.Timestamp):
            try:
                timestamps = pd.to_datetime(timestamps)
            except Exception as e:
                logger.warning(f"Could not convert timestamps: {e}")
        
        # 生成系统信息和进程表格的单独图像
        system_table_path = os.path.join(os.path.dirname(output_path), 'system_table.png')
        process_table_path = os.path.join(os.path.dirname(output_path), 'process_table.png')
        
        # 将表格导出为图像
        system_table.write_image(system_table_path, engine="kaleido")
        process_table.write_image(process_table_path, engine="kaleido")
        
        # 添加表格图像作为图表
        fig.add_trace(
            go.Image(z=open(system_table_path, 'rb').read(), name="系统概览"),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Image(z=open(process_table_path, 'rb').read(), name="进程监控统计"),
            row=2, col=1
        )
        
        # 清理临时文件
        try:
            os.remove(system_table_path)
            os.remove(process_table_path)
        except Exception as e:
            logger.warning(f"Could not remove temporary table images: {e}")
        
        # 添加系统负载图表
        fig.add_trace(
            go.Scatter(x=timestamps, y=data.get('system_load_1', []), name="1分钟", legendgroup="load"),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=timestamps, y=data.get('system_load_5', []), name="5分钟", legendgroup="load"),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=timestamps, y=data.get('system_load_15', []), name="15分钟", legendgroup="load"),
            row=3, col=1
        )
        
        # 添加进程CPU使用率图表
        proc_cpu_cols = [col for col in data.keys() if col.endswith('_cpu_percent') and not col.startswith('cpu_')]
        for col in proc_cpu_cols:
            proc_name = col.split('_cpu_percent')[0]
            fig.add_trace(
                go.Scatter(x=timestamps, y=data.get(col, []), name=proc_name, legendgroup="proc_cpu"),
                row=4, col=1
            )
        
        # 添加进程内存使用图表
        proc_mem_cols = [col for col in data.keys() if col.endswith('_memory_rss')]
        for col in proc_mem_cols:
            proc_name = col.split('_memory_rss')[0]
            # 转换为MB
            memory_mb = [val/1024/1024 for val in data.get(col, [])]
            fig.add_trace(
                go.Scatter(x=timestamps, y=memory_mb, name=proc_name, legendgroup="proc_mem"),
                row=5, col=1
            )
        
        # 更新布局
        fig.update_layout(
            height=1200,  # 增加高度以容纳表格
            title_text=report_title,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                groupclick="toggleitem"
            ),
            annotations=[
                dict(
                    text="监控时段: " + timestamps[0].strftime('%Y-%m-%d %H:%M:%S') + " 至 " + timestamps[-1].strftime('%Y-%m-%d %H:%M:%S'),
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=1.05,
                    font=dict(size=10)
                ),
                dict(
                    text="注: 本报告显示系统和进程的监控数据，包括CPU使用率、内存使用和系统负载。",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=-0.18,
                    font=dict(size=8),
                    align="left"
                )
            ]
        )
        
        # 添加Y轴标题
        fig.update_yaxes(title_text="负载", row=3, col=1)
        fig.update_yaxes(title_text="CPU %", row=4, col=1)
        fig.update_yaxes(title_text="内存 (MB)", row=5, col=1)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出为PDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created system PDF report: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating system PDF report: {e}", exc_info=True)
        return None


def create_cpu_cores_pdf(data, output_path):
    """
    直接从数据创建CPU核心监控PDF报告
    
    Args:
        data: 监控数据字典
        output_path: 输出PDF文件路径
        
    Returns:
        生成的PDF文件路径，如果失败则返回None
    """
    if not KALEIDO_AVAILABLE:
        logger.error("Kaleido is required for PDF export. Please install with 'pip install kaleido'")
        return None
        
    try:
        # 获取所有CPU核心列
        cpu_cols = [col for col in data.keys() if col.startswith('cpu_') and col.endswith('_percent')]
        
        # 计算子图布局
        cpu_count = len(cpu_cols)
        subplot_cols = min(4, cpu_count)  # 最多4列
        subplot_rows = (cpu_count + subplot_cols - 1) // subplot_cols  # 向上取整
        
        # 创建子图
        fig = make_subplots(
            rows=subplot_rows,
            cols=subplot_cols,
            subplot_titles=[f"CPU {col.split('_')[1]}" for col in cpu_cols],
            vertical_spacing=0.1,
            horizontal_spacing=0.05
        )
        
        # 确保时间戳是datetime对象
        timestamps = data.get('timestamp', [])
        if timestamps and not isinstance(timestamps[0], pd.Timestamp):
            try:
                timestamps = pd.to_datetime(timestamps)
            except Exception as e:
                logger.warning(f"Could not convert timestamps: {e}")
        
        # 添加每个CPU核心的使用率图表
        for i, col in enumerate(cpu_cols):
            cpu_num = col.split('_')[1]
            row = i // subplot_cols + 1
            col_pos = i % subplot_cols + 1
            
            fig.add_trace(
                go.Scatter(x=timestamps, y=data.get(col, []), name=f"CPU {cpu_num}"),
                row=row, col=col_pos
            )
            
            # 添加Y轴标题
            fig.update_yaxes(title_text="CPU %", row=row, col=col_pos)
        
        # 更新布局
        fig.update_layout(
            height=200 * subplot_rows,  # 根据行数调整高度
            title_text="CPU核心使用率监控报告",
            showlegend=False  # 隐藏图例，因为子图标题已经足够
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出为PDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created CPU cores PDF report: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating CPU cores PDF report: {e}", exc_info=True)
        return None


def create_pdf_reports(data, base_path):
    """
    从监控数据创建PDF报告
    
    Args:
        data: 监控数据字典
        base_path: 基础文件路径（不含扩展名）
        
    Returns:
        生成的PDF文件路径列表
    """
    pdf_paths = []
    
    # 创建文本摘要PDF
    summary_path = f"{base_path}_summary.pdf"
    
    # 创建摘要图表
    summary_fig = go.Figure()
    
    # 添加标题
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    timestamps = data.get('timestamp', [])
    if timestamps:
        start_time = pd.to_datetime(timestamps[0]).strftime('%Y-%m-%d %H:%M:%S')
        end_time = pd.to_datetime(timestamps[-1]).strftime('%Y-%m-%d %H:%M:%S')
        monitoring_period = f"监控时间段: {start_time} 至 {end_time}"
    else:
        monitoring_period = "监控时间段: 未知"
    
    # 生成系统信息表格
    system_table = create_system_info_table(data)
    
    # 生成进程信息表格
    process_table = create_process_table(data)
    
    # 添加摘要文本
    summary_fig.add_annotation(
        text=f"<b>系统和进程监控报告</b><br>{monitoring_period}<br>生成时间: {current_time}",
        xref="paper", yref="paper",
        x=0.5, y=0.95,
        showarrow=False,
        font=dict(size=16)
    )
    
    # 添加表格
    for i, table in enumerate([system_table, process_table]):
        table_img_path = os.path.join(os.path.dirname(base_path), f"table_{i}.png")
        table.write_image(table_img_path, engine="kaleido")
        
        # 读取图像文件内容
        with open(table_img_path, 'rb') as img_file:
            img_bytes = img_file.read()
        
        # 添加图像到图表
        summary_fig.add_trace(
            go.Image(z=img_bytes, name=f"Table {i}")
        )
        
        # 清理临时文件
        try:
            os.remove(table_img_path)
        except Exception as e:
            logger.warning(f"Could not remove temporary table image: {e}")
    
    # 添加页脚
    summary_fig.add_annotation(
        text="注: 本报告显示系统和进程的监控数据统计信息。详细图表请参考其他PDF文件。",
        xref="paper", yref="paper",
        x=0, y=0,
        showarrow=False,
        font=dict(size=10),
        align="left",
        xanchor="left", yanchor="bottom"
    )
    
    # 设置图表布局
    summary_fig.update_layout(
        height=800,
        width=600,
        margin=dict(l=40, r=40, t=80, b=40)
    )
    
    # 导出摘要PDF
    try:
        summary_fig.write_image(summary_path, engine="kaleido")
        pdf_paths.append(summary_path)
        logger.info(f"Successfully created summary PDF report: {summary_path}")
    except Exception as e:
        logger.error(f"Error creating summary PDF report: {e}", exc_info=True)
    
    # 创建系统监控PDF
    system_pdf_path = f"{base_path}_system.pdf"
    system_result = create_system_pdf(data, system_pdf_path)
    if system_result:
        pdf_paths.append(system_result)
    
    # 创建CPU核心监控PDF
    cpu_pdf_path = f"{base_path}_cpu_cores.pdf"
    cpu_result = create_cpu_cores_pdf(data, cpu_pdf_path)
    if cpu_result:
        pdf_paths.append(cpu_result)
    
    return pdf_paths
