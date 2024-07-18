import os

def is_safe_path(allowed_base_directory: str, target_path: str) -> bool:
    # Normalize the paths to remove any '..' components
    normalized_allowed_base_directory = os.path.normpath(allowed_base_directory)
    normalized_target_path = os.path.normpath(target_path)
    
    # Convert the paths to absolute paths
    abs_allowed_base_directory = os.path.abspath(normalized_allowed_base_directory)
    abs_target_path = os.path.abspath(normalized_target_path)
    
    # Check if the resolved absolute path is within the base directory
    return os.path.commonpath([abs_target_path, abs_allowed_base_directory]) == abs_allowed_base_directory