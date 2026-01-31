def resolve_group_for_dest(dest_iata: str) -> str:
    dest = dest_iata.upper()
    if dest == "REC":
        return "RECIFE"
    if dest in {"GRU", "VCP", "CGH"}:
        return "SAO PAULO"
    if dest in {"GIG", "SDU"}:
        return "RIO"
    return "GERAL"

if __name__ == "__main__":
    for test in ["REC", "GRU", "VCP", "CGH", "GIG", "SDU", "POA"]:
        print(f"{test} → {resolve_group_for_dest(test)}")
