import sys
import traceback

print("Testing app_config import...")
try:
    import app_config
    print(f"Module imported: {app_config}")
    print(f"Module file: {app_config.__file__}")
    print(f"Module dict: {list(vars(app_config).keys())}")
    print(f"Has FLASK_HOST: {hasattr(app_config, 'FLASK_HOST')}")
    if hasattr(app_config, 'FLASK_HOST'):
        print(f"FLASK_HOST value: {app_config.FLASK_HOST}")
    else:
        print("FLASK_HOST not found in module!")
        print("Trying to read file directly...")
        with open(app_config.__file__, 'r') as f:
            content = f.read()
            print(f"File length: {len(content)}")
            print(f"First 200 chars: {content[:200]}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

