from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

FINCHES = DATA / "DF_and_their_relatives"
HONEYCREEPERS = DATA / "Honeycreepers_watertight"
CARDUELINES = DATA / "HC_Relatives_watertight"
PEROMYSCUS = DATA / "Peromyscus"
HUMAN = DATA / "Human_cranium"

DATASET = DATA / "Dataset.xlsx"
DATASET_TRAINING = DATA / "Dataset_training.xlsx"
DATASET_OTHER_TAXA = DATA / "Dataset_other_taxa.xlsx"

FIGURE_INPUTS = DATA / "figure_inputs"


def output_dir(script_file):
    script = Path(script_file).resolve()
    out = script.parent / "output" / script.stem
    out.mkdir(parents=True, exist_ok=True)
    return out
