from flask import Flask, request, jsonify
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = '/tmp'  # Vercel 中使用 /tmp 目录
ALLOWED_EXTENSIONS = {'csv', 'json'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
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
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'task_id': task_id,
                'filename': filename
            }), 200
        else:
            return jsonify({'error': 'File type not allowed. Please upload CSV or JSON files.'}), 400
            
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

# Vercel 需要这个函数作为入口点
def handler(request):
    with app.app_context():
        return app.full_dispatch_request()

if __name__ == '__main__':
    app.run(debug=True) 