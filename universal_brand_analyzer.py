#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用品牌创作者分析器
支持动态数据源和通用品牌判断条件
"""

import os
import sys
import json
import csv
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
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
    is_brand: bool
    is_matrix_account: bool
    is_ugc_creator: bool
    extracted_brand_name: str
    analysis_details: str
    author_followers_count: int
    author_followings_count: int
    videoCount: int
    author_avatar: str
    create_times: str

class UniversalBrandAnalyzer:
    """通用品牌文本分析器"""
    
    def __init__(self, output_dir: str = "analyzed_data", custom_logger=None):
        """
        初始化分析器
        
        Args:
            output_dir: 输出目录
            custom_logger: 自定义logger实例（用于Web应用）
        """
        # 初始化Gemini客户端
        self.client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        
        # 输出目录
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置logger
        if custom_logger:
            self.logger = custom_logger
        else:
            self.logger = logger
        
        # 用于跟踪已分配的品牌名称，确保唯一性
        self.assigned_brands = set()
        # 存储品牌候选者信息，用于智能选择最佳代表
        self.brand_candidates = {}
        
        self.logger.info(f"Universal Brand Analyzer initialized, output dir: {self.output_dir}")
    
    def convert_timestamp_to_date(self, timestamp) -> str:
        """将Unix时间戳转换为年月日格式"""
        try:
            if timestamp and str(timestamp).isdigit():
                dt = datetime.fromtimestamp(int(timestamp))
                return dt.strftime('%Y-%m-%d')
            return ""
        except (ValueError, OSError) as e:
            self.logger.warning(f"时间戳转换失败: {timestamp}, 错误: {e}")
            return ""
    
    def get_tiktok_user_info(self, unique_id: str) -> Dict:
        """获取TikTok用户信息"""
        if not unique_id or unique_id == 'None':
            return self._default_user_info()
            
        url = "https://tiktok-scraper7.p.rapidapi.com/user/info"
        querystring = {"unique_id": unique_id}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "tiktok-scraper7.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and 'data' in data:
                    user_data = data['data'].get('user', {})
                    stats_data = data['data'].get('stats', {})
                    return {
                        'signature': user_data.get('signature', ''),
                        'followerCount': stats_data.get('followerCount', 0),
                        'followingCount': stats_data.get('followingCount', 0),
                        'videoCount': stats_data.get('videoCount', 0),
                        'avatar': user_data.get('avatarThumb', ''),
                        'author_followers_count': stats_data.get('followerCount', 0),
                        'author_followings_count': stats_data.get('followingCount', 0),
                        'author_avatar': user_data.get('avatarThumb', '')
                    }
                else:
                    self.logger.warning(f"TikTok API 返回错误代码: {data.get('code', 'unknown')} for {unique_id}")
            else:
                self.logger.warning(f"TikTok API请求失败: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"获取TikTok用户信息时出错 {unique_id}: {e}")
            
        return self._default_user_info()
    
    def _default_user_info(self) -> Dict:
        """返回默认用户信息"""
        return {
            'signature': '',
            'followerCount': 0,
            'followingCount': 0,
            'videoCount': 0,
            'avatar': '',
            'author_followers_count': 0,
            'author_followings_count': 0,
            'author_avatar': ''
        }
    
    def is_official_account(self, unique_id: str, nickname: str, signature: str) -> bool:
        """检查是否为官方账号"""
        official_indicators = [
            'official', 'verified', '@company.com', '@brand.com', 
            'team', 'support', 'headquarters', 'corporate'
        ]
        
        combined_text = f"{unique_id} {nickname} {signature}".lower()
        return any(indicator in combined_text for indicator in official_indicators)
    
    def analyze_creator_with_gemini(self, signature: str, nickname: str, unique_id: str, context: str = "", user_info: Dict = None) -> Dict:
        """使用Gemini API分析创作者类型"""
        
        is_official = self.is_official_account(unique_id, nickname, signature)
        
        prompt = f"""Analyze the following TikTok creator profile and classify them into ONE of these three categories:

Creator Username: {unique_id}
Display Name: {nickname}
Bio/Signature: {signature}
Is Official Account: {is_official}
Content Context: {context}

CLASSIFICATION CATEGORIES:

