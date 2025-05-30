#!/usr/bin/env python3
"""
u7b80u5316u7248PDFu751fu6210u5de5u5177

u63d0u4f9bu7b80u5355u7684PDFu751fu6210u529fu80fduff0cu5305u542bu8868u683cu548cu6587u5b57u4fe1u606f
"""

import os
import logging
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# u914du7f6eu65e5u5fd7
logger = logging.getLogger(__name__)

# u5c1du8bd5u5bfcu5165kaleidouff08Plotlyu7684u9759u6001u5bfcu51fau5f15u64ceuff09
try:
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError:
    logger.warning("Kaleido not available. PDF export will be limited.")
    KALEIDO_AVAILABLE = False


def create_pdf_report(data, output_path):
    """
    u521bu5efau5305u542bu8868u683cu548cu56feu8868u7684PDFu62a5u544a
    
    Args:
        data: u76d1u63a7u6570u636eu5b57u5178
        output_path: u8f93u51faPDFu6587u4ef6u8defu5f84
        
    Returns:
        u751fu6210u7684PDFu6587u4ef6u8defu5f84uff0cu5982u679cu5931u8d25u5219u8fd4u56deNone
    """
    if not KALEIDO_AVAILABLE:
        logger.error("Kaleido is required for PDF export. Please install with 'pip install kaleido'")
        return None
        
    try:
        # u786eu4fddu65f6u95f4u6233u662fdatetimeu5bf9u8c61
        timestamps = data.get('timestamp', [])
        if timestamps and not isinstance(timestamps[0], pd.Timestamp):
            try:
                timestamps = pd.to_datetime(timestamps)
            except Exception as e:
                logger.warning(f"Could not convert timestamps: {e}")
        
        # u51c6u5907u7cfbu7edfu6982u89c8u6570u636e
        system_info = []
        
        # u7cfbu7edfu8d1fu8f7d
        for load_key, load_name in [
            ('system_load_1', '1u5206u949fu8d1fu8f7d'),
            ('system_load_5', '5u5206u949fu8d1fu8f7d'),
            ('system_load_15', '15u5206u949fu8d1fu8f7d')
        ]:
            if load_key in data:
                load_values = data[load_key]
                system_info.append([
                    load_name,
                    f"{np.mean(load_values):.2f}",
                    f"{np.max(load_values):.2f}",
                    f"{np.min(load_values):.2f}"
                ])
        
        # CPUu4f7fu7528u7387
        cpu_cols = [col for col in data.keys() if col.startswith('cpu_') and col.endswith('_percent')]
        if cpu_cols:
            cpu_values = []
            for col in cpu_cols:
                if col in data:
                    cpu_values.extend(data[col])
            
            system_info.append([
                'CPUu4f7fu7528u7387 (%)',
                f"{np.mean(cpu_values):.2f}",
                f"{np.max(cpu_values):.2f}",
                f"{np.min(cpu_values):.2f}"
            ])
        
        # u51c6u5907u8fdbu7a0bu4fe1u606fu6570u636e
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
            
            # CPUu4f7fu7528u7387
            cpu_avg = "N/A"
            cpu_max = "N/A"
            if cpu_key in data:
                cpu_values = [v for v in data[cpu_key] if v is not None]
                if cpu_values:
                    cpu_avg = f"{np.mean(cpu_values):.2f}%"
                    cpu_max = f"{np.max(cpu_values):.2f}%"
            
            # u5185u5b58u4f7fu7528
            mem_avg = "N/A"
            mem_max = "N/A"
            if mem_key in data:
                mem_values = [v for v in data[mem_key] if v is not None]
                if mem_values:
                    mem_avg = f"{np.mean(mem_values)/1024/1024:.2f} MB"
                    mem_max = f"{np.max(mem_values)/1024/1024:.2f} MB"
            
            # u72b6u6001
            status = "N/A"
            if status_key in data:
                statuses = [s for s in data[status_key] if s is not None]
                if statuses:
                    # u83b7u53d6u6700u540eu4e00u4e2au72b6u6001
                    status = statuses[-1]
            
            proc_info.append([proc_name, cpu_avg, cpu_max, mem_avg, mem_max, status])
        
        # u521bu5efau4e00u4e2au5305u542bu591au4e2au5b50u56feu7684u56feu8868
        fig = make_subplots(
            rows=5, 
            cols=1,
            subplot_titles=(
                "u7cfbu7edfu6982u89c8u8868",
                "u8fdbu7a0bu76d1u63a7u7edfu8ba1u8868",
                "u7cfbu7edfu8d1fu8f7du56fe", 
                "u8fdbu7a0bCPUu4f7fu7528u7387u56fe", 
                "u8fdbu7a0bu5185u5b58u4f7fu7528u56fe"
            ),
            vertical_spacing=0.05,
            row_heights=[0.15, 0.2, 0.2, 0.2, 0.2]
        )
        
        # u6dfbu52a0u7cfbu7edfu6982u89c8u8868u683c
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['<b>u6307u6807</b>', '<b>u5e73u5747u503c</b>', '<b>u6700u5927u503c</b>', '<b>u6700u5c0fu503c</b>'],
                    line_color='darkslategray',
                    fill_color='royalblue',
                    align='center',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=list(zip(*system_info)) if system_info else [[], [], [], []],
                    line_color='darkslategray',
                    fill_color='lightcyan',
                    align='center'
                )
            ),
            row=1, col=1
        )
        
        # u6dfbu52a0u8fdbu7a0bu76d1u63a7u7edfu8ba1u8868u683c
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['<b>u8fdbu7a0bu540d</b>', '<b>u5e73u5747CPU</b>', '<b>u6700u5927CPU</b>', 
                           '<b>u5e73u5747u5185u5b58</b>', '<b>u6700u5927u5185u5b58</b>', '<b>u6700u540eu72b6u6001</b>'],
                    line_color='darkslategray',
                    fill_color='forestgreen',
                    align='center',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=list(zip(*proc_info)) if proc_info else [[], [], [], [], [], []],
                    line_color='darkslategray',
                    fill_color='palegreen',
                    align='center'
                )
            ),
            row=2, col=1
        )
        
        # u6dfbu52a0u7cfbu7edfu8d1fu8f7du56feu8868
        fig.add_trace(
            go.Scatter(x=timestamps, y=data.get('system_load_1', []), name="1u5206u949f", legendgroup="load"),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=timestamps, y=data.get('system_load_5', []), name="5u5206u949f", legendgroup="load"),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=timestamps, y=data.get('system_load_15', []), name="15u5206u949f", legendgroup="load"),
            row=3, col=1
        )
        
        # u6dfbu52a0u8fdbu7a0bCPUu4f7fu7528u7387u56feu8868
        proc_cpu_cols = [col for col in data.keys() if col.endswith('_cpu_percent') and not col.startswith('cpu_')]
        for col in proc_cpu_cols:
            proc_name = col.split('_cpu_percent')[0]
            fig.add_trace(
                go.Scatter(x=timestamps, y=data.get(col, []), name=proc_name, legendgroup="proc_cpu"),
                row=4, col=1
            )
        
        # u6dfbu52a0u8fdbu7a0bu5185u5b58u4f7fu7528u56feu8868
        proc_mem_cols = [col for col in data.keys() if col.endswith('_memory_rss')]
        for col in proc_mem_cols:
            proc_name = col.split('_memory_rss')[0]
            # u8f6cu6362u4e3aMB
            memory_mb = [val/1024/1024 for val in data.get(col, [])]
            fig.add_trace(
                go.Scatter(x=timestamps, y=memory_mb, name=proc_name, legendgroup="proc_mem"),
                row=5, col=1
            )
        
        # u751fu6210u62a5u544au6807u9898u548cu65f6u95f4u4fe1u606f
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if timestamps:
            start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
            end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
            monitoring_period = f"u76d1u63a7u65f6u95f4u6bb5: {start_time} u81f3 {end_time}"
        else:
            monitoring_period = "u76d1u63a7u65f6u95f4u6bb5: u672au77e5"
        
        report_title = f"u7cfbu7edfu548cu8fdbu7a0bu76d1u63a7u62a5u544a<br>{monitoring_period}<br>u751fu6210u65f6u95f4: {current_time}"
        
        # u66f4u65b0u5e03u5c40
        fig.update_layout(
            height=1200,  # u8c03u6574u9ad8u5ea6u4ee5u5bb9u7eb3u6240u6709u5185u5bb9
            title=dict(
                text=report_title,
                font=dict(size=16)
            ),
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
                    text="u6ce8: u672cu62a5u544au663eu793au7cfbu7edfu548cu8fdbu7a0bu7684u76d1u63a7u6570u636euff0cu5305u62ecCPUu4f7fu7528u7387u3001u5185u5b58u4f7fu7528u548cu7cfbu7edfu8d1fu8f7du3002",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=-0.18,
                    font=dict(size=10),
                    align="left"
                )
            ]
        )
        
        # u6dfbu52a0Yu8f74u6807u9898
        fig.update_yaxes(title_text="u8d1fu8f7d", row=3, col=1)
        fig.update_yaxes(title_text="CPU %", row=4, col=1)
        fig.update_yaxes(title_text="u5185u5b58 (MB)", row=5, col=1)
        
        # u786eu4fddu8f93u51fau76eeu5f55u5b58u5728
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # u5bfcu51fau4e3aPDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created PDF report: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating PDF report: {e}", exc_info=True)
        return None


