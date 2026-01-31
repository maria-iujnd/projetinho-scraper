from bot.browser import open_browser

# Abre o navegador
browser = open_browser(headless=False)


# Acessa o site simples
browser.get("https://www.booking.com/")

input("Pressione ENTER para fechar o navegador...")

browser.quit()
