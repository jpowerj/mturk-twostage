import sys

import pandas as pd

def main():
    num_hits = int(sys.argv[1])
    df = pd.DataFrame()
    df['hit_id'] = [f'P01_{str(hnum).zfill(2)}' for hnum in range(num_hits)]
    output_fpath = f"pilot_input_{num_hits}.csv"
    df.to_csv(output_fpath, index=False)
    print(f"Saved to {output_fpath}.")

if __name__ == "__main__":
    main()