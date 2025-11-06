# ml/prepare_clean_data.py
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import LabelEncoder

# ============================================================
# CONFIG
# ============================================================

SELECTED_CLASSES = [
    'BENIGN',
    'DoS Hulk',
    'PortScan',
    'DDoS'
]

# Dựa trên kết quả explore - chính xác tên columns
SELECTED_FEATURES = [
    # Core Flow Features (8)
    ' Destination Port',  # CÓ space
    ' Flow Duration',  # CÓ space
    'Flow Bytes/s',  # KHÔNG có space
    ' Flow Packets/s',  # CÓ space
    ' Total Fwd Packets',  # CÓ space
    ' Total Backward Packets',  # CÓ space
    'Total Length of Fwd Packets',  # KHÔNG có space
    ' Total Length of Bwd Packets',  # CÓ space

    # Packet Length (6)
    ' Fwd Packet Length Max',  # CÓ space
    ' Fwd Packet Length Min',  # CÓ space
    ' Fwd Packet Length Mean',  # CÓ space
    ' Bwd Packet Length Mean',  # CÓ space
    ' Average Packet Size',  # CÓ space
    ' Packet Length Mean',  # CÓ space

    # IAT - Timing (6)
    ' Flow IAT Mean',  # CÓ space
    ' Flow IAT Std',  # CÓ space
    ' Fwd IAT Mean',  # CÓ space
    ' Fwd IAT Std',  # CÓ space
    ' Bwd IAT Mean',  # CÓ space
    ' Bwd IAT Std',  # CÓ space

    # TCP Flags (6)
    'FIN Flag Count',  # KHÔNG có space
    ' SYN Flag Count',  # CÓ space
    ' RST Flag Count',  # CÓ space
    ' PSH Flag Count',  # CÓ space
    ' ACK Flag Count',  # CÓ space
    ' URG Flag Count',  # CÓ space

    # Header & Segment (4)
    ' Fwd Header Length',  # CÓ space
    ' Bwd Header Length',  # CÓ space
    ' Avg Fwd Segment Size',  # CÓ space
    ' Avg Bwd Segment Size',  # CÓ space

    # Subflow & Window (5)
    'Subflow Fwd Packets',  # KHÔNG có space
    ' Subflow Fwd Bytes',  # CÓ space
    ' Subflow Bwd Packets',  # CÓ space
    ' Subflow Bwd Bytes',  # CÓ space
    'Init_Win_bytes_forward',  # KHÔNG có space
    ' Init_Win_bytes_backward',  # CÓ space

    # Label
    ' Label'  # CÓ space
]


# ============================================================
# FUNCTIONS
# ============================================================

def load_all_data(data_dir='data'):
    """Load tất cả CSV files"""
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

    # Loại trừ cleaned_data.csv nếu đã tồn tại
    csv_files = [f for f in csv_files if f != 'cleaned_data.csv']

    print(f"Loading {len(csv_files)} CSV files...")
    dfs = []

    for file in csv_files:
        path = os.path.join(data_dir, file)
        df = pd.read_csv(path, encoding='latin1')
        dfs.append(df)
        print(f"  ✓ {file}: {len(df):,} rows")

    full_df = pd.concat(dfs, ignore_index=True)
    print(f"\n✓ Total: {len(full_df):,} rows")

    return full_df


def filter_classes(df, selected_classes):
    """Lọc chỉ giữ các classes cần thiết"""
    print(f"\nFiltering classes...")

    label_col = ' Label'
    original_count = len(df)

    # Filter
    df_filtered = df[df[label_col].isin(selected_classes)].copy()

    print(f"  Original: {original_count:,} rows")
    print(f"  Filtered: {len(df_filtered):,} rows")
    print(
        f"  Removed: {original_count - len(df_filtered):,} rows ({((original_count - len(df_filtered)) / original_count) * 100:.2f}%)")

    # Show distribution
    print(f"\n  Class distribution:")
    for cls in selected_classes:
        count = (df_filtered[label_col] == cls).sum()
        pct = (count / len(df_filtered)) * 100
        print(f"    {cls:<15} {count:>10,} ({pct:>5.2f}%)")

    return df_filtered


def select_features(df, selected_features):
    """Chọn các features cần thiết"""
    print(f"\nSelecting {len(selected_features)} features...")

    # Check features tồn tại
    missing_features = []
    available_features = []

    for feat in selected_features:
        if feat not in df.columns:
            missing_features.append(feat)
        else:
            available_features.append(feat)

    if missing_features:
        print(f"\n  ⚠️ Warning: {len(missing_features)} features not found:")
        for feat in missing_features:
            print(f"    - '{feat}'")

        print(f"\n  Attempting to find similar columns...")
        for feat in missing_features:
            # Tìm column tương tự (ignore spaces)
            feat_clean = feat.strip()
            for col in df.columns:
                if col.strip() == feat_clean:
                    print(f"    Found: '{feat}' → '{col}'")
                    available_features.append(col)
                    break

        if len(available_features) < len(selected_features) - 1:
            print(f"\n  ❌ Too many missing features. Cannot proceed.")
            return None

    df_selected = df[available_features].copy()
    print(f"  ✓ Selected: {df_selected.shape[1]} columns")

    return df_selected


