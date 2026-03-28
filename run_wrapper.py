import sys
import traceback
import runpy

print("Running model training to catch exact Exception...")
try:
    runpy.run_path('src/model_training.py', run_name='__main__')
except Exception as e:
    with open('error_log.txt', 'w', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    print("Exception written to error_log.txt")
