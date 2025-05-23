import time
import tracemalloc
import itertools


def negate_literal(literal):
    """Flips the sign of a literal (e.g., 'p' becomes '-p', '-q' becomes 'q')."""
    return literal[1:] if literal.startswith("-") else "-" + literal

def get_variable(literal):
    """Gets the variable name from a literal (removes '-' if present)."""
    return literal[1:] if literal.startswith("-") else literal

def resolve_pair(clause1, clause2):
    """
    Attempts to resolve two clauses.
    Returns a set of resolvent clauses (as frozensets).
    """
    resolvents = set()
    for lit in clause1:
        neg_lit = negate_literal(lit)
        if neg_lit in clause2:
            new_clause = (clause1 - {lit}) | (clause2 - {neg_lit})
            if not any(negate_literal(x) in new_clause for x in new_clause):
                resolvents.add(frozenset(new_clause))
    return resolvents

def solve_resolution(initial_formula):
    """
    Performs resolution to check if formula is satisfiable.
    Returns False if unsatisfiable (empty clause derived), True otherwise.
    """
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
    for i in range(1, 15): 
        formula.append({f"x{i}", f"-x{i+1}"})
    formula.append({f"x15"})
    return {frozenset(clause) for clause in formula}



def main():
    formula = generate_large_formula()
    iterations = 5
    print(f"Running Resolution SAT solver {iterations} times...\n")

    tracemalloc.start()
    t0 = time.perf_counter()
    cpu0 = time.process_time()

    for _ in range(iterations):
        solve_resolution(formula)

    cpu1 = time.process_time()
    t1 = time.perf_counter()
    mem = tracemalloc.get_traced_memory()[1] / 1024  # KB
    tracemalloc.stop()

    print("✅ Test formula (first few clauses):")
    for clause in list(formula)[:5]:
        print(f"  {clause}")
    if len(formula) > 5:
        print("  ...")

    print(f"\nResult after {iterations} runs (last result not shown):")
    print(f"⏱️  Wall time: {t1 - t0:.12f} seconds")
    print(f"🧮  CPU time:  {cpu1 - cpu0:.12f} seconds")
    print(f"🧠  Peak memory: {mem:.4f} KB")

if __name__ == "__main__":
    main()
