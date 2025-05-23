import time
import tracemalloc
from copy import deepcopy
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def negate_literal(lit):
    return lit[1:] if lit.startswith("-") else "-" + lit

def get_variable(lit):
    return lit[1:] if lit.startswith("-") else lit

def unit_prop(formula, assignments):
    current_formula = {frozenset(cl) for cl in formula}
    made_change = True
    while made_change:
        made_change = False
        unit_literal = None
        for clause in current_formula:
            if len(clause) == 1:
                unit_literal = next(iter(clause))
                break
        if unit_literal:
            made_change = True
            var = get_variable(unit_literal)
            assignments[var] = not unit_literal.startswith("-")
            negated_unit = negate_literal(unit_literal)
            new_formula_temp = set()
            for cl in current_formula:
                if unit_literal in cl:
                    continue
                if negated_unit in cl:
                    new_clause = cl - {negated_unit}
                    if not new_clause:
                        return {frozenset()}, assignments
                    new_formula_temp.add(new_clause)
                else:
                    new_formula_temp.add(cl)
            current_formula = new_formula_temp
    return current_formula, assignments

def get_most_frequent_variable(formula):
    counts = {}
    for clause in formula:
        for literal in clause:
            var = get_variable(literal)
            counts[var] = counts.get(var, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)

def solve_sat(formula_orig, assignments_orig=None):
    formula = {frozenset(cl) for cl in formula_orig}
    assignments = {} if assignments_orig is None else deepcopy(assignments_orig)
    formula, assignments = unit_prop(formula, assignments)
    if not formula:
        return True, assignments
    if any(not cl for cl in formula):
        return False, {}
    var_to_branch = None
    min_clause_len = float('inf')
    for cl in formula:
        if cl:
            if len(cl) < min_clause_len:
                min_clause_len = len(cl)
                var_to_branch = get_variable(next(iter(cl)))
    if not var_to_branch:
        return True, assignments
    formula_true = deepcopy(formula)
    formula_true.add(frozenset({var_to_branch}))
    res_true, assign_true = solve_sat(formula_true, deepcopy(assignments))
    if res_true:
        final_assignments = assignments.copy()
        final_assignments.update(assign_true)
        final_assignments[var_to_branch] = True
        return True, final_assignments
    formula_false = deepcopy(formula)
    formula_false.add(frozenset({negate_literal(var_to_branch)}))
    res_false, assign_false = solve_sat(formula_false, deepcopy(assignments))
    if res_false:
        final_assignments = assignments.copy()
        final_assignments.update(assign_false)
        final_assignments[var_to_branch] = False
        return True, final_assignments
    return False, {}

def parse_cnf_content(cnf_string):
    formula_set = set()
    num_vars_problem = 0
    num_clauses_problem = 0
    max_var_index = 0
    lines = cnf_string.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('c') or line.startswith('%'):
            continue
        if line.startswith('p cnf'):
            parts = line.split()
            try:
                num_vars_problem = int(parts[2])
                num_clauses_problem = int(parts[3])
            except (IndexError, ValueError):
                pass
            continue
        parts = line.split()
        current_clause_literals = []
        for part_str in parts:
            if part_str == '0':
                break
            try:
                literal_val = int(part_str)
                var_index = abs(literal_val)
                max_var_index = max(max_var_index, var_index)
                variable_name = f"x{var_index}"
                if literal_val < 0:
                    current_clause_literals.append(f"-{variable_name}")
                else:
                    current_clause_literals.append(variable_name)
            except ValueError:
                continue
        if current_clause_literals:
            formula_set.add(frozenset(current_clause_literals))
    formula = [set(cl) for cl in formula_set]
    if num_vars_problem == 0 and max_var_index > 0:
        num_vars_problem = max_var_index
    return formula, num_vars_problem, len(formula)

