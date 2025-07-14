#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌分析器 API后端
"""

import os
import sys
import json
import time
import logging
import threading
from datetime import datetime
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid

# 导入我们的分析器
from universal_brand_analyzer import UniversalBrandAnalyzer
from convert_csv_to_json_v2 import TikTokDataConverter

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'analyzed_data'
ALLOWED_EXTENSIONS = {'json', 'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# 存储分析任务的全局字典
analysis_tasks = {}

# 任务清理配置
MAX_TASKS_IN_MEMORY = 50  # 最大保存的任务数量
TASK_TIMEOUT_HOURS = 24   # 任务超时时间（小时）

def cleanup_old_tasks():
    """清理旧任务以防止内存泄漏"""
    current_time = datetime.now()
    tasks_to_remove = []
    
    for task_id, task_data in analysis_tasks.items():
        try:
            # 检查任务创建时间
            created_at_str = task_data.get('created_at')
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00').replace('+00:00', ''))
                age_hours = (current_time - created_at).total_seconds() / 3600
                
                # 清理超过24小时的任务
                if age_hours > TASK_TIMEOUT_HOURS:
                    tasks_to_remove.append(task_id)
                    print(f"Marking task {task_id} for cleanup (age: {age_hours:.1f} hours)")
            
        except Exception as e:
            print(f"Error checking task {task_id} age: {e}")
            # 如果无法解析时间，也标记为删除
            tasks_to_remove.append(task_id)
    
    # 如果任务数量超过限制，清理最旧的已完成任务
    if len(analysis_tasks) > MAX_TASKS_IN_MEMORY:
        completed_tasks = [(task_id, task_data) for task_id, task_data in analysis_tasks.items() 
                          if task_data.get('status') in ['completed', 'error']]
        
        # 按创建时间排序，删除最旧的
        completed_tasks.sort(key=lambda x: x[1].get('created_at', ''))
        excess_count = len(analysis_tasks) - MAX_TASKS_IN_MEMORY
        
        for i in range(min(excess_count, len(completed_tasks))):
            task_id = completed_tasks[i][0]
            if task_id not in tasks_to_remove:
                tasks_to_remove.append(task_id)
                print(f"Marking task {task_id} for cleanup (memory limit)")
    
    # 执行清理
    for task_id in tasks_to_remove:
        try:
            del analysis_tasks[task_id]
            print(f"Cleaned up task {task_id}")
        except KeyError:
            pass
    
    if tasks_to_remove:
        print(f"Cleaned up {len(tasks_to_remove)} old tasks. Remaining: {len(analysis_tasks)}")

def start_cleanup_thread():
    """启动清理线程"""
    def cleanup_worker():
        while True:
            try:
                cleanup_old_tasks()
                time.sleep(3600)  # 每小时清理一次
            except Exception as e:
                print(f"Error in cleanup thread: {e}")
                time.sleep(600)  # 出错时等待10分钟再试
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("Started task cleanup thread")

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

class LoggingCSVConverter:
    """带日志功能的CSV转换器包装类"""
    
    def __init__(self, task_id, logger):
        self.task_id = task_id
        self.logger = logger
        self.converter = TikTokDataConverter(max_workers=5)
        
    def log(self, message):
        """发送日志消息"""
        self.logger.info(message)
        # 同时更新任务进度
        if self.task_id in analysis_tasks:
            analysis_tasks[self.task_id]['progress'] = message
    
    def process_csv_with_logging(self, csv_file_path, output_file_path, max_records=None):
        """带日志的CSV处理过程"""
        import csv
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        self.log("🔍 Reading CSV file...")
        
        # 读取CSV数据
        video_data_list = []
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # 跳过标题行
                
                for row in reader:
                    if len(row) >= 2:
                        video_link = row[0].strip()
                        creator_handler = row[1].strip()
                        
                        if video_link and creator_handler:
                            video_data_list.append((video_link, creator_handler))
                            
                            if max_records and len(video_data_list) >= max_records:
                                break
                                
        except Exception as e:
            self.log(f"❌ Error reading CSV file: {str(e)}")
            return []
        
        self.log(f"📊 Found {len(video_data_list)} records to process")
        self.log(f"🚀 Starting conversion with {self.converter.max_workers} workers...")
        
        # 处理数据
        results = []
        processed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.converter.max_workers) as executor:
            # 提交所有任务
            future_to_data = {
                executor.submit(self.converter.process_single_video, video_link, creator_handler): (video_link, creator_handler)
                for video_link, creator_handler in video_data_list
            }
            
            # 收集结果
            for future in as_completed(future_to_data):
                video_link, creator_handler = future_to_data[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        processed_count += 1
                        
                        # 每处理5个creator更新一次进度
                        if processed_count % 5 == 0:
                            self.log(f"⚡ Progress: {processed_count}/{len(video_data_list)} creators processed...")
                            
                except Exception as e:
                    self.log(f"⚠️ Failed to process {creator_handler}: {str(e)}")
        
        # 保存结果
        try:
            import json
            with open(output_file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(results, jsonfile, indent=2, ensure_ascii=False)
            self.log(f"✅ Successfully saved {len(results)} records to {output_file_path}")
        except Exception as e:
            self.log(f"❌ Error saving JSON file: {str(e)}")
            return []
        
        self.log(f"🎉 CSV conversion completed! {len(results)} valid records converted")
        return results

def run_analysis(task_id, file_path, is_csv=False):
    """在后台运行分析任务"""
    try:
        # 确保任务存在于字典中
        if task_id not in analysis_tasks:
            print(f"Warning: Task {task_id} not found in analysis_tasks")
            return
            
        # 更新任务状态
        analysis_tasks[task_id]['status'] = 'running'
        analysis_tasks[task_id]['progress'] = 'Starting analysis...'
        
        print(f"Starting analysis for task {task_id}, file: {file_path}, is_csv: {is_csv}")
        
        # 创建自定义logger（无论是否CSV都需要）
        custom_logger = logging.getLogger(f'analyzer_{task_id}')
        custom_logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        custom_logger.handlers = []
        
        # 设置自定义日志处理器
        handler = WebAppHandler(task_id)
        handler.setFormatter(logging.Formatter('%(message)s'))
        custom_logger.addHandler(handler)
        
        # 如果是CSV文件，先进行转换
        if is_csv:
            custom_logger.info('📂 CSV file detected, starting conversion...')
            analysis_tasks[task_id]['progress'] = 'Converting CSV to JSON...'
            
            # 创建带日志的转换器
            logging_converter = LoggingCSVConverter(task_id, custom_logger)
            
            # 生成临时JSON文件路径
            json_file_path = file_path.replace('.csv', '_converted.json')
            
            # 执行转换
            results = logging_converter.process_csv_with_logging(file_path, json_file_path, max_records=None)
            
            if not results:
                analysis_tasks[task_id]['status'] = 'error'
                analysis_tasks[task_id]['progress'] = 'CSV转换失败：未转换任何数据'
                custom_logger.error('❌ CSV conversion failed: No data converted')
                print(f"CSV conversion failed for task {task_id}")
                return
            
            # 更新任务状态
            custom_logger.info(f'🔄 CSV conversion completed: {len(results)} records converted')
            custom_logger.info('🧠 Starting brand analysis...')
            analysis_tasks[task_id]['progress'] = 'CSV转换完成，开始品牌分析...'
            
            # 使用转换后的JSON文件
            file_path = json_file_path
        else:
            custom_logger.info('📄 JSON file detected, starting analysis...')
            analysis_tasks[task_id]['progress'] = 'JSON文件检测完成，开始分析...'
        
        # 创建分析器实例，传入自定义logger
        print(f"Creating analyzer for task {task_id}")
        analyzer = UniversalBrandAnalyzer(output_dir=RESULTS_FOLDER, custom_logger=custom_logger)
        
        # 运行分析
        print(f"Running analysis for task {task_id}")
        analysis_tasks[task_id]['progress'] = '正在进行品牌分析...'
        results = analyzer.analyze_creators(file_path)
        
        print(f"Analysis completed for task {task_id}, results count: {len(results) if results else 0}")
        
        if results:
            # 保存结果
            custom_logger.info('💾 Saving analysis results...')
            analysis_tasks[task_id]['progress'] = '保存分析结果...'
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
            
            # 确保任务仍然存在于字典中（防止被清理）
            if task_id in analysis_tasks:
                # 更新任务状态
                analysis_tasks[task_id].update({
                    'status': 'completed',
                    'progress': '🎉 分析完成！',
                    'completed_at': datetime.now().isoformat(),
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
                custom_logger.info(f'✅ Analysis completed successfully! Processed {len(results)} creators')
                print(f"Task {task_id} completed successfully")
            else:
                print(f"Warning: Task {task_id} was removed from analysis_tasks during processing")
        else:
            if task_id in analysis_tasks:
                analysis_tasks[task_id]['status'] = 'error'
                analysis_tasks[task_id]['progress'] = '分析失败：没有成功分析任何创作者'
            custom_logger.error('❌ Analysis failed: No creators were successfully analyzed')
            print(f"Analysis failed for task {task_id}: No results")
            
    except Exception as e:
        error_msg = f'分析失败：{str(e)}'
        print(f"Exception in run_analysis for task {task_id}: {str(e)}")
        
        # 确保任务仍然存在
        if task_id in analysis_tasks:
            analysis_tasks[task_id]['status'] = 'error'
            analysis_tasks[task_id]['progress'] = error_msg
            analysis_tasks[task_id]['error_at'] = datetime.now().isoformat()
        
        # 也尝试记录到日志
        try:
            if 'custom_logger' in locals():
                custom_logger.error(f'❌ Analysis error: {str(e)}')
        except:
            pass
    
    finally:
        # 清理自定义logger
        try:
            if 'custom_logger' in locals():
                custom_logger.handlers = []
        except:
            pass
        
        print(f"Analysis thread for task {task_id} finished")

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'message': 'Brand Analyzer API is running'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 检测文件类型
        is_csv = file.filename.lower().endswith('.csv')
        file_type = 'CSV' if is_csv else 'JSON'
        
        # 初始化任务状态
        analysis_tasks[task_id] = {
            'status': 'pending',
            'progress': f'{file_type} file uploaded successfully, preparing to start analysis...',
            'file_path': file_path,
            'filename': file.filename,
            'file_type': file_type.lower(),
            'logs': [],
            'created_at': datetime.now().isoformat()
        }
        
        # 在后台线程中运行分析
        thread = threading.Thread(target=run_analysis, args=(task_id, file_path, is_csv))
        thread.daemon = True
        thread.start()
        
        return jsonify({'task_id': task_id})
    
    return jsonify({'error': 'Unsupported file format, please upload JSON or CSV file'}), 400

@app.route('/api/status')
def get_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id parameter'}), 400
    
    print(f"Getting status for task {task_id}")
    print(f"Current tasks in memory: {list(analysis_tasks.keys())}")
    
    if task_id in analysis_tasks:
        task_data = analysis_tasks[task_id]
        print(f"Task {task_id} status: {task_data.get('status', 'unknown')}")
        
        # 添加调试信息
        debug_info = {
            'task_exists': True,
            'current_tasks_count': len(analysis_tasks),
            'task_created_at': task_data.get('created_at', 'unknown')
        }
        
        response_data = {**task_data, 'debug': debug_info}
        return jsonify(response_data)
    
    print(f"Task {task_id} not found in analysis_tasks")
    return jsonify({
        'error': 'Task not found', 
        'debug': {
            'task_exists': False,
            'current_tasks_count': len(analysis_tasks),
            'available_tasks': list(analysis_tasks.keys())[:5]  # 只显示前5个任务ID
        }
    }), 404

@app.route('/api/download')
def download_file():
    task_id = request.args.get('task_id')
    file_type = request.args.get('file_type')
    
    if not task_id or not file_type:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    if task_id not in analysis_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = analysis_tasks[task_id]
    if task['status'] != 'completed':
        return jsonify({'error': 'Analysis not completed yet'}), 400
    
    if file_type == 'brand_related':
        filename = task['results']['brand_file']
    elif file_type == 'non_brand':
        filename = task['results']['non_brand_file']
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    file_path = os.path.join(RESULTS_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/logs')
def get_logs():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({'error': 'Missing task_id parameter'}), 400
    
    print(f"Getting logs for task {task_id}")
    
    if task_id in analysis_tasks:
        logs = analysis_tasks[task_id].get('logs', [])
        print(f"Task {task_id} has {len(logs)} log entries")
        return jsonify({'logs': logs})
    
    print(f"Task {task_id} not found for logs")
    return jsonify({'error': 'Task not found'}), 404

if __name__ == '__main__':
    start_cleanup_thread() # 启动清理线程
    app.run(debug=True, host='0.0.0.0', port=5000) 