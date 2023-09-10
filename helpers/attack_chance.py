import numpy as np
from collections import Counter


attacker_dice_probs = dict()
for attacker_dice in range(4):
    defender_dice_probs = dict()
    for defender_dice in range(3):
        probs = Counter()
        cnt = 0

        for pos in range(6 ** (attacker_dice + defender_dice)):
            cur = pos
            attacker_ls = []
            defender_ls = []
            for i in range(attacker_dice):
                attacker_ls.append(cur % 6 + 1)
                cur /= 6
            for i in range(defender_dice):
                defender_ls.append(cur % 6 + 1)
                cur /= 6
            attacker_ls = sorted(attacker_ls, reverse=True)
            defender_ls = sorted(defender_ls, reverse=True)

            attack_loss = 0
            defend_loss = 0
            for i in range(min(attacker_dice, defender_dice)):
                if attacker_ls[i] > defender_ls[i]:
                    defend_loss += 1
                else:
                    attack_loss += 1
            probs[(attack_loss, defend_loss)] += 1
            cnt += 1

        probs_norm = dict()
        for k in probs.keys():
            probs_norm[k] = probs[k] / cnt
        defender_dice_probs[defender_dice] = probs_norm

    attacker_dice_probs[attacker_dice] = defender_dice_probs


def calc_dp(attacker_troops: int, defender_troops: int, fraction=None):
    dp = np.zeros((attacker_troops + 1, defender_troops + 1))
    dp[attacker_troops, defender_troops] = 1
    for att_cnt in range(attacker_troops, -1, -1):
        for def_cnt in range(defender_troops, -1, -1):
            att_dice = min(3, att_cnt - 1)
            def_dice = min(2, def_cnt)
            if att_dice <= 0 or def_dice <= 0 or (fraction is not None and att_cnt < def_cnt * fraction):
                continue

            for pos, prob in attacker_dice_probs[att_dice][def_dice].items():
                dp[max(0, att_cnt - pos[0]), max(0, def_cnt - pos[1])] += prob * dp[att_cnt][def_cnt]
    return dp


def get_chances(attacker_troops: int, defender_troops: int, fraction):
    dp = calc_dp(attacker_troops, defender_troops, fraction)
    outcomes = []
    for att_cnt in range(attacker_troops, -1, -1):
        for def_cnt in range(defender_troops, -1, -1):
            att_dice = min(3, att_cnt - 1)
            def_dice = min(2, def_cnt)
            if att_dice <= 0 or def_dice <= 0 or att_cnt < def_cnt * fraction:
                if dp[att_cnt][def_cnt] > 0:
                    outcomes.append(((att_cnt, def_cnt), dp[att_cnt][def_cnt]))
    return outcomes