def run_benchmark(cnf_dir_path):
    benchmark_results = []
    cnf_files = glob.glob(os.path.join(cnf_dir_path, '**', '*.cnf'), recursive=True)
    if not cnf_files:
        print(f"No .cnf files found in directory: {cnf_dir_path}")
        return pd.DataFrame()
    print(f"Found {len(cnf_files)} CNF files to process.")
    for i, cnf_file_path in enumerate(cnf_files):
        print(f"\nProcessing file {i+1}/{len(cnf_files)}: {os.path.basename(cnf_file_path)} ...")
        try:
            with open(cnf_file_path, 'r') as f:
                cnf_content_str = f.read()
        except Exception as e:
            print(f"  Error reading file: {e}")
            benchmark_results.append({
                'File': os.path.basename(cnf_file_path),
                'Result': 'Read Error',
                'Time (s)': 0,
                'CPU Time (s)': 0,
                'Peak Memory (KB)': 0,
                'Variables': 0,
                'Clauses': 0,
                'Error': str(e)
            })
            continue
        formula, num_vars, num_clauses = parse_cnf_content(cnf_content_str)
        if not formula:
            print("  No clauses parsed. Skipping.")
            benchmark_results.append({
                'File': os.path.basename(cnf_file_path),
                'Result': 'Parse Error',
                'Time (s)': 0,
                'CPU Time (s)': 0,
                'Peak Memory (KB)': 0,
                'Variables': num_vars,
                'Clauses': num_clauses,
                'Error': 'No clauses parsed'
            })
            continue
        tracemalloc.start()
        t0 = time.perf_counter()
        cpu0 = time.process_time()
        satisfiable, assignments = solve_sat(deepcopy(formula))
        cpu1 = time.process_time()
        t1 = time.perf_counter()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        benchmark_results.append({
            'File': os.path.basename(cnf_file_path),
            'Result': 'SAT' if satisfiable else 'UNSAT',
            'Time (s)': t1 - t0,
            'CPU Time (s)': cpu1 - cpu0,
            'Peak Memory (KB)': peak_mem / 1024,
            'Variables': num_vars,
            'Clauses': num_clauses,
            'Error': None
        })
        print(f"  Result: {'SAT' if satisfiable else 'UNSAT'}, Time: {t1 - t0:.4f}s, Mem: {peak_mem / 1024:.2f}KB")
    return pd.DataFrame(benchmark_results)

def visualize_benchmarks(df):
    if df.empty:
        print("No benchmark data to visualize.")
        return
    print("\n\n--- Benchmark Summary ---")
    print(df[['Time (s)', 'CPU Time (s)', 'Peak Memory (KB)', 'Variables', 'Clauses']].describe())
    print("\n--- Result Counts ---")
    print(df['Result'].value_counts())
    sns.set_theme(style="whitegrid")
    df_sorted_time = df[df['Result'].isin(['SAT', 'UNSAT'])].sort_values(by='Time (s)', ascending=False)
    plt.figure(figsize=(15, 8))
    num_to_plot = min(20, len(df_sorted_time))
    sns.barplot(x='Time (s)', y='File', data=df_sorted_time.head(num_to_plot), palette="viridis")
    plt.title(f'Top {num_to_plot} Longest Solving Times')
    plt.xlabel('Time (seconds)')
    plt.ylabel('CNF File')
    plt.tight_layout()
    plt.savefig("benchmark_solving_times.png")
    plt.show()
    df_solvable = df[df['Result'].isin(['SAT', 'UNSAT'])]
    if not df_solvable.empty:
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='Variables', y='Time (s)', hue='Result', data=df_solvable, palette={'SAT':'blue', 'UNSAT':'red'}, alpha=0.7)
        plt.title('Solving Time vs. Number of Variables')
        plt.xlabel('Number of Variables')
        plt.ylabel('Time (seconds)')
        plt.xscale('log')
        plt.yscale('log')
        plt.tight_layout()
        plt.savefig("benchmark_time_vs_variables.png")
        plt.show()
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='Clauses', y='Time (s)', hue='Result', data=df_solvable, palette={'SAT':'green', 'UNSAT':'orange'}, alpha=0.7)
        plt.title('Solving Time vs. Number of Clauses')
        plt.xlabel('Number of Clauses')
        plt.ylabel('Time (seconds)')
        plt.xscale('log')
        plt.yscale('log')
        plt.tight_layout()
        plt.savefig("benchmark_time_vs_clauses.png")
        plt.show()
        plt.figure(figsize=(10, 6))
        sns.histplot(df_solvable['Time (s)'], bins=20, kde=True)
        plt.title('Distribution of Solving Times')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Frequency')
        plt.tight_layout()
        plt.savefig("benchmark_time_distribution.png")
        plt.show()
    print("\n--- Detailed Results (First 20 rows) ---")
    pd.set_option('display.max_rows', 25)
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 1000)
    print(df.head(20))
    df.to_csv("benchmark_results_full.csv", index=False)
    print("\nFull benchmark results saved to benchmark_results_full.csv")

def main():
    cnf_directory = input("Enter the directory path containing your CNF files: ")
    if not os.path.isdir(cnf_directory):
        print(f"Error: Directory '{cnf_directory}' not found.")
        return
    benchmark_data = run_benchmark(cnf_directory)
    if not benchmark_data.empty:
        visualize_benchmarks(benchmark_data)
    else:
        print("Benchmarking did not produce any data.")

if __name__ == "__main__":
    main()
