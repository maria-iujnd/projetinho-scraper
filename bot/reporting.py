from collections import Counter, defaultdict

def count_by_reason(reports):
    counts = defaultdict(int)
    for r in reports:
        key = f"{r.phase}:{r.reason}"
        counts[key] += 1
    return dict(counts)

def print_summary(reports):
    counts = count_by_reason(reports)
    print("\n===== RESUMO FINAL =====")
    for key, count in sorted(counts.items()):
        print(f"{key}: {count}")
    print("========================\n")