1. OFFICIAL_BRAND: Official brand/company accounts or primary promotional accounts
   - Username contains the brand/product name (e.g., @appname, @brandname, @productname)
   - Bio directly promotes their own product/service with app store links, download calls
   - Clear company branding and product ownership
   - Primary account representing the brand/product
   - Examples: @getnoteai, @ainotebook_app, @quizard.ai, @notabilityapp, @appleofficial

2. MATRIX_ACCOUNT: Creator profiles with clear connection to a specific brand
   - Profile has obvious brand links, descriptions, partnerships with ONE specific brand
   - Bio mentions working for/with a specific company or brand
   - Clear affiliation or employment with a particular brand shown in profile
   - Consistent promotion of a single brand across content
   - Examples: "Apple employee", "Brand ambassador for Nike", "Working at Tesla"

3. UGC_CREATOR: Only creators with clear brand partnership signals
   - Look for these SPECIFIC SIGNALS of brand partnerships:
     * Brand mentions/tags in content or bio
     * Use of #ad, #sponsored, #partner tags
     * Disclosure of partnerships or sponsorships
     * Bio links to brand/store (Shopify, LTK, etc.)
     * Discount codes or affiliate links mentioned
     * Call-to-actions encouraging purchases ("Use my code X")
     * Consistent posting about same brand/products with commercial intent
   - Examples: @brandnat with #tldvpartner, creators with discount codes, affiliate marketers
   - IMPORTANT: Only assign brand name if clear partnership signals exist

CRITICAL CLASSIFICATION RULES:
1. If the USERNAME contains a product/brand name AND the bio promotes that same product → OFFICIAL_BRAND
2. If profile clearly shows connection to ONE specific brand (but not official account) → MATRIX_ACCOUNT  
3. For UGC_CREATOR: ONLY assign brand name if clear partnership signals exist (tags, codes, sponsorship disclosure)
4. Content creators who just review/mention products WITHOUT partnership signals should be UGC_CREATOR with NO brand name
5. For major tech companies (Apple, Google, etc.), be strict about "official" indicators for OFFICIAL_BRAND
6. For smaller apps/products, if username = product name → OFFICIAL_BRAND
7. Only ONE category should be True, others must be False

Please respond with EXACTLY 6 values separated by pipes (|):

1. OFFICIAL_BRAND [True/False]
2. MATRIX_ACCOUNT [True/False] 
3. UGC_CREATOR [True/False]
4. Brand Name [Specific brand name or "None"] - ONLY provide brand name if clear partnership signals exist
5. Confidence Score [0.0-1.0] - How confident are you in this classification?
6. Analysis Details [Brief explanation] - Explain your classification reasoning and any partnership signals found

Examples:
- True|False|False|GetNote AI|0.95|Username contains brand name 'getnoteai' and bio promotes GetNote AI app
- True|False|False|AI Notebook App|0.90|Username is 'ainotebook_app' directly promoting their own product
- False|True|False|tldv.io|0.85|Bio shows clear partnership with tldv.io through #tldvpartner tag
- False|False|True|Nike|0.80|Profile shows #nikeambassador and discount codes for Nike products
- False|False|True|None|0.90|General tech reviewer with no clear brand partnership signals or sponsorship disclosure

