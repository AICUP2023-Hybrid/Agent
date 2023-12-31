### Sigma Agent

# Intro
This Agent has been specifically developed for the [AICup 2023 competition](https://aicup2023.ir/), employing a combination of graph algorithms and probability theory to devise robust strategies for a multiplayer game resembling the classic Risk board game.

# Strategies
### Overview
Our primary objective is to maximize our troop gains while simultaneously minimizing our opponents' gains in each game round. Our strategy revolves around assigning a utility score to each candidate move and selecting the one with the highest utility. Additionally, we implement a surprise attack strategy when the game can be won by capturing one or two strategic nodes in the current round.

### Definitions
To determine the feasibility of capturing a node with `x` troops, we calculate the expected casualties it would take. Utilizing this information, we construct a weighted directed graph known as the *expected casualty graph*. This graph's edge weights correspond to the expected casualties (`expected_casualties(x)`). We generate the list of candidate moves by identifying low-casualty defense and offense routes within this graph.

The scoring algorithm assesses the expected troop gains upon successfully capturing a node and the damage inflicted on other players. Several optimizations, such as matrix multiplication and custom-guided binary searches were implemented to ensure algorithm efficiency.

The concept of the danger associated with a node $u$ and the attack power of a player with specified source and target nodes are pivotal definitions for our algorithms. These concepts are repeatedly employed to inform our strategic decisions. Let $P$ represent the set of all players in the game. The calculation of $danger(u)$ is defined as follows, where $p$ is the player to which $u$ belongs, $V_i$ is the set of all nodes belonging to player $i$, and $U$ is the set of all nodes not occupied by any players:

$$danger(u) = \max\limits_{i \in P\setminus \{p\}} \max\limits_{v \in V_i \bigcup U} \texttt{attackpower}(i,v,u)$$

where `attackpower` of a player with the source node $v$ and the target node $u$ is defined as follows ($\mathcal{P}^{i}_{vu}$ is the set of all feasible paths or straight attack plans for the player $i$, and $c_i$ is the estimated troops gained by the player $i$ in their own turn):

$$attackpower(i,v,u) =  \max\limits_{0 \leq j \leq c} \max\limits_{path \in \mathcal{P}^{i}_{vu}}  (troops(v) + j) - \texttt{expected$\textunderscore$casualty}(path)$$

where $troops(v)$ is the current number of troops on the node $v$, and expected_casualty of a path is the sum of its weights in the *expected casualty graph*.


# One Strategic Attack
This strategy is devised to identify the optimal attack route from players' strategic nodes to other nodes. It is composed of two stages: candidate generation and candidate scoring.

In the initial stage, we systematically iterate over all source nodes (players' strategic nodes). We employ the Dijkstra algorithm on the expected casualty graph to calculate the shortest paths from each source node to all other nodes. These calculated paths are then added to the list of candidates.

In the subsequent stage, we compute a score for each candidate move. The score is defined as sum of following terms:

$$ hold = \sum_{x \in H} p(x) * (indanger(src) * (src_{strategic\ score} + src_{loss gain}) + tar_{strategic\ score} + tar_{gain}) $$

$$ tradeoff_{tar} = \sum_{x \in T_{tar}} p(x) * (indanger(src) * (src_{strategic\ score} + src_{loss gain}) + tar_{gain}) $$

$$ tradeoff_{src} = \sum_{x \in T_{src}} p(x) * ((1 - indanger(src)) * -(src_{strategic\ score} + src_{loss gain}) + tar_{strategic\ score} + tar_{gain}) $$

$$ zero = \sum_{x \in Z} p(x) * ((1 - indanger(src)) * -(src_{strategic\ score} + src_{loss gain}) + tar_{gain}) $$

Where,

$$ indanger(u) = 
\begin{cases}
  0, & danger(u) \leq 0 \\
  1, & 0 < danger(u) \\
\end{cases}
$$

and $p(x)$ is the probability distribution over all attack outcomes, also $strategic\ score$ refers to the nodes strategic score, for more details about $loss gain$ and $gain$ refer to our implementation.

Now, it's only necessary to define the sets $H$, $T_{tar}$, $T_{src}$, and $Z$. Let's denote the remaining number of troops after an attack as $x$. If we can allocate these troops in such a way that the danger level in the source region ($src$) and target region ($tar$) is less than or equal to zero, we include this outcome in the set $H$. Similarly, if we can allocate $x$ troops in a manner that the danger level in either the source or target region is less than or equal to zero (but not in both), we add $x$ to the respective set $S_u$, where $u$ belongs to the set ${src, tar}$. If none of these conditions are met, we include this outcome in the set $Z$ (note that if the attack fails before reaching $tar$ node we define $x$ to be equal to zero).

Since some outcomes might be shared between $S_{src}$ and $S_{tar}$, we'll define $T_{tar}$ and $T_{src}$ as following:

$$
\begin{cases}
T_{src} := S_{src} \setminus S_{tar}, T_{tar} := S_{tar}, & src_{strategic\ score} < tar_{strategic\ score} \\
T_{tar} := S_{tar} \setminus S_{src}, T_{src} := S_{src}, & src_{strategic\ score} \geq tar_{strategic\ score}
\end{cases}
$$

Our implementation also accounts for specific corner cases that broaden the scoring system. These cases include scenarios where no attacks were successful, resulting in a lack of the +3 troop bonus for successful attacks. Additionally, it addresses situations where there's no intention to attack other nodes, and the focus is solely on deploying troops to a particular node.

# Two Strategic Attack
If there's a possibility to win by capturing two strategic nodes, this strategy is implemented. It systematically evaluates all feasible attack plans with at most one branch point for capturing these two nodes and selects the one with the highest likelihood of success. By an attack with one branch point, we mean a forest where only one node has 3 neighbors, which is the split point.


# ThreePlus Attack
Since a successful attack gives us 3 additional troops gains for the next round, an additional strategy to `One Strategic Attack` is provided in case no attack is performed in the previous strategies. Assuming we have $M$ troops to put in our turn, let $0 \leq i \leq M$ be a candidate number of troops to put in order to attack. Also, let $u$ be a node in which we are planning to place the $i$ troops, with the initial troops $I$, and let $v$ be a neighboring node of $u$ that we wish to attack, with $J$ troops. We associate a score to the plan $(u,v,i)$ and choose the tuple with the maximum score. The loss is defined as follows ($c$ is the expected casualty of attacking $J$ troops with $I$ troops) :
$$loss(u,v,i) = c + 0.15 * (i - max(0, c - I))$$
And letting $w$ be the winning probability of attacking $J$ troops with $I$ troops, we have
$$score = 3 * w - loss$$
with the condition that $J \leq 4$ and $loss \leq 3$ (otherwise, we don't perform any attacks).

# Maximize Score
This strategy is only deployed when victory is assured. The algorithm is specifically crafted to maximize node acquisition with the current troop count on the map. It employs a greedy approach similar to Prim's algorithm for identifying Minimum Spanning Trees (MSTs) in graphs.

# Acknowledgement
We want to thank VahidGhafourian for implementing the game kernel without Flask, which you can check out in his [repository](https://github.com/VahidGhafourian/AICup2023-No-Flask). Additionally, a big thanks to the AICUP team for putting together this event!
