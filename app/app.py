import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Append parent directory

from services.DataStore import DataStore
from services.EventBus import EventBus

class App:
    def __init__(self):
        self.data_store = DataStore()
        self.event_bus = EventBus()
    def main(self):
        pass


if __name__ == '__main__':
    app = App()
    app.main()
