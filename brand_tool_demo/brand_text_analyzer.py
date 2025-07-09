#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌创作者分析器 - 使用Gemini API分析创作者是否代表品牌
"""

import os
import json
import csv
import logging
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API配置
GEMINI_API_KEY = 'AIzaSyB8GkbKtlc9OfyHE2c_wasXpCatYRC11IY'
RAPIDAPI_KEY = '34ba1ae26fmsha15de959b0b5d6ep11e6e6jsn64ad77705138'

# 大型科技公司列表（需要更严格的判断）
MAJOR_TECH_COMPANIES = {
    'apple', 'microsoft', 'google', 'amazon', 'facebook', 'meta', 'samsung', 
    'sony', 'intel', 'nvidia', 'ibm', 'oracle', 'adobe', 'salesforce', 
    'netflix', 'uber', 'twitter', 'linkedin', 'snapchat', 'tiktok', 'instagram'
}

@dataclass
class CreatorAnalysis:
    """创作者分析结果"""
    video_id: str
    author_unique_id: str
    author_link: str
    signature: str
    is_brand_representative: bool
    extracted_brand_name: str
    analysis_details: str
    author_followers_count: int
    author_followings_count: int
    videoCount: int
    author_avatar: str
    create_times: str

class BrandTextAnalyzer:
    """使用Gemini API的品牌文本分析器"""
    
    def __init__(self):
        # 初始化Gemini客户端
        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        # 用于追踪已分配的brand names
        self.assigned_brands = set()
        
    def convert_timestamp_to_date(self, timestamp) -> str:
        """将Unix时间戳转换为年月日格式"""
        try:
            if timestamp and str(timestamp).isdigit():
                dt = datetime.fromtimestamp(int(timestamp))
                return dt.strftime('%Y-%m-%d')
            return ''
        except (ValueError, OSError) as e:
            logger.warning(f"时间戳转换失败: {timestamp}, 错误: {e}")
            return ''
        
    def get_tiktok_user_info(self, unique_id: str) -> Dict:
        """获取TikTok用户信息"""
        url = f"https://tiktok-scraper7.p.rapidapi.com/user/info?unique_id={unique_id}"
        headers = {
            'x-rapidapi-host': 'tiktok-scraper7.p.rapidapi.com',
            'x-rapidapi-key': RAPIDAPI_KEY
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('code') == 0 and 'data' in data:
                user_data = data['data']['user']
                stats_data = data['data']['stats']
                
                return {
                    'signature': user_data.get('signature', ''),
                    'author_followers_count': stats_data.get('followerCount', 0),
                    'author_followings_count': stats_data.get('followingCount', 0),
                    'videoCount': stats_data.get('videoCount', 0),
                    'author_avatar': user_data.get('avatarThumb', ''),
                    'success': True
                }
            else:
                logger.warning(f"TikTok API 返回错误代码: {data.get('code', 'unknown')} for {unique_id}")
                return self._default_user_info()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"TikTok API 请求失败 for {unique_id}: {e}")
            return self._default_user_info()
        except Exception as e:
            logger.error(f"TikTok API 处理错误 for {unique_id}: {e}")
            return self._default_user_info()
    
    def _default_user_info(self) -> Dict:
        """默认用户信息"""
        return {
            'signature': '',
            'author_followers_count': 0,
            'author_followings_count': 0,
            'videoCount': 0,
            'author_avatar': '',
            'success': False
        }
        
    def is_official_account(self, unique_id: str, nickname: str, signature: str) -> bool:
        """判断是否为官方账号"""
        official_indicators = ['official', 'app', 'company', 'corp', 'inc', 'llc', 'ltd', 'team', 'support']
        
        # 检查用户名和昵称中的官方指示词
        text_to_check = f"{unique_id.lower()} {nickname.lower()}"
        
        for indicator in official_indicators:
            if indicator in text_to_check:
                return True
                
        # 检查signature中是否有公司邮箱
        if '@' in signature and any(domain in signature for domain in ['.com', '.org', '.net', '.co']):
            return True
            
        return False
        
    def analyze_creator_with_gemini(self, signature: str, nickname: str, unique_id: str) -> Dict:
        """使用Gemini API分析创作者是否代表品牌"""
        
        is_official = self.is_official_account(unique_id, nickname, signature)
        
        prompt = f"""Analyze the following TikTok creator profile to determine if they represent a brand:

Creator Username: {unique_id}
Display Name: {nickname}
Bio/Signature: {signature}
Is Official Account: {is_official}

IMPORTANT RULES:
1. For major tech companies (Apple, Microsoft, Google, Amazon, Samsung, etc.), ONLY mark as brand representative if this is clearly an OFFICIAL account (contains "official", company email, verified status, etc.)
2. Individual creators promoting products from major companies should NOT be marked as brand representatives for those companies
3. For apps and smaller brands, be more lenient if there's clear promotion/partnership

Please analyze and respond with EXACTLY 4 values separated by pipes (|):

