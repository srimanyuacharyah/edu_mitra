import pandas as pd

df = pd.read_excel('data/student_performance_enhanced.xlsx')
with open('data_info.txt', 'w', encoding='utf-8') as f:
    f.write("Columns: " + str(df.columns.tolist()) + "\n")
    for col in df.select_dtypes(include=['object']).columns:
        f.write(f"{col}: {list(df[col].unique())}\n")
    # Also write target values
    f.write("Missing: " + str(df.isnull().sum().to_dict()) + "\n")
