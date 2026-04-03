import random

from constants import COMMODITIES


def roll_dice() -> tuple[str, str, float]:
    stock = random.choice(COMMODITIES)
    action = random.choice(["Up", "Down", "Dividend"])
    value = random.choice([0.05, 0.10, 0.20])
    return stock, action, value
