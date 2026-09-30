
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths

try:
    file_name = str(paths.DATASET)
    df = pd.read_excel(file_name)


    df_analysis = df.copy()
    df_analysis['1/curvature'] = df_analysis['sphere_radius']

    row_vars = ['ellipsoid_axis_a', 'ellipsoid_axis_b', 'ellipsoid_axis_c', '1/curvature', 'curvature']
    col_vars = ['length_x', 'width_y', 'height_z', '1/curvature', 'curvature']

    display_cols = ['length x', 'width y', 'height z', '1/curvature', 'curvature']

    all_needed_vars = list(set(row_vars + col_vars))
    missing_cols = [col for col in all_needed_vars if col not in df_analysis.columns]

    if missing_cols:
        print("--- Error: Cannot Generate Correlation Table ---")
        print("Your Excel file is missing the following required columns:")
        for col in missing_cols:
            if col != '1/curvature':
                print(f"- {col}")
    else:
        print("--- Combined Pearson Correlation Matrix (Linear) ---")

        corr_matrix_pearson = df_analysis[all_needed_vars].corr(method='pearson')

        final_table_pearson = corr_matrix_pearson.loc[row_vars, col_vars]

        final_table_pearson.columns = display_cols
        final_table_pearson.index.name = 'Variable'

        print(tabulate(final_table_pearson, headers='keys', tablefmt='psql', floatfmt=".2f"))

        print("\n" + "=" * 50 + "\n")
        print("--- Combined Spearman Correlation Matrix (Monotonic) ---")

        corr_matrix_spearman = df_analysis[all_needed_vars].corr(method='spearman')

        final_table_spearman = corr_matrix_spearman.loc[row_vars, col_vars]

        final_table_spearman.columns = display_cols
        final_table_spearman.index.name = 'Variable'

        print(tabulate(final_table_spearman, headers='keys', tablefmt='psql', floatfmt=".2f"))


except FileNotFoundError:
    print(f"Error: The file '{file_name}' was not found. Please check the file name and path.")
except KeyError as e:
    print(f"Error: A required column was not found. {e}")
except ImportError:
    print("Error: The 'tabulate' library is required. Please install it using: pip install tabulate")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
