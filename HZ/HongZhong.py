import random
import sys
import os
import time
from collections import Counter
import datetime

# 引入 utils.logger
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from utils.logger import update_log_file, get_player_stats
except ImportError:
    # 兼容如果没有 utils 模块的情况（虽然根据任务应该有）
    pass

# 牌的定义
# 0-8: 1-9万
# 9-17: 1-9条
# 18-26: 1-9筒
# 27: 红中
RED_DRAGON = 27
TILE_NAMES = {}
for i in range(9):
    TILE_NAMES[i] = f"{i+1}万"
    TILE_NAMES[i+9] = f"{i+1}条"
    TILE_NAMES[i+18] = f"{i+1}筒"
TILE_NAMES[27] = "红中"

# 反向映射，方便解析用户输入
NAME_TO_TILE = {v: k for k, v in TILE_NAMES.items()}
# 增加一些别名支持
for i in range(9):
    NAME_TO_TILE[f"{i+1}w"] = i
    NAME_TO_TILE[f"{i+1}t"] = i+9
    NAME_TO_TILE[f"{i+1}b"] = i+18
    NAME_TO_TILE[f"{i+1}W"] = i
    NAME_TO_TILE[f"{i+1}T"] = i+9
    NAME_TO_TILE[f"{i+1}B"] = i+18
NAME_TO_TILE["hz"] = 27
NAME_TO_TILE["HZ"] = 27
NAME_TO_TILE["hongzhong"] = 27

def get_full_deck():
    """生成112张牌"""
    deck = []
    # 108张常规牌
    for i in range(27):
        deck.extend([i] * 4)
    # 4张红中
    deck.extend([RED_DRAGON] * 4)
    return deck

def tile_to_str(tile):
    return TILE_NAMES.get(tile, "?")

def hand_to_str(hand):
    # 排序：万->条->筒->红中
    sorted_hand = sorted(hand)
    return " ".join([tile_to_str(t) for t in sorted_hand])

def parse_input(text):
    """解析用户输入，返回牌ID"""
    text = text.strip()
    if text in NAME_TO_TILE:
        return NAME_TO_TILE[text]
    # 尝试模糊匹配，如 "1万" "1w"
    # 如果用户输入 "1万 2条" 这种多个，暂只取第一个
    # 这里简单处理，假设用户输入标准名称或别名
    return None

def split_suits(hand):
    """将手牌按花色分组"""
    wan = []
    tiao = []
    tong = []
    hongzhong = 0
    for t in hand:
        if 0 <= t <= 8:
            wan.append(t)
        elif 9 <= t <= 17:
            tiao.append(t - 9) # 归一化到 0-8
        elif 18 <= t <= 26:
            tong.append(t - 18) # 归一化到 0-8
        elif t == RED_DRAGON:
            hongzhong += 1
    return wan, tiao, tong, hongzhong

def need_laizi_for_sets(tiles):
    """
    计算一组牌凑成全刻子/顺子（3n）所需的最少癞子数
    tiles: 归一化后的牌列表 (0-8)，已排序
    使用简单的回溯或贪心+回溯
    """
    if not tiles:
        return 0
    
    n = len(tiles)
    # 状态缓存 key: tuple(tiles) -> min_laizi
    # 这里牌数很少，直接回溯即可
    
    # 1. 尝试组成刻子 tiles[0]
    # 2. 尝试组成顺子 tiles[0]
    
    first = tiles[0]
    counts = Counter(tiles)
    
    best_cost = 999
    
    # 选项A: 组成刻子 (AAA)
    # 消耗 1个first, 还需要 2个first (如果手里有，就扣掉，没有就用癞子)
    # 但由于tiles是列表，我们直接看有多少个first
    c = counts[first]
    
    # Case 1: 构成刻子
    # 移除 min(3, c) 个 first
    # 癞子代价: max(0, 3-c)
    # 但这样不好递归。应该按“剔除”逻辑。
    
    # 递归函数 inner(current_counts) -> cost
    pass

