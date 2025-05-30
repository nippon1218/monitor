#!/usr/bin/env python3
"""
Process Monitor - A tool to monitor system and process metrics
"""

import os
import time
import datetime
import threading
import logging
import psutil
import yaml
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 导入Web应用模块
try:
    from web_app import create_web_app
    WEB_SUPPORT = True
except ImportError:
    print("Warning: web_app module not found. Web interface will be disabled.")
    WEB_SUPPORT = False
    
# 导入PDF转换模块
try:
    from pdf_converter import PDFConverter
    PDF_SUPPORT = True
except ImportError:
    print("Warning: pdf_converter module not found. PDF conversion will be disabled.")
    PDF_SUPPORT = False
    
# 导入Plotly PDF生成模块
try:
    from simple_pdf import create_pdf_reports
    PLOTLY_PDF_SUPPORT = True
except ImportError:
    print("Warning: simple_pdf module not found. Direct PDF generation will be disabled.")
    PLOTLY_PDF_SUPPORT = False


class ProcessMonitor:
    def __init__(self, config_path="config.yaml"):
        """Initialize the process monitor with configuration"""
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.config = self._load_config()
        self.process_list = self.config["processes"]
        self.settings = self.config["settings"]
        self.interval = self.settings.get("interval", 10)
        self.output_dir = self.settings.get("output_dir", "./output")
        self.web_enabled = self.settings.get("web_enabled", False)
        self.web_port = self.settings.get("web_port", 5000)
        self.pdf_enabled = self.settings.get("pdf_enabled", False)
        self.direct_pdf = self.settings.get("direct_pdf", True)  # 默认使用直接PDF生成
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize data storage
        self.data = {
            "timestamp": [],
            "system_load_1": [],
            "system_load_5": [],
            "system_load_15": [],
        }
        
        # Add CPU usage columns for each CPU
        cpu_count = psutil.cpu_count()
        for i in range(cpu_count):
            self.data[f"cpu_{i}_percent"] = []
        
        # Add columns for each process
        for proc in self.process_list:
            proc_name = proc["name"]
            self.data[f"{proc_name}_cpu_percent"] = []
            self.data[f"{proc_name}_memory_rss"] = []
            self.data[f"{proc_name}_status"] = []
            
        # Initialize web app if enabled
        self.web_app = None
        self.web_thread = None
        if self.web_enabled and WEB_SUPPORT:
            self._setup_web_app()

    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            # Return default config if file can't be loaded
            return {
                "processes": [{"name": "python"}],
                "settings": {
                    "interval": 10, 
                    "output_dir": "./output",
                    "web_enabled": False,
                    "web_port": 5000,
                    "pdf_enabled": False
                }
            }
            
    def _setup_web_app(self):
        """Setup web application for real-time monitoring"""
        if not WEB_SUPPORT:
            print("Web support is not available. Please install required packages.")
            return
            
        try:
            self.web_app = create_web_app(port=self.web_port)
            self.web_thread = threading.Thread(target=self.web_app.start)
            self.web_thread.daemon = True  # Thread will exit when main program exits
            self.web_thread.start()
            print(f"Web interface started on http://localhost:{self.web_port}")
        except Exception as e:
            print(f"Error starting web interface: {e}")

    def _get_process_info(self, process_name):
        """Get information about a specific process"""
        cpu_percent = 0
        memory_rss = 0
        status = "not_found"
        
        # Find all processes with the given name
        for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info', 'status']):
            try:
                if process_name in proc.info['name']:
                    # Accumulate CPU and memory for all matching processes
                    cpu_percent += proc.info['cpu_percent'] or 0
                    memory_rss += proc.info['memory_info'].rss if proc.info['memory_info'] else 0
                    status = proc.info['status']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return cpu_percent, memory_rss, status

    def collect_data(self):
        """Collect a single data point for all metrics"""
        timestamp = datetime.datetime.now()
        self.data["timestamp"].append(timestamp)
        
        # Collect system load
        load_avg = psutil.getloadavg()
        self.data["system_load_1"].append(load_avg[0])
        self.data["system_load_5"].append(load_avg[1])
        self.data["system_load_15"].append(load_avg[2])
        
        # Collect CPU usage per CPU
        cpu_percent = psutil.cpu_percent(percpu=True)
        for i, percent in enumerate(cpu_percent):
            self.data[f"cpu_{i}_percent"].append(percent)
        
        # Collect process information
        for proc in self.process_list:
            proc_name = proc["name"]
            cpu_percent, memory_rss, status = self._get_process_info(proc_name)
            self.data[f"{proc_name}_cpu_percent"].append(cpu_percent)
            self.data[f"{proc_name}_memory_rss"].append(memory_rss)
            self.data[f"{proc_name}_status"].append(status)
            
        # Update web app data if enabled
        if self.web_enabled and self.web_app:
            self.web_app.update_data(self.data)
    
    def save_to_csv(self):
        """Save collected data to CSV file"""
        df = pd.DataFrame(self.data)
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = os.path.join(self.output_dir, f"monitor_data_{timestamp_str}.csv")
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def generate_visualizations(self, csv_path):
        """Generate visualizations from the collected data"""
        df = pd.read_csv(csv_path)
        
        # Convert timestamp strings to datetime objects
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create base output HTML file path (without extension)
        base_html_path = csv_path.replace('.csv', '')
        html_paths = []
        
        # 1. Generate system and process overview HTML file (excluding CPU data)
        system_html_path = f"{base_html_path}_system.html"
        html_paths.append(system_html_path)
        
        # Create system overview with subplots (excluding per-core CPU)
        fig_system = make_subplots(
            rows=3, 
            cols=1,
            subplot_titles=(
                "System Load Average", 
                "Process CPU Usage", 
                "Process Memory Usage (RSS)"
            ),
            vertical_spacing=0.1
        )
        
        # Plot 1: System Load
        fig_system.add_trace(
            go.Scatter(x=df['timestamp'], y=df['system_load_1'], name="1 min", legendgroup="load"),
            row=1, col=1
        )
        fig_system.add_trace(
            go.Scatter(x=df['timestamp'], y=df['system_load_5'], name="5 min", legendgroup="load"),
            row=1, col=1
        )
        fig_system.add_trace(
            go.Scatter(x=df['timestamp'], y=df['system_load_15'], name="15 min", legendgroup="load"),
            row=1, col=1
        )
        
        # Plot 2: Process CPU Usage
        proc_cpu_cols = [col for col in df.columns if col.endswith('_cpu_percent')]
        for col in proc_cpu_cols:
            proc_name = col.split('_cpu_percent')[0]
            fig_system.add_trace(
                go.Scatter(x=df['timestamp'], y=df[col], name=f"{proc_name}", legendgroup="proc_cpu", legendgrouptitle_text="进程CPU使用率"),
                row=2, col=1
            )
        
        # Plot 3: Process Memory Usage
        proc_mem_cols = [col for col in df.columns if col.endswith('_memory_rss')]
        for col in proc_mem_cols:
            proc_name = col.split('_memory_rss')[0]
            # Convert to MB for better readability
            fig_system.add_trace(
                go.Scatter(x=df['timestamp'], y=df[col]/1024/1024, name=f"{proc_name}", legendgroup="proc_mem", legendgrouptitle_text="进程内存使用"),
                row=3, col=1
            )
        
        # Update layout for system overview
        fig_system.update_layout(
            height=900,
            title_text="System and Process Monitoring",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,  # 调低位置以适应分组图例
                xanchor="center",
                x=0.5,
                groupclick="toggleitem"  # 允许点击组名切换整组的可见性
            )
        )
        
        # Add y-axis titles for system overview
        fig_system.update_yaxes(title_text="Load", row=1, col=1)
        fig_system.update_yaxes(title_text="CPU %", row=2, col=1)
        fig_system.update_yaxes(title_text="Memory (MB)", row=3, col=1)
        
        # Save system overview figure
        fig_system.write_html(system_html_path)
        
        # 2. Generate CPU cores HTML file with all CPU cores
        cpu_html_path = f"{base_html_path}_cpu_cores.html"
        html_paths.append(cpu_html_path)
        
        # Get all CPU columns
        cpu_cols = [col for col in df.columns if col.startswith('cpu_') and col.endswith('_percent')]
        
        # Calculate number of rows and columns for subplots based on CPU count
        cpu_count = len(cpu_cols)
        subplot_cols = min(4, cpu_count)  # Maximum 4 columns
        subplot_rows = (cpu_count + subplot_cols - 1) // subplot_cols  # Ceiling division
        
        # Create figure with subplots for all CPU cores
        fig_cpu = make_subplots(
            rows=subplot_rows,
            cols=subplot_cols,
            subplot_titles=[f"CPU {col.split('_')[1]}" for col in cpu_cols],
            vertical_spacing=0.1,
            horizontal_spacing=0.05
        )
        
        # Add traces for each CPU core
        for i, col in enumerate(cpu_cols):
            cpu_num = col.split('_')[1]
            row = i // subplot_cols + 1
            col_pos = i % subplot_cols + 1
            
            fig_cpu.add_trace(
                go.Scatter(x=df['timestamp'], y=df[col], name=f"CPU {cpu_num}"),
                row=row, col=col_pos
            )
            
            # Add y-axis title for each subplot
            fig_cpu.update_yaxes(title_text="CPU %", row=row, col=col_pos)
        
        # Update layout
        fig_cpu.update_layout(
            height=200 * subplot_rows,  # Adjust height based on number of rows
            title_text="CPU Cores Usage",
            showlegend=False  # Hide legend as it would be redundant with subplot titles
        )
        
        # Save CPU cores figure
        fig_cpu.write_html(cpu_html_path)
        
        return html_paths
    
    def run(self, duration=None):
        """Run the monitoring process
        
        Args:
            duration: Optional duration in seconds to run the monitor.
                     If None, runs indefinitely until interrupted.
        """
        print(f"Starting process monitor. Press Ctrl+C to stop.")
        print(f"Monitoring processes: {[p['name'] for p in self.process_list]}")
        print(f"Interval: {self.interval} seconds")
        
        if self.web_enabled:
            if self.web_app:
                print(f"Web interface enabled at http://localhost:{self.web_port}")
            else:
                print("Web interface could not be started. Check logs for details.")
        
        try:
            start_time = time.time()
            while True:
                self.collect_data()
                print(f"Collected data point at {datetime.datetime.now()}")
                
                # Check if we've reached the duration
                if duration and (time.time() - start_time) >= duration:
                    break
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("Monitoring stopped by user.")
        finally:
            if self.data["timestamp"]:  # Only save if we have data
                print("Saving data and generating visualizations...")
                csv_path = self.save_to_csv()
                html_paths = self.generate_visualizations(csv_path)
                print(f"Data saved to: {csv_path}")
                print(f"Visualizations saved to:")
                for path in html_paths:
                    print(f"  - {path}")
                    
                # 如果启用了PDF生成
                if self.pdf_enabled:
                    print("Generating PDF reports...")
                    pdf_paths = []
                    
                    # 优先使用直接PDF生成方式
                    if self.direct_pdf and PLOTLY_PDF_SUPPORT:
                        print("Using direct PDF generation...")
                        base_path = csv_path.replace('.csv', '')
                        pdf_paths = create_pdf_reports(self.data, base_path)
                    # 如果直接生成失败或未启用，则尝试使用HTML转换
                    elif PDF_SUPPORT:
                        print("Converting HTML to PDF...")
                        pdf_paths = self.convert_html_to_pdf(html_paths)
                    
                    if pdf_paths:
                        print("PDF files generated:")
                        for path in pdf_paths:
                            print(f"  - {path}")
                    else:
                        print("Failed to generate PDF files.")


    def convert_html_to_pdf(self, html_paths):
        """Convert HTML files to PDF
        
        Args:
            html_paths: List of HTML file paths to convert
            
        Returns:
            List of generated PDF file paths, or None if conversion failed
        """
        if not PDF_SUPPORT:
            self.logger.warning("PDF conversion is not supported. Please install WeasyPrint.")
            return None
            
        try:
            from pdf_converter import PDFConverter
            converter = PDFConverter()
            return converter.convert_multiple_html_to_pdf(html_paths)
        except Exception as e:
            self.logger.error(f"Error converting HTML to PDF: {e}")
            return None


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process and System Monitor")
    parser.add_argument("-c", "--config", default="config.yaml", 
                        help="Path to configuration file")
    parser.add_argument("-d", "--duration", type=int, default=None,
                        help="Duration to run in seconds (default: run indefinitely)")
    parser.add_argument("--web", action="store_true",
                        help="Enable web interface regardless of config setting")
    parser.add_argument("--port", type=int, default=None,
                        help="Port for web interface (overrides config setting)")
    parser.add_argument("--pdf", action="store_true",
                        help="Enable PDF generation regardless of config setting")
    args = parser.parse_args()
    
    monitor = ProcessMonitor(config_path=args.config)
    
    # Override config settings with command line arguments if provided
    if args.web:
        monitor.web_enabled = True
    if args.port is not None:
        monitor.web_port = args.port
        if monitor.web_app:
            monitor.web_app.port = args.port
    if args.pdf:
        monitor.pdf_enabled = True
    
    monitor.run(duration=args.duration)


if __name__ == "__main__":
    main()
