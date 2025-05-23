import time
import tracemalloc
from copy import deepcopy

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

def generate_large_formula():
    formula = []
    for i in range(1, 101):
        formula.append({f"x{i}", f"-x{i+1}"})
    formula.append({f"x101"})
    return [set(clause) for clause in formula]

def main():
    formula = generate_large_formula()
    iterations = 15000
    print(f"Running solver {iterations} times...\n")

    tracemalloc.start()
    t0 = time.perf_counter()
    cpu0 = time.process_time()

    for _ in range(iterations):
        solve_sat(formula)

    cpu1 = time.process_time()
    t1 = time.perf_counter()
    mem = tracemalloc.get_traced_memory()[1] / 1024
    tracemalloc.stop()

    print(f"⏱️  Wall time: {t1 - t0:.12f} seconds")
    print(f"🧮  CPU time:  {cpu1 - cpu0:.12f} seconds")
    print(f"🧠  Peak memory: {mem:.4f} KB")

if __name__ == "__main__":
    main()