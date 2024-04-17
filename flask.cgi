
#!/usr/bin/env python3

import sys
import traceback

# Adding the specific path to sys.path to ensure the Python interpreter finds the required packages
sys.path.insert(0, '/misc/linux/centos7/x86_64/local/stow/python-3.6/lib/python3.6/site-packages/')

try:
    from wsgiref.handlers import CGIHandler
    from app import app
    CGIHandler().run(app)
except Exception as e:
    print("Content-Type: text/plain")
    print()  # This ensures the header is separated from the body by a blank line
    print("Failed to import the Flask app:")
    print(f"Exception type: {type(e)._name_}")
    print(f"Exception message: {str(e)}")
    print("Traceback:")
    
    # Capture the traceback and format it into a string, then print the string
    traceback_details = traceback.format_exc()
    print(traceback_details)