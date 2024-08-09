from random import choices
from string import ascii_lowercase


def random_name() -> str:
    return '_' + ''.join(choices(ascii_lowercase, k=12))