# 由于Python递归深度和性能，对于麻将这种小规模，可以使用带剪枝的DFS
# 为了性能，我们使用计数数组 (长度9)
def get_min_laizi(counts):
    """
    counts: list of size 9
    return: min laizi needed to form 3n
    """
    # 找到第一个非0的牌
    idx = -1
    for i in range(9):
        if counts[i] > 0:
            idx = i
            break
            
    if idx == -1:
        return 0
    
    best = 99
    
    # 尝试刻子
    if counts[idx] >= 3:
        counts[idx] -= 3
        best = min(best, get_min_laizi(counts))
        counts[idx] += 3
    elif counts[idx] == 2:
        counts[idx] -= 2
        best = min(best, 1 + get_min_laizi(counts))
        counts[idx] += 2
    elif counts[idx] == 1:
        counts[idx] -= 1
        best = min(best, 2 + get_min_laizi(counts))
        counts[idx] += 1
        
    # 尝试顺子
    if idx + 2 < 9:
        # 顺子需要 idx, idx+1, idx+2
        # 我们至少有1个 idx
        # 看看 idx+1 和 idx+2 的情况
        
        # 顺子 (idx, idx+1, idx+2)
        # 癞子消耗: (1 if no idx+1) + (1 if no idx+2)
        
        need = 0
        if counts[idx+1] == 0: need += 1
        if counts[idx+2] == 0: need += 1
        
        counts[idx] -= 1
        if counts[idx+1] > 0: counts[idx+1] -= 1
        if counts[idx+2] > 0: counts[idx+2] -= 1
        
        best = min(best, need + get_min_laizi(counts))
        
        # 回溯
        if counts[idx+2] >= 0: counts[idx+2] += 1 # 注意这里不是简单的 +=1，而是要恢复原来的状态
        # 上面的回溯逻辑有误，因为我们不知道原来是多少（虽然如果是0就没减）
        # 正确做法：不要修改原counts，而是传副本，或者记录减了哪些
        pass 
        
    return best

# 重新实现一个更清晰的 Need Laizi 算法
def calc_need_laizi(counts):
    """
    计算凑成 3n 组合所需的最少癞子数
    counts: list of int, length 9, 表示 1-9 的数量
    """
    total = sum(counts)
    if total == 0:
        return 0
        
    # 深度优先搜索
    def dfs(idx):
        if idx >= 9:
            return 0
        
        if counts[idx] == 0:
            return dfs(idx + 1)
            
        # 此时 counts[idx] > 0
        # 只有三种选择：
        # 1. 做刻子 (AAA)
        # 2. 做顺子 (ABC)
        # 3. 剩下的不管了？不行，必须全部分配完。
        # 实际上，对于 idx 这张牌，它必须被用掉。
        
        res = 99
        
        # 1. 构成刻子
        # 需要 3 张，现有 counts[idx]
        # 癞子消耗: max(0, 3 - counts[idx])
        # 但这里有个问题：如果 counts[idx] == 4，用掉3张剩1张？
        # 麻将里 4张一样可以算杠，或者 3+1。这里只考虑 3n。
        # 如果 counts[idx] >= 3，用掉3张，剩下继续 dfs(idx) -- 因为可能还有剩
        
        # 方式A：拿走3张做刻子
        if counts[idx] >= 3:
            counts[idx] -= 3
            res = min(res, dfs(idx))
            counts[idx] += 3
        else:
            # 只有 1 或 2 张，强行配刻子需要补癞子
            # 补癞子后，这 1或2 张就被消掉了
            need = 3 - counts[idx]
            old_val = counts[idx]
            counts[idx] = 0
            res = min(res, need + dfs(idx + 1))
            counts[idx] = old_val
            
        # 2. 构成顺子 (idx, idx+1, idx+2)
        if idx + 2 < 9:
            # 我们至少用掉一张 idx
            counts[idx] -= 1
            
            # 看看 idx+1 和 idx+2
            need = 0
            dec_1 = False
            dec_2 = False
            
            if counts[idx+1] > 0:
                counts[idx+1] -= 1
                dec_1 = True
            else:
                need += 1
                
            if counts[idx+2] > 0:
                counts[idx+2] -= 1
                dec_2 = True
            else:
                need += 1
                
            res = min(res, need + dfs(idx)) # 再次 dfs(idx)，因为 idx 可能还有剩
            
            # 回溯
            if dec_2: counts[idx+2] += 1
            if dec_1: counts[idx+1] += 1
            counts[idx] += 1
            
        return res

    return dfs(0)

