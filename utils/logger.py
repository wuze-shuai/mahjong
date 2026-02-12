import os
import datetime
import hashlib

# 定义日志文件路径（相对于项目根目录或绝对路径）
# 假设 utils 在 D:\project\100DIY\006mahjong\utils
# 日志文件放在 D:\project\100DIY\006mahjong\logs\mahjong_stats.csv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "logs", "mahjong_stats.csv")

def generate_uid(player_name, timestamp):
    """
    生成唯一UID
    规则：MD5(PlayerName)[0:8] + "-" + MD5(Timestamp)[0:6]
    """
    p_hash = hashlib.md5(player_name.encode('utf-8')).hexdigest()[:8]
    t_hash = hashlib.md5(timestamp.encode('utf-8')).hexdigest()[:6]
    return f"{p_hash}-{t_hash}"

def update_log_file(player_name, total_count, correct_count, total_time, session_start_time=None, mode="Unknown"):
    """
    更新日志文件（追加模式，CSV格式，带UID）
    每次程序运行（Session）只更新同一条记录
    
    Args:
        session_start_time: 本次会话开始的时间戳（字符串），用于生成固定的UID
        mode: 游戏模式 (Uniform, HongZhong)
    """
    if session_start_time is None:
        # 如果未提供（兼容旧代码），使用当前时间
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_uid = generate_uid(player_name, timestamp)
    else:
        # 使用会话开始时间作为记录时间戳
        timestamp = session_start_time
        target_uid = generate_uid(player_name, session_start_time)
        
    avg_time = total_time / total_count if total_count > 0 else 0.0
    
    # 构造新的一行内容
    # 格式：UID,Name,Mode,Date,Accuracy,AvgTime
    new_line = f"{target_uid},{player_name},{mode},{timestamp},{correct_count}/{total_count},{avg_time:.2f}\n"
    
    # 确保目录存在
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except:
            pass 
            
    # 如果文件不存在，直接写入
    if not os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("UID,名字,模式,日期,正确率,平均耗时\n")
                f.write(new_line)
        except Exception as e:
            print(f"写入日志文件失败: {e}")
        return

    # 读取现有内容
    lines = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"读取日志文件失败: {e}")
        return

    # 查找并更新
    found = False
    new_lines = []
    
    # 处理可能的BOM头或空文件
    if not lines:
        new_lines.append("UID,名字,模式,日期,正确率,平均耗时\n")
    
    # 遍历查找UID
    header_checked = False
    for line in lines:
        if not header_checked:
            # 检查是否有 Mode 列，如果没有（旧文件），需要升级Header
            if "UID" in line and "模式" not in line:
                new_lines.append("UID,名字,模式,日期,正确率,平均耗时\n")
                header_checked = True
                continue
            header_checked = True
            
        parts = line.strip().split(",")
        if len(parts) >= 1 and parts[0] == target_uid:
            new_lines.append(new_line) # 替换
            found = True
        else:
            # 兼容旧数据行：如果旧数据只有5列，补全为6列（在Name后插入Mode=Uniform）
            # UID,Name,Date,Acc,Time -> UID,Name,Uniform,Date,Acc,Time
            if len(parts) == 5 and "UID" not in parts[0]: # 排除Header
                 # 简单处理：如果不是Header且只有5列，插入默认Mode
                 parts.insert(2, "Uniform")
                 new_lines.append(",".join(parts) + "\n")
            else:
                 new_lines.append(line)
            
    if not found:
        # 如果是已有文件但没表头（异常情况），补表头
        if new_lines and "UID" not in new_lines[0]:
             new_lines.insert(0, "UID,名字,模式,日期,正确率,平均耗时\n")
        new_lines.append(new_line)
        
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"写入日志文件失败: {e}")

def get_player_stats(player_name, mode=None):
    """
    从CSV日志中解析玩家历史数据（聚合统计）
    Args:
        mode: 如果提供，只统计该模式的数据
    Returns: (total, correct, avg_time)
    """
    if not os.path.exists(LOG_FILE):
        return 0, 0, 0.0 # total, correct, avg_time
        
    total_games = 0
    total_correct = 0
    sum_time = 0.0
    
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
            start_idx = 0
            if lines and "名字" in lines[0]:
                start_idx = 1
                
            for line in lines[start_idx:]:
                parts = line.strip().split(",")
                
                # 兼容不同版本格式
                current_name = ""
                accuracy_str = ""
                avg_time_str = ""
                current_mode = "Uniform" # 默认旧数据为Uniform
                
                if len(parts) == 6: # 新格式：UID,Name,Mode,Date,Acc,Time
                    current_name = parts[1]
                    current_mode = parts[2]
                    accuracy_str = parts[4]
                    avg_time_str = parts[5]
                elif len(parts) == 5: # 中间格式：UID,Name,Date,Acc,Time
                    current_name = parts[1]
                    accuracy_str = parts[3]
                    avg_time_str = parts[4]
                elif len(parts) == 4: # 最旧格式：Name,Date,Acc,Time
                    current_name = parts[0]
                    accuracy_str = parts[2]
                    avg_time_str = parts[3]
                else:
                    continue
                    
                if current_name != player_name:
                    continue
                
                if mode and current_mode != mode:
                    continue
                
                # 解析数据并聚合
                if "/" in accuracy_str:
                    try:
                        correct_s, total_s = accuracy_str.split("/")
                        t = int(total_s)
                        c = int(correct_s)
                        avg = float(avg_time_str)
                        
                        total_games += t
                        total_correct += c
                        sum_time += avg * t 
                    except ValueError:
                        continue
                        
    except Exception as e:
        print(f"读取日志出错: {e}")
        
    final_avg_time = sum_time / total_games if total_games > 0 else 0.0
    return total_games, total_correct, final_avg_time
