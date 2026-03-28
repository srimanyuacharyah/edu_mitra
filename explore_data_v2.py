import pandas as pd
import os

df = pd.read_excel(r'c:\Users\Lenovo\edu_mitra\data\student_performance_enhanced.xlsx')
print(df.columns)
print(df.head())
print(df.dtypes)
