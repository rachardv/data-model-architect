import sys
import os

# Set root directory in sys.path for all pytest modules
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
for sub in ["src", "forge"]:
    sub_path = os.path.join(root_dir, sub)
    if sub_path not in sys.path:
        sys.path.insert(0, sub_path)