# 优化版：带缓存的 DP
# 由于 counts 是可变的，转为 tuple 作为 key
memo_laizi = {}
def get_laizi_cost(counts_tuple):
    if counts_tuple in memo_laizi:
        return memo_laizi[counts_tuple]
    
    idx = -1
    for i in range(9):
        if counts_tuple[i] > 0:
            idx = i
            break
    if idx == -1:
        return 0
        
    c_list = list(counts_tuple)
    res = 99
    
    # 1. 刻子
    if c_list[idx] >= 3:
        c_list[idx] -= 3
        res = min(res, get_laizi_cost(tuple(c_list)))
        c_list[idx] += 3
    else:
        # 补癞子成刻
        need = 3 - c_list[idx]
        old = c_list[idx]
        c_list[idx] = 0
        res = min(res, need + get_laizi_cost(tuple(c_list)))
        c_list[idx] = old
        
    # 2. 顺子
    if idx + 2 < 9:
        c_list[idx] -= 1
        need = 0
        dec1 = False
        dec2 = False
        
        if c_list[idx+1] > 0:
            c_list[idx+1] -= 1
            dec1 = True
        else:
            need += 1
            
        if c_list[idx+2] > 0:
            c_list[idx+2] -= 1
            dec2 = True
        else:
            need += 1
            
        res = min(res, need + get_laizi_cost(tuple(c_list)))
        
        if dec2: c_list[idx+2] += 1
        if dec1: c_list[idx+1] += 1
        c_list[idx] += 1
        
    memo_laizi[counts_tuple] = res
    return res

