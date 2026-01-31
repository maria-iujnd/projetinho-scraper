# Centralized selectors for Viajala scraping

# Card structure
CSS_CARD_RESULT_OW = "div.segments.result-item-ow"
CSS_CARD_RESULT_ITEM = "div.segments.result-item"
CSS_CARD_SEGMENTS = "div.segments"

# Price
CSS_PRICE_VALUE = "span.price-value"
CSS_PRICE_VALUE_PRIMARY = "div.price > span.price-value"
CSS_PRICE_CANDIDATES = "span.price-value, span.fare-upsell-price"
CSS_PRICE_ATTR_SELECTORS = ["[data-price]", "[data-amount]", "[data-value]"]
CSS_PRICE_ATTR_NAMES = ["data-price", "data-amount", "data-value"]

# Link
CSS_LINK_BOOK = "a.btn.book"
CSS_LINK_BOOK_REDIRECT = "a.btn.book[href*='viajala.com.br/redirect']"

# Overlays / dialogs
CSS_ARIA_CLOSE_GENERIC = "[aria-label*='close' i], [aria-label*='fechar' i]"
CSS_ARIA_CLOSE_BUTTON = "button[aria-label*='close' i]"
CSS_ARIA_FECHAR_BUTTON = "button[aria-label*='fechar' i]"
CSS_DIALOG_ROLE = "[role='dialog']"
CSS_MODAL_MAT = "mat-dialog-container, .mat-mdc-dialog-surface"

# Partner modal
CSS_PARTNER_MODAL = "div.frame-container.modal"
CSS_PARTNER_MODAL_HEADER = "div.frame-container.modal div.header"
CSS_PARTNER_MODAL_CLOSE = "app-svg-icon.smart-close"
CSS_PARTNER_MODAL_CLOSE_ICON = "app-svg-icon.smart-close[name='close']"
CSS_PARTNER_MODAL_CLOSE_MAT_ICON = "app-svg-icon.smart-close .mat-icon"
CSS_SVG = "svg"

# Card content
CSS_PARTNER_LABEL = "div.partner-label > div"
CSS_AIRLINE_LOGO_IMG = "div.airline-logo img"
CSS_LAYOVERS = "div.layovers"
CSS_AIRPORT = "div.airport"
CSS_NEXTDAY = "div.nextday"
CSS_DEPARTURE_TIME = "div.departure strong"
CSS_ARRIVAL_TIME = "div.arrival strong"
CSS_DURATION = "span.duration"

# XPath selectors
XPATH_BTN_ACEITAR = "//button[contains(., 'Aceitar')]"
XPATH_BTN_CONCORDO = "//button[contains(., 'Concordo')]"
XPATH_BTN_ENTENDI = "//button[contains(., 'Entendi')]"
XPATH_BTN_FECHAR = "//button[contains(., 'Fechar')]"
XPATH_BTN_CONTINUAR = "//button[contains(., 'Continuar')]"

XPATH_OVERLAY_CLOSE_SELECTORS = [
    "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'FECHAR')]",
    "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ENTENDI')]",
    "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'OK')]",
    "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'CONTINUAR')]",
]

XPATH_COOKIE_ACCEPT_LINK = (
    "//a[normalize-space()='Aceitar' or "
    "contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ACEITAR')]"
)
XPATH_COOKIE_ACCEPT_BUTTON = (
    "//button[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ACEITAR')]"
)

XPATH_INTERSTITIAL_CLOSE = "//button[contains(., '×') or contains(., 'X')]"
XPATH_CARD_IN_MODAL = "ancestor::div[contains(@class,'frame-container') and contains(@class,'modal')]"
