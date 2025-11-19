import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
from game_logic import calculate_mixed_nash, calculate_attacker_best_response, calculate_defender_best_response, calculate_qre_attacker, calculate_qre_defender
from data_handler import save_to_file, load_from_file

class NashCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Fighting Game Nash Equilibrium Calculator")
        self.root.geometry("1000x700")

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Menu bar
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Scenario", command=self.save_scenario)
        file_menu.add_command(label="Load Scenario", command=self.load_scenario)
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Make Binary", command=self.make_binary)

        self.input_frame = ttk.Frame(root, padding="10")
        self.input_frame.grid(row=0, column=0, sticky="nsew")
        self.result_frame = ttk.Frame(root, padding="10")
        self.result_frame.grid(row=0, column=1, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.create_input_widgets()
        self.create_result_widgets()

    def create_input_widgets(self):
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.columnconfigure(1, weight=1)
        self.input_frame.rowconfigure(2, weight=1)
        self.input_frame.rowconfigure(3, weight=1)
        self.input_frame.rowconfigure(7, weight=0)

        self.attacker_lock_var = tk.BooleanVar()
        self.attacker_lock_check = ttk.Checkbutton(self.input_frame, text="Lock Attacker", variable=self.attacker_lock_var, command=self.toggle_attacker_probs)
        self.attacker_lock_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.defender_lock_var = tk.BooleanVar()
        self.defender_lock_check = ttk.Checkbutton(self.input_frame, text="Lock Defender", variable=self.defender_lock_var, command=self.toggle_defender_probs)
        self.defender_lock_check.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.moves_canvas = tk.Canvas(self.input_frame)
        moves_scrollbar = ttk.Scrollbar(self.input_frame, orient="vertical", command=self.moves_canvas.yview)
        self.moves_canvas.configure(yscrollcommand=moves_scrollbar.set)
        self.moves_frame = ttk.LabelFrame(self.moves_canvas, text="Move Names", padding="5")
        self.moves_canvas.create_window((0, 0), window=self.moves_frame, anchor="nw")
        self.moves_canvas.grid(row=2, column=0, columnspan=2, sticky="nsew")
        moves_scrollbar.grid(row=2, column=2, sticky="ns")

        self.matrix_canvas = tk.Canvas(self.input_frame)
        matrix_v_scrollbar = ttk.Scrollbar(self.input_frame, orient="vertical", command=self.matrix_canvas.yview)
        matrix_h_scrollbar = ttk.Scrollbar(self.input_frame, orient="horizontal", command=self.matrix_canvas.xview)
        self.matrix_canvas.configure(yscrollcommand=matrix_v_scrollbar.set, xscrollcommand=matrix_h_scrollbar.set)
        self.matrix_frame = ttk.LabelFrame(self.matrix_canvas, text="Payoff Matrix", padding="5")
        self.matrix_canvas.create_window((0, 0), window=self.matrix_frame, anchor="nw")
        self.matrix_canvas.grid(row=3, column=0, columnspan=2, sticky="nsew")
        matrix_v_scrollbar.grid(row=3, column=2, sticky="ns")
        matrix_h_scrollbar.grid(row=4, column=0, columnspan=2, sticky="ew")

        ttk.Label(self.input_frame, text="Simplification Threshold (%):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.threshold_spinbox = tk.Spinbox(self.input_frame, from_=0, to=20, increment=1, width=5)
        self.threshold_spinbox.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.threshold_spinbox.delete(0, tk.END)
        self.threshold_spinbox.insert(0, "10")

        ttk.Label(self.input_frame, text="Exploit Weight:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.exploit_spinbox = tk.Spinbox(self.input_frame, from_=0, to=1, increment=0.1, width=5)
        self.exploit_spinbox.grid(row=6, column=1, padx=5, pady=5, sticky="w")
        self.exploit_spinbox.delete(0, tk.END)
        self.exploit_spinbox.insert(0, "0.3")

        ttk.Label(self.input_frame, text="QRE Lambda:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.lambda_spinbox = tk.Spinbox(self.input_frame, from_=0.1, to=20, increment=1, width=5)
        self.lambda_spinbox.grid(row=7, column=1, padx=5, pady=5, sticky="w")
        self.lambda_spinbox.delete(0, tk.END)
        self.lambda_spinbox.insert(0, "15.0")

        button_frame = ttk.Frame(self.input_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        button_frame.columnconfigure(4, weight=1)
        button_frame.columnconfigure(5, weight=1)
        button_frame.columnconfigure(6, weight=1)

        buttons = [
            ("Calculate Nash", self.calculate),
            ("Best Response", self.calculate_best_response),
            ("Subtle Exploit", self.calculate_subtle_exploit),
            ("Simplify Attacker", self.simplify_attacker_strategy),
            ("Simplify Defender", self.simplify_defender_strategy),
            ("Set QRE Attacker", self.set_qre_attacker),
            ("Set QRE Defender", self.set_qre_defender)
        ]
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

        self.attacker_entries = []
        self.defender_entries = []
        self.payoff_entries = []
        self.attacker_prob_entries = []
        self.defender_prob_entries = []
        self.attacker_delete_buttons = []
        self.defender_delete_buttons = []
        self.update_inputs()

        self.moves_frame.bind("<Configure>", lambda e: self.moves_canvas.configure(scrollregion=self.moves_canvas.bbox("all")))
        self.matrix_frame.bind("<Configure>", lambda e: self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all")))

    def create_result_widgets(self):
        ttk.Label(self.result_frame, text="Results", font=("Arial", 12, "bold")).grid(row=0, column=0, pady=5)
        self.result_text = tk.Text(self.result_frame, height=20, width=50, font=("Arial", 10), bg="#f0f0f0", relief="flat")
        self.result_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.result_text.tag_configure("title", font=("Arial", 12, "bold"), foreground="#2c3e50", justify="center")
        self.result_text.tag_configure("header", font=("Arial", 11, "bold"), foreground="#34495e")
        self.result_text.tag_configure("item", font=("Arial", 10), foreground="#333333")
        self.result_text.tag_configure("value_active", font=("Arial", 10, "bold"), foreground="#2980b9")
        self.result_text.tag_configure("value_inactive", font=("Arial", 10), foreground="#7f8c8d")
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(1, weight=1)

    def update_inputs(self, new_payoffs=None, attacker_moves=None, defender_moves=None):
        old_attacker_moves = attacker_moves if attacker_moves is not None else [entry.get() for entry in self.attacker_entries] if self.attacker_entries else ["Move 1", "Move 2"]
        old_defender_moves = defender_moves if defender_moves is not None else [entry.get() for entry in self.defender_entries] if self.defender_entries else ["Move 1", "Move 2"]
        old_payoffs = new_payoffs if new_payoffs is not None else [entry.get() for entry in self.payoff_entries] if self.payoff_entries else []

        for widget in self.moves_frame.winfo_children():
            widget.destroy()
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()

        self.attacker_entries = []
        self.defender_entries = []
        self.payoff_entries = []
        self.attacker_prob_entries = []
        self.defender_prob_entries = []
        self.attacker_delete_buttons = []
        self.defender_delete_buttons = []

        n_attacker = len(old_attacker_moves)
        n_defender = len(old_defender_moves)
        expected_payoffs = n_attacker * n_defender
        if len(old_payoffs) != expected_payoffs and old_payoffs:
            old_payoffs = ["0"] * expected_payoffs

        ttk.Label(self.moves_frame, text="Attacker Moves:").grid(row=0, column=0, padx=5, pady=2)
        ttk.Label(self.moves_frame, text="Prob (%)").grid(row=0, column=2, padx=5, pady=2)
        for i, move in enumerate(old_attacker_moves):
            entry = ttk.Entry(self.moves_frame, width=15)
            entry.grid(row=i+1, column=0, padx=5, pady=2)
            entry.insert(0, move)
            self.attacker_entries.append(entry)

            delete_btn = ttk.Button(self.moves_frame, text="X", width=2, command=lambda x=i: self.delete_attacker_move(x))
            delete_btn.grid(row=i+1, column=1, padx=2, pady=2)
            self.attacker_delete_buttons.append(delete_btn)

            prob_entry = ttk.Entry(self.moves_frame, width=8)
            prob_entry.grid(row=i+1, column=2, padx=2, pady=2)
            prob_entry.insert(0, "0")
            prob_entry.config(state="disabled" if not self.attacker_lock_var.get() else "normal")
            self.attacker_prob_entries.append(prob_entry)

        self.attacker_add_button = ttk.Button(self.moves_frame, text="+", command=self.add_attacker_move)
        self.attacker_add_button.grid(row=n_attacker+1, column=0, padx=5, pady=5)

        ttk.Label(self.moves_frame, text="Defender Moves:").grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(self.moves_frame, text="Prob (%)").grid(row=0, column=5, padx=5, pady=2)
        for i, move in enumerate(old_defender_moves):
            entry = ttk.Entry(self.moves_frame, width=15)
            entry.grid(row=i+1, column=3, padx=5, pady=2)
            entry.insert(0, move)
            self.defender_entries.append(entry)

            delete_btn = ttk.Button(self.moves_frame, text="X", width=2, command=lambda x=i: self.delete_defender_move(x))
            delete_btn.grid(row=i+1, column=4, padx=2, pady=2)
            self.defender_delete_buttons.append(delete_btn)

            prob_entry = ttk.Entry(self.moves_frame, width=8)
            prob_entry.grid(row=i+1, column=5, padx=2, pady=2)
            prob_entry.insert(0, "0")
            prob_entry.config(state="disabled" if not self.defender_lock_var.get() else "normal")
            self.defender_prob_entries.append(prob_entry)

        self.defender_add_button = ttk.Button(self.moves_frame, text="+", command=self.add_defender_move)
        self.defender_add_button.grid(row=n_defender+1, column=3, padx=5, pady=5)

        for j, move in enumerate(old_defender_moves):
            ttk.Label(self.matrix_frame, text=move, wraplength=60).grid(row=0, column=j+1, padx=2, pady=2)
        for i in range(n_attacker):
            ttk.Label(self.matrix_frame, text=old_attacker_moves[i], wraplength=60).grid(row=i+1, column=0, padx=2, pady=2, sticky="e")
            for j in range(n_defender):
                entry = ttk.Entry(self.matrix_frame, width=12)
                entry.grid(row=i+1, column=j+1, padx=2, pady=2)
                idx = i * n_defender + j
                entry.insert(0, old_payoffs[idx] if idx < len(old_payoffs) else "0")
                self.payoff_entries.append(entry)

        self.moves_frame.update_idletasks()
        self.matrix_frame.update_idletasks()
        self.moves_canvas.configure(scrollregion=self.moves_canvas.bbox("all"))
        self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all"))

    def update_inputs_from_scenario(self, scenario):
        attacker_moves = scenario.get("attacker_moves", ["Move 1", "Move 2"])
        defender_moves = scenario.get("defender_moves", ["Move 1", "Move 2"])
        payoffs = scenario.get("payoffs", [])
        n_attacker = len(attacker_moves)
        n_defender = len(defender_moves)

        expected_payoffs = n_attacker * n_defender
        if len(payoffs) != expected_payoffs:
            raise ValueError(f"Payoff count mismatch: expected {expected_payoffs}, got {len(payoffs)}")

        self.update_inputs(new_payoffs=payoffs, attacker_moves=attacker_moves, defender_moves=defender_moves)

    def toggle_attacker_probs(self):
        state = "normal" if self.attacker_lock_var.get() else "disabled"
        for entry in self.attacker_prob_entries:
            entry.config(state=state)

    def toggle_defender_probs(self):
        state = "normal" if self.defender_lock_var.get() else "disabled"
        for entry in self.defender_prob_entries:
            entry.config(state=state)

    def add_attacker_move(self):
        n_attacker = len(self.attacker_entries)
        n_defender = len(self.defender_entries)

        if self.attacker_add_button:
            self.attacker_add_button.grid_forget()

        entry = ttk.Entry(self.moves_frame, width=15)
        entry.grid(row=n_attacker+1, column=0, padx=5, pady=2)
        entry.insert(0, f"Move {n_attacker+1}")
        self.attacker_entries.append(entry)

        delete_btn = ttk.Button(self.moves_frame, text="X", width=2, command=lambda x=n_attacker: self.delete_attacker_move(x))
        delete_btn.grid(row=n_attacker+1, column=1, padx=2, pady=2)
        self.attacker_delete_buttons.append(delete_btn)

        prob_entry = ttk.Entry(self.moves_frame, width=8)
        prob_entry.grid(row=n_attacker+1, column=2, padx=2, pady=2)
        prob_entry.insert(0, "0")
        prob_entry.config(state="disabled" if not self.attacker_lock_var.get() else "normal")
        self.attacker_prob_entries.append(prob_entry)

        for j in range(n_defender):
            entry = ttk.Entry(self.matrix_frame, width=12)
            entry.grid(row=n_attacker+1, column=j+1, padx=2, pady=2)
            entry.insert(0, "0")
            self.payoff_entries.append(entry)
        ttk.Label(self.matrix_frame, text=entry.get(), wraplength=60).grid(row=n_attacker+1, column=0, padx=2, pady=2, sticky="e")

        self.attacker_add_button = ttk.Button(self.moves_frame, text="+", command=self.add_attacker_move)
        self.attacker_add_button.grid(row=n_attacker+2, column=0, padx=5, pady=5)

        self.moves_frame.update_idletasks()
        self.matrix_canvas.update_idletasks()
        self.moves_canvas.configure(scrollregion=self.moves_canvas.bbox("all"))
        self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all"))

    def add_defender_move(self):
        n_attacker = len(self.attacker_entries)
        n_defender = len(self.defender_entries)

        # Store current payoffs
        current_payoffs = [entry.get() for entry in self.payoff_entries]

        # Rebuild the entire payoff matrix to ensure correct alignment
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()
        self.payoff_entries = []

        if self.defender_add_button:
            self.defender_add_button.grid_forget()

        entry = ttk.Entry(self.moves_frame, width=15)
        entry.grid(row=n_defender+1, column=3, padx=5, pady=2)
        entry.insert(0, f"Move {n_defender+1}")
        self.defender_entries.append(entry)

        delete_btn = ttk.Button(self.moves_frame, text="X", width=2, command=lambda x=n_defender: self.delete_defender_move(x))
        delete_btn.grid(row=n_defender+1, column=4, padx=2, pady=2)
        self.defender_delete_buttons.append(delete_btn)

        prob_entry = ttk.Entry(self.moves_frame, width=8)
        prob_entry.grid(row=n_defender+1, column=5, padx=2, pady=2)
        prob_entry.insert(0, "0")
        prob_entry.config(state="disabled" if not self.defender_lock_var.get() else "normal")
        self.defender_prob_entries.append(prob_entry)

        # Update matrix frame
        old_defender_moves = [entry.get() for entry in self.defender_entries]
        old_attacker_moves = [entry.get() for entry in self.attacker_entries]
        for j, move in enumerate(old_defender_moves):
            ttk.Label(self.matrix_frame, text=move, wraplength=60).grid(row=0, column=j+1, padx=2, pady=2)
        for i in range(n_attacker):
            ttk.Label(self.matrix_frame, text=old_attacker_moves[i], wraplength=60).grid(row=i+1, column=0, padx=2, pady=2, sticky="e")
            for j in range(n_defender + 1):
                entry = ttk.Entry(self.matrix_frame, width=12)
                entry.grid(row=i+1, column=j+1, padx=2, pady=2)
                if j < n_defender and i * n_defender + j < len(current_payoffs):
                    entry.insert(0, current_payoffs[i * n_defender + j])
                else:
                    entry.insert(0, "0")
                self.payoff_entries.append(entry)

        self.defender_add_button = ttk.Button(self.moves_frame, text="+", command=self.add_defender_move)
        self.defender_add_button.grid(row=n_defender+2, column=3, padx=5, pady=5)

        self.moves_frame.update_idletasks()
        self.matrix_canvas.update_idletasks()
        self.moves_canvas.configure(scrollregion=self.moves_canvas.bbox("all"))
        self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all"))

    def delete_attacker_move(self, index):
        if len(self.attacker_entries) <= 2:
            self.status_var.set("Cannot delete: Minimum of 2 attacker moves required.")
            return
        n_attacker = len(self.attacker_entries)
        n_defender = len(self.defender_entries)
        try:
            old_payoffs = [float(entry.get()) for entry in self.payoff_entries]
            payoff_matrix = np.array(old_payoffs).reshape(n_attacker, n_defender)
            new_payoffs = np.delete(payoff_matrix, index, axis=0).flatten().tolist()
            del self.attacker_entries[index]
            del self.attacker_prob_entries[index]
            del self.attacker_delete_buttons[index]
            self.update_inputs_with_payoffs(new_payoffs)
        except ValueError:
            self.status_var.set("Invalid payoff values detected.")
            self.update_inputs()

    def delete_defender_move(self, index):
        if len(self.defender_entries) <= 2:
            self.status_var.set("Cannot delete: Minimum of 2 defender moves required.")
            return
        n_attacker = len(self.attacker_entries)
        n_defender = len(self.defender_entries)
        try:
            old_payoffs = [float(entry.get()) for entry in self.payoff_entries]
            payoff_matrix = np.array(old_payoffs).reshape(n_attacker, n_defender)
            new_payoffs = np.delete(payoff_matrix, index, axis=1).flatten().tolist()
            expected_length = n_attacker * (n_defender - 1)
            if len(new_payoffs) != expected_length:
                raise ValueError(f"Payoff length mismatch: expected {expected_length}, got {len(new_payoffs)}")
            del self.defender_entries[index]
            del self.defender_prob_entries[index]
            del self.defender_delete_buttons[index]
            self.update_inputs_with_payoffs(new_payoffs)
        except ValueError as e:
            self.status_var.set(f"Invalid payoff values detected: {str(e)}")
            self.update_inputs()

    def update_inputs_with_payoffs(self, new_payoffs):
        self.update_inputs(new_payoffs=new_payoffs)

    def calculate(self):
        try:
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker = len(attacker_moves)
            n_defender = len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            result = calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix)
            self.display_result(result, title="Mixed Strategy Nash Equilibrium")
        except Exception as e:
            self.status_var.set(str(e))

    def calculate_best_response(self):
        try:
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker = len(attacker_moves)
            n_defender = len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            attacker_locked = self.attacker_lock_var.get()
            defender_locked = self.defender_lock_var.get()

            if attacker_locked and not defender_locked:
                attacker_probs = [float(entry.get()) / 100 for entry in self.attacker_prob_entries]
                if abs(sum(attacker_probs) - 1) > 1e-2:
                    raise ValueError(f"Attacker probabilities sum to {sum(attacker_probs)*100:.2f}%, must be 100%")
                result = calculate_defender_best_response(attacker_moves, defender_moves, payoff_matrix, attacker_probs)
                self.display_result(result, title="Best Response (Defender Optimized)")
            elif defender_locked and not attacker_locked:
                defender_probs = [float(entry.get()) / 100 for entry in self.defender_prob_entries]
                if abs(sum(defender_probs) - 1) > 1e-2:
                    raise ValueError(f"Defender probabilities sum to {sum(defender_probs)*100:.2f}%, must be 100%")
                result = calculate_attacker_best_response(attacker_moves, defender_moves, payoff_matrix, defender_probs)
                self.display_result(result, title="Best Response (Attacker Optimized)")
            else:
                self.status_var.set("Lock exactly one side for best response")
        except Exception as e:
            self.status_var.set(str(e))

    def calculate_subtle_exploit(self):
        try:
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker = len(attacker_moves)
            n_defender = len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            attacker_locked = self.attacker_lock_var.get()
            defender_locked = self.defender_lock_var.get()

            nash_result = calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix)
            if isinstance(nash_result, str):
                raise ValueError("Cannot compute Nash for comparison")
            nash_attacker_probs, nash_defender_probs = nash_result[2], nash_result[3]

            if attacker_locked and not defender_locked:
                attacker_probs = [float(entry.get()) / 100 for entry in self.attacker_prob_entries]
                if abs(sum(attacker_probs) - 1) > 1e-2:
                    raise ValueError(f"Attacker probabilities sum to {sum(attacker_probs)*100:.2f}%, must be 100%")
                pure_result = calculate_defender_best_response(attacker_moves, defender_moves, payoff_matrix, attacker_probs)
                if isinstance(pure_result, str):
                    raise ValueError("Cannot compute pure best response")
                pure_defender_probs = pure_result[3]
                exploit_weight = float(self.exploit_spinbox.get())
                dominant_idx = np.argmax(pure_defender_probs)
                subtle_defender_probs = nash_defender_probs * (1 - exploit_weight)
                subtle_defender_probs[dominant_idx] += exploit_weight
                game_value = np.dot(attacker_probs, np.dot(payoff_matrix, subtle_defender_probs))
                result = (attacker_moves, defender_moves, np.array(attacker_probs), subtle_defender_probs, game_value)
                self.display_result(result, title="Subtle Exploit (Defender Adjusted)")
            elif defender_locked and not attacker_locked:
                defender_probs = [float(entry.get()) / 100 for entry in self.defender_prob_entries]
                if abs(sum(defender_probs) - 1) > 1e-2:
                    raise ValueError(f"Defender probabilities sum to {sum(defender_probs)*100:.2f}%, must be 100%")
                pure_result = calculate_attacker_best_response(attacker_moves, defender_moves, payoff_matrix, defender_probs)
                if isinstance(pure_result, str):
                    raise ValueError("Cannot compute pure best response")
                pure_attacker_probs = pure_result[2]
                exploit_weight = float(self.exploit_spinbox.get())
                dominant_idx = np.argmax(pure_attacker_probs)
                subtle_attacker_probs = nash_attacker_probs * (1 - exploit_weight)
                subtle_attacker_probs[dominant_idx] += exploit_weight
                game_value = np.dot(subtle_attacker_probs, np.dot(payoff_matrix, defender_probs))
                result = (attacker_moves, defender_moves, subtle_attacker_probs, np.array(defender_probs), game_value)
                self.display_result(result, title="Subtle Exploit (Attacker Adjusted)")
            else:
                self.status_var.set("Lock all moves for exactly one side for subtle exploit")
        except Exception as e:
            self.status_var.set(str(e))

    def set_qre_attacker(self):
        if not self.attacker_lock_var.get():
            self.status_var.set("Attacker must be locked to set QRE")
            return
        try:
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            n_attacker = len(self.attacker_entries)
            n_defender = len(self.defender_entries)
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            lambda_param = float(self.lambda_spinbox.get())
            attacker_probs = calculate_qre_attacker(payoff_matrix, lambda_param)
            if np.any(np.isnan(attacker_probs)):
                raise ValueError("QRE computation failed: Invalid payoff matrix")
            # Convert to percentages and normalize to sum to 100
            attacker_percentages = np.array(attacker_probs) * 100
            total = attacker_percentages.sum()
            if total == 0:
                attacker_percentages = np.ones(n_attacker) * (100 / n_attacker)
            else:
                attacker_percentages = attacker_percentages * (100 / total)
            # Round to 3 decimal places and adjust largest probability to ensure sum is 100
            attacker_percentages = np.round(attacker_percentages, 3)
            total = attacker_percentages.sum()
            if total != 100:
                max_idx = np.argmax(attacker_percentages)
                attacker_percentages[max_idx] += 100 - total
            # Log probabilities and sum
            for i, prob in enumerate(attacker_percentages):
                self.attacker_prob_entries[i].delete(0, tk.END)
                self.attacker_prob_entries[i].insert(0, f"{prob:.3f}")
            self.status_var.set(f"Attacker probabilities set to QRE (lambda={lambda_param})")
        except Exception as e:
            self.status_var.set(f"Error setting QRE: {str(e)}")

    def set_qre_defender(self):
        if not self.defender_lock_var.get():
            self.status_var.set("Defender must be locked to set QRE")
            return
        try:
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            n_attacker = len(self.attacker_entries)
            n_defender = len(self.defender_entries)
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            lambda_param = float(self.lambda_spinbox.get())
            defender_probs = calculate_qre_defender(payoff_matrix, lambda_param)
            if np.any(np.isnan(defender_probs)):
                raise ValueError("QRE computation failed: Invalid payoff matrix")
            # Convert to percentages and normalize to sum to 100
            defender_percentages = np.array(defender_probs) * 100
            total = defender_percentages.sum()
            if total == 0:
                defender_percentages = np.ones(n_defender) * (100 / n_defender)
            else:
                defender_percentages = defender_percentages * (100 / total)
            # Round to 3 decimal places and adjust largest probability to ensure sum is 100
            defender_percentages = np.round(defender_percentages, 3)
            total = defender_percentages.sum()
            if total != 100:
                max_idx = np.argmax(defender_percentages)
                defender_percentages[max_idx] += 100 - total
            # Log probabilities and sum
            for i, prob in enumerate(defender_percentages):
                self.defender_prob_entries[i].delete(0, tk.END)
                self.defender_prob_entries[i].insert(0, f"{prob:.3f}")
            self.status_var.set(f"Defender probabilities set to QRE (lambda={lambda_param})")
        except Exception as e:
            self.status_var.set(f"Error setting QRE: {str(e)}")

    def save_scenario(self):
        try:
            scenario = {
                "attacker_moves": [entry.get() for entry in self.attacker_entries],
                "defender_moves": [entry.get() for entry in self.defender_entries],
                "payoffs": [entry.get() for entry in self.payoff_entries],
                "n_attacker": len(self.attacker_entries),
                "n_defender": len(self.defender_entries)
            }
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                save_to_file(scenario, file_path)
                self.status_var.set("Scenario saved successfully!")
        except Exception as e:
            self.status_var.set(f"Failed to save: {str(e)}")

    def load_scenario(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if not file_path:
                return
            scenario = load_from_file(file_path)
            self.update_inputs_from_scenario(scenario)
            self.status_var.set("Scenario loaded successfully!")
        except ValueError as e:
            self.status_var.set(f"Failed to load: {str(e)}")
        except Exception as e:
            self.status_var.set(f"Failed to load: Invalid file format ({str(e)})")

    def make_binary(self):
        try:
            for entry in self.payoff_entries:
                num = float(entry.get())
                new_value = 1 if num >= 1000 else -1 if num <= -1000 else 0
                entry.delete(0, tk.END)
                entry.insert(0, str(new_value))
            self.status_var.set("Payoffs converted to binary!")
        except Exception as e:
            self.status_var.set(f"Error converting to binary: {str(e)}")

    def compute_nash_for_subset(self, payoff_matrix, attacker_subset=None, defender_subset=None):
        n_attacker, n_defender = payoff_matrix.shape
        if attacker_subset is None:
            attacker_subset = list(range(n_attacker))
        if defender_subset is None:
            defender_subset = list(range(n_defender))
        sub_matrix = payoff_matrix[np.ix_(attacker_subset, defender_subset)]
        attacker_moves = [self.attacker_entries[i].get() for i in attacker_subset]
        defender_moves = [self.defender_entries[j].get() for j in defender_subset]
        result = calculate_mixed_nash(attacker_moves, defender_moves, sub_matrix)
        if isinstance(result, str):
            return None, None, None
        return result[2], result[3], result[4]

    def simplify_attacker_strategy(self):
        try:
            threshold_percent = float(self.threshold_spinbox.get())
            lower_threshold_factor = 1 - (threshold_percent / 100)
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker = len(attacker_moves)
            n_defender = len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            if len(payoffs) != n_attacker * n_defender:
                raise ValueError(f"Payoff length mismatch: expected {n_attacker * n_defender}, got {len(payoffs)}")
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            nash_result = calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix)
            if isinstance(nash_result, str):
                raise ValueError("Cannot compute full Nash equilibrium")
            original_ev = nash_result[4]
            lower_threshold = lower_threshold_factor * original_ev
            current_subset = list(range(n_attacker))
            while True:
                best_ev = -float('inf')
                best_subset = None
                for i in current_subset:
                    test_subset = [x for x in current_subset if x != i]
                    if len(test_subset) == 0:
                        continue
                    a_probs, d_probs, ev = self.compute_nash_for_subset(payoff_matrix, test_subset, None)
                    if ev is not None and ev > best_ev:
                        best_ev = ev
                        best_subset = test_subset
                if best_subset is None or best_ev < lower_threshold:
                    break
                current_subset = best_subset
            a_probs, d_probs, simplified_ev = self.compute_nash_for_subset(payoff_matrix, current_subset, None)
            if a_probs is None:
                raise ValueError("Failed to compute simplified strategy")
            simplified_moves = [attacker_moves[i] for i in current_subset]
            result = (simplified_moves, defender_moves, a_probs, d_probs, simplified_ev)
            self.display_simplified_result(result, "attacker", original_ev)
        except Exception as e:
            self.status_var.set(f"Failed to simplify attacker strategy: {str(e)}")

    def simplify_defender_strategy(self):
        try:
            threshold_percent = float(self.threshold_spinbox.get())
            upper_threshold_factor = 1 + (threshold_percent / 100)
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker = len(attacker_moves)
            n_defender = len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            if len(payoffs) != n_attacker * n_defender:
                raise ValueError(f"Payoff length mismatch: expected {n_attacker * n_defender}, got {len(payoffs)}")
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            nash_result = calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix)
            if isinstance(nash_result, str):
                raise ValueError("Cannot compute full Nash equilibrium")
            original_ev = nash_result[4]
            upper_threshold = upper_threshold_factor * original_ev
            current_subset = list(range(n_defender))
            while True:
                best_ev = float('inf')
                best_subset = None
                for j in current_subset:
                    test_subset = [x for x in current_subset if x != j]
                    if len(test_subset) == 0:
                        continue
                    a_probs, d_probs, ev = self.compute_nash_for_subset(payoff_matrix, None, test_subset)
                    if ev is not None and ev < best_ev:
                        best_ev = ev
                        best_subset = test_subset
                if best_subset is None or best_ev > upper_threshold:
                    break
                current_subset = best_subset
            a_probs, d_probs, simplified_ev = self.compute_nash_for_subset(payoff_matrix, None, current_subset)
            if d_probs is None:
                raise ValueError("Failed to compute simplified strategy")
            simplified_moves = [defender_moves[j] for j in current_subset]
            result = (attacker_moves, simplified_moves, a_probs, d_probs, simplified_ev)
            self.display_simplified_result(result, "defender", original_ev)
        except Exception as e:
            self.status_var.set(f"Failed to simplify defender strategy: {str(e)}")

    def display_simplified_result(self, result, player, original_ev):
        attacker_moves, defender_moves, attacker_probs, defender_probs, simplified_ev = result
        self.result_text.delete(1.0, tk.END)
        title = f"Simplified {'Attacker' if player == 'attacker' else 'Defender'} Strategy"
        self.result_text.insert(tk.END, f"{title}\n\n", "title")
        attacker_data = sorted(zip(attacker_moves, attacker_probs), key=lambda x: x[1], reverse=True)
        sorted_attacker_moves, sorted_attacker_probs = zip(*attacker_data)
        self.result_text.insert(tk.END, "Attacker Strategies (Sorted by Frequency):\n", "header")
        max_move_len = max(len(move) for move in sorted_attacker_moves)
        for move, prob in zip(sorted_attacker_moves, sorted_attacker_probs):
            formatted_move = f"{move:<{max_move_len}}"
            tag = "value_active" if prob > 0 else "value_inactive"
            self.result_text.insert(tk.END, f"  {formatted_move}: ", "item")
            self.result_text.insert(tk.END, f"{100*prob:6.2f}%\n", tag)
        self.result_text.insert(tk.END, "\n")
        defender_data = sorted(zip(defender_moves, defender_probs), key=lambda x: x[1], reverse=True)
        sorted_defender_moves, sorted_defender_probs = zip(*defender_data)
        self.result_text.insert(tk.END, "Defender Strategies (Sorted by Frequency):\n", "header")
        max_move_len = max(len(move) for move in sorted_defender_moves)
        for move, prob in zip(sorted_defender_moves, sorted_defender_probs):
            formatted_move = f"{move:<{max_move_len}}"
            tag = "value_active" if prob > 0 else "value_inactive"
            self.result_text.insert(tk.END, f"  {formatted_move}: ", "item")
            self.result_text.insert(tk.END, f"{100*prob:6.2f}%\n", tag)
        self.result_text.insert(tk.END, "\n")
        self.result_text.insert(tk.END, "Expected Payoff (Attacker’s Perspective):\n", "header")
        self.result_text.insert(tk.END, f"  Original EV: {original_ev:6.4f}\n", "item")
        self.result_text.insert(tk.END, f"  Simplified EV: {simplified_ev:6.4f}\n", "value_active")
        percent_retained = (simplified_ev / original_ev) * 100
        self.result_text.insert(tk.END, f"  EV Retained: {percent_retained:.2f}%\n", "item")
        original_n_attacker = len(self.attacker_entries)
        original_n_defender = len(self.defender_entries)
        if player == "attacker":
            simplified_n = len(attacker_moves)
            self.result_text.insert(tk.END, f"\nAttacker Moves Reduced: {original_n_attacker} → {simplified_n}\n", "item")
        elif player == "defender":
            simplified_n = len(defender_moves)
            self.result_text.insert(tk.END, f"\nDefender Moves Reduced: {original_n_defender} → {simplified_n}\n", "item")

    def display_result(self, result, title="Mixed Strategy Nash Equilibrium"):
        self.result_text.delete(1.0, tk.END)
        if isinstance(result, str):
            self.result_text.insert(tk.END, result)
            return
        attacker_moves, defender_moves, attacker_probs, defender_probs, game_value = result
        self.result_text.insert(tk.END, f"{title}\n\n", "title")
        self.result_text.insert(tk.END, "Attacker Strategies:\n", "header")
        for move, prob in sorted(zip(attacker_moves, attacker_probs), key=lambda x: x[1], reverse=True):
            tag = "value_active" if prob > 0 else "value_inactive"
            self.result_text.insert(tk.END, f"  {move}: ", "item")
            self.result_text.insert(tk.END, f"{100*prob:6.2f}%\n", tag)
        self.result_text.insert(tk.END, "\nDefender Strategies:\n", "header")
        for move, prob in sorted(zip(defender_moves, defender_probs), key=lambda x: x[1], reverse=True):
            tag = "value_active" if prob > 0 else "value_inactive"
            self.result_text.insert(tk.END, f"  {move}: ", "item")
            self.result_text.insert(tk.END, f"{100*prob:6.2f}%\n", tag)
        self.result_text.insert(tk.END, f"\nExpected Payoff: {game_value:6.4f}\n", "value_active")