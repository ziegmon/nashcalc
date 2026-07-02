import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import os
from game_logic import calculate_mixed_nash, resolve_scenario_ev, process_scenario_for_comparison, simplify_strategy as solve_simplified_strategy, enumerate_optimal_strategies
from data_handler import save_to_file, load_from_file
from sf6_data import SF6_CHARACTERS, DRIVE_MAX, SUPER_MAX, POSITIONS, JAMIE, DRINK_MAX
import ctypes

LINKED_BG = "#cce5ff"   # linked-cell background

class NashCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Fighting Game Nash Equilibrium Calculator")
        self.root.geometry("1000x700")

        # flat_idx → {path: str, ev: float, dmg: float}
        self.cell_links = {}
        self.current_file_path = None

        # Scenario context (labels only; no effect on the Nash calculation)
        default_char = SF6_CHARACTERS[0] if SF6_CHARACTERS else ""
        self.attacker_char_var = tk.StringVar(value=default_char)
        self.defender_char_var = tk.StringVar(value=default_char)
        self.attacker_drive_var = tk.IntVar(value=DRIVE_MAX)
        self.defender_drive_var = tk.IntVar(value=DRIVE_MAX)
        self.attacker_super_var = tk.IntVar(value=0)
        self.defender_super_var = tk.IntVar(value=0)
        self.attacker_drink_var = tk.IntVar(value=0)
        self.defender_drink_var = tk.IntVar(value=0)
        self.position_var = tk.StringVar(value=POSITIONS[0])

        try:
            myappid = 'nashcalc.gui.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Failed to set AppUserModelID: {e}")

        try:
            self.root.iconbitmap("src/icon.ico")
        except Exception as e:
            print(f"Failed to load icon: {e}")

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
        file_menu.add_separator()
        file_menu.add_command(label="Compare Folder...", command=self.compare_folder)

        self.input_frame = ttk.Frame(root, padding="10")
        self.input_frame.grid(row=0, column=0, sticky="nsew")
        self.result_frame = ttk.Frame(root, padding="10")
        self.result_frame.grid(row=0, column=1, sticky="nsew")

        self.root.columnconfigure(0, weight=50)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.create_context_widgets()
        self.create_input_widgets()
        self.create_result_widgets()

    def create_context_widgets(self):
        ctx = ttk.LabelFrame(self.input_frame, text="Scenario Context", padding="5")
        ctx.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        for c in range(4):
            ctx.columnconfigure(c, weight=1)

        ttk.Label(ctx, text="Attacker:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        atk_cb = ttk.Combobox(ctx, textvariable=self.attacker_char_var, values=SF6_CHARACTERS,
                              state="readonly", width=14)
        atk_cb.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        atk_cb.bind("<<ComboboxSelected>>", lambda e: self._update_drink_visibility())
        ttk.Label(ctx, text="Defender:").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        dfn_cb = ttk.Combobox(ctx, textvariable=self.defender_char_var, values=SF6_CHARACTERS,
                              state="readonly", width=14)
        dfn_cb.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        dfn_cb.bind("<<ComboboxSelected>>", lambda e: self._update_drink_visibility())

        ttk.Label(ctx, text="Attacker Drive:").grid(row=1, column=0, padx=5, pady=2, sticky="e")
        tk.Spinbox(ctx, from_=0, to=DRIVE_MAX, width=4,
                   textvariable=self.attacker_drive_var).grid(row=1, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(ctx, text="Defender Drive:").grid(row=1, column=2, padx=5, pady=2, sticky="e")
        tk.Spinbox(ctx, from_=0, to=DRIVE_MAX, width=4,
                   textvariable=self.defender_drive_var).grid(row=1, column=3, padx=5, pady=2, sticky="w")

        ttk.Label(ctx, text="Attacker Super:").grid(row=2, column=0, padx=5, pady=2, sticky="e")
        tk.Spinbox(ctx, from_=0, to=SUPER_MAX, width=4,
                   textvariable=self.attacker_super_var).grid(row=2, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(ctx, text="Defender Super:").grid(row=2, column=2, padx=5, pady=2, sticky="e")
        tk.Spinbox(ctx, from_=0, to=SUPER_MAX, width=4,
                   textvariable=self.defender_super_var).grid(row=2, column=3, padx=5, pady=2, sticky="w")

        ttk.Label(ctx, text="Position:").grid(row=3, column=0, padx=5, pady=2, sticky="e")
        pos_frame = ttk.Frame(ctx)
        pos_frame.grid(row=3, column=1, columnspan=3, padx=5, pady=2, sticky="w")
        for pos in POSITIONS:
            ttk.Radiobutton(pos_frame, text=pos, value=pos,
                            variable=self.position_var).pack(side="left", padx=5)

        # Jamie-only Drink Level (0-4); shown per player only when that player is Jamie.
        self.attacker_drink_label = ttk.Label(ctx, text="Attacker Drink:")
        self.attacker_drink_spin = tk.Spinbox(ctx, from_=0, to=DRINK_MAX, width=4,
                                               textvariable=self.attacker_drink_var)
        self.defender_drink_label = ttk.Label(ctx, text="Defender Drink:")
        self.defender_drink_spin = tk.Spinbox(ctx, from_=0, to=DRINK_MAX, width=4,
                                               textvariable=self.defender_drink_var)
        self._update_drink_visibility()

    def _update_drink_visibility(self):
        """Show each player's Drink Level control only when that player is Jamie."""
        if self.attacker_char_var.get() == JAMIE:
            self.attacker_drink_label.grid(row=4, column=0, padx=5, pady=2, sticky="e")
            self.attacker_drink_spin.grid(row=4, column=1, padx=5, pady=2, sticky="w")
        else:
            self.attacker_drink_label.grid_remove()
            self.attacker_drink_spin.grid_remove()
        if self.defender_char_var.get() == JAMIE:
            self.defender_drink_label.grid(row=4, column=2, padx=5, pady=2, sticky="e")
            self.defender_drink_spin.grid(row=4, column=3, padx=5, pady=2, sticky="w")
        else:
            self.defender_drink_label.grid_remove()
            self.defender_drink_spin.grid_remove()

    def create_input_widgets(self):
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.columnconfigure(1, weight=1)
        self.input_frame.rowconfigure(2, weight=1)
        self.input_frame.rowconfigure(3, weight=1)
        self.input_frame.rowconfigure(7, weight=0)

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
        self.threshold_spinbox = tk.Spinbox(self.input_frame, from_=0, to=100, increment=1, width=5)
        self.threshold_spinbox.grid(row=5, column=1, padx=5, pady=5, sticky="w")
        self.threshold_spinbox.delete(0, tk.END)
        self.threshold_spinbox.insert(0, "10")

        button_frame = ttk.Frame(self.input_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)

        buttons = [
            ("Calculate Nash", self.calculate),
            ("Simplify Attacker", lambda: self.simplify_strategy("attacker")),
            ("Simplify Defender", lambda: self.simplify_strategy("defender")),
            ("Make Binary", self.make_binary)
        ]
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(button_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

        alt_btn = ttk.Button(button_frame, text="Alternate Optima", command=self.show_alternate_optima)
        alt_btn.grid(row=1, column=0, columnspan=4, padx=5, pady=(0, 5), sticky="ew")

        self.attacker_entries = []
        self.defender_entries = []
        self.payoff_entries = []
        self.attacker_matrix_labels = []
        self.defender_matrix_labels = []
        self.update_inputs()

        self.moves_frame.bind("<Configure>", lambda e: self.moves_canvas.configure(scrollregion=self.moves_canvas.bbox("all")))
        self.matrix_frame.bind("<Configure>", lambda e: self.matrix_canvas.configure(scrollregion=self.matrix_canvas.bbox("all")))

    def create_result_widgets(self):
        ttk.Label(self.result_frame, text="Results", font=("Arial", 12, "bold")).grid(row=0, column=0, pady=5)
        self.result_text = tk.Text(self.result_frame, height=20, width=50, font=("Arial", 10), bg="#f0f0f0", relief="flat")
        self.result_text.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.result_text.tag_configure("title", font=("Arial", 12, "bold"), foreground="#2c3e50", justify="center")
        self.result_text.tag_configure("subtitle", font=("Arial", 9), foreground="#7f8c8d", justify="center")
        self.result_text.tag_configure("header", font=("Arial", 11, "bold"), foreground="#34495e")
        self.result_text.tag_configure("item", font=("Arial", 10), foreground="#333333")
        self.result_text.tag_configure("value_active", font=("Arial", 10, "bold"), foreground="#2980b9")
        self.result_text.tag_configure("value_inactive", font=("Arial", 8), foreground="#7f8c8d")
        self.result_text.tag_configure("warn", font=("Arial", 10, "bold"), foreground="#e67e22")
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(1, weight=1)

    # ── scenario context ──────────────────────────────────────────────────────

    def _read_context(self):
        """Read the context widgets into a plain dict for saving. Drink level is
        recorded only for a player who is Jamie."""
        ctx = {
            "attacker_char": self.attacker_char_var.get(),
            "defender_char": self.defender_char_var.get(),
            "attacker_drive": self.attacker_drive_var.get(),
            "defender_drive": self.defender_drive_var.get(),
            "attacker_super": self.attacker_super_var.get(),
            "defender_super": self.defender_super_var.get(),
            "position": self.position_var.get(),
        }
        if self.attacker_char_var.get() == JAMIE:
            ctx["attacker_drink"] = self.attacker_drink_var.get()
        if self.defender_char_var.get() == JAMIE:
            ctx["defender_drink"] = self.defender_drink_var.get()
        return ctx

    def _apply_context(self, ctx):
        """Populate the context widgets from a saved dict, filling defaults for
        missing keys so scenarios saved before this feature still load cleanly."""
        ctx = ctx or {}
        default_char = SF6_CHARACTERS[0] if SF6_CHARACTERS else ""
        self.attacker_char_var.set(ctx.get("attacker_char", default_char))
        self.defender_char_var.set(ctx.get("defender_char", default_char))
        self.attacker_drive_var.set(ctx.get("attacker_drive", DRIVE_MAX))
        self.defender_drive_var.set(ctx.get("defender_drive", DRIVE_MAX))
        self.attacker_super_var.set(ctx.get("attacker_super", 0))
        self.defender_super_var.set(ctx.get("defender_super", 0))
        self.attacker_drink_var.set(ctx.get("attacker_drink", 0))
        self.defender_drink_var.set(ctx.get("defender_drink", 0))
        self.position_var.set(ctx.get("position", POSITIONS[0]))
        self._update_drink_visibility()

    def _context_summary(self):
        """One-line human-readable summary of the current context."""
        c = self._read_context()
        summary = (f"{c['attacker_char']} vs {c['defender_char']}  ·  {c['position']}  ·  "
                   f"Drive {c['attacker_drive']}/{c['defender_drive']}  ·  "
                   f"Super {c['attacker_super']}/{c['defender_super']}")
        drinks = [f"{who} {c[key]}" for who, key in (("Attacker", "attacker_drink"),
                                                     ("Defender", "defender_drink")) if key in c]
        if drinks:
            summary += "  ·  Drink " + " ".join(drinks)
        return summary

    def _default_filename(self):
        """Suggested save filename derived from the current context, e.g.
        'Cammy_vs_JP_Corner_D4-6_S0-2'."""
        c = self._read_context()
        parts = [f"{c['attacker_char']}_vs_{c['defender_char']}", c['position'],
                 f"D{c['attacker_drive']}-{c['defender_drive']}",
                 f"S{c['attacker_super']}-{c['defender_super']}"]
        if "attacker_drink" in c or "defender_drink" in c:
            parts.append(f"Drink{c.get('attacker_drink', 0)}-{c.get('defender_drink', 0)}")
        name = "_".join(parts)
        # Strip characters that are invalid in filenames on Windows.
        for ch in ' .<>:"/\\|?*':
            name = name.replace(ch, "")
        return name or "scenario"

    # ── payoff entry helpers ──────────────────────────────────────────────────

    def _create_payoff_entry(self, parent, row, col, flat_idx, value):
        if flat_idx in self.cell_links:
            link = self.cell_links[flat_idx]
            display_val = str(int(round(link["dmg"] + link["ev"])))
            entry = tk.Entry(parent, width=12, readonlybackground=LINKED_BG)
            entry.grid(row=row, column=col, padx=2, pady=2)
            entry.insert(0, display_val)
            entry.configure(state="readonly")
        else:
            entry = tk.Entry(parent, width=12)
            entry.grid(row=row, column=col, padx=2, pady=2)
            entry.insert(0, self.format_payoff(value))
        entry.bind("<Button-3>", lambda e, idx=flat_idx: self.show_cell_context_menu(e, idx))
        return entry

    def show_cell_context_menu(self, event, cell_idx):
        menu = tk.Menu(self.root, tearoff=0)
        if cell_idx in self.cell_links:
            link = self.cell_links[cell_idx]
            filename = os.path.basename(link["path"])
            menu.add_command(label=f"Linked: {filename} (EV={int(round(link['ev']))})", state="disabled")
            menu.add_separator()
            menu.add_command(label="Change linked scenario...", command=lambda: self.link_scenario(cell_idx))
            menu.add_command(label="Remove link", command=lambda: self.remove_link(cell_idx))
        else:
            menu.add_command(label="Link scenario...", command=lambda: self.link_scenario(cell_idx))
        menu.tk_popup(event.x_root, event.y_root)

    def link_scenario(self, cell_idx):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        try:
            ev = resolve_scenario_ev(file_path)
            entry = self.payoff_entries[cell_idx]
            if cell_idx in self.cell_links:
                dmg = self.cell_links[cell_idx]["dmg"]
            else:
                try:
                    dmg = float(entry.get().replace(',', '.'))
                except ValueError:
                    dmg = 0.0

            self.cell_links[cell_idx] = {"path": file_path, "ev": ev, "dmg": dmg}

            total = str(int(round(dmg + ev)))
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, total)
            entry.configure(state="readonly", readonlybackground=LINKED_BG)

            filename = os.path.basename(file_path)
            self.status_var.set(f"Linked to {filename} (EV={int(round(ev)):+d})")
        except Exception as e:
            self.status_var.set(f"Failed to link scenario: {str(e)}")

    def remove_link(self, cell_idx):
        if cell_idx not in self.cell_links:
            return
        dmg = self.cell_links[cell_idx]["dmg"]
        del self.cell_links[cell_idx]
        entry = self.payoff_entries[cell_idx]
        entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, str(int(dmg)))
        self.status_var.set("Link removed")

    # ── link index remapping ──────────────────────────────────────────────────

    def _remap_links_delete_attacker(self, deleted_row, n_defender):
        new_links = {}
        for flat_idx, link in self.cell_links.items():
            row, col = flat_idx // n_defender, flat_idx % n_defender
            if row == deleted_row:
                continue
            new_row = row if row < deleted_row else row - 1
            new_links[new_row * n_defender + col] = link
        self.cell_links = new_links

    def _remap_links_delete_defender(self, deleted_col, n_defender):
        new_links = {}
        for flat_idx, link in self.cell_links.items():
            row, col = flat_idx // n_defender, flat_idx % n_defender
            if col == deleted_col:
                continue
            new_col = col if col < deleted_col else col - 1
            new_links[row * (n_defender - 1) + new_col] = link
        self.cell_links = new_links

    def _remap_links_add_defender(self, n_defender):
        new_links = {}
        for flat_idx, link in self.cell_links.items():
            row, col = flat_idx // n_defender, flat_idx % n_defender
            new_links[row * (n_defender + 1) + col] = link
        self.cell_links = new_links

    # ── matrix construction ───────────────────────────────────────────────────

    def format_payoff(self, value):
        try:
            if isinstance(value, str):
                value = value.replace(',', '.')
            return str(int(float(value)))
        except (ValueError, TypeError):
            return "0"

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
        self.attacker_matrix_labels = []
        self.defender_matrix_labels = []

        n_attacker = len(old_attacker_moves)
        n_defender = len(old_defender_moves)
        expected_payoffs = n_attacker * n_defender
        if len(old_payoffs) != expected_payoffs and old_payoffs:
            old_payoffs = ["0"] * expected_payoffs

        ttk.Label(self.moves_frame, text="Attacker Moves:").grid(row=0, column=0, padx=5, pady=2)
        for i, move in enumerate(old_attacker_moves):
            entry = ttk.Entry(self.moves_frame, width=15)
            entry.grid(row=i+1, column=0, padx=5, pady=2)
            entry.insert(0, move)
            entry.bind("<KeyRelease>", lambda e, idx=i: self.update_attacker_label(idx, e))
            self.attacker_entries.append(entry)

            delete_btn = ttk.Button(self.moves_frame, text="X", width=2, command=lambda x=i: self.delete_attacker_move(x))
            delete_btn.grid(row=i+1, column=1, padx=2, pady=2)

        self.attacker_add_button = ttk.Button(self.moves_frame, text="+", command=self.add_attacker_move)
        self.attacker_add_button.grid(row=n_attacker+1, column=0, padx=5, pady=5)

        ttk.Label(self.moves_frame, text="Defender Moves:").grid(row=0, column=3, padx=5, pady=2)
        for i, move in enumerate(old_defender_moves):
            entry = ttk.Entry(self.moves_frame, width=15)
            entry.grid(row=i+1, column=3, padx=5, pady=2)
            entry.insert(0, move)
            entry.bind("<KeyRelease>", lambda e, idx=i: self.update_defender_label(idx, e))
            self.defender_entries.append(entry)

            delete_btn = ttk.Button(self.moves_frame, text="X", width=2, command=lambda x=i: self.delete_defender_move(x))
            delete_btn.grid(row=i+1, column=4, padx=2, pady=2)

        self.defender_add_button = ttk.Button(self.moves_frame, text="+", command=self.add_defender_move)
        self.defender_add_button.grid(row=n_defender+1, column=3, padx=5, pady=5)

        for j, move in enumerate(old_defender_moves):
            lbl = ttk.Label(self.matrix_frame, text=move, wraplength=60)
            lbl.grid(row=0, column=j+1, padx=2, pady=2)
            self.defender_matrix_labels.append(lbl)

        for i in range(n_attacker):
            lbl = ttk.Label(self.matrix_frame, text=old_attacker_moves[i], wraplength=60)
            lbl.grid(row=i+1, column=0, padx=2, pady=2, sticky="e")
            self.attacker_matrix_labels.append(lbl)

            for j in range(n_defender):
                idx = i * n_defender + j
                val = old_payoffs[idx] if idx < len(old_payoffs) else "0"
                entry = self._create_payoff_entry(self.matrix_frame, i+1, j+1, idx, val)
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

    def add_attacker_move(self):
        # New row goes at the end of the flat index, so existing cell links are untouched.
        n_defender = len(self.defender_entries)
        attacker_moves = [e.get() for e in self.attacker_entries] + [f"Move {len(self.attacker_entries)+1}"]
        payoffs = [e.get() for e in self.payoff_entries] + ["0"] * n_defender
        self.update_inputs(new_payoffs=payoffs, attacker_moves=attacker_moves,
                           defender_moves=[e.get() for e in self.defender_entries])

    def add_defender_move(self):
        # New column shifts every row's flat indices, so links must be remapped first.
        n_attacker = len(self.attacker_entries)
        n_defender = len(self.defender_entries)
        current = [e.get() for e in self.payoff_entries]
        payoffs = []
        for i in range(n_attacker):
            payoffs.extend(current[i * n_defender:(i + 1) * n_defender])
            payoffs.append("0")
        self._remap_links_add_defender(n_defender)
        defender_moves = [e.get() for e in self.defender_entries] + [f"Move {n_defender+1}"]
        self.update_inputs(new_payoffs=payoffs, attacker_moves=[e.get() for e in self.attacker_entries],
                           defender_moves=defender_moves)

    def _read_payoffs(self):
        """Read the payoff entries into a list of floats, treating blanks/garbage as 0.0."""
        values = []
        for entry in self.payoff_entries:
            val = entry.get()
            try:
                values.append(float(val.replace(',', '.')) if val else 0.0)
            except ValueError:
                values.append(0.0)
        return values

    def delete_attacker_move(self, index):
        if len(self.attacker_entries) <= 2:
            self.status_var.set("Cannot delete: Minimum of 2 attacker moves required.")
            return
        n_attacker = len(self.attacker_entries)
        n_defender = len(self.defender_entries)
        try:
            payoff_matrix = np.array(self._read_payoffs()).reshape(n_attacker, n_defender)
            new_payoffs = np.delete(payoff_matrix, index, axis=0).flatten().tolist()
            del self.attacker_entries[index]
            self._remap_links_delete_attacker(index, n_defender)
            self.update_inputs(new_payoffs=new_payoffs)
        except Exception as e:
            self.status_var.set(f"Error deleting attacker move: {str(e)}")
            self.update_inputs()

    def delete_defender_move(self, index):
        if len(self.defender_entries) <= 2:
            self.status_var.set("Cannot delete: Minimum of 2 defender moves required.")
            return
        n_attacker = len(self.attacker_entries)
        n_defender = len(self.defender_entries)
        try:
            payoff_matrix = np.array(self._read_payoffs()).reshape(n_attacker, n_defender)
            new_payoffs = np.delete(payoff_matrix, index, axis=1).flatten().tolist()
            expected_length = n_attacker * (n_defender - 1)
            if len(new_payoffs) != expected_length:
                raise ValueError(f"Payoff length mismatch: expected {expected_length}, got {len(new_payoffs)}")
            del self.defender_entries[index]
            self._remap_links_delete_defender(index, n_defender)
            self.update_inputs(new_payoffs=new_payoffs)
        except ValueError as e:
            self.status_var.set(f"Invalid payoff values detected: {str(e)}")
            self.update_inputs()

    def update_attacker_label(self, index, event):
        if 0 <= index < len(self.attacker_entries) and 0 <= index < len(self.attacker_matrix_labels):
            self.attacker_matrix_labels[index].config(text=self.attacker_entries[index].get())

    def update_defender_label(self, index, event):
        if 0 <= index < len(self.defender_entries) and 0 <= index < len(self.defender_matrix_labels):
            self.defender_matrix_labels[index].config(text=self.defender_entries[index].get())

    def calculate(self):
        try:
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker = len(attacker_moves)
            n_defender = len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            result = calculate_mixed_nash(attacker_moves, defender_moves, payoff_matrix)
            atk = enumerate_optimal_strategies(attacker_moves, defender_moves, payoff_matrix, "attacker")
            dfn = enumerate_optimal_strategies(attacker_moves, defender_moves, payoff_matrix, "defender")
            attacker_alt = len(atk[1]) if atk else None
            defender_alt = len(dfn[1]) if dfn else None
            self.display_result(result, title="Mixed Strategy Nash Equilibrium",
                                attacker_alt=attacker_alt, defender_alt=defender_alt)
        except Exception as e:
            self.status_var.set(str(e))

    def save_scenario(self):
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")],
                                                     initialfile=self._default_filename())
            if not file_path:
                return
            base_dir = os.path.dirname(file_path)
            payoffs = []
            for idx, entry in enumerate(self.payoff_entries):
                if idx in self.cell_links:
                    link = self.cell_links[idx]
                    link_path = link["path"]
                    try:
                        link_path = os.path.relpath(link_path, base_dir)
                    except ValueError:
                        pass
                    payoffs.append({"dmg": link["dmg"], "link": link_path})
                else:
                    payoffs.append(entry.get())
            scenario = {
                "attacker_moves": [entry.get() for entry in self.attacker_entries],
                "defender_moves": [entry.get() for entry in self.defender_entries],
                "payoffs": payoffs,
                "n_attacker": len(self.attacker_entries),
                "n_defender": len(self.defender_entries),
                "context": self._read_context()
            }
            self.current_file_path = file_path
            save_to_file(scenario, file_path)
            self.status_var.set("Scenario saved successfully!")
        except Exception as e:
            self.status_var.set(f"Failed to save: {str(e)}")

    def _load_scenario_from_path(self, file_path):
        scenario = load_from_file(file_path)
        self.current_file_path = file_path
        base_dir = os.path.dirname(file_path)
        new_links = {}
        resolved_payoffs = []
        for idx, p in enumerate(scenario.get("payoffs", [])):
            if isinstance(p, dict) and "link" in p:
                dmg = float(p.get("dmg", 0))
                link_path = p["link"]
                if not os.path.isabs(link_path):
                    link_path = os.path.normpath(os.path.join(base_dir, link_path))
                try:
                    ev = resolve_scenario_ev(link_path)
                    new_links[idx] = {"path": link_path, "ev": ev, "dmg": dmg}
                    resolved_payoffs.append(str(int(round(dmg + ev))))
                except Exception as e:
                    self.status_var.set(f"Warning: Could not resolve link '{p['link']}': {e}")
                    resolved_payoffs.append(str(int(dmg)))
            else:
                resolved_payoffs.append(p if isinstance(p, str) else str(p))
        self.cell_links = new_links
        scenario["payoffs"] = resolved_payoffs
        self.update_inputs_from_scenario(scenario)
        self._apply_context(scenario.get("context"))
        name = os.path.splitext(os.path.basename(file_path))[0]
        self.status_var.set(f"Loaded: {name}")

    def load_scenario(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if not file_path:
                return
            self._load_scenario_from_path(file_path)
        except ValueError as e:
            self.status_var.set(f"Failed to load: {str(e)}")
        except Exception as e:
            self.status_var.set(f"Failed to load: Invalid file format ({str(e)})")

    def compare_folder(self):
        folder = filedialog.askdirectory(title="Select folder to compare")
        if not folder:
            return

        # Collect all JSON files recursively
        scenario_files = []
        for dirpath, _, filenames in os.walk(folder):
            for filename in filenames:
                if filename.lower().endswith('.json'):
                    scenario_files.append(os.path.join(dirpath, filename))

        if not scenario_files:
            self.status_var.set("No scenario files found.")
            return

        threshold = float(self.threshold_spinbox.get())
        rows = []
        failed = 0
        for file_path in scenario_files:
            try:
                data = process_scenario_for_comparison(file_path, threshold)
                if data is None:
                    failed += 1
                    continue
                rel_dir = os.path.relpath(os.path.dirname(file_path), folder)
                if rel_dir == '.':
                    rel_dir = '(root)'
                name = os.path.splitext(os.path.basename(file_path))[0]
                rows.append({
                    "folder":   rel_dir,
                    "scenario": name,
                    "context":  data.get("context_str", ""),
                    "ev":       data["ev"],
                    "strategy": data["strategy_str"],
                    "path":     file_path,
                })
            except Exception:
                failed += 1

        rows.sort(key=lambda r: r["ev"], reverse=True)

        # ── build window ──────────────────────────────────────────────────────
        win = tk.Toplevel(self.root)
        win.title("Scenario Comparison")
        win.geometry("1050x540")
        win.columnconfigure(0, weight=1)
        win.rowconfigure(1, weight=1)

        header = ttk.Frame(win, padding=(10, 8, 10, 4))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=folder, foreground="#555555").pack(side="left")
        summary = f"{len(rows)} scenarios loaded" + (f"   ({failed} skipped)" if failed else "")
        ttk.Label(header, text=summary, foreground="#888888").pack(side="right")

        tree_frame = ttk.Frame(win, padding=(10, 0, 10, 10))
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        col_config = {
            "folder":   ("Folder",                       160, "w"),
            "scenario": ("Scenario",                     150, "w"),
            "context":  ("Context",                      160, "w"),
            "ev":       ("EV",                            70, "e"),
            "strategy": ("Simplified Attacker Strategy", 500, "w"),
        }
        cols = list(col_config.keys())
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for col, (heading, width, anchor) in col_config.items():
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor=anchor, minwidth=40, stretch=(col == "strategy"))

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        path_map = {}
        sort_state = {"col": "ev", "reverse": True}

        def populate(sorted_rows):
            for item in tree.get_children():
                tree.delete(item)
            path_map.clear()
            for row in sorted_rows:
                iid = tree.insert("", "end", values=(
                    row["folder"],
                    row["scenario"],
                    row["context"],
                    f"{row['ev']:.2f}",
                    row["strategy"],
                ))
                path_map[iid] = row["path"]

        def sort_by(col):
            descending = not (sort_state["col"] == col and sort_state["reverse"])
            sort_state["col"], sort_state["reverse"] = col, descending
            key = (lambda r: r["ev"]) if col == "ev" else (lambda r: r[col].lower())
            populate(sorted(rows, key=key, reverse=descending))
            for c, (h, _, _) in col_config.items():
                indicator = (" ↓" if descending else " ↑") if c == col else ""
                tree.heading(c, text=h + indicator, command=lambda _c=c: sort_by(_c))

        for col in cols:
            tree.heading(col, command=lambda c=col: sort_by(c))

        # Initial populate with EV ↓ indicator
        populate(rows)
        tree.heading("ev", text="EV ↓", command=lambda: sort_by("ev"))

        def on_double_click(event):
            item = tree.focus()
            if item and item in path_map:
                try:
                    self._load_scenario_from_path(path_map[item])
                    self.root.lift()
                except Exception as e:
                    self.status_var.set(f"Failed to load: {str(e)}")

        tree.bind("<Double-1>", on_double_click)

    def make_binary(self):
        try:
            for idx, entry in enumerate(self.payoff_entries):
                if idx in self.cell_links:
                    continue
                num = float(entry.get())
                new_value = 1 if num >= 1000 else -1 if num <= -1000 else 0
                entry.delete(0, tk.END)
                entry.insert(0, str(new_value))
            self.status_var.set("Payoffs converted to binary!")
        except Exception as e:
            self.status_var.set(f"Error converting to binary: {str(e)}")

    def simplify_strategy(self, player):
        try:
            threshold_percent = float(self.threshold_spinbox.get())
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker, n_defender = len(attacker_moves), len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            if len(payoffs) != n_attacker * n_defender:
                raise ValueError(f"Payoff length mismatch: expected {n_attacker * n_defender}, got {len(payoffs)}")
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            result = solve_simplified_strategy(attacker_moves, defender_moves, payoff_matrix, player, threshold_percent)
            if result is None:
                raise ValueError("Failed to compute simplified strategy")
            self.display_simplified_result(result[:5], player, result[5])
        except Exception as e:
            self.status_var.set(f"Failed to simplify {player} strategy: {str(e)}")

    def show_alternate_optima(self):
        try:
            attacker_moves = [entry.get() for entry in self.attacker_entries]
            defender_moves = [entry.get() for entry in self.defender_entries]
            n_attacker, n_defender = len(attacker_moves), len(defender_moves)
            payoffs = [float(entry.get()) for entry in self.payoff_entries]
            if len(payoffs) != n_attacker * n_defender:
                raise ValueError(f"Payoff length mismatch: expected {n_attacker * n_defender}, got {len(payoffs)}")
            payoff_matrix = np.array(payoffs).reshape(n_attacker, n_defender)
            atk = enumerate_optimal_strategies(attacker_moves, defender_moves, payoff_matrix, "attacker")
            dfn = enumerate_optimal_strategies(attacker_moves, defender_moves, payoff_matrix, "defender")
            if atk is None or dfn is None:
                raise ValueError("Solver failed")
            self.display_alternate_optima(attacker_moves, defender_moves, atk, dfn)
        except Exception as e:
            self.status_var.set(f"Failed to compute alternate optima: {str(e)}")

    def display_alternate_optima(self, attacker_moves, defender_moves, atk, dfn):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        game_value = atk[0] if abs(atk[0]) > 5e-5 else 0.0
        self.result_text.insert(tk.END, "Alternate Optimal Strategies\n", "title")
        self.result_text.insert(tk.END, f"{self._context_summary()}\n", "subtitle")
        self.result_text.insert(tk.END, f"Game Value (EV): {game_value:.4f}  —  all equilibria share this EV\n\n", "item")

        for label, moves, (_, strategies) in (("Attacker", attacker_moves, atk),
                                              ("Defender", defender_moves, dfn)):
            count = len(strategies)
            if count <= 1:
                self.result_text.insert(tk.END, f"{label}: optimal strategy is unique.\n\n", "header")
                if count == 1:
                    self._insert_strategy_line(moves, strategies[0])
                    self.result_text.insert(tk.END, "\n")
                continue
            self.result_text.insert(tk.END, f"{label}: {count} distinct optimal strategies\n", "header")
            for n, probs in enumerate(strategies, 1):
                self.result_text.insert(tk.END, f"  #{n}\n", "item")
                self._insert_strategy_line(moves, probs)
            self.result_text.insert(tk.END, "\n")
        self.result_text.config(state=tk.DISABLED)

    def _insert_strategy_line(self, moves, probs):
        for move, prob in sorted(zip(moves, probs), key=lambda x: x[1], reverse=True):
            prob = prob if prob > 5e-5 else 0.0   # clamp numerical noise / negative zero
            tag = "value_active" if prob > 0.005 else "value_inactive"
            self.result_text.insert(tk.END, f"    {move}: ", "item")
            self.result_text.insert(tk.END, f"{100*prob:6.2f}%\n", tag)

    def display_simplified_result(self, result, player, original_ev):
        self.result_text.config(state=tk.NORMAL)
        attacker_moves, defender_moves, attacker_probs, defender_probs, simplified_ev = result
        self.result_text.delete(1.0, tk.END)
        title = f"Simplified {'Attacker' if player == 'attacker' else 'Defender'} Strategy"
        self.result_text.insert(tk.END, f"{title}\n", "title")
        self.result_text.insert(tk.END, f"{self._context_summary()}\n\n", "subtitle")
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
        self.result_text.insert(tk.END, "Expected Payoff (Attacker's Perspective):\n", "header")
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
        self.result_text.config(state=tk.DISABLED)

    def display_result(self, result, title="Mixed Strategy Nash Equilibrium",
                       attacker_alt=None, defender_alt=None):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)

        if isinstance(result, str):
            self.result_text.insert(tk.END, result)
            return

        attacker_moves, defender_moves, attacker_probs, defender_probs, game_value = result
        self.result_text.insert(tk.END, f"{title}\n", "title")
        self.result_text.insert(tk.END, f"{self._context_summary()}\n\n", "subtitle")
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

        alts = [(label, n) for label, n in (("Attacker", attacker_alt), ("Defender", defender_alt))
                if n is not None and n > 1]
        if alts:
            detail = ", ".join(f"{label} {n}" for label, n in alts)
            self.result_text.insert(tk.END,
                f"\n⚠ Multiple optimal strategies exist ({detail}).\n"
                "   Press 'Alternate Optima' to see them.\n", "warn")
        elif attacker_alt is not None and defender_alt is not None:
            self.result_text.insert(tk.END, "\nEquilibrium is unique.\n", "item")

        self.result_text.config(state=tk.DISABLED)
