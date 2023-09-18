import online_src
from clients.game_client import GameClient
from clients.utils.attack_chance import get_expected_casualty
from clients.utils.get_possible_danger import get_node_danger


def initialize_turn(game: GameClient | online_src.game.Game):
    game.game_data.update_game_state()

    gdata = game.game_data

    # Get the strategic resource
    nodes_sorted = sorted(gdata.nodes, key=lambda x: -x.score_of_strategic)
    for node in nodes_sorted:
        if not node.is_strategic:
            break
        if node.owner is None:
            print(game.put_one_troop(node.id), "-- putting one troop on", node.id)
            return

    my_nodes = [
        (node, get_node_danger(game.game_data, node))
        for node in nodes_sorted if node.owner == gdata.player_id
    ]
    my_nodes = sorted(my_nodes, key=lambda x: -x[1])
    print([(node.id, node.number_of_troops, danger) for node, danger in my_nodes])
    print('complex calculation')
    for node, danger in my_nodes:
        if danger > 0:
            print(game.put_one_troop(node.id), "-- putting one troop on", node.id)
            return
