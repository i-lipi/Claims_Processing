#!/usr/bin/env python
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import json
import warnings
import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
from visionproj.crew import Visionproj

def run():
    """
    Run the crew.
    """
    try:
        
        inputs = json.loads(sys.stdin.read())
        extracted_text = inputs['extracted_text']     
           
        Visionproj().crew().kickoff(inputs={'extracted_text': extracted_text })
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    run()
    
    
    
    
    
