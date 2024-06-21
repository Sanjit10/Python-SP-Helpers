import threading
from EventBus import EventBus
from typing import Any
import logging
import pathlib as path
import yaml

FILE_path = path.Path(__file__).parent.resolve()


class SingletonMeta(type):
    """
    Metaclass for creating a Singleton instance.
    """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]



class DataStore(metaclass=SingletonMeta):
    """
    DataStore is a centralized state manager for a Python application.
    It manages variables in a thread-safe manner.
    """
    def __init__(self):
        self._data = {}
        self._event_bus = EventBus()
        self._lock = threading.Lock()
        self.configure_logging()
    
    def configure_logging(self):
        """
        Configure logging for the application.
        """
        log_file_path = FILE_path / 'logs' / 'DataStore.log'
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        config_path = FILE_path / 'config.yaml'
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Set up the logger
        self.logger = logging.getLogger('DataStore')
        debug_mode = config.get('START_MODE', 'LIVE') == 'BUILD'
        
        # Set up the file handler with appropriate formatter
        file_handler = logging.FileHandler(log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s' if debug_mode else '%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def update_data(self, key: str, value: Any):
        """
        INFO: Update or add the value associated with a given key in the _data dictionary.
        ARGS:
            key: str - The key to update or add to the _data dictionary.
            value: Any - The value to update or add to the _data dictionary.
        RETURNS:
            None
        """
        with self._lock:
            is_update = key in self._data
            self._data[key] = value
            action = 'update' if is_update else 'add'
            self.logger.info(f"{action.capitalize()} data: {key} = {value}")  # Log the action
            self._notify_data_updated(key, value, action)

    def get_data(self, key: str) -> Any:
        """
        INFO: Retrieve the value associated with a given key from the _data dictionary.
        ARGS:
            key: str - The key to retrieve the value from the _data dictionary.
        RETURNS:
            Any - The value associated with the given key, or None if the key does not exist.
        """
        with self._lock:
            if key not in self._data:
                self.logger.info(f"Attempted access to non-existent key: {key}")
                return None
            value = self._data.get(key)
            self.logger.info(f"Accessed data: {key} = {value}")  # Log data access
            return value

    def delete_data(self, key: str):
        """
        INFO: Delete the value associated with a given key from the _data dictionary.
        ARGS:
            key: str - The key to delete from the _data dictionary.
        RETURNS:
            None
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                self.logger.info(f"Deleted data: {key}")  # Log data deletion
                self._notify_data_updated(key, None, 'delete')
            else:
                raise ValueError(f"Key {key} does not exist.")


    def _notify_data_updated(self, key: str, data: Any, action: str):
        """
        INFO: Notify subscribers about data updates.
        ARGS:
            key: str - The key associated with the data update.
            data: Any - The updated data.
            action: str - The action performed on the data.
        RETURNS:
            None
        """
        data_info = {
            'action': action,
            'data': data
        }
        channel = 'data' + action
        self._event_bus.emit(event_name=key, data=data_info, channel=channel)
        self.logger.info(f"Notified subscribers about data update: {key} = {data}")
