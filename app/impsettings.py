
import importlib.util
path = '../RouteCalc_data/settings.py'
spec = importlib.util.spec_from_file_location("settings", path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)