1. Is Brand Representative [True/False] - Does this creator officially represent, work for, or have a clear partnership with a specific brand/company?
2. Brand Name [Brand name or "None"] - If they represent a brand, what is the brand name? Extract the main brand they represent.
3. Confidence Score [0.0-1.0] - How confident are you in the brand identification (0.0 = not confident, 1.0 = very confident)?
4. Analysis Details [Brief explanation] - Explain why you think they do/don't represent a brand and what indicators you found.

Look for these indicators:
- Company emails (@company.com)
- Official brand accounts
- Clear employment statements ("Product Manager @ Company")
- Business-related keywords in username
- Direct product promotion language
- Brand partnerships mentions
- Official app/service names in username
- Company descriptions

Examples:
- notabilityapp|True|Notability|0.9|Official app account with company branding
- studymoofin|False|None|0.1|Personal study content creator, no clear brand affiliation
- paperlikeofficial|True|Paperlike|0.95|Official company account with clear branding
- randomuser123|False|None|0.1|Individual user promoting Apple products but not official Apple representative

Format: True|BrandName|0.9|Brief explanation
OR: False|None|0.1|Brief explanation"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-05-20",
                contents=[prompt]
            )
            
            if response.text:
                parts = [p.strip() for p in response.text.split('|')]
                if len(parts) == 4:
                    brand_name = parts[1] if parts[1].lower() != 'none' else ''
                    
                    # 检查brand name是否已经被分配
                    if brand_name and brand_name.lower() in self.assigned_brands:
                        logger.warning(f"品牌 '{brand_name}' 已经被分配给其他创作者，将此创作者标记为非品牌代表")
                        return {
                            'is_brand_representative': False,
                            'brand_name': '',
                            'brand_confidence': 0.0,
                            'analysis_details': f'Brand name "{brand_name}" already assigned to another creator'
                        }
                    
                    # 如果是品牌代表，将brand name添加到已分配列表
                    if parts[0].lower() == 'true' and brand_name:
                        self.assigned_brands.add(brand_name.lower())
                    
                    # 安全地转换置信度分数
                    try:
                        confidence = float(str(parts[2]))
                    except (ValueError, AttributeError):
                        confidence = 0.0
                    
                    return {
                        'is_brand_representative': parts[0].lower() == 'true',
                        'brand_name': brand_name,
                        'brand_confidence': confidence,
                        'analysis_details': parts[3]
                    }
                else:
                    logger.warning(f"Unexpected Gemini response format: {response.text}")
                    return self._default_analysis()
            else:
                logger.warning("Empty response from Gemini")
                return self._default_analysis()
                
        except Exception as e:
            logger.error(f"Gemini API error for {unique_id}: {e}")
            return self._default_analysis()
    
    def _default_analysis(self) -> Dict:
        """默认分析结果"""
        return {
            'is_brand_representative': False,
            'brand_name': '',
            'brand_confidence': 0.0,
            'analysis_details': 'Analysis failed'
        }
    
    def process_creator_batch(self, creators_batch: List[Dict]) -> List[CreatorAnalysis]:
        """处理一批创作者"""
        results = []
        
        for creator in creators_batch:
            try:
                # 从嵌套结构中提取信息
                basic_info = creator.get('basic_info', {})
                author_unique_id = basic_info.get('author_unique_id', '').strip()
                author_nickname = basic_info.get('author_nickname', '').strip()
                create_time = basic_info.get('create_time', '')
                
                if not author_unique_id:
                    logger.warning(f"跳过空的 author_unique_id: {creator.get('video_id', 'unknown')}")
                    continue
                
                # 转换时间戳为年月日格式
                create_times = self.convert_timestamp_to_date(create_time)
                
                # 获取TikTok用户信息
                logger.info(f"获取用户信息: {author_unique_id}")
                user_info = self.get_tiktok_user_info(author_unique_id)
                
                # 使用真实的signature或回退到nickname
                signature = user_info.get('signature', '') or f"Creator: {author_nickname}"
                
                # 使用Gemini API分析
                logger.info(f"分析创作者: {author_unique_id} ({author_nickname})")
                analysis_result = self.analyze_creator_with_gemini(signature, author_nickname, author_unique_id)
                
                # 创建分析结果
                analysis = CreatorAnalysis(
                    video_id=str(creator.get('video_id', '')),
                    author_unique_id=author_unique_id,
                    author_link=f"https://www.tiktok.com/@{author_unique_id}",
                    signature=signature.replace('\n', ' ').replace('\r', ' '),  # 清理换行符
                    is_brand_representative=analysis_result['is_brand_representative'],
                    extracted_brand_name=analysis_result['brand_name'],
                    analysis_details=analysis_result['analysis_details'],
                    author_followers_count=user_info.get('author_followers_count', 0),
                    author_followings_count=user_info.get('author_followings_count', 0),
                    videoCount=user_info.get('videoCount', 0),
                    author_avatar=user_info.get('author_avatar', ''),
                    create_times=create_times
                )
                
                results.append(analysis)
                
                # 添加延迟避免API限制
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"处理创作者时出错: {e}")
                continue
                
        return results
    
    def analyze_creators(self, input_file: str = "creator_list.json") -> List[CreatorAnalysis]:
        """分析创作者列表"""
        logger.info(f"开始分析创作者，输入文件: {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                creators = json.load(f)
        except FileNotFoundError:
            logger.error(f"输入文件 {input_file} 不存在")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return []
        
        logger.info(f"加载了 {len(creators)} 个创作者")
        
        # 去重：基于author_unique_id
        unique_creators = {}
        for creator in creators:
            basic_info = creator.get('basic_info', {})
            unique_id = basic_info.get('author_unique_id', '').strip()
            if unique_id and unique_id not in unique_creators:
                unique_creators[unique_id] = creator
        
        creators_list = list(unique_creators.values())
        logger.info(f"去重后有 {len(creators_list)} 个唯一创作者")
        
        # 分批处理
        batch_size = 35  # 每批处理35个创作者
        all_results = []
        
        # 使用ThreadPoolExecutor进行并发处理
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = []
            
            for i in range(0, len(creators_list), batch_size):
                batch = creators_list[i:i + batch_size]
                future = executor.submit(self.process_creator_batch, batch)
                futures.append(future)
                
                # 批次间添加延迟
                if i + batch_size < len(creators_list):
                    time.sleep(1)
            
            # 收集结果
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    all_results.extend(batch_results)
                    logger.info(f"完成批处理，当前总结果数: {len(all_results)}")
                except Exception as e:
                    logger.error(f"批处理失败: {e}")
        
        logger.info(f"分析完成，总共处理了 {len(all_results)} 个创作者")
        return all_results
    
    def save_results(self, results: List[CreatorAnalysis]):
        """保存结果到两个分离的CSV文件"""
        logger.info(f"开始保存结果，总共 {len(results)} 个创作者")
        
        # 分离品牌创作者和非品牌创作者
        brand_creators = [r for r in results if r.is_brand_representative]
        non_brand_creators = [r for r in results if not r.is_brand_representative]
        
        logger.info(f"品牌创作者: {len(brand_creators)}, 非品牌创作者: {len(non_brand_creators)}")
        
        # CSV字段
        fieldnames = [
            'video_id', 'author_unique_id', 'author_link', 'signature',
            'is_brand_representative', 'extracted_brand_name', 'analysis_details',
            'author_followers_count', 'author_followings_count', 'videoCount',
            'author_avatar', 'create_times'
        ]
        
        # 保存品牌创作者
        os.makedirs('analyzed_data', exist_ok=True)
        with open('analyzed_data/brand_creator.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for creator in brand_creators:
                writer.writerow({
                    'video_id': creator.video_id,
                    'author_unique_id': creator.author_unique_id,
                    'author_link': creator.author_link,
                    'signature': creator.signature,
                    'is_brand_representative': creator.is_brand_representative,
                    'extracted_brand_name': creator.extracted_brand_name,
                    'analysis_details': creator.analysis_details,
                    'author_followers_count': creator.author_followers_count,
                    'author_followings_count': creator.author_followings_count,
                    'videoCount': creator.videoCount,
                    'author_avatar': creator.author_avatar,
                    'create_times': creator.create_times
                })
        
        # 保存非品牌创作者
        with open('analyzed_data/non_brand_creator.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            
            for creator in non_brand_creators:
                writer.writerow({
                    'video_id': creator.video_id,
                    'author_unique_id': creator.author_unique_id,
                    'author_link': creator.author_link,
                    'signature': creator.signature,
                    'is_brand_representative': creator.is_brand_representative,
                    'extracted_brand_name': creator.extracted_brand_name,
                    'analysis_details': creator.analysis_details,
                    'author_followers_count': creator.author_followers_count,
                    'author_followings_count': creator.author_followings_count,
                    'videoCount': creator.videoCount,
                    'author_avatar': creator.author_avatar,
                    'create_times': creator.create_times
                })
        
        logger.info(f"品牌创作者结果已保存到 analyzed_data/brand_creator.csv ({len(brand_creators)} 个)")
        logger.info(f"非品牌创作者结果已保存到 analyzed_data/non_brand_creator.csv ({len(non_brand_creators)} 个)")

def main():
    """主函数"""
    start_time = time.time()
    
    analyzer = BrandTextAnalyzer()
    
    # 分析创作者
    results = analyzer.analyze_creators()
    
    if results:
        # 保存结果
        analyzer.save_results(results)
        
        # 输出统计信息
        brand_count = sum(1 for r in results if r.is_brand_representative)
        total_count = len(results)
        brand_percentage = (brand_count / total_count) * 100 if total_count > 0 else 0
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"\n=== 分析完成 ===")
        logger.info(f"总创作者数: {total_count}")
        logger.info(f"品牌创作者数: {brand_count}")
        logger.info(f"品牌创作者比例: {brand_percentage:.2f}%")
        logger.info(f"处理用时: {elapsed_time:.1f} 秒")
        
        # 输出已分配的品牌列表
        if analyzer.assigned_brands:
            logger.info(f"\n已识别的品牌: {sorted(analyzer.assigned_brands)}")
    else:
        logger.error("没有成功分析任何创作者")

if __name__ == "__main__":
    main() 