def is_hu_with_laizi(hand):
    """
    判断是否胡牌（带红中）
    hand: 14张牌的列表
    """
    wan, tiao, tong, laizi_count = split_suits(hand)
    
    # 将各花色转为计数数组
    def to_counts(tiles):
        c = [0] * 9
        for t in tiles:
            c[t] += 1
        return tuple(c)
        
    wan_counts = to_counts(wan)
    tiao_counts = to_counts(tiao)
    tong_counts = to_counts(tong)
    
    # 计算各花色凑成 3n 所需的癞子数
    # cost_3n = get_laizi_cost(counts)
    
    # 我们需要遍历哪一种花色做“将” (2, 5, 8, 11, 14...)
    # 做将意味着：先拿出一对（需0-2癞子），剩下的凑3n
    # 剩下的花色直接凑3n
    
    # 1. 计算每个花色纯3n的代价
    cost_wan_3n = get_laizi_cost(wan_counts)
    cost_tiao_3n = get_laizi_cost(tiao_counts)
    cost_tong_3n = get_laizi_cost(tong_counts)
    
    # 2. 尝试万做将
    # 遍历万的每一种牌作为将
    # 如果该牌有2张，消耗0癞子；1张，消耗1癞子；0张，消耗2癞子
    min_laizi_needed = 99
    
    # 优化：只尝试手牌里有的牌做将，或者如果不缺癞子，可以尝试任意牌做将
    # 但由于癞子可以变任意牌，如果手牌里没有1万，我们也可以用2个癞子变1万做将。
    # 只要总癞子够就行。
    # 实际上，如果手牌里有某张牌，用它做将最省。
    # 如果全都靠癞子做将，那消耗2个癞子。
    
    # 尝试万做将
    for i in range(9):
        # 假设用 i 做将
        c_list = list(wan_counts)
        need_for_pair = 0
        if c_list[i] >= 2:
            c_list[i] -= 2
        elif c_list[i] == 1:
            c_list[i] -= 1
            need_for_pair = 1
        else:
            # 没有这张牌，强行做将需2癞子
            need_for_pair = 2
        
        cost_body = get_laizi_cost(tuple(c_list))
        total = need_for_pair + cost_body + cost_tiao_3n + cost_tong_3n
        if total <= laizi_count:
            return True
            
    # 尝试条做将
    for i in range(9):
        c_list = list(tiao_counts)
        need_for_pair = 0
        if c_list[i] >= 2:
            c_list[i] -= 2
        elif c_list[i] == 1:
            c_list[i] -= 1
            need_for_pair = 1
        else:
            need_for_pair = 2
            
        cost_body = get_laizi_cost(tuple(c_list))
        total = need_for_pair + cost_body + cost_wan_3n + cost_tong_3n
        if total <= laizi_count:
            return True

    # 尝试筒做将
    for i in range(9):
        c_list = list(tong_counts)
        need_for_pair = 0
        if c_list[i] >= 2:
            c_list[i] -= 2
        elif c_list[i] == 1:
            c_list[i] -= 1
            need_for_pair = 1
        else:
            need_for_pair = 2
            
        cost_body = get_laizi_cost(tuple(c_list))
        total = need_for_pair + cost_body + cost_wan_3n + cost_tiao_3n
        if total <= laizi_count:
            return True
            
    # 特殊情况：红中做将
    # 如果红中做将，需要2个红中。
    # 剩下的全都要凑3n
    if laizi_count >= 2:
        total = cost_wan_3n + cost_tiao_3n + cost_tong_3n
        if total <= (laizi_count - 2):
            return True
            
    return False

def get_valid_ting_counts(hand_13):
    """
    计算打出某张牌后，能听多少张牌（有效张数）
    return: int (有效张数)
    """
    # 遍历所有可能的34种牌 + 红中? 
    # 红中算听牌吗？算。
    # 34种常规牌 + 红中 = 35种
    
    # 统计手牌已有数量，用于计算有效张数
    hand_counts = Counter(hand_13)
    
    ting_list = []
    # 遍历 0-26 (常规) + 27 (红中)
    for tile in range(28):
        # 检查是否胡牌
        if is_hu_with_laizi(hand_13 + [tile]):
            ting_list.append(tile)
            
    # 计算有效张数
    valid_count = 0
    for t in ting_list:
        already_have = hand_counts[t]
        # 总张数4 - 手里有的
        left = 4 - already_have
        if left > 0:
            valid_count += left
            
    return valid_count, ting_list

def analyze_hand(hand_14):
    """
    分析手牌，返回每种打法的听牌数
    return: dict { discard_tile: (valid_count, ting_list) }
    """
    results = {}
    unique_tiles = sorted(list(set(hand_14)))
    
    for discard in unique_tiles:
        # 临时移除这张牌
        temp_hand = list(hand_14)
        temp_hand.remove(discard)
        
        count, tings = get_valid_ting_counts(temp_hand)
        if count > 0:
            results[discard] = (count, tings)
            
    return results

