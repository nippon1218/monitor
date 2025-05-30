# SDC Monitor Installation and Usage Guide

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Edit the `config.yaml` file to specify which processes you want to monitor:

```yaml
# Process monitoring configuration
processes:
  - name: python  # Process name to monitor
  - name: bash
  # Add more processes as needed

# Monitoring settings
settings:
  interval: 10  # Monitoring interval in seconds
  output_dir: "./output"  # Directory to save results
```

## Usage

### Running manually

```bash
# Run with default configuration
python monitor.py

# Run with a custom configuration file
python monitor.py -c /path/to/custom_config.yaml

# Run for a specific duration (in seconds)
python monitor.py -d 3600  # Run for 1 hour
```

### Running as a systemd service

1. Copy the service file to the systemd directory:

```bash
sudo cp sdc_monitor.service /etc/systemd/system/
```

2. Reload systemd to recognize the new service:

```bash
sudo systemctl daemon-reload
```

3. Enable the service to start on boot:

```bash
sudo systemctl enable sdc_monitor
```

4. Start the service:

```bash
sudo systemctl start sdc_monitor
```

5. Check the service status:

```bash
sudo systemctl status sdc_monitor
```

## Output

The monitor will create two types of output files in the configured output directory:

1. CSV files with raw monitoring data: `monitor_data_YYYYMMDD_HHMMSS.csv`
2. HTML files with interactive visualizations: `monitor_data_YYYYMMDD_HHMMSS.html`

You can open the HTML files in any web browser to view the visualizations.
