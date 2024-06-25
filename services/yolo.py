import yaml, cv2, os, pickle, time, sys, numpy as np, queue
from copy import deepcopy
from ultralytics import YOLO
import traceback
from data_structure.cooked_state_manager import CookedStateManager
from data_structure.event_bus import EventBus
# from ck_determiner.CookedStateDeterminer import CookedStateDeterminer
from data_structure.cooked_state_manager import CookedState
import queue
import traceback


class YOLOObjectDetector:
    def __init__(self, model, cooked_state_manager: CookedStateManager, event_bus: EventBus):

        self.model = YOLO(model)
        self.cooked_state_manager = cooked_state_manager
        # self.cooked_state_determiner = cooked_state_determiner
        self.event_bus = event_bus

    def draw_bounding_boxes(self, image, bounding_boxes, color):
        for box in bounding_boxes:
            points = np.array(box, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(image, [points], isClosed=True, color=color, thickness=2)

    def process_cake_image(self, orig_img, coords, id_):
        x1, y1, x2, y2, x3, y3, x4, y4 = coords
        if not self.cooked_state_manager.check_id(id_):
            cake = orig_img[min(y1, y2, y3, y4):max(y1, y2, y3, y4), min(x1, x2, x3, x4):max(x1, x2, x3, x4)]
            if cake.size == 0:
                raise ValueError("Extracted cake image is empty.")
            cooked_state = np.random.choice([CookedState.UNDERCOOKED, CookedState.COOKED, CookedState.OVERCOOKED])
            self.cooked_state_manager.add_id(id_, cooked_state)
            self.cooked_state_manager.update_counter(cooked_state)
        else:
            cooked_state = self.cooked_state_manager.get_cooked_state(id_)
        return cooked_state

    def get_color_based_on_state(self, cooked_state, undercooked_count, overcooked_count):
        if cooked_state == CookedState.UNDERCOOKED:
            undercooked_count += 1
            return (0, 0, 255), undercooked_count, overcooked_count
        elif cooked_state == CookedState.OVERCOOKED:
            overcooked_count += 1
            return (255, 0, 0), undercooked_count, overcooked_count
        return (0, 255, 0), undercooked_count, overcooked_count


    def check_for_events(self, undercooked_count, overcooked_count, total_detections):
        EVENT_THRESHOLD = 50
        if total_detections > 0:
            undercooked_percentage = (undercooked_count / total_detections) * 100
            overcooked_percentage = (overcooked_count / total_detections) * 100
            if overcooked_percentage > EVENT_THRESHOLD:
                self.event_bus.emit("raise_alarm_overcooked")
            if undercooked_percentage > EVENT_THRESHOLD:
                self.event_bus.emit("raise_alarm_undercooked")

    def process_detections(self, results, orig_img, start_time):
        THRESHOLD = 0.50
        total_detections = 0
        undercooked_count = 0
        overcooked_count = 0
        annotated_img = orig_img.copy()

        for result in results:
            all_info = result.obb
            no_of_box = len(all_info.xyxyxyxy)

            if no_of_box > 0:
                for box in all_info:
                    conf_ = str(box.conf.cpu().numpy()[0])
                    if float(conf_) < THRESHOLD:
                        continue
                    if box.xyxyxyxy.flatten().size == 0:
                        continue
                    total_detections += 1
                    coords = [int(coord) for coord in box.xyxyxyxy.flatten()]
                    if box.id is None:
                        continue
                    id_ = str(box.id.cpu().numpy()[0])
                    coords = [max(0, coord) for coord in coords]

                    cooked_state = self.process_cake_image(orig_img, coords, id_)
                    color, undercooked_count, overcooked_count = self.get_color_based_on_state(cooked_state, undercooked_count, overcooked_count)
                    self.draw_bounding_boxes(annotated_img, [coords], color)
                    cv2.putText(annotated_img, f"{id_} {conf_}", (coords[0], coords[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

        detection_time = time.time() - start_time #setup a logger later
        
        self.check_for_events(undercooked_count, overcooked_count, total_detections)

        return annotated_img

    def object_detection_yolo(self, num_array):
        original_shape = num_array.shape 
        orig_img = deepcopy(num_array)
        start_time = time.time()
      
        # Perform object detection using YOLO V8
        results = self.model.track(orig_img, device='cuda', persist=True)
        
        # Process detection results
        annotated_img = self.process_detections(results, orig_img, start_time)

        # Resize image to original shape and return
        return cv2.resize(annotated_img, (original_shape[1], original_shape[0]))