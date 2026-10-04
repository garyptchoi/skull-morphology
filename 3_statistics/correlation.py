
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import paths


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

try:
    file_name = str(paths.DATASET)
    df = pd.read_excel(file_name)

    dimension_columns = ['length_x', 'width_y', 'height_z']
    for col in dimension_columns:
        if col not in df.columns:
            raise KeyError(f"The required column '{col}' was not found in your Excel file.")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Radius and Curvature vs. Object Dimensions with Linear Approximation', fontsize=16)

    max_radius = df['sphere_radius'].max() * 1.5
    max_curvature = df['curvature'].max() * 1.5
    
    sns.regplot(ax=axes[0, 0], data=df, x='length_x', y='sphere_radius')
    axes[0, 0].set_ylim(0, max_radius)
    axes[0, 0].set_title('Radius vs. Length')
    axes[0, 0].set_xlabel('Length (x)')
    axes[0, 0].set_ylabel('Radius')

    sns.regplot(ax=axes[0, 1], data=df, x='width_y', y='sphere_radius')
    axes[0, 1].set_ylim(0, max_radius)
    axes[0, 1].set_title('Radius vs. Width')
    axes[0, 1].set_xlabel('Width (y)')
    axes[0, 1].set_ylabel('Radius')

    sns.regplot(ax=axes[0, 2], data=df, x='height_z', y='sphere_radius')
    axes[0, 2].set_ylim(0, max_radius)
    axes[0, 2].set_title('Radius vs. Height')
    axes[0, 2].set_xlabel('Height (z)')
    axes[0, 2].set_ylabel('Radius')

    sns.regplot(ax=axes[1, 0], data=df, x='length_x', y='curvature')
    axes[1, 0].set_ylim(0, max_curvature)
    axes[1, 0].set_title('Curvature vs. Length')
    axes[1, 0].set_xlabel('Length (x)')
    axes[1, 0].set_ylabel('Curvature (1/Radius)')

    sns.regplot(ax=axes[1, 1], data=df, x='width_y', y='curvature')
    axes[1, 1].set_ylim(0, max_curvature)
    axes[1, 1].set_title('Curvature vs. Width')
    axes[1, 1].set_xlabel('Width (y)')
    axes[1, 1].set_ylabel('Curvature (1/Radius)')

    sns.regplot(ax=axes[1, 2], data=df, x='height_z', y='curvature')
    axes[1, 2].set_ylim(0, max_curvature)
    axes[1, 2].set_title('Curvature vs. Height')
    axes[1, 2].set_xlabel('Height (z)')
    axes[1, 2].set_ylabel('Curvature (1/Radius)')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plot_file = paths.output_dir(__file__) / 'combined_radius_curvature_plots.png'
    plt.savefig(plot_file)
    print(f"Combined scatter plots with linear regression saved as '{plot_file}'")
    print("\n" + "=" * 50 + "\n")


    print("--- Analysis for: sphere_radius ---")
    pearson_radius = df[['sphere_radius'] + dimension_columns].corr(method='pearson')
    print("Pearson Correlation (Linear):")
    print(pearson_radius)
    print("-" * 25)
    spearman_radius = df[['sphere_radius'] + dimension_columns].corr(method='spearman')
    print("Spearman Correlation (Monotonic):")
    print(spearman_radius)
    print("\n" + "=" * 50 + "\n")

    print("--- Analysis for: curvature ---")
    pearson_curvature = df[['curvature'] + dimension_columns].corr(method='pearson')
    print("Pearson Correlation (Linear):")
    print(pearson_curvature)
    print("-" * 25)
    spearman_curvature = df[['curvature'] + dimension_columns].corr(method='spearman')
    print("Spearman Correlation (Monotonic):")
    print(spearman_curvature)

except FileNotFoundError:
    print(f"Error: The file '{file_name}' was not found. Please check the file name and path.")
except KeyError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
