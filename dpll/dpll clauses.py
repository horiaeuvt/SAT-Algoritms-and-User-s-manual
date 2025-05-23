
import time
import tracemalloc
from copy import deepcopy
import matplotlib.pyplot as plt


def negate_literal(lit):
    return lit[1:] if lit.startswith("-") else "-" + lit

def get_variable(lit):
    return lit[1:] if lit.startswith("-") else lit

def unit_prop(formula, assignments):
    formula = {frozenset(cl) for cl in formula}
    made_change = True
    while made_change:
        made_change = False
        unit = None
        for clause in formula:
            if len(clause) == 1:
                unit = next(iter(clause))
                break
        if unit:
            made_change = True
            var = get_variable(unit)
            assignments[var] = not unit.startswith("-")
            neg_unit = negate_literal(unit)
            new_formula = set()
            for clause in formula:
                if unit in clause:
                    continue
                new_clause = clause - {neg_unit}
                if not new_clause:
                    return {frozenset()}, assignments
                new_formula.add(new_clause)
            formula = new_formula
    return formula, assignments

def resolve(formula, var):
    pos = {cl for cl in formula if var in cl}
    neg = {cl for cl in formula if negate_literal(var) in cl}
    other = {cl for cl in formula if var not in cl and negate_literal(var) not in cl}
    new_formula = set()
    for p in pos:
        for n in neg:
            res = (p - {var}) | (n - {negate_literal(var)})
            if not any(negate_literal(l) in res for l in res):
                new_formula.add(res)
    return new_formula | other

def solve_sat(formula, assignments=None):
    if assignments is None:
        assignments = {}
    formula, assignments = unit_prop(formula, assignments)
    if not formula:
        return True, assignments
    if any(len(clause) == 0 for clause in formula):
        return False, {}
    var = get_variable(next(iter(next(iter(formula)))))
    return solve_sat(resolve(formula, var), assignments)



def generate_formula(clause_count):
    formula = []
    for i in range(1, clause_count + 1):
        formula.append({f"x{i}", f"-x{i+1}"})
    formula.append({f"x{clause_count + 1}"})
    return [set(clause) for clause in formula]



def benchmark():
    clause_sizes = list(range(10, 1001, 20)) 
    cpu_times = []
    memory_peaks = []
    iterations = 1

    for size in clause_sizes:
        formula = generate_formula(size)
        print(f"\nRunning size {size} with {iterations} iterations...")

        tracemalloc.start()
        cpu0 = time.process_time()

        for _ in range(iterations):
            solve_sat(deepcopy(formula))

        cpu1 = time.process_time()
        mem = tracemalloc.get_traced_memory()[1] / 1024
        tracemalloc.stop()

        cpu_times.append(cpu1 - cpu0)
        memory_peaks.append(mem)

        print(f"✔️  Clauses: {size}, CPU: {cpu1 - cpu0:.6f}s, Mem: {mem:.2f}KB")


    plt.figure(figsize=(10, 6))
    plt.plot(clause_sizes, cpu_times, marker="o", color="blue", label="CPU Time (s)")
    plt.title("DPLL SAT Solver Benchmark: CPU Time vs Clause Count")
    plt.xlabel("Number of Clauses")
    plt.ylabel("CPU Time (seconds)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


    plt.figure(figsize=(10, 6))
    plt.plot(clause_sizes, memory_peaks, marker="^", color="purple")
    plt.title("DPLL SAT Solver Benchmark: Memory Usage vs Clause Count")
    plt.xlabel("Number of Clauses")
    plt.ylabel("Peak Memory (KB)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()



if __name__ == "__main__":
    benchmark()
