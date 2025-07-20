from http.server import BaseHTTPRequestHandler
import json
import urllib.parse as urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 解析查询参数
            parsed_url = urlparse.urlparse(self.path)
            query_params = urlparse.parse_qs(parsed_url.query)
            
            # 支持两种参数名：type 和 file_type
            if 'type' in query_params:
                file_type = query_params['type'][0]
            elif 'file_type' in query_params:
                file_type = query_params['file_type'][0]
            else:
                self._send_error(400, 'Missing type or file_type parameter')
                return
            
            # 模拟 CSV 数据
            if file_type == 'brand':
                filename = 'brand_related_creators.csv'
                csv_content = '''Creator Name,Platform,Followers,Brand Association,Classification
Creator A,TikTok,1000000,Nike,Official Account
Creator B,TikTok,500000,Adidas,Matrix Account  
Creator C,TikTok,250000,Nike,UGC Creator
Creator D,TikTok,100000,Puma,UGC Creator
Creator E,TikTok,750000,Nike,Matrix Account'''
            elif file_type == 'non_brand':
                filename = 'non_brand_creators.csv'  
                csv_content = '''Creator Name,Platform,Followers,Classification
Creator F,TikTok,800000,Non-branded
Creator G,TikTok,300000,Non-branded
Creator H,TikTok,150000,Non-branded
Creator I,TikTok,450000,Non-branded'''
            elif file_type == 'merged':
                filename = 'merged_results.csv'
                csv_content = '''Creator Name,Platform,Followers,Brand Association,Classification
Creator A,TikTok,1000000,Nike,Official Account
Creator B,TikTok,500000,Adidas,Matrix Account
Creator C,TikTok,250000,Nike,UGC Creator  
Creator D,TikTok,100000,Puma,UGC Creator
Creator E,TikTok,750000,Nike,Matrix Account
Creator F,TikTok,800000,None,Non-branded
Creator G,TikTok,300000,None,Non-branded
Creator H,TikTok,150000,None,Non-branded
Creator I,TikTok,450000,None,Non-branded'''
            else:
                self._send_error(400, 'Invalid file type')
                return
            
            # 发送 CSV 文件
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(csv_content.encode('utf-8'))
            
        except Exception as e:
            self._send_error(500, f'Download failed: {str(e)}')
    
    def do_OPTIONS(self):
        # 处理 CORS preflight 请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_error(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = {'error': message}
        self.wfile.write(json.dumps(error_data).encode()) 