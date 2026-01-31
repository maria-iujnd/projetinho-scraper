import random
import time

class HumanDelayHelper:
    def __init__(self, short_range=(0.2, 0.9), medium_range=(1, 3), rare_range=(6, 12), rare_chance=0.05):
        self.short_range = short_range
        self.medium_range = medium_range
        self.rare_range = rare_range
        self.rare_chance = rare_chance

    def short_pause(self):
        delay = random.uniform(*self.short_range)
        time.sleep(delay)

    def medium_pause(self):
        delay = random.uniform(*self.medium_range)
        time.sleep(delay)

    def rare_pause(self):
        delay = random.uniform(*self.rare_range)
        time.sleep(delay)

    def maybe_rare_pause(self):
        if random.random() < self.rare_chance:
            self.rare_pause()

    def human_pause(self):
        # Use medium pause most of the time, with a chance for rare pause
        self.medium_pause()
        self.maybe_rare_pause()

# Exemplo de uso:
# from human_delay_helper import HumanDelayHelper
# delay = HumanDelayHelper()
# delay.short_pause()
# delay.medium_pause()
# delay.human_pause()
