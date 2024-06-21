from services.EventBus import EventBus
from services.DataStore import DataStore

# Define a callback function to handle events
def handle_event(data):
    print(f"Event handled with data: {data}")

# Initialize EventBus and DataStore
event_bus = EventBus()
data_store = DataStore()

# Register an event
event_bus.register_event('test_event')

# Subscribe the callback to the event
event_bus.subscribe('test_event', handle_event)

# Update some data in DataStore which triggers an event
data_store.update_data('test_key', 'test_value')

# Emit the event manually
event_bus.emit('test_event', data={'key': 'test_key', 'value': 'test_value'})

# Unsubscribe the callback
event_bus.unsubscribe('test_event', handle_event)
