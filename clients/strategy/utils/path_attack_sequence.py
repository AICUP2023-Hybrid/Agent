from clients.strategy.startegy import AttackAction


def get_one_path_attack_sequence(path):
    attack_actions = []
    for i in range(len(path) - 1):
        attack = AttackAction(src=path[i], dest=path[i + 1], fraction=0, move_fraction=0.999)
        attack_actions.append(attack)
    return attack_actions
