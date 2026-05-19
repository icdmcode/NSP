# Code for "EGA-NSP: Efficient Negative Sequential Pattern Mining Based on Improved Genetic Algorithm"

This repository contains the source code for the paper submitted to ICDM 2026.

## Repository Structure

- GA-NSP.py              : Main implementation of the proposed EGA-NSP algorithm
- PrefixSpan.py          : PrefixSpan algorithm for positive sequential pattern mining
- PrefixSpan-eNSP.py     : Implementation of the e-NSP baseline method
- datasets/              : Folder containing all experimental datasets
- test/                  : Output folder for mined patterns (CSV files)

## Requirements

- Python 3.8+
- Required packages: psutil

Install psutil using pip:

    pip install psutil

## Usage

### Step 1: Mine Positive Sequential Patterns (PSP)

Run PrefixSpan.py:

    python PrefixSpan.py

Before running, modify the parameters in the main function:

    S = read("datasets/test.txt")  # Change to your dataset file
    min_sup = math.ceil(len(S) * 0.4)  # 0.4 = 40% as in the paper
    patterns = prefixSpan(sequencePattern([], sys.maxsize), S, min_sup)
    save_patterns_to_csv(patterns, "test/psp_list_test_0.4.csv")

### Step 2: Mine Negative Sequential Patterns (NSP)

#### Option A: Using e-NSP (Baseline)

Run PrefixSpan-eNSP.py:

    python PrefixSpan-eNSP.py

Modify the parameters:

    file_path = 'datasets/test.txt'
    dataset = read(file_path)
    file_path = 'test/psp_list_test_0.4.csv'
    psp_list = read_patterns_from_csv(file_path)
    min_sup = math.ceil(len(dataset) * 0.4)

#### Option B: Using EGA-NSP (Proposed Method)

Run GA-NSP.py:

    python GA-NSP.py

Modify the parameters:

    file_path = 'datasets/test.txt'
    dataset = read(file_path)
    file_path = 'test/psp_list_test_0.4.csv'
    psp_list = read_patterns_from_csv(file_path)
    min_sup = math.ceil(len(dataset) * 0.4)

GA parameters (in the function call):

    genetic_algorithm(
        psp_list,
        min_sup,
        population_size=500,     # Population size (P)
        num_generations=100,     # Number of iterations (G)
        mutation_rate=0.05,      # Mutation rate (M)
        crossover_rate=0.6,      # Crossover rate (C)
        k=50                     # Selection ratio (K, percentage)
    )

## GA Parameters (as defined in the paper)

Parameter         | Meaning              | Default Value | Description
------------------|----------------------|---------------|--------------------------------------------
population_size   | Population size (P)  | 500 (adaptive)| Avoids limiting the number of patterns
num_generations   | Iterations (G)       | 100           | Used for comparative experiments
crossover_rate    | Crossover rate (C)   | 0.6           | Balances exploration and exploitation
mutation_rate     | Mutation rate (M)    | 0.05          | Maintains population diversity
k                 | Selection ratio (K)  | 50            | Top-K selection strategy (percentage)

## Datasets

The datasets/ folder contains eight real-world datasets:

- BMS1.txt     : Clickstream data from e-commerce (KDD CUP 2000)
- BMS2.txt     : Clickstream data from e-commerce (KDD CUP 2000)
- FIFA.txt     : FIFA World Cup 98 website clickstream
- SIGN.txt     : Sign language utterance sequences
- BIKE.txt     : Bike sharing station sequences
- BIBLE.txt    : The Bible (each word as an item)
- LEVIATHAN.txt: Novel "Leviathan" by Thomas Hobbes
- MSNBC.txt    : MSNBC website clickstream
- test.txt     : Example dataset from Table I in the paper

Dataset format (SPMF standard):
- -1 separates items within a sequence
- -2 marks the end of a sequence

Example:
    a b c -2
    a (a b) -2

## Reproducibility

To reproduce the experimental results:

1. Run PrefixSpan.py for each dataset with the corresponding min_sup threshold
2. Run GA-NSP.py for each dataset with the same min_sup threshold

The code outputs:
- Total runtime (in milliseconds)
- Peak memory usage (in MB)
- Number of discovered NSPs

All results for EGA-NSP are averaged over 10 independent runs.

## License

This code is provided for review purposes only.

## Contact

For questions regarding the code, please refer to the paper.
