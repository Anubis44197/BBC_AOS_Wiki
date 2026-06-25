import os
import sys
from collections import Counter

class DataProcessor:
    def __init__(self, size: int) -> None:
        self.size = size
        
    def filter_data(self, data: list) -> list:
        return [x for x in data if x is not None]

def global_handler(item):
    print("handling", item)