
import cv2, pickle
import numpy as np
from data_structure.global_stateManager import DataStore
from data_structure.cooked_state_manager import CookedState
import pathlib as PIL

parent_dir = PIL.Path(__file__).parent.parent

class CookedStateDeterminer:
    _instance = None
    def __new__(cls, hist_size=180):
        if cls._instance is None:
            cls._instance = super(CookedStateDeterminer, cls).__new__(cls)
            cls._instance.hist_size = hist_size
            cls._instance.global_state_manager = DataStore()
            cls._instance.hsv_values = cls._instance.load_hsv_values_from_pickle()
            cls._instance.ref_histograms = cls._instance.initialize_reference_histograms()
            
        return cls._instance
    
    def load_hsv_values_from_pickle(self):
        brand_name = self.global_state_manager.get_dataclass_attribute('config_key', 'brand_name')
        pickle_path = parent_dir / 'Brands' / brand_name / 'pickle_values' / 'cake_hsv_highlighter.pkl'
        with open(pickle_path, 'rb') as file:
            hsv_values = pickle.load(file)
        return hsv_values

    def  generate_mask(self, image):
        hsv_ranges = self.hsv_values
        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        combined_mask = np.zeros(image.shape[:2], dtype=np.uint8)  # Ensure it's 8-bit

        for low, high in hsv_ranges:
            low_array = np.array(low)
            high_array = np.array(high)
            temp_mask = cv2.inRange(hsv_image, low_array, high_array)
            combined_mask = cv2.bitwise_or(combined_mask, temp_mask)

        return combined_mask

    def initialize_reference_histograms(self):
        reference_images = {
            'good': 'good',
            'over_cooked': 'over_cooked',
            'under_cooked': 'under_cooked'
        }

        # default images for initialization
        good = cv2.cvtColor(cv2.imread(r'data_structure\data\good\good1.png'), cv2.COLOR_BGR2RGB)
        over_cooked = cv2.cvtColor(cv2.imread(r'data_structure\data\over_cooked\over1.png'), cv2.COLOR_BGR2RGB)
        under_cooked = cv2.cvtColor(cv2.imread(r'data_structure\data\under_cooked\under1.png'), cv2.COLOR_BGR2RGB)

        self.global_state_manager.update_data('good_reference', good)
        self.global_state_manager.update_data('over_cooked_reference', over_cooked)
        self.global_state_manager.update_data('under_cooked_reference', under_cooked)

        ref_histograms = {}
        for state, image_name in reference_images.items():
            image = self.global_state_manager.get_data(image_name+'_reference')
            if image is None:
                raise ValueError("Provided image is None.")
            hsv_mask = self.generate_mask(image)
            histogram = self.calculate_hue_histogram(image, hsv_mask)
            if histogram is not None:
                ref_histograms[state] = histogram

        return ref_histograms

    def calculate_hue_histogram(self, image, hsv_mask):
        if image is None or image.size == 0:
            print("Empty or None image provided for histogram calculation.")
            return None

        hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        hue_hist = cv2.calcHist([hsv_image], [0], hsv_mask, [self.hist_size], [0, self.hist_size])
        cv2.normalize(hue_hist, hue_hist)
        return hue_hist.flatten()

    def calculate_chi_squared_distance(self, histA, histB, eps=1e-10):
        return 0.5 * np.sum(((a - b) ** 2) / (a + b + eps) for a, b in zip(histA, histB))

    def determine_cooked_state(self, image):

        if image is None:
            raise ValueError("Provided image is None.")
        
        hsv_mask = self.generate_mask(image)
        
        sample_hist = self.calculate_hue_histogram(image, hsv_mask)
        if sample_hist is None:
            raise ValueError("Provided sample histogram is None.")
        
        distances = {state: self.calculate_chi_squared_distance(sample_hist, ref_hist)
                     for state, ref_hist in self.ref_histograms.items()}
        state = min(distances, key=distances.get)

        if state is None: 
            raise ValueError("No state found.")
        
        cooked_state = {
            'good': CookedState.COOKED,
            'over_cooked': CookedState.OVERCOOKED,
            'under_cooked': CookedState.UNDERCOOKED
        }.get(state, None)

        return cooked_state, distances
    
    def update_reference_histograms(self):
        ref_histograms = {}
        reference_images = {
            'good': 'good',
            'over_cooked': 'over_cooked',
            'under_cooked': 'under_cooked'
        }
        for state, image_name in reference_images.items():
            image = self.global_state_manager.get_data(image_name+'_reference')
            histogram = self.calculate_hue_histogram(image)
            if histogram is not None:
                ref_histograms[state] = histogram
        self.ref_histograms = ref_histograms
        print("Reference histograms updated.")
