#!/usr/bin/env python3
"""
简化版PDF生成工具

提供简单的PDF生成功能，包含表格和文字信息
"""

import os
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from PyPDF2 import PdfMerger

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入kaleido（Plotly的静态导出引擎）
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    logger.warning("Kaleido not available. PDF export will be limited.")
    KALEIDO_AVAILABLE = False


def create_system_info_table(data, output_path):
    """
    创建系统信息表格PDF
    
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
        # 准备系统概览数据
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
            
        # 转置数据以适应表格格式
        headers = ['指标', '平均值', '最大值', '最小值']
        cells_data = list(zip(*system_info)) if system_info else [[] for _ in range(len(headers))]
        
        # 创建表格图形
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=headers,
                line_color='darkslategray',
                fill_color='royalblue',
                align='center',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=cells_data,
                line_color='darkslategray',
                fill_color='lightcyan',
                align='center'
            )
        )])
        
        # 设置标题
        timestamps = data.get('timestamp', [])
        if len(timestamps) > 0:
            try:
                timestamps = pd.to_datetime(timestamps)
                start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
                end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
                monitoring_period = f"监控时间段: {start_time} 至 {end_time}"
            except:
                monitoring_period = "监控时间段: 未知"
        else:
            monitoring_period = "监控时间段: 未知"
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fig.update_layout(
            title=f"系统概览统计<br>{monitoring_period}<br>生成时间: {current_time}",
            height=400
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出为PDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created system info table PDF: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating system info table PDF: {e}", exc_info=True)
        return None


def create_process_table(data, output_path):
    """
    创建进程信息表格PDF
    
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
        # 准备进程信息数据
        proc_info = []
        proc_names = set()
        for key in data.keys():
            if key.endswith('_cpu_percent') and not key.startswith('cpu_'):
                proc_name = key.split('_cpu_percent')[0]
                proc_names.add(proc_name)
        
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
            
        # 转置数据以适应表格格式
        headers = ['进程名', '平均CPU', '最大CPU', '平均内存', '最大内存', '最后状态']
        cells_data = list(zip(*proc_info)) if proc_info else [[] for _ in range(len(headers))]
        
        # 创建表格图形
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=headers,
                line_color='darkslategray',
                fill_color='forestgreen',
                align='center',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=cells_data,
                line_color='darkslategray',
                fill_color='palegreen',
                align='center'
            )
        )])
        
        # 设置标题
        timestamps = data.get('timestamp', [])
        if len(timestamps) > 0:
            try:
                timestamps = pd.to_datetime(timestamps)
                start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
                end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
                monitoring_period = f"监控时间段: {start_time} 至 {end_time}"
            except:
                monitoring_period = "监控时间段: 未知"
        else:
            monitoring_period = "监控时间段: 未知"
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        fig.update_layout(
            title=f"进程监控统计<br>{monitoring_period}<br>生成时间: {current_time}",
            height=400 + 30 * len(proc_info)  # 根据进程数量调整高度
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出为PDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created process table PDF: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating process table PDF: {e}", exc_info=True)
        return None


def create_system_charts(data, output_path):
    """
    创建系统监控图表PDF
    
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
        # 确保时间戳是datetime对象
        timestamps = data.get('timestamp', [])
        if len(timestamps) > 0:
            if not isinstance(timestamps[0], pd.Timestamp):
                try:
                    timestamps = pd.to_datetime(timestamps)
                except Exception as e:
                    logger.warning(f"Could not convert timestamps: {e}")
        
        # 创建一个包含两个子图的图表
        fig = go.Figure()
        
        # 添加系统负载图表
        for load_key, load_name, color in [
            ('system_load_1', "1分钟", "blue"),
            ('system_load_5', "5分钟", "green"),
            ('system_load_15', "15分钟", "red")
        ]:
            fig.add_trace(
                go.Scatter(x=timestamps, y=data.get(load_key, []), name=load_name, line=dict(color=color))
            )
        
        # 设置标题和布局
        if len(timestamps) > 0:
            try:
                start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
                end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
                monitoring_period = f"监控时间段: {start_time} 至 {end_time}"
            except:
                monitoring_period = "监控时间段: 未知"
        else:
            monitoring_period = "监控时间段: 未知"
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        fig.update_layout(
            title=f"系统负载监控<br>{monitoring_period}<br>生成时间: {current_time}",
            xaxis_title="时间",
            yaxis_title="负载",
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出为PDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created system charts PDF: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating system charts PDF: {e}", exc_info=True)
        return None


def create_process_charts(data, output_path):
    """
    创建进程监控图表PDF
    
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
        # 确保时间戳是datetime对象
        timestamps = data.get('timestamp', [])
        if len(timestamps) > 0:
            if not isinstance(timestamps[0], pd.Timestamp):
                try:
                    timestamps = pd.to_datetime(timestamps)
                except Exception as e:
                    logger.warning(f"Could not convert timestamps: {e}")
        
        # 创建图表
        fig = go.Figure()
        
        # 添加CPU使用率子图
        fig.add_trace(go.Scatter(x=[None], y=[None], name="CPU使用率", line=dict(color="rgba(0,0,0,0)")))
        
        # 添加进程CPU使用率图表
        proc_cpu_cols = [col for col in data.keys() if col.endswith('_cpu_percent') and not col.startswith('cpu_')]
        for i, col in enumerate(proc_cpu_cols):
            proc_name = col.split('_cpu_percent')[0]
            fig.add_trace(
                go.Scatter(x=timestamps, y=data.get(col, []), name=f"{proc_name} CPU", 
                          line=dict(color=f"hsl({(i*50)%360}, 70%, 50%)"))
            )
        
        # 添加内存使用率子图
        fig.add_trace(go.Scatter(x=[None], y=[None], name="内存使用", line=dict(color="rgba(0,0,0,0)")))
        
        # 添加进程内存使用图表
        proc_mem_cols = [col for col in data.keys() if col.endswith('_memory_rss')]
        for i, col in enumerate(proc_mem_cols):
            proc_name = col.split('_memory_rss')[0]
            # 转换为MB
            memory_mb = [val/1024/1024 for val in data.get(col, [])]
            fig.add_trace(
                go.Scatter(x=timestamps, y=memory_mb, name=f"{proc_name} 内存", 
                          line=dict(color=f"hsl({(i*50+180)%360}, 70%, 50%)"))
            )
        
        # 设置标题和布局
        if len(timestamps) > 0:
            try:
                start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
                end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
                monitoring_period = f"监控时间段: {start_time} 至 {end_time}"
            except:
                monitoring_period = "监控时间段: 未知"
        else:
            monitoring_period = "监控时间段: 未知"
            
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        fig.update_layout(
            title=f"进程CPU和内存监控<br>{monitoring_period}<br>生成时间: {current_time}",
            xaxis_title="时间",
            yaxis_title="使用率",
            height=800,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 导出为PDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created process charts PDF: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating process charts PDF: {e}", exc_info=True)
        return None


def create_cpu_cores_pdf(data, output_path):
    """
    创建CPU核心监控PDF报告
    
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
        from plotly.subplots import make_subplots
        fig = make_subplots(
            rows=subplot_rows,
            cols=subplot_cols,
            subplot_titles=[f"CPU {col.split('_')[1]}" for col in cpu_cols],
            vertical_spacing=0.1,
            horizontal_spacing=0.05
        )
        
        # 确保时间戳是datetime对象
        timestamps = data.get('timestamp', [])
        if len(timestamps) > 0:
            if not isinstance(timestamps[0], pd.Timestamp):
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
        
        # 生成报告标题和时间信息
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if len(timestamps) > 0:
            try:
                start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
                end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
                monitoring_period = f"监控时间段: {start_time} 至 {end_time}"
            except:
                monitoring_period = "监控时间段: 未知"
        else:
            monitoring_period = "监控时间段: 未知"
        
        report_title = f"CPU核心使用率监控报告<br>{monitoring_period}<br>生成时间: {current_time}"
        
        # 更新布局
        fig.update_layout(
            height=200 * subplot_rows + 100,  # 根据行数调整高度
            title=dict(
                text=report_title,
                font=dict(size=16)
            ),
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


def merge_pdfs(pdf_files, output_path):
    """
    合并多个PDF文件为一个
    
    Args:
        pdf_files: PDF文件路径列表
        output_path: 输出PDF文件路径
        
    Returns:
        合并后的PDF文件路径，如果失败则返回None
    """
    try:
        merger = PdfMerger()
        
        for pdf in pdf_files:
            if os.path.exists(pdf):
                merger.append(pdf)
            else:
                logger.warning(f"PDF file not found: {pdf}")
        
        merger.write(output_path)
        merger.close()
        
        logger.info(f"Successfully merged PDFs to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error merging PDFs: {e}", exc_info=True)
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
    temp_pdfs = []
    
    # 创建系统信息表格PDF
    system_table_path = f"{base_path}_system_table.pdf"
    system_table_result = create_system_info_table(data, system_table_path)
    if system_table_result:
        temp_pdfs.append(system_table_result)
    
    # 创建进程信息表格PDF
    process_table_path = f"{base_path}_process_table.pdf"
    process_table_result = create_process_table(data, process_table_path)
    if process_table_result:
        temp_pdfs.append(process_table_result)
    
    # 创建系统监控图表PDF
    system_charts_path = f"{base_path}_system_charts.pdf"
    system_charts_result = create_system_charts(data, system_charts_path)
    if system_charts_result:
        temp_pdfs.append(system_charts_result)
    
    # 创建进程监控图表PDF
    process_charts_path = f"{base_path}_process_charts.pdf"
    process_charts_result = create_process_charts(data, process_charts_path)
    if process_charts_result:
        temp_pdfs.append(process_charts_result)
    
    # 创建完整系统报告PDF（合并表格和图表）
    if temp_pdfs:
        system_pdf_path = f"{base_path}_system.pdf"
        merged_result = merge_pdfs(temp_pdfs, system_pdf_path)
        if merged_result:
            pdf_paths.append(merged_result)
            
            # 清理临时PDF文件
            for pdf in temp_pdfs:
                try:
                    os.remove(pdf)
                except:
                    pass
    
    # 创建CPU核心监控PDF
    cpu_pdf_path = f"{base_path}_cpu_cores.pdf"
    cpu_result = create_cpu_cores_pdf(data, cpu_pdf_path)
    if cpu_result:
        pdf_paths.append(cpu_result)
    
    return pdf_paths