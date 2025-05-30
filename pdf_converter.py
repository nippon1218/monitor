#!/usr/bin/env python3
"""HTML到PDF转换模块

使用WeasyPrint将HTML文件转换为PDF格式
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 尝试导入静态转换模块
try:
    from static_converter import prepare_html_for_pdf
    STATIC_CONVERTER_AVAILABLE = True
except ImportError:
    logger.warning("Static converter not available. PDF quality may be affected.")
    STATIC_CONVERTER_AVAILABLE = False

# 尝试导入WeasyPrint，如果不可用则提供警告
try:
    from weasyprint import HTML, CSS
    import weasyprint
    # 获取WeasyPrint版本信息
    WEASYPRINT_AVAILABLE = True
    logger.info(f"WeasyPrint version: {weasyprint.__version__}")
except ImportError as e:
    logger.error(f"WeasyPrint import error: {e}")
    print("Warning: WeasyPrint not available. PDF conversion will be disabled.")
    WEASYPRINT_AVAILABLE = False


class PDFConverter:
    """HTML到PDF转换器类"""
    
    def __init__(self):
        """初始化PDF转换器"""
        self.logger = logging.getLogger(__name__)
        
        if WEASYPRINT_AVAILABLE:
            self.logger.info("PDF converter initialized successfully")
        else:
            self.logger.warning("WeasyPrint is not available. PDF conversion will be disabled.")
    
    def convert_html_to_pdf(self, html_path, pdf_path=None, css_path=None):
        """将HTML文件转换为PDF
        
        Args:
            html_path: HTML文件路径
            pdf_path: 输出PDF文件路径，如果为None则使用与HTML相同的名称
            css_path: 可选的CSS文件路径，用于自定义PDF样式
            
        Returns:
            生成的PDF文件路径，如果转换失败则返回None
        """
        if not WEASYPRINT_AVAILABLE:
            self.logger.error("WeasyPrint is not available. Cannot convert to PDF.")
            return None
            
        try:
            # 如果未指定PDF路径，则基于HTML路径生成
            if pdf_path is None:
                pdf_path = str(Path(html_path).with_suffix('.pdf'))
                
            # 创建输出目录（如果不存在）
            os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
            
            self.logger.info(f"Converting {html_path} to {pdf_path}")
            
            # 检查HTML文件是否存在且可读
            if not os.path.exists(html_path):
                self.logger.error(f"HTML file does not exist: {html_path}")
                return None
            
            # 如果静态转换模块可用，先将HTML转换为静态版本
            prepared_html_path = html_path
            if STATIC_CONVERTER_AVAILABLE:
                self.logger.info(f"Preparing HTML for PDF conversion using static converter")
                try:
                    prepared_html_path = prepare_html_for_pdf(html_path)
                    self.logger.info(f"Using prepared HTML file: {prepared_html_path}")
                except Exception as e:
                    self.logger.error(f"Error preparing HTML for PDF: {e}", exc_info=True)
                    # 如果静态转换失败，回退到原始HTML
                    prepared_html_path = html_path
            
            # 检查HTML文件内容
            with open(prepared_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                self.logger.info(f"HTML file size: {len(html_content)} bytes")
                if len(html_content) < 100:  # 文件太小可能有问题
                    self.logger.warning(f"HTML file seems too small: {len(html_content)} bytes")
            
            # 使用WeasyPrint处理HTML
            self.logger.info(f"Processing HTML with WeasyPrint")
            html = HTML(filename=prepared_html_path)
            
            # 添加基本CSS以确保内容可见
            base_css = CSS(string="""
                @page { margin: 1cm; }
                body { font-family: Arial, sans-serif; }
                .chart-container { page-break-inside: avoid; }
                h1, h2 { page-break-after: avoid; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            """)
            
            # 加载自定义CSS（如果提供）
            css_list = [base_css]
            if css_path and os.path.exists(css_path):
                css = CSS(filename=css_path)
                css_list.append(css)
            
            # 生成PDF
            self.logger.info(f"Generating PDF file: {pdf_path}")
            html.write_pdf(pdf_path, stylesheets=css_list)
            
            # 检查生成的PDF文件
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                self.logger.info(f"Successfully converted {html_path} to {pdf_path}")
                self.logger.info(f"PDF file size: {os.path.getsize(pdf_path)} bytes")
                
                # 如果使用了静态转换模块生成的临时文件，清理它
                if STATIC_CONVERTER_AVAILABLE and prepared_html_path != html_path:
                    try:
                        temp_dir = os.path.dirname(prepared_html_path)
                        if os.path.exists(temp_dir) and temp_dir.startswith('/tmp/html_to_pdf_'):
                            shutil.rmtree(temp_dir)
                            self.logger.info(f"Cleaned up temporary directory: {temp_dir}")
                    except Exception as e:
                        self.logger.warning(f"Error cleaning up temporary files: {e}")
                
                return pdf_path
            else:
                self.logger.error(f"Generated PDF is empty or does not exist: {pdf_path}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error converting HTML to PDF: {e}", exc_info=True)
            return None
    
    def convert_multiple_html_to_pdf(self, html_paths, output_dir=None):
        """
        批量转换多个HTML文件为PDF
        
        Args:
            html_paths: HTML文件路径列表
            output_dir: 输出目录，如果为None则使用HTML文件所在目录
            
        Returns:
            生成的PDF文件路径列表
        """
        pdf_paths = []
        
        for html_path in html_paths:
            if output_dir:
                # 在指定输出目录中创建PDF
                filename = os.path.basename(html_path)
                pdf_filename = os.path.splitext(filename)[0] + '.pdf'
                pdf_path = os.path.join(output_dir, pdf_filename)
            else:
                # 使用与HTML相同的目录
                pdf_path = None
                
            result = self.convert_html_to_pdf(html_path, pdf_path)
            if result:
                pdf_paths.append(result)
                
        return pdf_paths


def html_to_pdf(html_path, pdf_path=None, css_path=None):
    """
    将HTML文件转换为PDF的便捷函数
    
    Args:
        html_path: HTML文件路径
        pdf_path: 输出PDF文件路径，如果为None则使用与HTML相同的名称
        css_path: 可选的CSS文件路径，用于自定义PDF样式
        
    Returns:
        生成的PDF文件路径，如果转换失败则返回None
    """
    converter = PDFConverter()
    return converter.convert_html_to_pdf(html_path, pdf_path, css_path)
