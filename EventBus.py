import logging
from PyQt5.QtCore import QObject
import threading
from typing import Callable
import pathlib as path
import yaml

FILE_path = path.Path(__file__).parent.resolve()

class SingletonMeta(type):
    """ Metaclass for creating a Singleton instance. """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]

class EventBus(metaclass=SingletonMeta):
    """ A thread-safe singleton class for managing events and their subscribers across different channels. """
    def __init__(self):
        self._subscribers = {}
        self._channels = {}
        self._lock = threading.Lock()
        self.logger = logging.getLogger('EventBus')
        self.configure_logging()

    def configure_logging(self):
        """ Configure logging for the EventBus. """
        log_file_path = FILE_path / 'logs' / 'eventbus.log'
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        config_path = FILE_path / 'config.yaml'
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)

        debug_mode = config.get('START_MODE', 'LIVE') == 'BUILD'
        
        # Set up the file handler with appropriate formatter
        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s' if debug_mode else '%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        

    def register_event(self, event_name : str, channel : str = 'default'):
        """ 
        Info: Registers a new event with no subscribers in a specified channel. 
        Args:   
            event_name: str
            channel: str
        Returns:
            None
        """
        with self._lock:
            if channel not in self._subscribers:
                self._subscribers[channel] = {}
            if event_name not in self._subscribers[channel]:
                self._subscribers[channel][event_name] = []
            self.logger.info(f"Registered event '{event_name}' in channel '{channel}'.")

    def subscribe(self, event_name: str, callback: Callable, filter_func: Callable = None, priority: int = 100, channel: str = 'default'):
        """
        Info: Subscribes a callback function to an event in a specified channel, optionally with a filter function and priority. 
        Args:
            event_name: str
            callback: Callable (function)
            filter_func: Callable | None
            priority: int (default: 100)
            channel: str
        Returns:
            None
        """
        with self._lock:
            if channel not in self._subscribers:
                self._subscribers[channel] = {}
            if event_name not in self._subscribers[channel]:
                self.register_event(event_name, channel)
            self._subscribers[channel][event_name].append((callback, filter_func, priority))
            self._subscribers[channel][event_name].sort(key=lambda x: x[2])  # Sort by priority
            self.logger.info(f"Subscribed to event '{event_name}' in channel '{channel}' with priority {priority}.")

    def emit(self, event_name: str, channel: str = 'default', *args, **kwargs):
        """
        Info: Emits an event in a specified channel, invoking all subscribed callbacks that pass their filter function, in order of priority. 
        Args:
            event_name: str
            channel: str (default: 'default')
            *args: Any
            **kwargs: Any
        Returns:
            None
        """
        with self._lock:
            subscribers = self._subscribers.get(channel, {}).get(event_name, []).copy()
        for callback, filter_func, _ in subscribers:
            if filter_func is None or filter_func(*args, **kwargs):
                callback(*args, **kwargs)
        self.logger.info(f"Emitted event '{event_name}' in channel '{channel}' with args {args} and kwargs {kwargs}.")

    def unsubscribe(self, event_name: str, callback: Callable, channel: str = 'default'):
        """
        Info: Unsubscribes a callback from an event in a specified channel. 
        Args:
            event_name: str
            callback: Callable (function)
            channel: str (default: 'default')
        Returns:
            None
        """
        with self._lock:
            if channel in self._subscribers and event_name in self._subscribers[channel]:
                self._subscribers[channel][event_name] = [
                    (cb, filter, prio) for cb, filter, prio in self._subscribers[channel][event_name] if cb != callback
                ]
                self.logger.info(f"Unsubscribed from event '{event_name}' in channel '{channel}'.")

    def register_pyqt_event(self, qt_signal : QObject, event_name : str, channel : str = 'default'):
        """ 
        Info: Connects a PyQt signal to an EventBus event in a specified channel. 
        Args:
            qt_signal: PyQt signal
            event_name: str
            channel: str (default: 'default')
        Returns:
            None
        """
        def signal_emitter(*args, **kwargs):
            self.emit(event_name, *args, **kwargs, channel=channel)
        
        qt_signal.connect(signal_emitter)
        self.logger.info(f"Connected PyQt signal to event '{event_name}' in channel '{channel}'.")