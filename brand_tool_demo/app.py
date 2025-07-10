#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌分析器 Web应用
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, session
from werkzeug.utils import secure_filename
import uuid

# 导入我们的分析器
from universal_brand_analyzer import UniversalBrandAnalyzer

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生产环境中请使用更安全的密钥

# 配置
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'analyzed_data'
ALLOWED_EXTENSIONS = {'json'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# 存储分析任务的全局字典
analysis_tasks = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class WebAppHandler(logging.Handler):
    """自定义日志处理器，用于实时显示日志"""
    
    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id
        self.logs = []
    
    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': record.levelname,
            'message': log_entry
        })
        
        # 更新任务状态
        if self.task_id in analysis_tasks:
            analysis_tasks[self.task_id]['logs'] = self.logs

def run_analysis(task_id, file_path):
    """在后台运行分析任务"""
    try:
        # 更新任务状态
        analysis_tasks[task_id]['status'] = 'running'
        analysis_tasks[task_id]['progress'] = '开始分析...'
        
        # 创建自定义logger
        custom_logger = logging.getLogger(f'analyzer_{task_id}')
        custom_logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        custom_logger.handlers = []
        
        # 设置自定义日志处理器
        handler = WebAppHandler(task_id)
        handler.setFormatter(logging.Formatter('%(message)s'))
        custom_logger.addHandler(handler)
        
        # 创建分析器实例，传入自定义logger
        analyzer = UniversalBrandAnalyzer(output_dir=RESULTS_FOLDER, custom_logger=custom_logger)
        
        # 运行分析
        results = analyzer.analyze_creators(file_path)
        
        if results:
            # 保存结果
            analyzer.save_results(results, file_path)
            
            # 生成结果文件路径
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            brand_file = f"{base_name}_brand_related_{timestamp}.csv"
            non_brand_file = f"{base_name}_non_brand_{timestamp}.csv"
            
            # 统计信息
            brand_count = sum(1 for r in results if r.is_brand)
            matrix_count = sum(1 for r in results if r.is_matrix_account)
            ugc_count = sum(1 for r in results if r.is_ugc_creator)
            
            brand_related_results = [r for r in results if 
                                   (r.extracted_brand_name and r.extracted_brand_name.strip()) or 
                                   r.is_brand or r.is_matrix_account]
            
            brand_in_related = sum(1 for r in brand_related_results if r.is_brand)
            matrix_in_related = sum(1 for r in brand_related_results if r.is_matrix_account)
            ugc_in_related = sum(1 for r in brand_related_results if r.is_ugc_creator)
            
            # 更新任务状态
            analysis_tasks[task_id].update({
                'status': 'completed',
                'progress': '分析完成！',
                'results': {
                    'total_count': len(results),
                    'brand_related_count': len(brand_related_results),
                    'non_brand_count': len(results) - len(brand_related_results),
                    'brand_count': brand_count,
                    'matrix_count': matrix_count,
                    'ugc_count': ugc_count,
                    'brand_in_related': brand_in_related,
                    'matrix_in_related': matrix_in_related,
                    'ugc_in_related': ugc_in_related,
                    'brand_file': brand_file,
                    'non_brand_file': non_brand_file
                }
            })
        else:
            analysis_tasks[task_id]['status'] = 'error'
            analysis_tasks[task_id]['progress'] = '分析失败：没有成功分析任何创作者'
            
    except Exception as e:
        analysis_tasks[task_id]['status'] = 'error'
        analysis_tasks[task_id]['progress'] = f'分析失败：{str(e)}'
    
    finally:
        # 清理自定义logger
        if 'custom_logger' in locals():
            custom_logger.handlers = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 初始化任务状态
        analysis_tasks[task_id] = {
            'status': 'pending',
            'progress': '文件上传成功，准备开始分析...',
            'file_path': file_path,
            'filename': file.filename,
            'logs': []
        }
        
        # 在后台线程中运行分析
        thread = threading.Thread(target=run_analysis, args=(task_id, file_path))
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id})
    
    return jsonify({'error': '不支持的文件格式，请上传JSON文件'}), 400

@app.route('/status/<task_id>')
def get_status(task_id):
    if task_id in analysis_tasks:
        return jsonify(analysis_tasks[task_id])
    return jsonify({'error': '任务不存在'}), 404

@app.route('/download/<task_id>/<file_type>')
def download_file(task_id, file_type):
    if task_id not in analysis_tasks:
        return jsonify({'error': '任务不存在'}), 404
    
    task = analysis_tasks[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': '分析尚未完成'}), 400
    
    if file_type == 'brand':
        filename = task['results']['brand_file']
    elif file_type == 'non_brand':
        filename = task['results']['non_brand_file']
    else:
        return jsonify({'error': '无效的文件类型'}), 400
    
    file_path = os.path.join(RESULTS_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    
    return jsonify({'error': '文件不存在'}), 404

@app.route('/logs/<task_id>')
def get_logs(task_id):
    if task_id in analysis_tasks:
        return jsonify({'logs': analysis_tasks[task_id].get('logs', [])})
    return jsonify({'error': '任务不存在'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 