def main():
    print("=== 红中麻将听牌训练 ===")
    print("规则：手牌14张（含红中），选择打出一张牌，使听牌有效张数最多。")
    print("输入牌名（如 1万, 2条, 5筒, 红中），输入 'q' 退出。")
    print("-" * 50)
    
    player_name = input("请输入玩家名称: ").strip() or "Anonymous"
    
    # 加载历史数据
    try:
        hist_total, hist_correct, hist_avg_time = get_player_stats(player_name, mode="HongZhong")
        if hist_total > 0:
            print(f"欢迎 {player_name}！历史记录(HongZhong): 答题 {hist_total} 道，正确率 {hist_correct/hist_total:.1%}，平均耗时 {hist_avg_time:.2f}秒")
        else:
            print(f"欢迎 {player_name}！(新玩家)")
    except Exception as e:
        print(f"读取历史记录失败: {e}")

    session_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    session_count = 0
    session_correct = 0
    session_total_time = 0.0
    
    while True:
        # 发牌
        full_deck = get_full_deck()
        random.shuffle(full_deck)
        hand = sorted(full_deck[:14])
        
        # DEBUG: Force specific hand
        # 234m, 13457789s, 678p
        # hand = [1, 2, 3, 9, 11, 12, 13, 15, 15, 16, 17, 23, 24, 25]
        
        # 打印 "思考中..."
        
        start_time = time.time()
        
        # 计算最佳打法
        # 为了不让用户等太久，这里可能需要优化
        # 目前算法复杂度：
        # 14次循环 (打每一张) * 28次循环 (摸每一张) * 胡牌判定 (3次DP)
        # 14 * 28 * small_constant ~ 400次小运算，应该很快 (<0.1s)
        
        analysis = analyze_hand(hand)
        
        # 找出最大听牌数
        if not analysis:
            # 这种情况极少见（相公？），或者这把牌烂到打啥都不听
            # 重新发牌
            continue
            
        print(f"\n当前手牌: {hand_to_str(hand)}")
        
        max_score = max(v[0] for v in analysis.values())
        best_discards = [k for k, v in analysis.items() if v[0] == max_score]
        
        while True:
            user_input = input("请打出一张牌：").strip()
            end_time = time.time()
            
            if user_input.lower() == 'q':
                return
                
            discard_tile = parse_input(user_input)
            if discard_tile is None:
                print("输入无法识别，请重试（示例：1万, 2t, 红中）")
                continue
                
            if discard_tile not in hand:
                print("你手里没有这张牌！")
                continue
                
            # 验证答案
            duration = end_time - start_time
            session_count += 1
            session_total_time += duration
            
            user_score = 0
            if discard_tile in analysis:
                user_score = analysis[discard_tile][0]
            
            is_correct = (user_score == max_score)
            
            if is_correct:
                print(f"✅ 回答正确！打出【{tile_to_str(discard_tile)}】听 {user_score} 张牌。")
                if user_score > 0 and discard_tile in analysis:
                    print(f"   听牌详情: {' '.join([tile_to_str(t) for t in analysis[discard_tile][1]])}")
                session_correct += 1
            else:
                print(f"❌ 回答错误。打出【{tile_to_str(discard_tile)}】听 {user_score} 张牌。")
                if discard_tile in analysis:
                     print(f"   你的打法听: {' '.join([tile_to_str(t) for t in analysis[discard_tile][1]])}")
                
                print(f"最优解是打出：{' 或 '.join([tile_to_str(t) for t in best_discards])}，能听 {max_score} 张。")
                for best in best_discards:
                    if best in analysis:
                        print(f"   打出【{tile_to_str(best)}】听: {' '.join([tile_to_str(t) for t in analysis[best][1]])}")
                
            # 显示详细听牌信息（可选）
            # print(f"听牌详情: {[tile_to_str(t) for t in analysis[discard_tile][1]]}")
            
            # 记录日志
            try:
                update_log_file(player_name, session_count, session_correct, session_total_time, session_start_time, mode="HongZhong")
            except Exception:
                pass
                
            avg_time = session_total_time / session_count
            print(f"本次成绩: {session_correct}/{session_count} ({session_correct/session_count:.1%}) | 平均耗时: {avg_time:.2f}秒")
            
            break

if __name__ == "__main__":
    main()
