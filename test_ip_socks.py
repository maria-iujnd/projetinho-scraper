import os
import unittest

from bot.browser import open_browser, close_browser

class TestIpSocks(unittest.TestCase):
	def test_ip_socks(self):
		# se você não estiver usando proxy agora, não faz sentido falhar
		proxy = os.environ.get("BOT_PROXY")
		if not proxy:
			self.skipTest("BOT_PROXY não definido (teste de SOCKS opcional)")

		driver, wait = open_browser(headless=True)
		try:
			driver.get("https://api.ipify.org/?format=text")
			self.assertTrue(len(driver.page_source) > 0)
		finally:
			close_browser(driver)

if __name__ == "__main__":
	unittest.main()