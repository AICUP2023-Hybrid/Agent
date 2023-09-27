from clients.deep.deep_env import OnePlayerEnv


env = OnePlayerEnv(player_id=1)
env.reset()
for i in range(5):
    env.step(4)
env.render()
