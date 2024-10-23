import importlib
import time


def timed_import(module_name, attribute_name=None):
    """Function to measure the time taken to import a module or attribute."""
    start_time = time.perf_counter()
    
    # Import the module using importlib
    module = importlib.import_module(module_name)
    
    # If an attribute (like a class or function) is specified, retrieve it
    if attribute_name:
        imported_obj = getattr(module, attribute_name)
        print(f"Imported {attribute_name} from {module_name} in {time.perf_counter() - start_time:.4f} seconds.")
        return imported_obj
    
    print(f"Imported {module_name} in {time.perf_counter() - start_time:.4f} seconds.")
    return module