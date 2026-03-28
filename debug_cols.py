import pandas as pd
import sys

try:
    df = pd.read_excel('data/student_performance_enhanced.xlsx')
    with open('cols2.txt', 'w') as f:
        f.write(','.join(df.columns.astype(str)))
except Exception as e:
    with open('cols2.txt', 'w') as f:
        f.write('Error: ' + str(e))
