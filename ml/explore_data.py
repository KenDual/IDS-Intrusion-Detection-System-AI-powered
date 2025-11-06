import pandas as pd
import numpy as np
import os
from collections import Counter


def load_all_data(data_dir='data'):
    """Load tất cả CSV files"""
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    print(f"Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {f}")

    dfs = []
    for file in csv_files:
        path = os.path.join(data_dir, file)
        print(f"\nLoading {file}...")
        df = pd.read_csv(path, encoding='latin1')
        dfs.append(df)

    # Merge all
    full_df = pd.concat(dfs, ignore_index=True)
    print(f"\n✓ Total records: {len(full_df):,}")

    return full_df


def explore_dataset(df):
    """Khám phá dataset"""

    print("\n" + "=" * 60)
    print("DATASET OVERVIEW")
    print("=" * 60)

    # 1. Shape
    print(f"\nShape: {df.shape}")
    print(f"  - Rows: {df.shape[0]:,}")
    print(f"  - Columns: {df.shape[1]}")

    # 2. Columns
    print(f"\n{df.shape[1]} Features:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")

    # 3. Label distribution
    print("\n" + "=" * 60)
    print("ATTACK TYPES DISTRIBUTION")
    print("=" * 60)

    label_col = ' Label'  # Có space ở đầu
    if label_col not in df.columns:
        label_col = 'Label'

    label_counts = df[label_col].value_counts()
    total = len(df)

    print(f"\n{'Attack Type':<30} {'Count':>10} {'Percentage':>12}")
    print("-" * 55)
    for label, count in label_counts.items():
        pct = (count / total) * 100
        print(f"{label:<30} {count:>10,} {pct:>11.2f}%")

    # 4. Missing values
    print("\n" + "=" * 60)
    print("MISSING VALUES")
    print("=" * 60)

    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]

    if len(missing_cols) > 0:
        print(f"\nColumns with missing values:")
        for col, count in missing_cols.items():
            pct = (count / len(df)) * 100
            print(f"  {col}: {count:,} ({pct:.2f}%)")
    else:
        print("\n✓ No missing values")

    # 5. Infinity values
    print("\n" + "=" * 60)
    print("INFINITY VALUES")
    print("=" * 60)

    inf_count = 0
    inf_cols = []

    for col in df.select_dtypes(include=[np.number]).columns:
        inf_in_col = np.isinf(df[col]).sum()
        if inf_in_col > 0:
            inf_count += inf_in_col
            inf_cols.append((col, inf_in_col))

    if inf_count > 0:
        print(f"\nTotal infinity values: {inf_count:,}")
        print(f"\nTop 10 columns with infinity:")
        for col, count in sorted(inf_cols, key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {col}: {count:,}")
    else:
        print("\n✓ No infinity values")

    # 6. Data types
    print("\n" + "=" * 60)
    print("DATA TYPES")
    print("=" * 60)

    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        print(f"  {dtype}: {count} columns")

    # 7. Sample data
    print("\n" + "=" * 60)
    print("SAMPLE DATA (First 3 rows)")
    print("=" * 60)
    print(df.head(3))

    return df


def analyze_features(df):
    """Phân tích features quan trọng"""

    print("\n" + "=" * 60)
    print("FEATURE CATEGORIES")
    print("=" * 60)

    # Phân loại features
    flow_features = [col for col in df.columns if 'Flow' in col]
    fwd_features = [col for col in df.columns if 'Fwd' in col or 'Forward' in col]
    bwd_features = [col for col in df.columns if 'Bwd' in col or 'Backward' in col]
    packet_features = [col for col in df.columns if 'Packet' in col]
    flag_features = [col for col in df.columns if
                     any(flag in col for flag in ['PSH', 'URG', 'FIN', 'SYN', 'RST', 'ACK'])]
    time_features = [col for col in df.columns if 'Time' in col or 'IAT' in col]

    print(f"\n1. Flow Features ({len(flow_features)}): Duration, Bytes/s, Packets/s")
    print(f"2. Forward Features ({len(fwd_features)}): Client → Server")
    print(f"3. Backward Features ({len(bwd_features)}): Server → Client")
    print(f"4. Packet Features ({len(packet_features)}): Length, Size")
    print(f"5. Flag Features ({len(flag_features)}): TCP Flags")
    print(f"6. Time Features ({len(time_features)}): IAT (Inter-Arrival Time)")

    # Top important features (theo research)
    print("\n" + "=" * 60)
    print("TOP 20 IMPORTANT FEATURES (Literature)")
    print("=" * 60)

    important = [
        'Flow Duration',
        'Total Fwd Packets',
        'Total Backward Packets',
        'Flow Bytes/s',
        'Flow Packets/s',
        'Fwd Packet Length Mean',
        'Bwd Packet Length Mean',
        'Flow IAT Mean',
        'Fwd IAT Mean',
        'Bwd IAT Mean',
        'PSH Flag Count',
        'URG Flag Count',
        'FIN Flag Count',
        'SYN Flag Count',
        'RST Flag Count',
        'ACK Flag Count',
        'Average Packet Size',
        'Subflow Fwd Bytes',
        'Subflow Bwd Bytes',
        'Init_Win_bytes_forward'
    ]

    for i, feat in enumerate(important, 1):
        # Tìm exact match hoặc gần đúng
        matching = [col for col in df.columns if feat.lower() in col.lower()]
        if matching:
            print(f"  {i:2d}. {matching[0]}")
        else:
            print(f"  {i:2d}. {feat} (not found)")


# def save_summary(df, output_file='data/dataset_summary.txt'):
#     """Save summary ra file"""
#
#     label_col = ' Label' if ' Label' in df.columns else 'Label'
#
#     with open(output_file, 'w') as f:
#         f.write("CICIDS2017 DATASET SUMMARY\n")
#         f.write("=" * 60 + "\n\n")
#
#         f.write(f"Total Records: {len(df):,}\n")
#         f.write(f"Total Features: {df.shape[1]}\n\n")
#
#         f.write("Attack Types:\n")
#         for label, count in df[label_col].value_counts().items():
#             pct = (count / len(df)) * 100
#             f.write(f"  {label:<30} {count:>10,} ({pct:>5.2f}%)\n")
#
#     print(f"\n✓ Summary saved to {output_file}")


def main():
    print("=" * 60)
    print("CICIDS2017 DATASET EXPLORATION")
    print("=" * 60)

    # Load data
    df = load_all_data('data')

    # Explore
    df = explore_dataset(df)

    # Analyze features
    analyze_features(df)

    # Save summary
    # save_summary(df)

    print("\n" + "=" * 60)
    print("✓ EXPLORATION COMPLETE")
    print("=" * 60)

    return df


if __name__ == "__main__":
    df = main()