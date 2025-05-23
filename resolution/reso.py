import time
import matplotlib.pyplot as plt
def negate_literal(lit):
    return lit[1:] if lit.startswith("-") else "-" + lit

def resolve_pair(c1, c2):
    res = set()
    for lit in c1:
        neg = negate_literal(lit)
        if neg in c2:
            clause = (c1 - {lit}) | (c2 - {neg})
            if not any(negate_literal(x) in clause for x in clause):
                res.add(frozenset(clause))
    return res

def solve_resolution(initial_formula):
    if not initial_formula:
        return True
    clauses = {frozenset(c) for c in initial_formula}
    if frozenset() in clauses:
        return False
    while True:
        new_clauses = set()
        clause_list = list(clauses)
        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                c1 = clause_list[i]
                c2 = clause_list[j]
                resolvents = resolve_pair(c1, c2)
                for r in resolvents:
                    if not r:
                        return False
                    if r not in clauses:
                        new_clauses.add(r)
        if not new_clauses:
            return True
        clauses.update(new_clauses)


def generate_large_formula():
    formula = []
    for i in range(1, 30):
        formula.append({f"x{i}", f"-x{i+1}"})
    formula.append({f"x30"})
    return [frozenset(clause) for clause in formula]

def benchmark():
    iteration_counts = list(range(1, 20, 5))  # 1, 6, 11, ..., 56
    cpu_times = []

    for iters in iteration_counts:
        formula = generate_large_formula()
        t0 = time.process_time()
        for _ in range(iters):
            solve_resolution(formula)
        t1 = time.process_time()
        elapsed = t1 - t0
        print(f"Iterations: {iters:2d} -> CPU Time: {elapsed:.6f} sec")
        cpu_times.append(elapsed)

    plt.figure(figsize=(10, 6))
    plt.plot(iteration_counts, cpu_times, marker="o", linestyle="-", color="purple")
    plt.title("CPU Time vs Iterations for Resolution-Based SAT Solver")
    plt.xlabel("Number of Iterations")
    plt.ylabel("CPU Time (seconds)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    benchmark()
