import json
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

def _raw_payoff(p):
    """Coerce a stored payoff (raw value or {'dmg': ...} link) to a float."""
    if isinstance(p, dict):
        return float(p.get("dmg", 0))
    try:
        return float(str(p).replace(',', '.'))
    except (ValueError, TypeError):
        return 0.0

def resolve_scenario_ev(file_path):
    """Load a scenario JSON and return its attacker EV (game value).
    Nested links in the loaded scenario are ignored — only raw dmg values are used."""
    with open(file_path, 'r') as f:
        scenario = json.load(f)
    attacker_moves = scenario.get("attacker_moves", [])
    defender_moves = scenario.get("defender_moves", [])
    payoffs_raw = scenario.get("payoffs", [])
    n_attacker = len(attacker_moves)
    n_defender = len(defender_moves)
    if n_attacker == 0 or n_defender == 0 or len(payoffs_raw) != n_attacker * n_defender:
        raise ValueError("Invalid scenario data in linked file")
    payoff_matrix = np.array([_raw_payoff(p) for p in payoffs_raw]).reshape(n_attacker, n_defender)
    result = calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix)
    if isinstance(result, str):
        raise ValueError(f"Failed to solve linked scenario: {result}")
    return result[4]

def simplify_strategy(attacker_moves, defender_moves, payoff_matrix, player, threshold_percent=10):
    """Greedily drop the given player's moves while keeping the game value within threshold.

    The attacker simplifies by maximising the retained EV until it would fall below
    (1 - t)·EV₀; the defender simplifies by minimising the EV until it would rise above
    (1 + t)·EV₀. Returns (attacker_moves, defender_moves, attacker_probs, defender_probs,
    simplified_ev, original_ev) over the surviving moves, or None on solver failure.
    """
    nash = calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix)
    if isinstance(nash, str):
        return None
    original_ev = nash[4]
    all_attacker = list(range(len(attacker_moves)))
    all_defender = list(range(len(defender_moves)))

    def solve(subset):
        if player == "attacker":
            a_subset, d_subset = subset, all_defender
        else:
            a_subset, d_subset = all_attacker, subset
        sub = payoff_matrix[np.ix_(a_subset, d_subset)]
        r = calculate_mixed_nash([attacker_moves[i] for i in a_subset],
                                 [defender_moves[j] for j in d_subset], sub)
        return None if isinstance(r, str) else r

    if player == "attacker":
        bound = (1 - threshold_percent / 100) * original_ev
        is_better = lambda ev, best: ev > best        # keep most EV
        within_bound = lambda ev: ev >= bound
        best_seed = -float('inf')
        current = list(all_attacker)
    else:
        bound = (1 + threshold_percent / 100) * original_ev
        is_better = lambda ev, best: ev < best        # give up least EV
        within_bound = lambda ev: ev <= bound
        best_seed = float('inf')
        current = list(all_defender)

    while True:
        best_ev, best_subset = best_seed, None
        for k in current:
            test = [x for x in current if x != k]
            if not test:
                continue
            r = solve(test)
            if r is not None and is_better(r[4], best_ev):
                best_ev, best_subset = r[4], test
        if best_subset is None or not within_bound(best_ev):
            break
        current = best_subset

    r = solve(current)
    if r is None:
        return None
    return (r[0], r[1], r[2], r[3], r[4], original_ev)

def process_scenario_for_comparison(file_path, threshold_percent=10):
    """Load and solve a scenario file. Returns comparison dict or None on failure."""
    with open(file_path, 'r') as f:
        scenario = json.load(f)
    attacker_moves = scenario.get("attacker_moves", [])
    defender_moves = scenario.get("defender_moves", [])
    payoffs_raw = scenario.get("payoffs", [])
    n_attacker, n_defender = len(attacker_moves), len(defender_moves)
    if n_attacker < 2 or n_defender < 2 or len(payoffs_raw) != n_attacker * n_defender:
        return None
    payoff_matrix = np.array([_raw_payoff(p) for p in payoffs_raw]).reshape(n_attacker, n_defender)
    result = simplify_strategy(attacker_moves, defender_moves, payoff_matrix, "attacker", threshold_percent)
    if result is None:
        return None
    simp_moves, simp_probs, original_ev = result[0], result[2], result[5]
    pairs = sorted(zip(simp_moves, simp_probs), key=lambda x: x[1], reverse=True)
    strategy_str = "  ·  ".join(f"{m} {p*100:.0f}%" for m, p in pairs if p > 0.005)
    return {"ev": original_ev, "strategy_str": strategy_str}