Format: True|False|False|BrandName|0.9|Brief explanation"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-05-20",
                contents=[prompt]
            )
            
            if response.text:
                parts = [p.strip() for p in response.text.split('|')]
                if len(parts) == 6:
                    is_brand = parts[0].lower() == 'true'
                    is_matrix = parts[1].lower() == 'true'
                    is_ugc = parts[2].lower() == 'true'
                    brand_name = parts[3] if parts[3].lower() != 'none' else ''
                    
                    # 安全地转换置信度分数
                    try:
                        confidence = float(str(parts[4]))
                    except (ValueError, AttributeError):
                        confidence = 0.0
                    
                    # 验证分类的互斥性
                    classifications = [is_brand, is_matrix, is_ugc]
                    if sum(classifications) != 1:
                        self.logger.warning(f"Invalid classification for {unique_id}: multiple/no categories selected, defaulting to UGC")
                        is_brand, is_matrix, is_ugc = False, False, True
                        brand_name = ''
                    
                    # 不再使用智能选择机制拒绝品牌相关创作者
                    # 所有品牌相关的创作者都会被接受
                    if (is_brand or is_matrix) and brand_name:
                        self.assigned_brands.add(brand_name.lower())
                    
                    return {
                        'is_brand': is_brand,
                        'is_matrix_account': is_matrix,
                        'is_ugc_creator': is_ugc,
                        'brand_name': brand_name,
                        'brand_confidence': confidence,
                        'analysis_details': parts[5]
                    }
                else:
                    self.logger.warning(f"Unexpected Gemini response format: {response.text}")
                    return self._default_analysis()
            else:
                self.logger.warning("Empty response from Gemini")
                return self._default_analysis()
                
        except Exception as e:
            self.logger.error(f"Gemini API error for {unique_id}: {e}")
            return self._default_analysis()
    
    def _default_analysis(self) -> Dict:
        """默认分析结果"""
        return {
            'is_brand': False,
            'is_matrix_account': False,
            'is_ugc_creator': True,
            'brand_name': '',
            'brand_confidence': 0.0,
            'analysis_details': 'Analysis failed - defaulted to UGC creator'
        }
    
    def choose_best_brand_representative(self, brand_name: str, candidate_info: Dict) -> bool:
        """
        智能选择最佳品牌代表
        
        Args:
            brand_name: 品牌名称
            candidate_info: 候选者信息 (现在包含is_brand和is_matrix字段)
            
        Returns:
            是否应该选择当前候选者作为品牌代表
        """
        if brand_name.lower() not in self.brand_candidates:
            # 第一个候选者，直接接受
            self.brand_candidates[brand_name.lower()] = candidate_info
            return True
        
        current_best = self.brand_candidates[brand_name.lower()]
        
        # 比较标准（按优先级排序）:
        # 1. 官方品牌账号优先于矩阵账号
        # 2. 官方认证状态
        # 3. 置信度分数
        # 4. 粉丝数量
        # 5. 用户名中包含品牌名称
        
        current_is_brand = current_best.get('is_brand', False)
        current_is_matrix = current_best.get('is_matrix', False)
        new_is_brand = candidate_info.get('is_brand', False)
        new_is_matrix = candidate_info.get('is_matrix', False)
        
        # 优先级: Official Brand > Matrix Account
        if new_is_brand and current_is_matrix:
            self.brand_candidates[brand_name.lower()] = candidate_info
            self.logger.info(f"品牌 '{brand_name}': 选择官方品牌账号 {candidate_info['unique_id']} 替换矩阵账号 {current_best['unique_id']}")
            return True
        
        if current_is_brand and new_is_matrix:
            self.logger.info(f"品牌 '{brand_name}': 保持官方品牌账号 {current_best['unique_id']}，拒绝矩阵账号 {candidate_info['unique_id']}")
            return False
        
        # 如果类型相同，继续其他比较
        current_is_official = current_best.get('is_official', False)
        new_is_official = candidate_info.get('is_official', False)
        
        # 如果新候选者是官方认证而当前不是，选择新的
        if new_is_official and not current_is_official:
            self.brand_candidates[brand_name.lower()] = candidate_info
            self.logger.info(f"品牌 '{brand_name}': 选择新的官方认证账号 {candidate_info['unique_id']} 替换 {current_best['unique_id']}")
            return True
        
        # 如果当前是官方认证而新的不是，保持当前
        if current_is_official and not new_is_official:
            self.logger.info(f"品牌 '{brand_name}': 保持现有官方认证账号 {current_best['unique_id']}，拒绝 {candidate_info['unique_id']}")
            return False
        
        # 如果官方认证状态相同，比较置信度
        current_confidence = current_best.get('confidence', 0.0)
        new_confidence = candidate_info.get('confidence', 0.0)
        
        if new_confidence > current_confidence + 0.1:  # 显著更高的置信度
            self.brand_candidates[brand_name.lower()] = candidate_info
            self.logger.info(f"品牌 '{brand_name}': 选择高置信度账号 {candidate_info['unique_id']} (置信度: {new_confidence:.2f}) 替换 {current_best['unique_id']} (置信度: {current_confidence:.2f})")
            return True
        
        # 如果置信度接近，比较粉丝数量
        if abs(new_confidence - current_confidence) <= 0.1:
            current_followers = current_best.get('followers', 0)
            new_followers = candidate_info.get('followers', 0)
            
            if new_followers > current_followers * 1.5:  # 新候选者粉丝数显著更多
                self.brand_candidates[brand_name.lower()] = candidate_info
                self.logger.info(f"品牌 '{brand_name}': 选择高粉丝账号 {candidate_info['unique_id']} ({new_followers:,} 粉丝) 替换 {current_best['unique_id']} ({current_followers:,} 粉丝)")
                return True
        
        # 检查用户名中是否包含品牌名
        current_has_brand_in_name = brand_name.lower() in current_best['unique_id'].lower()
        new_has_brand_in_name = brand_name.lower() in candidate_info['unique_id'].lower()
        
        if new_has_brand_in_name and not current_has_brand_in_name:
            self.brand_candidates[brand_name.lower()] = candidate_info
            self.logger.info(f"品牌 '{brand_name}': 选择用户名包含品牌的账号 {candidate_info['unique_id']} 替换 {current_best['unique_id']}")
            return True
        
        # 默认保持当前选择
        self.logger.info(f"品牌 '{brand_name}': 保持现有代表 {current_best['unique_id']}，拒绝 {candidate_info['unique_id']}")
        return False
    
    def detect_data_format(self, data: List[Dict]) -> str:
        """检测数据格式类型"""
        if not data:
            return "unknown"
        
        sample = data[0]
        
        # 检查是否为嵌套格式（如creator_list.json）
        if 'basic_info' in sample and isinstance(sample['basic_info'], dict):
            return "nested"
        
        # 检查是否为平面格式（如shoe_list.json的扁平化版本）
        if 'author_unique_id' in sample:
            return "flat"
        
        return "unknown"
    
    def extract_creator_info(self, item: Dict, data_format: str) -> Optional[Dict]:
        """根据数据格式提取创作者信息"""
        try:
            if data_format == "nested":
                # 嵌套格式 (如 creator_list.json)
                basic_info = item.get('basic_info', {})
                author_unique_id = basic_info.get('author_unique_id', '').strip()
                
                if not author_unique_id or author_unique_id == 'None':
                    return None
                    
                return {
                    'video_id': item.get('video_id', ''),
                    'author_unique_id': author_unique_id,
                    'author_nickname': basic_info.get('author_nickname', ''),
                    'create_time': basic_info.get('create_time', ''),
                    'signature': item.get('description', ''),  # 可能在外层
                    'title': item.get('title', ''),
                    'basic_info': basic_info
                }
            
            elif data_format == "flat":
                # 扁平格式
                author_unique_id = item.get('author_unique_id', '').strip()
                
                if not author_unique_id or author_unique_id == 'None':
                    return None
                    
                return {
                    'video_id': item.get('video_id', ''),
                    'author_unique_id': author_unique_id,
                    'author_nickname': item.get('author_nickname', ''),
                    'create_time': item.get('create_time', ''),
                    'signature': item.get('signature', ''),
                    'title': item.get('title', ''),
                    'basic_info': item  # 整个item作为basic_info
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取创作者信息时出错: {e}")
            return None
    
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
                    self.logger.warning(f"跳过空的 author_unique_id: {creator.get('video_id', 'unknown')}")
                    continue
                
                # 转换时间戳为年月日格式（从JSON获取）
                create_times = self.convert_timestamp_to_date(str(create_time))
                
                # 获取TikTok用户信息（API获取signature, followers, etc.）
                self.logger.info(f"获取用户信息: {author_unique_id}")
                user_info = self.get_tiktok_user_info(author_unique_id)
                
                # 从API获取signature，从JSON获取author_avatar（如果有的话）
                signature = user_info.get('signature', '') or f"Creator: {author_nickname}"
                
                # 优先从JSON获取avatar，否则从API获取
                json_avatar = basic_info.get('author_avatar', '') or basic_info.get('thumbnail_url', '')
                api_avatar = user_info.get('author_avatar', '')
                author_avatar = json_avatar or api_avatar
                
                # 构建内容上下文
                title = creator.get('title', '')
                description = creator.get('signature', '') or creator.get('description', '')
                context = f"Title: {title}\nDescription: {description}".strip()
                
                # 使用Gemini API分析
                self.logger.info(f"分析创作者: {author_unique_id} ({author_nickname})")
                analysis_result = self.analyze_creator_with_gemini(
                    signature, author_nickname, author_unique_id, context, user_info
                )
                
                # 创建分析结果
                analysis = CreatorAnalysis(
                    video_id=str(creator.get('video_id', '')),
                    author_unique_id=author_unique_id,
                    author_link=f"https://www.tiktok.com/@{author_unique_id}",
                    signature=signature.replace('\n', ' ').replace('\r', ' '),  # 清理换行符
                    is_brand=analysis_result['is_brand'],
                    is_matrix_account=analysis_result['is_matrix_account'], # 新增字段，默认为False
                    is_ugc_creator=analysis_result['is_ugc_creator'], # 新增字段，默认为False
                    extracted_brand_name=analysis_result['brand_name'],
                    analysis_details=analysis_result['analysis_details'],
                    author_followers_count=user_info.get('author_followers_count', 0),
                    author_followings_count=user_info.get('author_followings_count', 0),
                    videoCount=user_info.get('videoCount', 0),
                    author_avatar=author_avatar,  # 使用优化后的avatar获取逻辑
                    create_times=create_times
                )
                
                results.append(analysis)
                
                # 添加延迟避免API限制
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"处理创作者时出错: {e}")
                continue
                
        return results
    
    def analyze_creators(self, input_file: str) -> List[CreatorAnalysis]:
        """分析创作者列表"""
        self.logger.info(f"开始分析创作者，输入文件: {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                creators_data = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"输入文件 {input_file} 不存在")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {e}")
            return []
        
        self.logger.info(f"加载了 {len(creators_data)} 个数据项")
        
        # 检测数据格式
        data_format = self.detect_data_format(creators_data)
        self.logger.info(f"检测到数据格式: {data_format}")
        
        # 提取唯一的创作者信息
        unique_creators = {}
        for item in creators_data:
            creator_info = self.extract_creator_info(item, data_format)
            if creator_info:
                unique_id = creator_info['author_unique_id']
                if unique_id not in unique_creators:
                    unique_creators[unique_id] = creator_info
        
        creators_list = list(unique_creators.values())
        self.logger.info(f"去重后有 {len(creators_list)} 个唯一创作者")
        
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
                    self.logger.info(f"完成批处理，当前总结果数: {len(all_results)}")
                except Exception as e:
                    self.logger.error(f"批处理失败: {e}")
        
        self.logger.info(f"分析完成，总共处理了 {len(all_results)} 个创作者")
        return all_results
    
    def save_results(self, results: List[CreatorAnalysis], input_filename: str):
        """保存结果到两个CSV文件：品牌相关 和 非品牌"""
        self.logger.info(f"开始保存结果，总共 {len(results)} 个创作者")
        
        # 重新定义品牌相关：有extracted_brand_name或者被标记为品牌/矩阵账号
        brand_related = [r for r in results if 
                        (r.extracted_brand_name and r.extracted_brand_name.strip()) or 
                        r.is_brand or r.is_matrix_account]
        non_brand = [r for r in results if r not in brand_related]
        
        # 在品牌相关账号中按三种类型分类统计
        official_brands = [r for r in brand_related if r.is_brand]
        matrix_accounts = [r for r in brand_related if r.is_matrix_account]
        ugc_in_brand = [r for r in brand_related if r.is_ugc_creator]
        
        self.logger.info(f"品牌相关账号: {len(brand_related)} (官方品牌: {len(official_brands)}, 矩阵账号: {len(matrix_accounts)}, UGC创作者: {len(ugc_in_brand)})")
        self.logger.info(f"非品牌账号: {len(non_brand)}")
        
        # 根据输入文件名生成输出文件名
        base_name = os.path.splitext(os.path.basename(input_filename))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        brand_file = os.path.join(self.output_dir, f"{base_name}_brand_related_{timestamp}.csv")
        non_brand_file = os.path.join(self.output_dir, f"{base_name}_non_brand_{timestamp}.csv")
        
        # CSV字段 (英文字段名)
        fieldnames = [
            'video_id', 'author_unique_id', 'author_link', 'signature',
            'is_brand', 'is_matrix_account', 'is_ugc_creator', 'brand_name', 'analysis_details',
            'author_followers_count', 'author_followings_count', 'videoCount',
            'author_avatar', 'create_times'
        ]
        
        def write_csv(file_path: str, creators: List[CreatorAnalysis]):
            """写入CSV文件的辅助函数"""
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                
                for creator in creators:
                    writer.writerow({
                        'video_id': creator.video_id,
                        'author_unique_id': creator.author_unique_id,
                        'author_link': creator.author_link,
                        'signature': creator.signature,
                        'is_brand': creator.is_brand,
                        'is_matrix_account': creator.is_matrix_account,
                        'is_ugc_creator': creator.is_ugc_creator,
                        'brand_name': creator.extracted_brand_name,
                        'analysis_details': creator.analysis_details,
                        'author_followers_count': creator.author_followers_count,
                        'author_followings_count': creator.author_followings_count,
                        'videoCount': creator.videoCount,
                        'author_avatar': creator.author_avatar,
                        'create_times': creator.create_times
                    })
        
        # 保存两个主要分类文件
        write_csv(brand_file, brand_related)
        write_csv(non_brand_file, non_brand)
        
        self.logger.info(f"品牌相关结果已保存到 {brand_file} ({len(brand_related)} 个)")
        self.logger.info(f"非品牌结果已保存到 {non_brand_file} ({len(non_brand)} 个)")
        
        # 输出品牌相关账号的详细分类统计
        if len(brand_related) > 0:
            brand_pct = (len(official_brands) / len(brand_related)) * 100
            matrix_pct = (len(matrix_accounts) / len(brand_related)) * 100
            ugc_pct = (len(ugc_in_brand) / len(brand_related)) * 100
            
            self.logger.info(f"\n=== brand_related_list 三种类型统计 ===")
            self.logger.info(f"品牌相关账号总数: {len(brand_related)}")
            self.logger.info(f"官方品牌账号 (is_brand): {len(official_brands)} ({brand_pct:.1f}%)")
            self.logger.info(f"矩阵账号 (is_matrix_account): {len(matrix_accounts)} ({matrix_pct:.1f}%)")
            self.logger.info(f"UGC创作者 (is_ugc_creator): {len(ugc_in_brand)} ({ugc_pct:.1f}%)")
            
            # 品牌分布统计
            brand_distribution = {}
            for result in brand_related:
                if result.extracted_brand_name:
                    brand = result.extracted_brand_name
                    if brand not in brand_distribution:
                        brand_distribution[brand] = {'brand': 0, 'matrix': 0, 'ugc': 0}
                    
                    if result.is_brand:
                        brand_distribution[brand]['brand'] += 1
                    elif result.is_matrix_account:
                        brand_distribution[brand]['matrix'] += 1
                    else:  # is_ugc_creator
                        brand_distribution[brand]['ugc'] += 1
            
            if brand_distribution:
                self.logger.info(f"\n=== 品牌分布详情 (在brand_related_list中) ===")
                for brand, counts in sorted(brand_distribution.items()):
                    total_brand = counts['brand'] + counts['matrix'] + counts['ugc']
                    self.logger.info(f"- {brand}: {total_brand} 个账号 (官方: {counts['brand']}, 矩阵: {counts['matrix']}, UGC: {counts['ugc']})")
        else:
            self.logger.info(f"\n=== brand_related_list 三种类型统计 ===")
            self.logger.info(f"没有发现品牌相关账号")
            
        # 总体分类统计（包含所有类型）
        total = len(results)
        if total > 0:
            brand_related_pct = (len(brand_related) / total) * 100
            non_brand_pct = (len(non_brand) / total) * 100
            
            self.logger.info(f"\n=== 总体创作者分类统计 ===")
            self.logger.info(f"品牌相关创作者: {len(brand_related)} ({brand_related_pct:.1f}%)")
            self.logger.info(f"非品牌创作者: {len(non_brand)} ({non_brand_pct:.1f}%)")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通用品牌创作者分析器')
    parser.add_argument('input_file', help='输入JSON文件路径')
    parser.add_argument('--output-dir', default='analyzed_data', help='输出目录 (默认: analyzed_data)')
    parser.add_argument('--batch-size', type=int, default=35, help='批处理大小 (默认: 35)')
    parser.add_argument('--max-workers', type=int, default=7, help='最大并发数 (默认: 7)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        logger.error(f"输入文件不存在: {args.input_file}")
        sys.exit(1)
    
    start_time = time.time()
    
    analyzer = UniversalBrandAnalyzer(output_dir=args.output_dir)
    
    # 分析创作者
    results = analyzer.analyze_creators(args.input_file)
    
    if results:
        # 保存结果
        analyzer.save_results(results, args.input_file)
        
        # 输出统计信息
        brand_count = sum(1 for r in results if r.is_brand)
        matrix_count = sum(1 for r in results if r.is_matrix_account)
        ugc_count = sum(1 for r in results if r.is_ugc_creator)
        
        # 重新定义品牌相关：有extracted_brand_name或者被标记为品牌/矩阵账号
        brand_related_results = [r for r in results if 
                               (r.extracted_brand_name and r.extracted_brand_name.strip()) or 
                               r.is_brand or r.is_matrix_account]
        non_brand_results = [r for r in results if r not in brand_related_results]
        
        # 在品牌相关账号中的三种类型统计
        brand_in_related = sum(1 for r in brand_related_results if r.is_brand)
        matrix_in_related = sum(1 for r in brand_related_results if r.is_matrix_account)
        ugc_in_related = sum(1 for r in brand_related_results if r.is_ugc_creator)
        
        brand_related_count = len(brand_related_results)
        total_count = len(results)
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"\n=== 分析完成 ===")
        logger.info(f"输入文件: {args.input_file}")
        logger.info(f"总创作者数: {total_count}")
        logger.info(f"品牌相关账号: {brand_related_count} ({(brand_related_count/total_count)*100:.1f}%)" if total_count > 0 else "品牌相关账号: 0")
        logger.info(f"非品牌账号: {len(non_brand_results)} ({(len(non_brand_results)/total_count)*100:.1f}%)" if total_count > 0 else "非品牌账号: 0")
        
        # brand_related_list中的三种类型占比
        if brand_related_count > 0:
            brand_in_related_pct = (brand_in_related / brand_related_count) * 100
            matrix_in_related_pct = (matrix_in_related / brand_related_count) * 100
            ugc_in_related_pct = (ugc_in_related / brand_related_count) * 100
            
            logger.info(f"\n=== brand_related_list中三种类型占比 ===")
            logger.info(f"官方品牌账号: {brand_in_related} ({brand_in_related_pct:.1f}%)")
            logger.info(f"矩阵账号: {matrix_in_related} ({matrix_in_related_pct:.1f}%)")
            logger.info(f"UGC创作者: {ugc_in_related} ({ugc_in_related_pct:.1f}%)")
        
        # 所有数据中的三分类统计（参考用）
        if total_count > 0:
            brand_total_pct = (brand_count / total_count) * 100
            matrix_total_pct = (matrix_count / total_count) * 100
            ugc_total_pct = (ugc_count / total_count) * 100
            
            logger.info(f"\n=== 全量数据三分类统计 (参考) ===")
            logger.info(f"官方品牌账号 (is_brand): {brand_count} ({brand_total_pct:.1f}%)")
            logger.info(f"矩阵账号 (is_matrix_account): {matrix_count} ({matrix_total_pct:.1f}%)")
            logger.info(f"UGC创作者 (is_ugc_creator): {ugc_count} ({ugc_total_pct:.1f}%)")
        
        logger.info(f"处理用时: {elapsed_time:.1f} 秒")
        
        # 输出已识别的品牌列表
        brand_list = set()
        for result in brand_related_results:
            if result.extracted_brand_name:
                brand_list.add(result.extracted_brand_name)
        
        if brand_list:
            logger.info(f"\n已识别的品牌: {sorted(brand_list)}")
            
        # 详细品牌分布统计
        brand_distribution = {}
        for result in brand_related_results:
            if result.extracted_brand_name:
                brand = result.extracted_brand_name
                if brand not in brand_distribution:
                    brand_distribution[brand] = {'brand': 0, 'matrix': 0, 'ugc': 0}
                
                if result.is_brand:
                    brand_distribution[brand]['brand'] += 1
                elif result.is_matrix_account:
                    brand_distribution[brand]['matrix'] += 1
                else:  # is_ugc_creator
                    brand_distribution[brand]['ugc'] += 1
        
        if brand_distribution:
            logger.info(f"\n=== 详细品牌分布 (brand_related_list) ===")
            for brand, counts in sorted(brand_distribution.items()):
                total_brand = counts['brand'] + counts['matrix'] + counts['ugc']
                logger.info(f"- {brand}: {total_brand} 个账号 (官方: {counts['brand']}, 矩阵: {counts['matrix']}, UGC: {counts['ugc']})")
    else:
        logger.error("没有成功分析任何创作者")

if __name__ == "__main__":
    main() 