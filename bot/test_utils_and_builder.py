from bot.pricing_utils import parse_brl_to_int, brl
from bot.date_utils import format_date_br
from bot.message_builder import build_grouped_message

# Testes rápidos
print('parse_brl_to_int("R$ 1.234") =', parse_brl_to_int("R$ 1.234"))  # Esperado: 1234
print('brl(1234) =', brl(1234))  # Esperado: '1.234'
print('format_date_br("2026-01-29") =', format_date_br("2026-01-29"))  # Esperado: '29/01/2026'

# Teste build_grouped_message
msg = build_grouped_message(
    trip_type="OW",
    origin_iata="GRU",
    dest_iata="BSB",
    depart_iso="2026-01-29",
    flights=[{
        'dep_time': '06:00', 'arr_time': '08:00', 'duration_text': '2h', 'stops': 0,
        'airline': 'LATAM', 'price_text': 'R$ 1.234', 'share_link': 'https://kiwi.com/abc123'
    }],
    min_price=1234,
    ceiling=1500
)
print('build_grouped_message(...) =\n', msg)
