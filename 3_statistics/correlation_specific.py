
import pandas as pd
import statsmodels.formula.api as smf

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths

try:
    file_name = str(paths.DATASET)
    df = pd.read_excel(file_name)

    model = smf.ols("curvature ~ length_x", data=df).fit()

    print("--- Regression Result ---")
    print(model.summary())

except FileNotFoundError:
    print(f"Error: The file '{file_name}' was not found. Please check the file path.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
