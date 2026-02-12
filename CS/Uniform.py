import random
import sys
import time
import os
import datetime

import re

# 引入自定义的日志模块
# 将utils目录添加到sys.path中，以便可以导入
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.logger import update_log_file, get_player_stats

def get_full_deck():
    """生成一副清一色麻将牌（1-9各4张）"""
    return [i for i in range(1, 10) for _ in range(4)]

def generate_hand():
    """随机生成13张手牌"""
    deck = get_full_deck()
    random.shuffle(deck)
    hand = sorted(deck[:13])
    return hand

def is_hu(hand):
    """
    判断14张牌是否胡牌
    标准胡牌：4句话 + 1对将
    Returns: (bool, structure_info)
    """
    if len(hand) != 14:
        return False, []
    
    # 统计每张牌的数量
    counts = {}
    for card in hand:
        counts[card] = counts.get(card, 0) + 1
    
    # 尝试每一张牌作为将牌
    for card in sorted(counts.keys()):
        if counts[card] >= 2:
            # 复制一份牌的统计，避免修改原数据
            temp_counts = counts.copy()
            temp_counts[card] -= 2
            
            # 检查剩余的12张牌是否能组成4句话
            result, sets = get_hu_structure(temp_counts, 4)
            if result:
                return True, [{"type": "pair", "card": card}] + sets
    return False, []

def check_sets(counts, sets_needed):
    """
    保留原有接口，为了兼容旧代码（虽然可以直接改用get_hu_structure）
    """
    res, _ = get_hu_structure(counts, sets_needed)
    return res

def get_hu_structure(counts, sets_needed):
    """
    检查剩余的牌是否能组成指定数量的顺子或刻子，并返回结构
    counts: 剩余牌的计数 {card: count}
    sets_needed: 需要组成的句子数量
    Return: (bool, list_of_sets)
    """
    if sets_needed == 0:
        return True, []
    
    # 找到最小的一张牌
    first_card = -1
    for card in range(1, 10):
        if counts.get(card, 0) > 0:
            first_card = card
            break
    
    if first_card == -1:
        return True, [] 

    # 尝试组成刻子 (AAA)
    if counts[first_card] >= 3:
        counts[first_card] -= 3
        res, sets = get_hu_structure(counts, sets_needed - 1)
        if res:
            return True, [{"type": "triplet", "card": first_card}] + sets
        counts[first_card] += 3 # 回溯

    # 尝试组成顺子 (ABC)
    if (first_card + 1 in counts and counts[first_card + 1] > 0 and 
        first_card + 2 in counts and counts[first_card + 2] > 0):
        
        counts[first_card] -= 1
        counts[first_card + 1] -= 1
        counts[first_card + 2] -= 1
        
        res, sets = get_hu_structure(counts, sets_needed - 1)
        if res:
            return True, [{"type": "sequence", "start": first_card}] + sets
            
        # 回溯
        counts[first_card] += 1
        counts[first_card + 1] += 1
        counts[first_card + 2] += 1
        
    return False, []

def get_waiting_cards(hand):
    """
    计算当前手牌（13张）听哪些牌
    """
    waiting = []
    hand_counts = {}
    for card in hand:
        hand_counts[card] = hand_counts.get(card, 0) + 1
        
    for card in range(1, 10):
        # 检查是否已经有4张了，如果有4张则不可能再摸到（但在纯听牌逻辑中，有时也会算作听，只是摸不到。
        # 题目要求“提供给玩家的13张牌...判断胡哪些数字”。
        # 如果手牌已有4张，实际上无法胡这张（除非杠？题目未提）。
        # 这里假设如果手牌已有4张，则不能再作为有效进张。
        if hand_counts.get(card, 0) == 4:
            continue
            
        # 尝试加入这张牌
        temp_hand = sorted(hand + [card])
        is_hu_res, _ = is_hu(temp_hand)
        if is_hu_res:
            waiting.append(card)
            
    return waiting

