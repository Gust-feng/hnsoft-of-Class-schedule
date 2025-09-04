#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
课表爬虫统一启动脚本
提供用户友好的界面来选择和运行不同的爬虫任务
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """
    打印程序横幅
    """
    print("=" * 70)
    print("                    课表爬虫系统")
    print("=" * 70)
    print("功能说明:")
    print("1. 自动爬取课表数据")
    print("2. 自动处理和转换数据")
    print("3. 自动清理中间文件")
    print("4. 只保留最终处理结果")
    print("=" * 70)

def check_scripts_exist():
    """
    检查必要的脚本文件是否存在
    
    Returns:
        dict: 脚本存在状态
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    scripts = {
        'current_week': os.path.join(current_dir, 'get_current_week_schedule.py'),
        'all_weeks': os.path.join(current_dir, 'get_all_weeks_schedule.py'),
        'processor': os.path.join(current_dir, 'schedule_data_processor.py')
    }
    
    status = {}
    for name, path in scripts.items():
        status[name] = os.path.exists(path)
    
    return status, scripts

def show_menu(script_status):
    """
    显示主菜单
    
    Args:
        script_status (dict): 脚本存在状态
    """
    print("\n请选择要执行的任务:")
    print("-" * 50)
    
    if script_status['current_week']:
        print("1. 爬取当前周课表数据")
        print("   - 获取本周的课程安排")
        print("   - 自动处理并生成CSV和JSON文件")
        print("   - 清理中间文件")
    else:
        print("1. [不可用] 爬取当前周课表数据 (脚本文件缺失)")
    
    print()
    
    if script_status['all_weeks']:
        print("2. 爬取整个学期课表数据")
        print("   - 获取整个学期的课程安排")
        print("   - 自动处理并生成汇总文件")
        print("   - 清理中间文件")
    else:
        print("2. [不可用] 爬取整个学期课表数据 (脚本文件缺失)")
    
    print()
    
    if script_status['processor']:
        print("3. 仅处理已有数据")
        print("   - 处理之前爬取的原始数据")
        print("   - 不进行新的数据爬取")
    else:
        print("3. [不可用] 仅处理已有数据 (处理脚本缺失)")
    
    print()
    print("4. 退出程序")
    print("-" * 50)

def run_script(script_path, script_name):
    """
    运行指定的脚本
    
    Args:
        script_path (str): 脚本路径
        script_name (str): 脚本名称
        
    Returns:
        bool: 执行是否成功
    """
    try:
        print(f"\n正在启动 {script_name}...")
        print("=" * 60)
        
        # 获取脚本所在目录
        script_dir = os.path.dirname(script_path)
        
        # 运行脚本
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=script_dir,
            text=True
        )
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print(f"✅ {script_name} 执行完成")
            return True
        else:
            print(f"❌ {script_name} 执行失败 (退出码: {result.returncode})")
            return False
            
    except KeyboardInterrupt:
        print(f"\n⚠️  用户中断了 {script_name} 的执行")
        return False
    except Exception as e:
        print(f"\n❌ 运行 {script_name} 时发生错误: {e}")
        return False

def run_processor_only(processor_path):
    """
    仅运行数据处理脚本
    
    Args:
        processor_path (str): 处理脚本路径
        
    Returns:
        bool: 执行是否成功
    """
    try:
        print("\n正在启动数据处理脚本...")
        print("=" * 60)
        
        # 获取脚本所在目录
        script_dir = os.path.dirname(processor_path)
        
        # 运行处理脚本（交互式）
        result = subprocess.run(
            [sys.executable, processor_path],
            cwd=script_dir
        )
        
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ 数据处理完成")
            return True
        else:
            print(f"❌ 数据处理失败 (退出码: {result.returncode})")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断了数据处理")
        return False
    except Exception as e:
        print(f"\n❌ 运行数据处理脚本时发生错误: {e}")
        return False

def show_final_summary(success, task_name):
    """
    显示最终执行摘要
    
    Args:
        success (bool): 执行是否成功
        task_name (str): 任务名称
    """
    print("\n" + "=" * 70)
    print("                    执行摘要")
    print("=" * 70)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"执行时间: {current_time}")
    print(f"执行任务: {task_name}")
    
    if success:
        print("执行状态: ✅ 成功完成")
        print("\n输出文件位置: 当前目录")
        print("文件类型:")
        print("  - *.csv: 课程表数据文件")
        print("  - *parsed*.json: 解析后的数据文件")
        print("  - *summary*.json: 汇总数据文件")
        print("\n注意: 所有中间文件已自动清理")
    else:
        print("执行状态: ❌ 执行失败")
        print("\n建议:")
        print("  1. 检查网络连接")
        print("  2. 确认用户凭据正确")
        print("  3. 查看错误信息进行排查")
    
    print("=" * 70)

def main():
    """
    主函数
    """
    print_banner()
    
    # 检查脚本文件
    script_status, script_paths = check_scripts_exist()
    
    # 检查是否有缺失的关键脚本
    missing_scripts = [name for name, exists in script_status.items() if not exists]
    if missing_scripts:
        print("\n⚠️  警告: 以下脚本文件缺失:")
        for script in missing_scripts:
            print(f"  - {script}")
        print("\n某些功能可能不可用。")
    
    while True:
        try:
            show_menu(script_status)
            
            choice = input("\n请输入选择 (1-4): ").strip()
            
            if choice == "1":
                if script_status['current_week']:
                    success = run_script(script_paths['current_week'], "当前周课表爬虫")
                    show_final_summary(success, "爬取当前周课表数据")
                else:
                    print("\n❌ 当前周爬虫脚本不存在，无法执行")
            
            elif choice == "2":
                if script_status['all_weeks']:
                    success = run_script(script_paths['all_weeks'], "整个学期课表爬虫")
                    show_final_summary(success, "爬取整个学期课表数据")
                else:
                    print("\n❌ 整个学期爬虫脚本不存在，无法执行")
            
            elif choice == "3":
                if script_status['processor']:
                    success = run_processor_only(script_paths['processor'])
                    show_final_summary(success, "处理已有数据")
                else:
                    print("\n❌ 数据处理脚本不存在，无法执行")
            
            elif choice == "4":
                print("\n👋 感谢使用课表爬虫系统！")
                break
            
            else:
                print("\n❌ 无效选择，请输入 1-4")
                continue
            
            # 询问是否继续
            if choice in ["1", "2", "3"]:
                print("\n" + "-" * 50)
                continue_choice = input("是否继续使用？(y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', '是', '']:
                    print("\n👋 感谢使用课表爬虫系统！")
                    break
        
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，感谢使用课表爬虫系统！")
            break
        except Exception as e:
            print(f"\n❌ 程序运行时发生错误: {e}")
            print("请重试或联系开发者。")

if __name__ == "__main__":
    main()