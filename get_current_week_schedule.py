#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当前周课表爬虫脚本
专门用于获取当前周的课程表数据
"""

import requests
import json
import time
import os
import subprocess
import sys
import glob
from datetime import datetime
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

class CurrentWeekScheduleCrawler:
    """
    当前周课表爬虫类
    """
    
    def __init__(self):
        self.base_url = "http://222.243.161.213:81"
        self.session = requests.Session()
        self.token = None
        self.user_info = None
        
        # 通用请求头
        self.headers = {
            'Host': '222.243.161.213:81',
            'Cache-Control': 'no-cache',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Origin': 'http://222.243.161.213:81',
            'Referer': 'http://222.243.161.213:81/hnrjzyxysjd/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
    
    def login(self, user_no, password):
        print(f"正在登录用户: {user_no}")
        
        # 登录URL和参数
        login_url = f"{self.base_url}/hnrjzyxyhd/login"
        login_params = {
            'userNo': user_no,
            'pwd': password,
            'encode': '1',
            'captchaData': '',
            'codeVal': ''
        }
        
        # 设置登录请求头
        login_headers = self.headers.copy()
        login_headers['token'] = 'null'
        login_headers['Content-Length'] = '0'
        
        try:
            # 发送登录请求
            response = self.session.post(
                login_url, 
                params=login_params, 
                headers=login_headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == '1':  # 登录成功
                    self.token = data['data']['token']
                    self.user_info = data['data']
                    
                    print(f"登录成功！欢迎 {self.user_info['name']}")
                    print(f"学院: {self.user_info['academyName']}")
                    print(f"班级: {self.user_info['clsName']}")
                    print(f"Token: {self.token[:50]}...")
                    
                    # 保存登录响应
                    self._save_response(response.text, "current_week_login")
                    return True
                else:
                    print(f"登录失败: {data.get('Msg', '未知错误')}")
                    return False
            else:
                print(f"登录请求失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"登录过程发生错误: {e}")
            return False
    
    def get_teaching_week(self):
        """
        获取教学周信息
        """
        if not self.token:
            print("错误: 请先登录")
            return None
            
        try:
            url = f"{self.base_url}/hnrjzyxyhd/teachingWeek"
            headers = self.headers.copy()
            headers['token'] = self.token
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            # 保存响应到文件
            self._save_response(response.text, "current_week_teaching_week")
            
            try:
                data = response.json()
                print("教学周信息获取成功")
                return data
            except json.JSONDecodeError:
                print("教学周响应不是有效的JSON格式")
                return None
                
        except Exception as e:
            print(f"获取教学周信息时出错: {e}")
            return None
    
    def get_current_week_schedule(self, week="", kbjcmsid=""):
        """
        获取当前周课程表数据
        
        Args:
            week (str): 周次（空字符串表示当前周）
            kbjcmsid (str): 课表模式ID
            
        Returns:
            dict: 课程表数据
        """
        if not self.token:
            print("错误: 请先登录")
            return None
            
        try:
            # 使用真实的课程表数据接口
            url = f"{self.base_url}/hnrjzyxyhd/student/curriculum"
            params = {
                'week': week,
                'kbjcmsid': kbjcmsid
            }
            
            headers = self.headers.copy()
            headers['token'] = self.token
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            # 保存响应到文件
            self._save_response(response.text, "current_week_schedule_data")
            
            # 尝试解析JSON响应
            try:
                data = response.json()
                if data.get('code') == '1' or data.get('code') == 1 or 'data' in data:
                    print("当前周课程表数据获取成功")
                    return data
                else:
                    print(f"课程表数据获取失败: {data.get('Msg', data.get('msg', '未知错误'))}")
                    return None
            except json.JSONDecodeError:
                print("响应不是有效的JSON格式")
                return None
                
        except Exception as e:
            print(f"获取课程表数据时出错: {e}")
            return None
    
    def _save_response(self, content, response_type):
        """
        保存响应内容到文件
        
        Args:
            content (str): 响应内容
            response_type (str): 响应类型
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{response_type}_response_{timestamp}.html"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"{response_type}响应已保存到: {filepath}")
        except Exception as e:
            print(f"保存{response_type}响应失败: {e}")
    
    def crawl_current_week(self, user_no, password):

        print("开始执行当前周课表爬取流程")
        print("=" * 60)
        
        results = {
            'login_success': False,
            'user_info': None,
            'teaching_week': None,
            'current_week_data': None,
            'current_week_number': None
        }
        
        # 步骤1: 登录
        if self.login(user_no, password):
            results['login_success'] = True
            results['user_info'] = self.user_info
            
            # 等待一秒，避免请求过快
            time.sleep(1)
            
            # 步骤2: 获取教学周信息
            teaching_week = self.get_teaching_week()
            if teaching_week:
                results['teaching_week'] = teaching_week
                
                # 从教学周信息中获取当前周数
                try:
                    if teaching_week.get('data') and len(teaching_week['data']) > 0:
                        # 查找当前周
                        current_week = None
                        for week_info in teaching_week['data']:
                            if week_info.get('dqz') == '1':  # 当前周标识
                                current_week = week_info.get('zc')
                                break
                        
                        if current_week:
                            results['current_week_number'] = current_week
                            print(f"当前周数: 第{current_week}周")
                        else:
                            print("未找到当前周信息，将获取默认周数据")
                except Exception as e:
                    print(f"解析当前周数失败: {e}")
            
            # 等待一秒
            time.sleep(1)
            
            # 步骤3: 获取当前周课程表数据
            # 使用解析出的当前周数
            current_week_str = str(current_week) if current_week else ""
            current_week_data = self.get_current_week_schedule(week=current_week_str)
            if current_week_data:
                results['current_week_data'] = current_week_data
                print(f"第{current_week}周课程表数据获取成功")
            else:
                print(f"第{current_week}周课程表数据获取失败")
        
        print("\n" + "=" * 60)
        print("当前周爬取流程完成")
        
        return results
    
    def save_raw_data(self, data, filename_prefix="current_week_raw_data"):
        """
        保存原始数据到JSON文件
        
        Args:
            data (dict): 原始数据
            filename_prefix (str): 文件名前缀
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.json"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"原始数据已保存到: {filepath}")
            return filepath
        except Exception as e:
            print(f"保存原始数据失败: {e}")
            return None

def auto_process_data():
    """
    自动调用数据处理脚本
    """
    try:
        print("\n" + "=" * 60)
        print("开始自动处理数据...")
        
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        processor_script = os.path.join(current_dir, "schedule_data_processor.py")
        
        if not os.path.exists(processor_script):
            print(f"错误: 找不到数据处理脚本 {processor_script}")
            return False
        
        # 调用数据处理脚本，自动选择处理当前周数据
        print("正在调用数据处理脚本...")
        result = subprocess.run(
            [sys.executable, processor_script],
            input="1\n",  # 自动选择选项1（处理当前周数据）
            text=True,
            capture_output=True,
            cwd=current_dir
        )
        
        if result.returncode == 0:
            print("数据处理完成！")
            print(result.stdout)
            return True
        else:
            print(f"数据处理失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"自动处理数据时发生错误: {e}")
        return False

def organize_output_files():
    """
    整理输出文件，将CSV和JSON文件分别存放到专门的文件夹中
    """
    try:
        print("\n开始整理输出文件...")
        current_dir = os.getcwd()
        
        # 创建输出文件夹
        csv_dir = os.path.join(current_dir, "csv_files")
        json_dir = os.path.join(current_dir, "json_files")
        
        os.makedirs(csv_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)
        
        # 移动CSV文件
        csv_files = glob.glob(os.path.join(current_dir, '*.csv'))
        moved_csv = []
        for file_path in csv_files:
            filename = os.path.basename(file_path)
            new_path = os.path.join(csv_dir, filename)
            try:
                os.rename(file_path, new_path)
                moved_csv.append(filename)
                print(f"CSV文件已移动: {filename}")
            except Exception as e:
                print(f"移动CSV文件失败 {filename}: {e}")
        
        # 移动JSON文件
        json_files = glob.glob(os.path.join(current_dir, '*.json'))
        moved_json = []
        for file_path in json_files:
            filename = os.path.basename(file_path)
            new_path = os.path.join(json_dir, filename)
            try:
                os.rename(file_path, new_path)
                moved_json.append(filename)
                print(f"JSON文件已移动: {filename}")
            except Exception as e:
                print(f"移动JSON文件失败 {filename}: {e}")
        
        # 删除HTML响应文件
        html_files = glob.glob(os.path.join(current_dir, '*_response_*.html'))
        deleted_html = []
        for file_path in html_files:
            try:
                os.remove(file_path)
                deleted_html.append(os.path.basename(file_path))
                print(f"已删除HTML文件: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"删除HTML文件失败 {os.path.basename(file_path)}: {e}")
        
        # 输出整理结果
        print(f"\n文件整理完成:")
        print(f"  - 移动了 {len(moved_csv)} 个CSV文件到 csv_files/ 文件夹")
        print(f"  - 移动了 {len(moved_json)} 个JSON文件到 json_files/ 文件夹")
        print(f"  - 删除了 {len(deleted_html)} 个HTML响应文件")
        
        if moved_csv:
            print("\nCSV文件列表:")
            for filename in moved_csv:
                print(f"  - csv_files/{filename}")
        
        if moved_json:
            print("\nJSON文件列表:")
            for filename in moved_json:
                print(f"  - json_files/{filename}")
        
        return True
        
    except Exception as e:
        print(f"整理输出文件时发生错误: {e}")
        return False

def main():
    """
    主函数
    """
    print("当前周课表爬虫启动")
    print("=" * 60)
    
    # 创建爬虫实例
    crawler = CurrentWeekScheduleCrawler()
    
    # 用户凭据（需要根据实际情况修改）
    user_no = os.getenv("xuehao")
    password = os.getenv("mima")
    
    # 执行当前周爬取流程
    results = crawler.crawl_current_week(user_no, password)
    
    # 保存原始数据
    raw_data_saved = False
    if results['current_week_data']:
        raw_data_path = crawler.save_raw_data(results['current_week_data'])
        raw_data_saved = raw_data_path is not None
    
    # 输出爬取结果摘要
    print("\n" + "=" * 60)
    print("爬取结果摘要:")
    print("-" * 40)
    print(f"登录状态: {'成功' if results['login_success'] else '失败'}")
    
    if results['user_info']:
        print(f"用户姓名: {results['user_info']['name']}")
        print(f"学号: {results['user_info']['userNo']}")
        print(f"班级: {results['user_info']['clsName']}")
    
    if results['current_week_number']:
        print(f"当前周数: 第{results['current_week_number']}周")
    
    if results['current_week_data']:
        print(f"当前周课程表数据: 获取成功")
    else:
        print(f"当前周课程表数据: 获取失败")
        return
    
    # 如果数据爬取成功，自动处理数据
    if raw_data_saved:
        process_success = auto_process_data()
        
        if process_success:
            # 数据处理成功后，整理输出文件
            organize_success = organize_output_files()
            
            print("\n" + "=" * 60)
            print("✅ 数据处理完成！")
            print("-" * 40)
            print("生成的文件:")
            print("- 课表_weekraw_*.csv: 当前周课程表CSV文件")
            print("- current_week_raw_data_*.json: 原始JSON数据")
            if organize_success:
                print("\n文件已自动整理到对应文件夹中")
            else:
                print("\n注意: 文件整理失败，请手动整理")
        else:
            print("\n" + "=" * 60)
            print("⚠️  数据处理失败")
            print("原始数据文件已保存，您可以手动运行 schedule_data_processor.py 进行处理")
    else:
        print("\n" + "=" * 60)
        print("❌ 数据爬取失败，无法继续处理")

if __name__ == "__main__":
    main()