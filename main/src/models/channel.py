from enum import Enum


class ChannelType(str, Enum):
    ROSE = "ROSE"
    PERPETUAL = "PERPETUAL"
    WHALE = "WHALE"
    DAILYSCALP = "DAILYSCALP"
    TEST2 = "test2"
    TEST = "test"
    DARIUS = "darius"
    VEGAS = "VEGAS"
    JUSTIN = "JUSTIN"
    

class ChannelID(str, Enum):
    ROSE = "-1001527435167"
    PERPETUAL = "-1001765278507"
    WHALE = "-1001513983182"
    DAILYSCALP = "-1001527819844"
    VEGAS = "-1001676864542"
    SENTIMENT = "-1001653050413"
    JUSTIN = ""  # "-1001378498357"
