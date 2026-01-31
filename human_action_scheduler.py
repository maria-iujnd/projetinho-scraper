import random
import time
from typing import Callable, List, Tuple

class HumanActionScheduler:
    def __init__(self, debug_seed=None):
        self.debug_seed = debug_seed
        if debug_seed is not None:
            random.seed(debug_seed)

    def run_actions(self, actions: List[Tuple[Callable, tuple, dict]],
                    min_delay=0.2, max_delay=1.2, shuffle=True):
        """
        Executa ações randomizando ordem e delays.
        :param actions: Lista de tuplas (func, args, kwargs)
        :param min_delay: Delay mínimo entre ações
        :param max_delay: Delay máximo entre ações
        :param shuffle: Se True, randomiza ordem das ações
        """
        actions_to_run = actions[:]
        if shuffle:
            random.shuffle(actions_to_run)
        for func, args, kwargs in actions_to_run:
            func(*args, **kwargs)
            time.sleep(random.uniform(min_delay, max_delay))

    def run_loop(self, actions: List[Tuple[Callable, tuple, dict]],
                 iterations=3, min_delay=0.2, max_delay=1.2, shuffle=True):
        """
        Executa múltiplas iterações randomizando ordem e delays a cada ciclo.
        """
        for _ in range(iterations):
            self.run_actions(actions, min_delay, max_delay, shuffle)

# Exemplo de uso:
# scheduler = HumanActionScheduler(debug_seed=42)
# actions = [
#     (func1, (arg1,), {}),
#     (func2, (), {}),
#     (func3, (arg2, arg3), {"kw": 1}),
# ]
# scheduler.run_loop(actions, iterations=5)
