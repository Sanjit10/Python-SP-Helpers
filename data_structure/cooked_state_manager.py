class CookedState:
    UNDERCOOKED = 0
    COOKED = 1
    OVERCOOKED = 2

class CookedStateManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CookedStateManager, cls).__new__(cls)
            cls._instance.id_cooked_state = {}
            cls._instance.counter = {
                CookedState.UNDERCOOKED: 0,
                CookedState.COOKED: 0,
                CookedState.OVERCOOKED: 0
            }
        return cls._instance

    def add_id(self, id, cooked_state: CookedState):
        if not self.check_id(id):
            self.id_cooked_state[id] = cooked_state

    def check_id(self, id):
        return id in self.id_cooked_state

    def get_cooked_state(self, id):
        return self.id_cooked_state.get(id)

    def get_total_count(self):
        return self.counter[CookedState.COOKED] + self.counter[CookedState.UNDERCOOKED] + self.counter[CookedState.OVERCOOKED]
    
    def get_cooked_count(self):
        return self.counter[CookedState.COOKED]
    
    def get_undercooked_count(self):
        return self.counter[CookedState.UNDERCOOKED]
    
    def get_overcooked_count(self):
        return self.counter[CookedState.OVERCOOKED]
    
    def get_counter(self):
        return self.counter
    
    def update_counter(self, cooked_state):
        self.counter[cooked_state] += 1
    
    def get_good_count(self):
        return self.counter[CookedState.COOKED]
    
    def get_bad_count(self):
        return self.counter[CookedState.UNDERCOOKED] + self.counter[CookedState.OVERCOOKED]
    
    def reset_counter(self):
        self.counter = {
            CookedState.UNDERCOOKED: 0,
            CookedState.COOKED: 0,
            CookedState.OVERCOOKED: 0
        }
        self.id_cooked_state.clear()