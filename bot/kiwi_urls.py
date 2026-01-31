def build_kiwi_url_ow(origin_slug: str, dest_slug: str, depart_iso: str, sort_by_price: bool = True) -> str:
    base = f"https://www.kiwi.com/br/search/results/{origin_slug}/{dest_slug}/{depart_iso}/no-return/"
    return base + ("?sortBy=price" if sort_by_price else "")

def build_kiwi_url_rt(origin_slug: str, dest_slug: str, depart_iso: str, return_iso: str, sort_by_price: bool = True) -> str:
    base = f"https://www.kiwi.com/br/search/results/{origin_slug}/{dest_slug}/{depart_iso}/{return_iso}/"
    return base + ("?sortBy=price" if sort_by_price else "")
