### Sigma Agent

# Intro
This Agent has been specifically developed for the [AICup 2023 competition](https://aicup2023.ir/), employing a combination of graph algorithms and probability theory to devise robust strategies for a multiplayer game resembling the classic Risk board game.

# Strategies
### Overview
Our primary objective is to maximize our troop gains while simultaneously minimizing our opponents' gains in each game round. Our strategy revolves around assigning a utility score to each candidate move and selecting the one with the highest utility. Additionally, we implement a surprise attack strategy when the game can be won by capturing one or two strategic nodes in the current round.

### Definitions
To determine the feasibility of capturing a node with 'x' troops, we calculate the expected casualties it would take. Utilizing this information, we construct a weighted directed graph known as the *expected casualty graph*. This graph's edge weights correspond to the expected casualties ('expected casualties(x)'). We generate the list of candidate moves by identifying low-casualty defense and offense routes within this graph.

The scoring algorithm assesses the expected troop gains upon successfully capturing a node and the damage inflicted on other players. Several optimizations, such as matrix multiplication and custom-guided binary searches were implemented to ensure algorithm efficiency.

The concept of the danger associated with a node 'u' and the attack power of a player with specified source and target nodes are pivotal definitions for our algorithms. These concepts are repeatedly employed to inform our strategic decisions. Let 'P' represent the set of all players in the game. The calculation of danger(u) is defined as follows, where 'p' is the player to which 'u' belongs, 'V_i' is the set of all nodes belonging to player 'i,' and 'U' is the set of all nodes not occupied by any players:

$$danger(u) = \max\limits_{i \in P\setminus \{p\}} \max\limits_{v \in V_i \bigcup U} \texttt{attackpower}(i,v,u)$$

where `attackpower` of a player with the source node $v$ and the target node $u$ is defined as follows ($\mathcal{P}^{i}_{vu}$ is the set of all feasible paths or straight attack plans for the player $i$, and $c_i$ is the estimated troops gained by the player $i$ in their own turn):

$$attackpower(i,v,u) =  \max\limits_{0 \leq j \leq c} \max\limits_{path \in \mathcal{P}^{i}_{vu}}  (troops(v) + j) - \texttt{expected$\textunderscore$casualty}(path)$$

where $troops(v)$ is the current number of troops on the node $v$, and expected_casualty of a path is the sum of its weights in the `expected casualty graph`.


# One Strategic Attack
This strategy is devised to identify the optimal attack route from players' strategic nodes to other nodes. It is composed of two stages: candidate generation and candidate scoring.

In the initial stage, we systematically iterate over all source nodes (players' strategic nodes). We employ the Dijkstra algorithm on the expected casualty graph to calculate the shortest paths from each source node to all other nodes. These calculated paths are then added to the list of candidates.

In the subsequent stage, we compute a score for each candidate move. The score function is as follows

# Two Strategic Attack


# ThreePlus Attack
Since a successful attack gives us 3 additional troops gains for the next round, an additional strategy to `One Strategic Attack` is provided in case no attack is performed in the previous strategies. Assuming we have $M$ troops to put in our turn, let $0 \leq i \leq M$ be a candidate number of troops to put in order to attack. Also, let $u$ be a node in which we are planning to place the $i$ troops, with the initial troops $I$, and let $v$ be a neighboring node of $u$ that we wish to attack, with $J$ troops. We associate a score to the plan $(u,v,i)$ and choose the tuple with the maximum score. The loss is defined as follows ($c$ is the expected casualty of attacking $J$ troops with $I$ troops) :
$$loss(u,v,i) = c + 0.15 * (i - max(0, c - I))$$
And letting $w$ be the winning probability of attacking $J$ troops with $I$ troops, we have
$$score = 3 * w - loss$$
with the condition that $J \leq 4$ and $loss \leq 3$ (otherwise, we don't perform any attacks).

# Maximize Score