def create_cpu_cores_pdf(data, output_path):
    """
    u521bu5efaCPUu6838u5fc3u76d1u63a7PDFu62a5u544a
    
    Args:
        data: u76d1u63a7u6570u636eu5b57u5178
        output_path: u8f93u51faPDFu6587u4ef6u8defu5f84
        
    Returns:
        u751fu6210u7684PDFu6587u4ef6u8defu5f84uff0cu5982u679cu5931u8d25u5219u8fd4u56deNone
    """
    if not KALEIDO_AVAILABLE:
        logger.error("Kaleido is required for PDF export. Please install with 'pip install kaleido'")
        return None
        
    try:
        # u83b7u53d6u6240u6709CPUu6838u5fc3u5217
        cpu_cols = [col for col in data.keys() if col.startswith('cpu_') and col.endswith('_percent')]
        
        # u8ba1u7b97u5b50u56feu5e03u5c40
        cpu_count = len(cpu_cols)
        subplot_cols = min(4, cpu_count)  # u6700u591a4u5217
        subplot_rows = (cpu_count + subplot_cols - 1) // subplot_cols  # u5411u4e0au53d6u6574
        
        # u521bu5efau5b50u56fe
        fig = make_subplots(
            rows=subplot_rows,
            cols=subplot_cols,
            subplot_titles=[f"CPU {col.split('_')[1]}" for col in cpu_cols],
            vertical_spacing=0.1,
            horizontal_spacing=0.05
        )
        
        # u786eu4fddu65f6u95f4u6233u662fdatetimeu5bf9u8c61
        timestamps = data.get('timestamp', [])
        if timestamps and not isinstance(timestamps[0], pd.Timestamp):
            try:
                timestamps = pd.to_datetime(timestamps)
            except Exception as e:
                logger.warning(f"Could not convert timestamps: {e}")
        
        # u6dfbu52a0u6bcfu4e2aCPUu6838u5fc3u7684u4f7fu7528u7387u56feu8868
        for i, col in enumerate(cpu_cols):
            cpu_num = col.split('_')[1]
            row = i // subplot_cols + 1
            col_pos = i % subplot_cols + 1
            
            fig.add_trace(
                go.Scatter(x=timestamps, y=data.get(col, []), name=f"CPU {cpu_num}"),
                row=row, col=col_pos
            )
            
            # u6dfbu52a0Yu8f74u6807u9898
            fig.update_yaxes(title_text="CPU %", row=row, col=col_pos)
        
        # u751fu6210u62a5u544au6807u9898u548cu65f6u95f4u4fe1u606f
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if timestamps:
            start_time = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
            end_time = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
            monitoring_period = f"u76d1u63a7u65f6u95f4u6bb5: {start_time} u81f3 {end_time}"
        else:
            monitoring_period = "u76d1u63a7u65f6u95f4u6bb5: u672au77e5"
        
        report_title = f"CPUu6838u5fc3u4f7fu7528u7387u76d1u63a7u62a5u544a<br>{monitoring_period}<br>u751fu6210u65f6u95f4: {current_time}"
        
        # u66f4u65b0u5e03u5c40
        fig.update_layout(
            height=200 * subplot_rows + 100,  # u6839u636eu884cu6570u8c03u6574u9ad8u5ea6
            title=dict(
                text=report_title,
                font=dict(size=16)
            ),
            showlegend=False  # u9690u85cfu56feu4f8buff0cu56e0u4e3au5b50u56feu6807u9898u5df2u7ecfu8db3u591f
        )
        
        # u786eu4fddu8f93u51fau76eeu5f55u5b58u5728
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # u5bfcu51fau4e3aPDF
        fig.write_image(output_path, engine="kaleido")
        
        logger.info(f"Successfully created CPU cores PDF report: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating CPU cores PDF report: {e}", exc_info=True)
        return None


def create_pdf_reports(data, base_path):
    """
    u4eceu76d1u63a7u6570u636eu521bu5efaPDFu62a5u544a
    
    Args:
        data: u76d1u63a7u6570u636eu5b57u5178
        base_path: u57fau7840u6587u4ef6u8defu5f84uff08u4e0du542bu6269u5c55u540duff09
        
    Returns:
        u751fu6210u7684PDFu6587u4ef6u8defu5f84u5217u8868
    """
    pdf_paths = []
    
    # u521bu5efau7cfbu7edfu548cu8fdbu7a0bu76d1u63a7PDF
    system_pdf_path = f"{base_path}_system.pdf"
    system_result = create_pdf_report(data, system_pdf_path)
    if system_result:
        pdf_paths.append(system_result)
    
    # u521bu5efaCPUu6838u5fc3u76d1u63a7PDF
    cpu_pdf_path = f"{base_path}_cpu_cores.pdf"
    cpu_result = create_cpu_cores_pdf(data, cpu_pdf_path)
    if cpu_result:
        pdf_paths.append(cpu_result)
    
    return pdf_paths
