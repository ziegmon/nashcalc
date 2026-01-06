# Fighting Game Nash Equilibrium Calculator

A graphical user interface (GUI) tool built with Python to calculate Nash Equilibria and related game theory strategies for fighting games.

## Prerequisites
- numpy>=1.24.0
- scipy>=1.10.0

## Installation
***1. Clone or Download the Repository:***
```
git clone https://github.com/simonziegs/nashcalc.git
```
***2. Install Dependencies:***
```
python -m pip install -r requirements.txt
```
***3. Run the Application:***
```
python src/main.py
```
## Usage
Set Moves:
- Add/remove moves.

- Edit move names in the "Move Names" section.

- Enter numerical payoffs in the matrix, representing the attacker’s utility for each move pair. (Positive values for the attacker, negative values favor the defender).

- Simplify strategies for attacker and defender using a greedy algorithm to remove as many moves as possible while maintaining a EV above a set threshold.

- Make Binary: Convert payoffs to -1, 0, or 1 based on a ±1000 threshold.

View Results:
- Results appear in the right panel, showing strategy frequencies and expected payoff (EV).

Manage Scenarios:
- Save Scenario: Save the current setup to a JSON file.

- Load Scenario: Load a previously saved scenario.
