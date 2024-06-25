from deepdiff import DeepDiff
import json
import numpy as np
from collections import OrderedDict
from deepdiff.model import PrettyOrderedSet
# Assuming PrettyOrderedSet is similar to OrderedDict for this example

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, PrettyOrderedSet):
            return list(obj)
        if isinstance(obj, OrderedDict):
            return list(obj.items())
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, DeepDiff):
            return obj.to_dict()
        return super().default(obj)
    
dict1 = json.load(open('template_crawler/vv8_logs/control/intersection_ctrl.json', 'r'))
dict2 = json.load(open('template_crawler/vv8_logs/ublock/actual/intersection_adb.json', 'r'))

# Find differences
diff = DeepDiff(dict1, dict2, ignore_order=True)
diff1 = DeepDiff(dict2, dict1, ignore_order=True)
print(type(diff))

json.dump(diff, open('deepdiff.out', 'w'),  cls=SetEncoder)
json.dump(diff1, open('deepdiff1.out', 'w'),  cls=SetEncoder)
