from datetime import date, datetime
from typing import Union

def format_date_for_user(dt: Union[str, date, datetime]) -> str:
    """
    REGRA DE OURO: Toda data exibida ao usuário DEVE passar por esta função!
    Nunca monte datas manualmente em texto para o usuário.
    
    Formata uma data para o padrão DD/MM/AAAA para exibição ao usuário.
    Aceita objetos date, datetime ou string ISO (YYYY-MM-DD).
    
    Exemplos de uso:
        format_date_for_user('2026-02-05') -> '05/02/2026'
        format_date_for_user(datetime.date(2026,2,5)) -> '05/02/2026'
        format_date_for_user(datetime.datetime.now()) -> 'DD/MM/AAAA'
    """
    if isinstance(dt, str):
        # Tenta converter string ISO para date
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            try:
                dt = datetime.strptime(dt, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"Data em formato inválido: {dt}")
    if isinstance(dt, datetime):
        dt = dt.date()
    if not isinstance(dt, date):
        raise TypeError("O parâmetro deve ser date, datetime ou string ISO.")
    return dt.strftime("%d/%m/%Y")
