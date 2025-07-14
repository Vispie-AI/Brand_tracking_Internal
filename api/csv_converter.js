import fs from 'fs';
import path from 'path';
import { spawn } from 'child_process';

export class CSVToJSONConverter {
  constructor(apiKey = "34ba1ae26fmsha15de959b0b5d6ep11e6e6jsn64ad77705138") {
    this.apiKey = apiKey;
  }

  async convertCSVToJSON(csvFilePath, outputJsonPath, updateStatusCallback = null) {
    return new Promise((resolve, reject) => {
      const logMessage = (msg) => {
        console.log(msg);
        if (updateStatusCallback) {
          updateStatusCallback('processing', 'Converting CSV to JSON...', [msg]);
        }
      };

      logMessage('Starting CSV to JSON conversion...');

      // 创建 Python 脚本来转换 CSV
      const pythonScript = this.generatePythonScript();
      const scriptPath = path.join(path.dirname(csvFilePath), 'temp_converter.py');
      
      try {
        // 写入临时 Python 脚本
        fs.writeFileSync(scriptPath, pythonScript);
        
        const pythonArgs = [
          scriptPath,
          csvFilePath,
          outputJsonPath,
          this.apiKey
        ];

        logMessage('Calling Python converter script...');

        // 启动 Python 进程
        const pythonProcess = spawn('python3', pythonArgs, {
          stdio: ['pipe', 'pipe', 'pipe']
        });

        let stdout = '';
        let stderr = '';

        pythonProcess.stdout.on('data', (data) => {
          const output = data.toString();
          stdout += output;
          const lines = output.split('\n').filter(line => line.trim());
          lines.forEach(line => logMessage(line));
        });

        pythonProcess.stderr.on('data', (data) => {
          const error = data.toString();
          stderr += error;
          console.error('Python stderr:', error);
        });

        pythonProcess.on('close', (code) => {
          // 清理临时脚本
          try {
            fs.unlinkSync(scriptPath);
          } catch (e) {
            console.warn('Failed to cleanup temp script:', e.message);
          }

          if (code === 0) {
            if (fs.existsSync(outputJsonPath)) {
              logMessage(`✓ CSV conversion completed! Output: ${outputJsonPath}`);
              resolve(outputJsonPath);
            } else {
              reject(new Error('Conversion completed but output file not found'));
            }
          } else {
            reject(new Error(`CSV conversion failed with exit code: ${code}\nstderr: ${stderr}`));
          }
        });

        pythonProcess.on('error', (error) => {
          // 清理临时脚本
          try {
            fs.unlinkSync(scriptPath);
          } catch (e) {
            console.warn('Failed to cleanup temp script:', e.message);
          }
          reject(error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  generatePythonScript() {
    return `
import csv
import json
import requests
import time
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

class TikTokDataConverter:
    def __init__(self, max_workers=5, api_key=""):
        self.max_workers = max_workers
        self.api_key = api_key
        self.processed_creators = set()
        self.lock = threading.Lock()
        
    def extract_video_id_and_creator(self, video_link):
        """从视频链接中提取video_id和creator_unique_id"""
        match = re.match(r'https://www\\.tiktok\\.com/@([^/]+)/video/(\\d+)', video_link)
        if match:
            creator_unique_id = match.group(1)
            video_id = match.group(2)
            return video_id, creator_unique_id
        return None, None

    def get_user_info(self, unique_id):
        """调用TikTok API获取用户信息"""
        url = f"https://tiktok-scraper7.p.rapidapi.com/user/info?unique_id=@{unique_id}"
        
        headers = {
            'x-rapidapi-host': 'tiktok-scraper7.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data'):
                    return data['data']
            print(f"用户信息API调用失败 for {unique_id}: {response.status_code}")
            return None
        except Exception as e:
            print(f"用户信息API调用出错 for {unique_id}: {str(e)}")
            return None

    def get_video_info(self, video_link):
        """调用TikTok API获取视频详细信息"""
        encoded_url = quote(video_link, safe='')
        url = f"https://tiktok-scraper7.p.rapidapi.com/?url={encoded_url}&hd=1"
        
        headers = {
            'x-rapidapi-host': 'tiktok-scraper7.p.rapidapi.com',
            'x-rapidapi-key': self.api_key
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and data.get('data'):
                    return data['data']
            print(f"视频信息API调用失败 for {video_link}: {response.status_code}")
            return None
        except Exception as e:
            print(f"视频信息API调用出错 for {video_link}: {str(e)}")
            return None

    def convert_to_json_format(self, video_id, creator_unique_id, video_link, user_data, video_data):
        """将数据转换为所需的JSON格式"""
        # 基础数据结构
        json_data = {
            "title": "",
            "video_id": video_id,
            "come_from": "custom",
            "basic_info": {
                "duration": "",
                "author_link": f"https://www.tiktok.com/@{creator_unique_id}",
                "create_time": "",
                "video_source": "tiktok_product",
                "thumbnail_url": "",
                "video_sale_gmv": 0,
                "author_nickname": "",
                "video_diggcount": 0,
                "video_playcount": 0,
                "author_followers": "0",
                "author_unique_id": creator_unique_id,
                "video_sharecount": 0,
                "video_commentcount": 0,
                "video_downloadcount": "None"
            },
            "created_at": None,
            "updated_at": None,
            "description": ""
        }
        
        # 填充用户数据
        if user_data:
            user = user_data.get('user', {})
            stats = user_data.get('stats', {})
            
            json_data["basic_info"]["author_nickname"] = user.get('nickname', '')
            json_data["basic_info"]["author_followers"] = str(stats.get('followerCount', 0))
            json_data["description"] = user.get('signature', '')
        
        # 填充视频数据
        if video_data:
            json_data["title"] = video_data.get('title', '')
            json_data["basic_info"]["duration"] = str(video_data.get('duration', ''))
            json_data["basic_info"]["create_time"] = str(video_data.get('create_time', ''))
            json_data["basic_info"]["thumbnail_url"] = video_data.get('cover', '')
            json_data["basic_info"]["video_diggcount"] = video_data.get('digg_count', 0)
            json_data["basic_info"]["video_playcount"] = video_data.get('play_count', 0)
            json_data["basic_info"]["video_sharecount"] = video_data.get('share_count', 0)
            json_data["basic_info"]["video_commentcount"] = video_data.get('comment_count', 0)
            json_data["basic_info"]["video_downloadcount"] = str(video_data.get('download_count', 'None'))
            
            # 如果没有用户数据，尝试从视频数据中获取作者信息
            if not user_data and video_data.get('author'):
                author = video_data['author']
                json_data["basic_info"]["author_nickname"] = author.get('nickname', '')
                json_data["description"] = author.get('signature', '')
        
        return json_data

    def process_single_video(self, video_link, creator_handler):
        """处理单个视频的完整流程"""
        try:
            video_id, creator_unique_id = self.extract_video_id_and_creator(video_link)
            
            if not video_id or not creator_unique_id:
                print(f"无法解析视频链接: {video_link}")
                return None
            
            # 检查是否已经处理过这个creator
            with self.lock:
                if creator_unique_id in self.processed_creators:
                    print(f"跳过重复的creator: {creator_unique_id}")
                    return None
                self.processed_creators.add(creator_unique_id)
            
            print(f"处理中: {creator_unique_id} (video: {video_id})")
            
            # 并行调用两个API
            user_data = None
            video_data = None
            
            with ThreadPoolExecutor(max_workers=2) as executor:
                # 提交两个API调用任务
                user_future = executor.submit(self.get_user_info, creator_unique_id)
                video_future = executor.submit(self.get_video_info, video_link)
                
                # 等待结果
                try:
                    user_data = user_future.result(timeout=20)
                except Exception as e:
                    print(f"获取用户信息失败 {creator_unique_id}: {str(e)}")
                
                try:
                    video_data = video_future.result(timeout=20)
                except Exception as e:
                    print(f"获取视频信息失败 {video_link}: {str(e)}")
            
            # 转换为JSON格式
            json_data = self.convert_to_json_format(
                video_id, creator_unique_id, video_link, user_data, video_data
            )
            
            print(f"✓ 完成处理: {creator_unique_id}")
            return json_data
            
        except Exception as e:
            print(f"处理视频时出错 {video_link}: {str(e)}")
            return None

    def process_csv_file(self, csv_file_path, output_file_path, max_records=None):
        """处理CSV文件并转换为JSON"""
        print(f"开始处理CSV文件，使用 {self.max_workers} 个worker...")
        
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
            print(f"读取CSV文件时出错: {str(e)}")
            return []
        
        print(f"从CSV中读取到 {len(video_data_list)} 条记录")
        
        # 使用多线程处理
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_data = {
                executor.submit(self.process_single_video, video_link, creator_handler): (video_link, creator_handler)
                for video_link, creator_handler in video_data_list
            }
            
            # 收集结果
            for future in as_completed(future_to_data):
                video_link, creator_handler = future_to_data[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"任务执行失败 {video_link}: {str(e)}")
        
        # 保存结果到JSON文件
        try:
            with open(output_file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(results, jsonfile, indent=2, ensure_ascii=False)
            print(f"✓ 成功保存 {len(results)} 条记录到 {output_file_path}")
        except Exception as e:
            print(f"保存JSON文件时出错: {str(e)}")
        
        return results

def main():
    if len(sys.argv) < 4:
        print("Usage: python script.py <csv_file> <output_json> <api_key>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_file = sys.argv[2]
    api_key = sys.argv[3]
    
    # 创建转换器实例
    converter = TikTokDataConverter(max_workers=5, api_key=api_key)
    
    # 开始处理
    start_time = time.time()
    results = converter.process_csv_file(csv_file, output_file, max_records=100)  # 限制100条记录避免API限制
    end_time = time.time()
    
    print(f"✓ 处理完成!")
    print(f"总共转换了 {len(results)} 条记录")
    print(f"耗时: {end_time - start_time:.2f} 秒")

if __name__ == "__main__":
    main()
`;
  }
}

export default CSVToJSONConverter; 