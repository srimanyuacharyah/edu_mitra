import pandas as pd
df = pd.read_excel('data/student_performance_enhanced.xlsx')
print(df.columns.tolist())
print(df.head(2))
