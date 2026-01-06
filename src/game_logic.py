import numpy as np
from scipy.optimize import linprog

def calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix):
    n_attacker = len(attacker_moves)
    n_defender = len(defender_moves)
    c_attacker = [-1] + [0] * n_attacker
    A_ub_attacker = np.hstack((np.ones((n_defender, 1)), -payoff_matrix.T))
    b_ub_attacker = np.zeros(n_defender)
    A_eq_attacker = np.array([[0] + [1] * n_attacker])
    b_eq_attacker = [1]
    bounds_attacker = [(None, None)] + [(0, 1)] * n_attacker
    res_attacker = linprog(c_attacker, A_ub=A_ub_attacker, b_ub=b_ub_attacker, A_eq=A_eq_attacker, b_eq=b_eq_attacker, bounds=bounds_attacker)
    if not res_attacker.success:
        return "Error: Attacker LP solver failed"
    c_defender = [1] + [0] * n_defender
    A_ub_defender = np.hstack((-np.ones((n_attacker, 1)), payoff_matrix))
    b_ub_defender = np.zeros(n_attacker)
    A_eq_defender = np.array([[0] + [1] * n_defender])
    b_eq_defender = [1]
    bounds_defender = [(None, None)] + [(0, 1)] * n_defender
    res_defender = linprog(c_defender, A_ub=A_ub_defender, b_ub=b_ub_defender, A_eq=A_eq_defender, b_eq=b_eq_defender, bounds=bounds_defender)
    if not res_defender.success:
        return "Error: Defender LP solver failed"
    attacker_probs_optimal = res_attacker.x[1:]
    defender_probs_optimal = res_defender.x[1:]
    game_value_optimal = -res_attacker.fun
    return (attacker_moves, defender_moves, attacker_probs_optimal, defender_probs_optimal, game_value_optimal)