def explain_hu(hand, waiting_cards):
    """
    解释为什么听这些牌
    """
    print("\n💡 提示分析：")
    for card in waiting_cards:
        temp_hand = sorted(hand + [card])
        _, structure = is_hu(temp_hand)
        
        # 格式化输出
        parts = []
        for item in structure:
            if item['type'] == 'pair':
                parts.append(f"将[{item['card']}{item['card']}]")
            elif item['type'] == 'triplet':
                c = item['card']
                parts.append(f"刻[{c}{c}{c}]")
            elif item['type'] == 'sequence':
                s = item['start']
                parts.append(f"顺[{s}{s+1}{s+2}]")
        
        print(f"{' + '.join(parts)}")

def main():
    print("=== 麻将清一色听牌训练 ===")
    player_name = input("请输入玩家名称: ").strip()
    if not player_name:
        player_name = "Anonymous"
        
    # 加载历史数据
    hist_total, hist_correct, hist_avg_time = get_player_stats(player_name, mode="Uniform")
    hist_total_time = hist_avg_time * hist_total
    
    print(f"欢迎 {player_name}！")
    if hist_total > 0:
        print(f"历史记录: 答题 {hist_total} 道，正确率 {hist_correct/hist_total:.1%}，平均耗时 {hist_avg_time:.2f}秒")
    else:
        print("新玩家，加油！")
        
    print("规则：手牌13张，输入你能胡的牌（数字1-9），如 '147'。输入 'q' 退出。")
    print("      输入 'h' 查看提示。")
    print("-" * 40)
    
    # 本次会话的统计
    session_count = 0
    session_correct = 0
    session_total_time = 0.0
    
    # 记录会话开始时间，用于生成固定的UID
    session_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    while True:
        hand = generate_hand()
        # 确保生成的手牌是有听牌的（可选，为了训练效率，如果随机生成的牌没听，可能体验不好？
        # 但完全随机也是一种训练，先保持完全随机）
        
        # 计算正确答案
        correct_waiting = get_waiting_cards(hand)
        
        # 如果是死胡（没听），重新发牌，保证有题可做
        if not correct_waiting:
            continue
            
        print(f"\n当前手牌: {hand}")
        
        start_time = time.time()
        
        # 增加一个内部循环来处理用户输入，以便在提示后能继续输入
        while True:
            user_input = input("请输入听牌数字：")
            end_time = time.time()
            
            if user_input.lower() == 'q':
                sys.exit(0) # 直接退出程序
            
            if user_input.lower() == 'h':
                explain_hu(hand, correct_waiting)
                print("\n请重新输入答案：")
                # 不重置start_time，这样思考时间会计入总时间（或者看需求是否重置）
                # 这里假设提示也是学习过程，计入时间
                continue
            
            # 如果不是命令，跳出内部循环进行判断
            break
            
        duration = end_time - start_time
        session_total_time += duration
        
        # 处理用户输入
        try:
            # 过滤非数字字符
            user_waiting = sorted(list(set([int(c) for c in user_input if c.isdigit()])))
        except ValueError:
            print("输入格式错误，请重试。")
            continue
            
        session_count += 1
        
        # 比较答案
        is_correct = False
        if user_waiting == correct_waiting:
            print("✅ 回答正确！")
            session_correct += 1
            is_correct = True
        else:
            print(f"❌ 回答错误。")
            print(f"你的答案: {user_waiting}")
            print(f"正确答案: {correct_waiting}")
            
        # 更新总统计
        total_acc_count = hist_total + session_count
        total_acc_correct = hist_correct + session_correct
        total_acc_time = hist_total_time + session_total_time

        # 记录日志
        # 传入 session_start_time，确保同一次会话只更新同一行
        update_log_file(player_name, session_count, session_correct, session_total_time, session_start_time, mode="Uniform")
        
        avg_time = session_total_time / session_count
        overall_avg_time = total_acc_time / total_acc_count
        
        print(f"本次耗时: {duration:.2f}秒")
        print(f"本次成绩: {session_correct}/{session_count} ({session_correct/session_count:.1%}) | 平均耗时: {avg_time:.2f}秒")
        print(f"历史累计: {total_acc_correct}/{total_acc_count} ({total_acc_correct/total_acc_count:.1%}) | 总平均耗时: {overall_avg_time:.2f}秒")

if __name__ == "__main__":
    main()
