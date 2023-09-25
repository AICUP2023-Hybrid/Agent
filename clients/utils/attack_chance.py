import os.path
from typing import List

import numpy as np
from collections import Counter

from components.node import Node

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


expected_casualty = []


def get_expected_casualty():
    global expected_casualty
    if len(expected_casualty) == 0:
        expected_casualty = []
        for d in range(40):
            expected_remain = 0
            for pr, prob in get_chances(d + 15, d, 0):
                expected_remain += pr[0] * prob
            expected_casualty.append(d + 15 - expected_remain)
        for i in range(40, 400):
            expected_casualty.append(0.688 * i)  # good approx
    return expected_casualty


def get_expected_casualty_by_troops(attack_troops, defend_troops):
    all_pos = get_chances(attack_troops, defend_troops, 0)
    exp = 0
    for (attack, defence), possibility in all_pos:
        exp += possibility * (attack_troops - attack)
    return exp


attack_outcome_table = None
MAX_TROOP_CALC = 100


# table is indexed like this [defender_troops, attack_troops, attack_remaining] = prob of attack remaining outcome
def get_attacker_outcome_table():
    global attack_outcome_table
    if attack_outcome_table is not None:
        return attack_outcome_table
    path = './clients/utils/attack_outcomes.npy'
    if os.path.exists(path):
        attack_outcome_table = np.load(path)
    else:
        attack_outcome_table = np.zeros((MAX_TROOP_CALC, MAX_TROOP_CALC, MAX_TROOP_CALC))
        for defender in range(MAX_TROOP_CALC):
            for attacker in range(MAX_TROOP_CALC):
                outcomes = get_chances(attacker, defender, 0)
                for (att_cnt, def_cnt), prob in outcomes:
                    attack_outcome_table[defender][attacker][att_cnt] += prob
        np.save(path, attack_outcome_table)
    return attack_outcome_table


def get_attack_outcomes(path: List[Node]):
    attack_outcomes = get_attacker_outcome_table()
    cur_outcome = np.zeros((MAX_TROOP_CALC,))
    cur_outcome[min(MAX_TROOP_CALC - 1, path[0].number_of_troops)] = 1.
    for node in path[1:]:
        defenders = min(MAX_TROOP_CALC - 1, node.number_of_troops + node.number_of_fort_troops)
        cur_outcome = np.matmul(cur_outcome, attack_outcomes[defenders])
        cur_outcome = np.roll(cur_outcome, -1)
        cur_outcome[0] += cur_outcome[-1]
        cur_outcome[-1] = 0
    return cur_outcome


def get_win_rate(attack_troops, defend_troops):
    attack_troops = min(attack_troops, MAX_TROOP_CALC - 1)
    defend_troops = min(defend_troops, MAX_TROOP_CALC - 1)
    loss = get_attacker_outcome_table()[defend_troops][attack_troops][0]
    loss += get_attacker_outcome_table()[defend_troops][attack_troops][1]
    return 1 - loss
