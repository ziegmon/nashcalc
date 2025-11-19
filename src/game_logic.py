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

def calculate_attacker_best_response(attacker_moves, defender_moves, payoff_matrix, defender_probs):
    n_attacker = len(attacker_moves)
    n_defender = len(defender_moves)
    fixed_defender_probs = np.array(defender_probs)
    c_attacker = -payoff_matrix @ fixed_defender_probs
    A_eq_attacker = np.ones((1, n_attacker))
    b_eq_attacker = [1]
    bounds_attacker = [(0, 1)] * n_attacker
    res_attacker = linprog(c_attacker, A_eq=A_eq_attacker, b_eq=b_eq_attacker, bounds=bounds_attacker, method='highs')
    if not res_attacker.success:
        return "Failed to find best response for attacker"
    attacker_probs = res_attacker.x
    game_value = np.dot(attacker_probs, np.dot(payoff_matrix, fixed_defender_probs))
    return attacker_moves, defender_moves, attacker_probs, fixed_defender_probs, game_value

def calculate_defender_best_response(attacker_moves, defender_moves, payoff_matrix, attacker_probs):
    n_attacker = len(attacker_moves)
    n_defender = len(defender_moves)
    fixed_attacker_probs = np.array(attacker_probs)
    c_defender = payoff_matrix.T @ fixed_attacker_probs
    A_eq_defender = np.ones((1, n_defender))
    b_eq_defender = [1]
    bounds_defender = [(0, 1)] * n_defender
    res_defender = linprog(c_defender, A_eq=A_eq_defender, b_eq=b_eq_defender, bounds=bounds_defender, method='highs')
    if not res_defender.success:
        return "Failed to find best response for defender"
    defender_probs = res_defender.x
    game_value = np.dot(fixed_attacker_probs, np.dot(payoff_matrix, defender_probs))
    return attacker_moves, defender_moves, fixed_attacker_probs, defender_probs, game_value

def calculate_qre(payoff_matrix, lambda_param=0.1, max_iter=5000, tol=1e-8):
    """
    Compute Quantal Response Equilibrium using damped fixed-point iteration.
    Returns attacker_probs and defender_probs, normalized to sum to 1.
    Uses enhanced payoff normalization, smoother damping, and tighter convergence.
    """
    n_attacker, n_defender = payoff_matrix.shape
    
    # Enhanced payoff normalization to [-1, 1]
    payoff_range = np.max(np.abs(payoff_matrix))
    if payoff_range == 0:
        return (np.ones(n_attacker) / n_attacker, np.ones(n_defender) / n_defender)
    normalized_payoffs = payoff_matrix / payoff_range
    
    # Cap lambda_param to avoid numerical issues, but allow Nash fallback for large lambda
    lambda_param = min(lambda_param, 20.0)
    
    # Fallback to Nash for very large lambda
    if lambda_param >= 20.0:
        nash_result = calculate_mixed_nash([f"A{i}" for i in range(n_attacker)], 
                                          [f"D{i}" for i in range(n_defender)], 
                                          payoff_matrix)
        if not isinstance(nash_result, str):
            attacker_probs, defender_probs = nash_result[2], nash_result[3]
            return attacker_probs, defender_probs
    
    # Initialize with uniform strategies
    attacker_probs = np.ones(n_attacker) / n_attacker
    defender_probs = np.ones(n_defender) / n_defender
    
    # Smoother damping factor
    alpha = 0.1
    
    for iteration in range(max_iter):
        attacker_probs_old = attacker_probs.copy()
        defender_probs_old = defender_probs.copy()
        
        # Update attacker probabilities
        expected_payoffs_attacker = normalized_payoffs @ defender_probs
        shifted_payoffs = lambda_param * expected_payoffs_attacker
        shifted_payoffs -= np.max(shifted_payoffs)  # Subtract max for numerical stability
        exp_payoffs_attacker = np.exp(shifted_payoffs)
        sum_exp = exp_payoffs_attacker.sum()
        if sum_exp == 0 or np.isnan(sum_exp):
            new_attacker_probs = np.ones(n_attacker) / n_attacker
        else:
            new_attacker_probs = exp_payoffs_attacker / sum_exp
        # Apply damping and normalize
        attacker_probs = alpha * new_attacker_probs + (1 - alpha) * attacker_probs_old
        attacker_probs = np.clip(attacker_probs, 0, 1)
        attacker_probs /= attacker_probs.sum() if attacker_probs.sum() > 0 else np.ones(n_attacker) / n_attacker
        
        # Update defender probabilities
        expected_payoffs_defender = normalized_payoffs.T @ attacker_probs
        shifted_payoffs = -lambda_param * expected_payoffs_defender  # Negative for minimization
        shifted_payoffs -= np.max(shifted_payoffs)
        exp_payoffs_defender = np.exp(shifted_payoffs)
        sum_exp = exp_payoffs_defender.sum()
        if sum_exp == 0 or np.isnan(sum_exp):
            new_defender_probs = np.ones(n_defender) / n_defender
        else:
            new_defender_probs = exp_payoffs_defender / sum_exp
        # Apply damping and normalize
        defender_probs = alpha * new_defender_probs + (1 - alpha) * defender_probs_old
        defender_probs = np.clip(defender_probs, 0, 1)
        defender_probs /= defender_probs.sum() if defender_probs.sum() > 0 else np.ones(n_defender) / n_defender
        
        # Check convergence
        attacker_diff = np.max(np.abs(attacker_probs - attacker_probs_old))
        defender_diff = np.max(np.abs(defender_probs - defender_probs_old))
        if attacker_diff < tol and defender_diff < tol:
            break
    
    # Final normalization
    attacker_probs = np.clip(attacker_probs, 0, 1)
    attacker_probs /= attacker_probs.sum() if attacker_probs.sum() > 0 else np.ones(n_attacker) / n_attacker
    defender_probs = np.clip(defender_probs, 0, 1)
    defender_probs /= defender_probs.sum() if defender_probs.sum() > 0 else np.ones(n_defender) / n_defender
    
    return attacker_probs, defender_probs

def calculate_qre_attacker(payoff_matrix, lambda_param=0.1):
    """Wrapper to get only attacker's QRE probabilities."""
    attacker_probs, _ = calculate_qre(payoff_matrix, lambda_param)
    return attacker_probs

def calculate_qre_defender(payoff_matrix, lambda_param=0.1):
    """Wrapper to get only defender's QRE probabilities."""
    _, defender_probs = calculate_qre(payoff_matrix, lambda_param)
    return defender_probs