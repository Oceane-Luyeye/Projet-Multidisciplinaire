import os
import glob
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Full delivery pipeline: from input CSV to final PDF report."
    )
    parser.add_argument(
        'input_csv',
        help='Path to the input CSV file with delivery addresses'
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Paths to your existing scripts
    matrix_script = os.path.join(script_dir, 'merge.py')
    pdf_script    = os.path.join(script_dir, 'generation-pdf.py')

    # 1) Run the merge.py script to generate coordinates_*.csv and matrix_*.csv
    print("🚀 Running matrix generation (merge.py)...")
    subprocess.run(['python', matrix_script, args.input_csv], check=True)

    # 2) Discover the latest output files
    coords_pattern = os.path.join(script_dir, 'data/output/csv/coordinates_*.csv')
    matrix_pattern = os.path.join(script_dir, 'data/output/csv/matrix_*.csv')
    coords_files = glob.glob(coords_pattern)
    matrix_files = glob.glob(matrix_pattern)
    if not coords_files or not matrix_files:
        print("❌ No coordinates or matrix CSVs found.")
        return
    latest_coords = max(coords_files, key=os.path.getmtime)
    latest_matrix = max(matrix_files, key=os.path.getmtime)
    print(f"✔ Selected coords: {latest_coords}")
    print(f"✔ Selected matrix: {latest_matrix}")

    # 3) Run your PDF generation script (uses static paths inside)
    print("🚀 Running PDF generation (generation-pdf.py)...")
    subprocess.run([
        'python', pdf_script,
        '--matrix', latest_matrix,
        '--coords', latest_coords
    ], check=True)

    print("🎉 Pipeline completed. PDF: recapitulatif_globale.pdf")

if __name__ == '__main__':
    main()