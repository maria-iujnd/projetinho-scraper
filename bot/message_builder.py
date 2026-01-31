from typing import Optional, List, Dict, Tuple
from bot.pricing_utils import brl, parse_brl_to_int
from bot.date_utils import format_date_br


def build_grouped_message(
    trip_type: str,
    origin_iata: str,
    dest_iata: str,
    depart_iso: str,
    flights: List[Dict],
    min_price: int,
    ceiling: int,
    return_iso: Optional[str] = None,
    avg_info: Optional[Tuple[int, int]] = None,  # (avg_or_median, samples)
    show_avg_drop_only: bool = True,
) -> str:
    # Cabeçalho
    if trip_type.upper() == "RT" and return_iso:
        header = (
            f"✈️ {origin_iata} → {dest_iata} (IDA E VOLTA)\n"
            f"📅 Ida: {format_date_br(depart_iso)} | Volta: {format_date_br(return_iso)}\n"
            f"💰 Agora: R$ {brl(min_price)}\n"
        )
    else:
        header = (
            f"✈️ {origin_iata} → {dest_iata}\n"
            f"📅 Data: {format_date_br(depart_iso)}\n"
            f"💰 Melhor preço: R$ {brl(min_price)}\n"
        )

    # Média histórica (se tiver amostras)
    if avg_info:
        avg_price, samples = avg_info
        if avg_price and avg_price > 0 and min_price > 0:
            drop = (avg_price - min_price) / avg_price
            if (not show_avg_drop_only) or (drop >= 0.15):
                pct = int(round(drop * 100))
                header += (
                    f"📊 Referência ({samples}): R$ {brl(avg_price)} → agora R$ {brl(min_price)} (-{pct}%)\n"
                )

    header += "—\n"

    lines = []
    for idx, f in enumerate(flights, start=1):
        line = (
            f"{idx}) {f.get('dep_time','?')}-{f.get('arr_time','?')} | {f.get('duration_text','N/A')} | {f.get('stops','?')}\n"
            f"   {f.get('airline','N/A')} | {f.get('price_text','N/A')}"
        )
        share_link = f.get('share_link')
        if share_link:
            line += f"\n   🔗 {share_link}"
        lines.append(line)

    return header + "\n".join(lines)
