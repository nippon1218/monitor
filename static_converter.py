#!/usr/bin/env python3
"""
HTMLu9759u6001u8f6cu6362u6a21u5757

u5c06u52a8u6001HTMLu6587u4ef6u8f6cu6362u4e3au9759u6001HTMLu6587u4ef6uff0cu4ee5u4fbfu4e8eWeasyPrintu5904u7406
"""

import os
import re
import logging
import tempfile
from pathlib import Path

# u914du7f6eu65e5u5fd7
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    logger.warning("Selenium not available. Static conversion will be limited.")
    SELENIUM_AVAILABLE = False


def convert_plotly_to_static(html_path, output_path=None):
    """
    u5c06u5305u542bPlotlyu56feu8868u7684HTMLu6587u4ef6u8f6cu6362u4e3au9759u6001u56feu50cf
    
    Args:
        html_path: u539fu59cbHTMLu6587u4ef6u8defu5f84
        output_path: u8f93u51fau6587u4ef6u8defu5f84uff0cu5982u679cu4e3aNoneu5219u751fu6210u4e00u4e2au4e34u65f6u6587u4ef6
        
    Returns:
        u9759u6001HTMLu6587u4ef6u8defu5f84
    """
    # u5982u679cu6ca1u6709u6307u5b9au8f93u51fau8defu5f84uff0cu751fu6210u4e00u4e2au4e34u65f6u6587u4ef6u8defu5f84
    if output_path is None:
        output_dir = os.path.dirname(html_path)
        output_filename = f"static_{os.path.basename(html_path)}"
        output_path = os.path.join(output_dir, output_filename)
    
    # u8bfbu53d6u539fu59cbHTMLu6587u4ef6
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # u68c0u67e5u662fu5426u5305u542bPlotlyu811au672c
    if 'plotly' in html_content.lower():
        logger.info(f"Found Plotly content in {html_path}")
        
        # u65b9u6cd51: u4f7fu7528u6b63u5219u8868u8fbeu5f0fu66ffu6362Plotlyu811au672cu4e3au9759u6001u56feu50cfu6807u8bb0
        if not SELENIUM_AVAILABLE:
            # u6dfbu52a0u4e00u4e2au63d0u793auff0cu8bf4u660eu56feu8868u65e0u6cd5u6b63u786eu6e32u67d3
            static_message = """
            <div style="border: 2px solid red; padding: 20px; margin: 20px; text-align: center;">
                <h2>u56feu8868u65e0u6cd5u6e32u67d3</h2>
                <p>u8be5u56feu8868u9700u8981JavaScriptu6267u884cu624du80fdu6e32u67d3u3002u8bf7u5728u6d4fu89c8u5668u4e2du67e5u770bu539fu59cbHTMLu6587u4ef6u3002</p>
            </div>
            """
            
            # u66ffu6362u6240u6709u56feu8868u5bb9u5668
            chart_pattern = r'<div id="[^"]*chart[^"]*"[^>]*>.*?</div>'
            html_content = re.sub(chart_pattern, static_message, html_content, flags=re.DOTALL)
            
            # u79fbu9664Plotlyu811au672c
            script_pattern = r'<script[^>]*plotly[^>]*>.*?</script>'
            html_content = re.sub(script_pattern, '', html_content, flags=re.DOTALL)
        else:
            # u65b9u6cd52: u4f7fu7528Seleniumu6e32u67d3u56feu8868u5e76u6355u83b7u56feu50cf
            # u8fd9u90e8u5206u4ee3u7801u9700u8981Seleniumu548cChrome WebDriver
            # u7531u4e8eu73afu5883u9650u5236uff0cu6211u4eecu8fd9u91ccu4e0du5b9eu73b0u8be5u529fu80fd
            logger.warning("Selenium rendering not implemented in this version.")
    
    # u5199u5165u9759u6001HTMLu6587u4ef6
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Created static HTML file: {output_path}")
    return output_path


def add_print_styles(html_path, output_path=None):
    """
    u6dfbu52a0u6253u5370u6837u5f0fu5230HTMLu6587u4ef6
    
    Args:
        html_path: u539fu59cbHTMLu6587u4ef6u8defu5f84
        output_path: u8f93u51fau6587u4ef6u8defu5f84uff0cu5982u679cu4e3aNoneu5219u751fu6210u4e00u4e2au4e34u65f6u6587u4ef6
        
    Returns:
        u6dfbu52a0u4e86u6253u5370u6837u5f0fu7684HTMLu6587u4ef6u8defu5f84
    """
    # u5982u679cu6ca1u6709u6307u5b9au8f93u51fau8defu5f84uff0cu751fu6210u4e00u4e2au4e34u65f6u6587u4ef6u8defu5f84
    if output_path is None:
        output_dir = os.path.dirname(html_path)
        output_filename = f"print_{os.path.basename(html_path)}"
        output_path = os.path.join(output_dir, output_filename)
    
    # u8bfbu53d6u539fu59cbHTMLu6587u4ef6
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # u6dfbu52a0u6253u5370u6837u5f0f
    print_styles = """
    <style>
        @media print {
            body { font-family: Arial, sans-serif; }
            .chart-container { page-break-inside: avoid; margin-bottom: 20px; }
            h1, h2 { page-break-after: avoid; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            @page { margin: 2cm; }
        }
    </style>
    """
    
    # u5c06u6253u5370u6837u5f0fu6dfbu52a0u5230<head>u6807u7b7eu4e2d
    if '<head>' in html_content:
        html_content = html_content.replace('<head>', f'<head>{print_styles}')
    else:
        # u5982u679cu6ca1u6709<head>u6807u7b7euff0cu5c31u6dfbu52a0u5230<html>u6807u7b7eu540e
        html_content = html_content.replace('<html>', f'<html><head>{print_styles}</head>')
    
    # u5199u5165u6dfbu52a0u4e86u6253u5370u6837u5f0fu7684HTMLu6587u4ef6
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Added print styles to HTML file: {output_path}")
    return output_path


def prepare_html_for_pdf(html_path):
    """
    u51c6u5907HTMLu6587u4ef6u7528u4e8ePDFu8f6cu6362
    
    Args:
        html_path: u539fu59cbHTMLu6587u4ef6u8defu5f84
        
    Returns:
        u51c6u5907u597du7684HTMLu6587u4ef6u8defu5f84
    """
    # u521bu5efau4e34u65f6u76eeu5f55
    temp_dir = tempfile.mkdtemp(prefix="html_to_pdf_")
    
    # u751fu6210u9759u6001HTMLu6587u4ef6u8defu5f84
    static_html_path = os.path.join(temp_dir, os.path.basename(html_path))
    
    # u5148u8f6cu6362u4e3au9759u6001HTML
    static_html_path = convert_plotly_to_static(html_path, static_html_path)
    
    # u7136u540eu6dfbu52a0u6253u5370u6837u5f0f
    print_html_path = add_print_styles(static_html_path)
    
    return print_html_path