def handle_infinity(df):
    """Xử lý infinity values"""
    print(f"\nHandling infinity values...")

    inf_count_before = 0
    inf_cols = []

    # Count infinity
    for col in df.select_dtypes(include=[np.number]).columns:
        inf_in_col = np.isinf(df[col]).sum()
        if inf_in_col > 0:
            inf_count_before += inf_in_col
            inf_cols.append((col, inf_in_col))

    print(f"  Found {inf_count_before:,} infinity values in {len(inf_cols)} columns")

    if inf_count_before > 0:
        # Replace infinity với max finite value của từng column
        for col, count in inf_cols:
            # Get max finite value
            finite_values = df[col][np.isfinite(df[col])]
            if len(finite_values) > 0:
                max_val = finite_values.max()
                df[col] = df[col].replace([np.inf, -np.inf], max_val)
                print(f"    ✓ {col}: {count:,} infinities → replaced with {max_val:.2f}")
            else:
                # Nếu toàn infinity, set = 0
                df[col] = df[col].replace([np.inf, -np.inf], 0)
                print(f"    ✓ {col}: {count:,} infinities → replaced with 0")
    else:
        print(f"  ✓ No infinity values found")

    return df


def handle_missing(df):
    """Xử lý missing values"""
    print(f"\nHandling missing values...")

    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]

    if len(missing_cols) > 0:
        print(f"  Found missing values in {len(missing_cols)} columns:")
        for col, count in missing_cols.items():
            pct = (count / len(df)) * 100
            print(f"    {col}: {count:,} ({pct:.2f}%)")

            # Fill với median cho numeric columns
            if df[col].dtype in ['int64', 'float64']:
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
                print(f"      → Filled with median: {median_val:.2f}")
    else:
        print(f"  ✓ No missing values")

    return df


def verify_data_quality(df):
    """Kiểm tra chất lượng data sau cleaning"""
    print(f"\n" + "=" * 60)
    print("DATA QUALITY CHECK")
    print("=" * 60)

    label_col = ' Label'

    # 1. Shape
    print(f"\nShape: {df.shape}")
    print(f"  Rows: {df.shape[0]:,}")
    print(f"  Columns: {df.shape[1]} ({df.shape[1] - 1} features + 1 label)")

    # 2. Missing values
    missing_total = df.isnull().sum().sum()
    print(f"\nMissing values: {missing_total}")

    # 3. Infinity values
    inf_count = 0
    for col in df.select_dtypes(include=[np.number]).columns:
        inf_count += np.isinf(df[col]).sum()
    print(f"Infinity values: {inf_count}")

    # 4. Data types
    print(f"\nData types:")
    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        print(f"  {dtype}: {count} columns")

    # 5. Label distribution
    print(f"\nLabel distribution:")
    for label, count in df[label_col].value_counts().items():
        pct = (count / len(df)) * 100
        print(f"  {label:<15} {count:>10,} ({pct:>5.2f}%)")

    # 6. Basic statistics
    print(f"\nNumeric features range:")
    numeric_cols = df.select_dtypes(include=[np.number]).columns[:5]
    for col in numeric_cols:
        print(f"  {col}: [{df[col].min():.2f}, {df[col].max():.2f}]")

    return df


def save_clean_data(df, output_path='data/cleaned_data.csv'):
    """Save cleaned data"""
    print(f"\nSaving cleaned data to {output_path}...")

    df.to_csv(output_path, index=False)

    # Check file size
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  ✓ Saved successfully")
    print(f"  File size: {file_size_mb:.2f} MB")

    return output_path


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("CREATING CLEAN DATASET")
    print("=" * 60)

    # 1. Load data
    df = load_all_data('data')

    # 2. Filter classes
    df = filter_classes(df, SELECTED_CLASSES)

    # 3. Select features
    df = select_features(df, SELECTED_FEATURES)

    if df is None:
        print("\n❌ Error: Feature selection failed")
        return

    # 4. Handle infinity
    df = handle_infinity(df)

    # 5. Handle missing
    df = handle_missing(df)

    # 6. Verify quality
    df = verify_data_quality(df)

    # 7. Save
    output_path = save_clean_data(df)

    print("\n" + "=" * 60)
    print("✓ CLEAN DATASET CREATED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nOutput: {output_path}")
    print(f"Records: {len(df):,}")
    print(f"Features: {df.shape[1] - 1} (+ 1 label)")
    print(f"Classes: {df[' Label'].nunique()}")

    return df


if __name__ == "__main__":
    df = main()