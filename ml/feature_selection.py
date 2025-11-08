"""
Feature Selection and Engineering for IDS Project
Analyzes feature importance, correlations, and selects optimal features
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import (
    SelectKBest, f_classif, mutual_info_classif,
    RFE, RFECV
)
from sklearn.inspection import permutation_importance
import xgboost as xgb
import joblib
import json
from pathlib import Path
import logging
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# Import config and utils
from app.config import (
    MODELS_DIR, REPORTS_DIR, ATTACK_LABELS,
    USE_GPU, XGBOOST_PARAMS, CLASS_WEIGHTS
)
from ml.utils import (
    load_preprocessors, plot_feature_importance,
    check_gpu_availability
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureSelector:
    """Handles feature selection and analysis"""

    def __init__(self):
        self.feature_scores = {}
        self.selected_features = []
        self.feature_stats = {}
        self.correlation_matrix = None

    def load_preprocessed_data(self):
        """Load preprocessed data and preprocessors"""
        logger.info("Loading preprocessed data...")

        # Load preprocessors
        preprocessors = load_preprocessors(MODELS_DIR)

        # Load feature names
        self.feature_names = preprocessors['feature_names']
        self.config = preprocessors['config']

        logger.info(f"Loaded {len(self.feature_names)} features")
        return preprocessors

    def analyze_correlation(self, X, threshold=0.95):
        """
        Analyze feature correlations and identify highly correlated pairs

        Args:
            X: Feature matrix
            threshold: Correlation threshold for flagging

        Returns:
            List of highly correlated feature pairs
        """
        logger.info("Analyzing feature correlations...")

        # Calculate correlation matrix
        corr_matrix = pd.DataFrame(X).corr().abs()
        self.correlation_matrix = corr_matrix

        # Find highly correlated features
        upper_tri = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        # Find features to drop
        to_drop = []
        correlated_pairs = []

        for column in upper_tri.columns:
            if column in to_drop:
                continue

            # Find correlated features
            correlated = list(upper_tri.index[upper_tri[column] > threshold])

            if correlated:
                # Keep the first feature, drop the rest
                to_drop.extend(correlated)
                for corr_feat in correlated:
                    corr_value = upper_tri.loc[corr_feat, column]
                    correlated_pairs.append({
                        'feature1': self.feature_names[column],
                        'feature2': self.feature_names[corr_feat],
                        'correlation': float(corr_value)
                    })

        logger.info(f"Found {len(correlated_pairs)} highly correlated feature pairs (>{threshold})")
        logger.info(f"Features to potentially drop: {len(to_drop)}")

        return correlated_pairs, to_drop

    def random_forest_importance(self, X, y, n_estimators=100):
        """
        Calculate feature importance using Random Forest

        Args:
            X: Feature matrix
            y: Labels
            n_estimators: Number of trees

        Returns:
            Feature importance scores
        """
        logger.info(f"Calculating Random Forest feature importance...")

        # Train Random Forest
        rf = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )

        rf.fit(X, y)

        # Get feature importances
        importances = rf.feature_importances_

        # Create importance dataframe
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)

        self.feature_scores['random_forest'] = importance_df

        logger.info(f"Top 5 features by Random Forest:")
        for idx, row in importance_df.head().iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")

        return importance_df

    def xgboost_importance(self, X, y):
        """
        Calculate feature importance using XGBoost

        Args:
            X: Feature matrix
            y: Labels

        Returns:
            Feature importance scores
        """
        logger.info(f"Calculating XGBoost feature importance...")
        logger.info(f"Using GPU: {USE_GPU}")

        # Check classes present in y
        unique_classes = np.unique(y)
        logger.info(f"Classes in sample: {unique_classes}")

        # If not all classes are present, remap labels to be continuous
        if len(unique_classes) < 4 or not np.array_equal(unique_classes, np.arange(len(unique_classes))):
            logger.warning("Not all classes present or non-continuous labels detected. Remapping...")
            # Create label mapping
            label_map = {old: new for new, old in enumerate(sorted(unique_classes))}
            y_mapped = np.array([label_map[label] for label in y])

            # Adjust num_class parameter
            params = XGBOOST_PARAMS.copy()
            params['num_class'] = len(unique_classes)
            params['n_estimators'] = 100  # Reduce for feature selection

            # Create sample weights for mapped labels
            # Map back to original class weights where possible
            sample_weights = np.ones(len(y_mapped))
            for orig_label, new_label in label_map.items():
                mask = y_mapped == new_label
                sample_weights[mask] = CLASS_WEIGHTS.get(orig_label, 1.0)
        else:
            # All classes present and continuous
            params = XGBOOST_PARAMS.copy()
            params['n_estimators'] = 100  # Reduce for feature selection
            y_mapped = y
            sample_weights = np.array([CLASS_WEIGHTS[label] for label in y])

        # Train XGBoost
        xgb_model = xgb.XGBClassifier(**params)
        xgb_model.fit(X, y_mapped, sample_weight=sample_weights)

        # Get feature importances
        importances = xgb_model.feature_importances_

        # Create importance dataframe
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importances
        }).sort_values('importance', ascending=False)

        self.feature_scores['xgboost'] = importance_df

        logger.info(f"Top 5 features by XGBoost:")
        for idx, row in importance_df.head().iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")

        return importance_df

    def univariate_selection(self, X, y, k=20):
        """
        Univariate feature selection using ANOVA F-value

        Args:
            X: Feature matrix
            y: Labels
            k: Number of top features

        Returns:
            Selected feature indices and scores
        """
        logger.info(f"Performing univariate feature selection...")

        # ANOVA F-value
        selector = SelectKBest(f_classif, k=k)
        selector.fit(X, y)

        # Get scores
        scores = selector.scores_

        # Create dataframe
        univariate_df = pd.DataFrame({
            'feature': self.feature_names,
            'f_score': scores
        }).sort_values('f_score', ascending=False)

        self.feature_scores['univariate'] = univariate_df

        logger.info(f"Top 5 features by F-score:")
        for idx, row in univariate_df.head().iterrows():
            logger.info(f"  {row['feature']}: {row['f_score']:.2f}")

        return univariate_df

    def mutual_information(self, X, y):
        """
        Calculate mutual information scores

        Args:
            X: Feature matrix
            y: Labels

        Returns:
            Mutual information scores
        """
        logger.info("Calculating mutual information scores...")

        # Calculate MI scores
        mi_scores = mutual_info_classif(X, y, random_state=42)

        # Create dataframe
        mi_df = pd.DataFrame({
            'feature': self.feature_names,
            'mi_score': mi_scores
        }).sort_values('mi_score', ascending=False)

        self.feature_scores['mutual_info'] = mi_df

        logger.info(f"Top 5 features by Mutual Information:")
        for idx, row in mi_df.head().iterrows():
            logger.info(f"  {row['feature']}: {row['mi_score']:.4f}")

        return mi_df

    def aggregate_scores(self, weights=None):
        """
        Aggregate feature scores from different methods

        Args:
            weights: Dictionary of weights for each method

        Returns:
            Aggregated feature scores
        """
        logger.info("Aggregating feature scores...")

        if weights is None:
            weights = {
                'random_forest': 0.3,
                'xgboost': 0.4,
                'univariate': 0.15,
                'mutual_info': 0.15
            }

        # Normalize scores to 0-1 range
        aggregated = pd.DataFrame({'feature': self.feature_names})

        for method, df in self.feature_scores.items():
            if method in weights:
                # Normalize scores
                max_score = df.iloc[:, 1].max()
                min_score = df.iloc[:, 1].min()

                if max_score > min_score:
                    normalized = (df.iloc[:, 1] - min_score) / (max_score - min_score)
                else:
                    normalized = df.iloc[:, 1]

                # Add weighted scores
                df_normalized = df.copy()
                df_normalized['normalized_score'] = normalized * weights[method]

                # Merge with aggregated
                aggregated = aggregated.merge(
                    df_normalized[['feature', 'normalized_score']],
                    on='feature',
                    suffixes=('', f'_{method}')
                )
                aggregated.rename(
                    columns={'normalized_score': f'score_{method}'},
                    inplace=True
                )

        # Calculate final score
        score_columns = [col for col in aggregated.columns if col.startswith('score_')]
        aggregated['final_score'] = aggregated[score_columns].sum(axis=1)

        # Sort by final score
        aggregated = aggregated.sort_values('final_score', ascending=False)

        logger.info(f"Top 10 features by aggregated score:")
        for idx, row in aggregated.head(10).iterrows():
            logger.info(f"  {row['feature']}: {row['final_score']:.4f}")

        return aggregated

    def select_final_features(self, aggregated_scores, n_features=25):
        """
        Select final features based on aggregated scores

        Args:
            aggregated_scores: Aggregated feature scores
            n_features: Number of features to select

        Returns:
            List of selected feature names
        """
        # Get top features
        top_features = aggregated_scores.head(n_features)['feature'].tolist()

        # Ensure critical features are included
        critical_features = [
            ' Flow Duration',
            'Flow Bytes/s',
            ' Flow Packets/s',
            ' SYN Flag Count',
            ' ACK Flag Count'
        ]

        for feat in critical_features:
            if feat not in top_features and feat in self.feature_names:
                # Replace least important feature
                top_features[-1] = feat

        self.selected_features = top_features

        logger.info(f"Selected {len(top_features)} final features")

        return top_features

    def create_feature_mapping(self):
        """
        Create mapping from raw packet features to model features

        Returns:
            Feature mapping dictionary
        """
        logger.info("Creating feature mapping...")

        # Map packet-level features to CICIDS2017 features
        feature_mapping = {
            'packet_features': {
                'src_ip': 'Source IP address',
                'dst_ip': 'Destination IP address',
                'src_port': 'Source port',
                'dst_port': 'Destination port',
                'protocol': 'Protocol type',
                'packet_size': 'Packet size in bytes',
                'flags': 'TCP flags if applicable',
                'timestamp': 'Packet timestamp'
            },
            'flow_features': {
                ' Destination Port': 'dst_port',
                ' Flow Duration': 'flow_end_time - flow_start_time',
                'Flow Bytes/s': 'total_bytes / flow_duration',
                ' Flow Packets/s': 'total_packets / flow_duration',
                ' Total Fwd Packets': 'count(src->dst packets)',
                ' Total Backward Packets': 'count(dst->src packets)',
                'Total Length of Fwd Packets': 'sum(fwd packet sizes)',
                ' Total Length of Bwd Packets': 'sum(bwd packet sizes)',
                ' Fwd Packet Length Max': 'max(fwd packet sizes)',
                ' Fwd Packet Length Min': 'min(fwd packet sizes)',
                ' Fwd Packet Length Mean': 'mean(fwd packet sizes)',
                ' Bwd Packet Length Mean': 'mean(bwd packet sizes)',
                'FIN Flag Count': 'count(FIN flags)',
                ' SYN Flag Count': 'count(SYN flags)',
                ' RST Flag Count': 'count(RST flags)',
                ' PSH Flag Count': 'count(PSH flags)',
                ' ACK Flag Count': 'count(ACK flags)',
                ' URG Flag Count': 'count(URG flags)'
            },
            'selected_features': self.selected_features,
            'feature_indices': {
                feat: idx for idx, feat in enumerate(self.selected_features)
            }
        }

        return feature_mapping

    def save_results(self, aggregated_scores, feature_mapping):
        """
        Save feature selection results

        Args:
            aggregated_scores: Aggregated feature scores
            feature_mapping: Feature mapping dictionary
        """
        logger.info("Saving feature selection results...")

        # Save selected features
        selected_features_path = MODELS_DIR / "selected_features.json"
        with open(selected_features_path, 'w') as f:
            json.dump({
                'selected_features': self.selected_features,
                'n_features': len(self.selected_features),
                'timestamp': datetime.now().isoformat()
            }, f, indent=4)
        logger.info(f"  Selected features saved to {selected_features_path}")

        # Save feature scores
        scores_path = REPORTS_DIR / "feature_scores.csv"
        aggregated_scores.to_csv(scores_path, index=False)
        logger.info(f"  Feature scores saved to {scores_path}")

        # Save feature mapping
        mapping_path = MODELS_DIR / "feature_mapping.json"
        with open(mapping_path, 'w') as f:
            json.dump(feature_mapping, f, indent=4)
        logger.info(f"  Feature mapping saved to {mapping_path}")

        # Generate feature importance report
        self.generate_report(aggregated_scores)

    def generate_report(self, aggregated_scores):
        """
        Generate comprehensive feature selection report

        Args:
            aggregated_scores: Aggregated feature scores
        """
        report_path = REPORTS_DIR / "feature_selection_report.txt"

        with open(report_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("FEATURE SELECTION REPORT\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Total features analyzed: {len(self.feature_names)}\n")
            f.write(f"Features selected: {len(self.selected_features)}\n\n")

            f.write("TOP 25 FEATURES BY AGGREGATED SCORE:\n")
            f.write("-" * 40 + "\n")
            for idx, row in aggregated_scores.head(25).iterrows():
                f.write(f"{idx + 1:2d}. {row['feature']:40s} {row['final_score']:.4f}\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("FEATURE IMPORTANCE BY METHOD:\n")
            f.write("=" * 60 + "\n\n")

            for method, df in self.feature_scores.items():
                f.write(f"\n{method.upper()}:\n")
                f.write("-" * 40 + "\n")
                for i, (idx, row) in enumerate(df.head(10).iterrows()):
                    score_col = df.columns[1]
                    f.write(f"{i + 1:2d}. {row['feature']:40s} {row[score_col]:.4f}\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("SELECTED FEATURES FOR MODEL:\n")
            f.write("-" * 40 + "\n")
            for i, feat in enumerate(self.selected_features):
                f.write(f"{i + 1:2d}. {feat}\n")

        logger.info(f"  Report saved to {report_path}")

    def visualize_results(self, aggregated_scores):
        """
        Create visualizations for feature selection

        Args:
            aggregated_scores: Aggregated feature scores
        """
        logger.info("Creating visualizations...")

        # 1. Feature importance bar plot
        plt.figure(figsize=(12, 8))
        top_20 = aggregated_scores.head(20)
        plt.barh(range(len(top_20)), top_20['final_score'].values)
        plt.yticks(range(len(top_20)), top_20['feature'].values)
        plt.xlabel('Aggregated Importance Score')
        plt.title('Top 20 Features by Aggregated Importance')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / 'feature_importance_aggregated.png', dpi=150)
        plt.close()

        # 2. Method comparison heatmap
        if len(self.feature_scores) > 1:
            methods = list(self.feature_scores.keys())
            top_features = aggregated_scores.head(15)['feature'].tolist()

            # Create comparison matrix
            comparison_data = []
            for feat in top_features:
                feat_scores = []
                for method in methods:
                    df = self.feature_scores[method]
                    score = df[df['feature'] == feat].iloc[0, 1] if feat in df['feature'].values else 0
                    # Normalize
                    max_score = df.iloc[:, 1].max()
                    normalized = score / max_score if max_score > 0 else 0
                    feat_scores.append(normalized)
                comparison_data.append(feat_scores)

            # Plot heatmap
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                comparison_data,
                xticklabels=methods,
                yticklabels=top_features,
                annot=True,
                fmt='.3f',
                cmap='YlOrRd'
            )
            plt.title('Feature Importance Comparison Across Methods')
            plt.tight_layout()
            plt.savefig(REPORTS_DIR / 'feature_comparison_heatmap.png', dpi=150)
            plt.close()

        # 3. Correlation matrix for selected features (if available)
        if self.correlation_matrix is not None and len(self.selected_features) <= 30:
            selected_indices = [self.feature_names.index(f) for f in self.selected_features
                                if f in self.feature_names]

            selected_corr = self.correlation_matrix.iloc[selected_indices, selected_indices]

            plt.figure(figsize=(12, 10))
            mask = np.triu(np.ones_like(selected_corr, dtype=bool))
            sns.heatmap(
                selected_corr,
                mask=mask,
                annot=False,
                cmap='coolwarm',
                center=0,
                vmin=-1,
                vmax=1,
                xticklabels=self.selected_features,
                yticklabels=self.selected_features
            )
            plt.title('Correlation Matrix of Selected Features')
            plt.xticks(rotation=90)
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.savefig(REPORTS_DIR / 'selected_features_correlation.png', dpi=150)
            plt.close()

        logger.info(f"  Visualizations saved to {REPORTS_DIR}")


def main():
    """Main execution function"""

    logger.info("=" * 60)
    logger.info("FEATURE SELECTION PIPELINE")
    logger.info("=" * 60)

    # Check GPU
    gpu_info = check_gpu_availability()
    if gpu_info['gpu_available']:
        logger.info(f"GPU detected: {gpu_info['gpu_names']}")
    else:
        logger.info("No GPU detected, using CPU")

    # Initialize selector
    selector = FeatureSelector()

    # Load preprocessed data
    preprocessors = selector.load_preprocessed_data()

    # Load a sample of data for feature selection (use saved preprocessed data)
    logger.info("Loading sample data for feature selection...")

    # Note: In production, you would load the actual preprocessed X_train and y_train
    # For now, we'll create a sample dataset
    from ml.preprocess import DataPreprocessor

    preprocessor = DataPreprocessor()
    # Load 10% sample for feature selection
    df = preprocessor.load_data(sample_size=0.1)
    df = preprocessor.validate_data(df)
    X, y = preprocessor.encode_labels(df)

    # Check if all classes are present
    unique_classes = np.unique(y)
    if len(unique_classes) < 4:
        logger.warning(f"Sample only has {len(unique_classes)} classes. Loading more data...")
        # Load larger sample to ensure all classes
        df = preprocessor.load_data(sample_size=0.2)
        df = preprocessor.validate_data(df)
        X, y = preprocessor.encode_labels(df)
        unique_classes = np.unique(y)
        logger.info(f"New sample has {len(unique_classes)} classes: {unique_classes}")

    # Convert to numpy array
    X = X.values

    logger.info(f"Using {len(X):,} samples for feature selection")

    # 1. Correlation analysis
    correlated_pairs, to_drop = selector.analyze_correlation(X, threshold=0.95)

    # 2. Random Forest importance
    rf_importance = selector.random_forest_importance(X, y, n_estimators=50)

    # 3. XGBoost importance
    xgb_importance = selector.xgboost_importance(X, y)

    # 4. Univariate selection
    univariate_scores = selector.univariate_selection(X, y, k=30)

    # 5. Mutual information
    mi_scores = selector.mutual_information(X, y)

    # 6. Aggregate scores
    aggregated = selector.aggregate_scores()

    # 7. Select final features
    final_features = selector.select_final_features(aggregated, n_features=25)

    # 8. Create feature mapping
    feature_mapping = selector.create_feature_mapping()

    # 9. Save results
    selector.save_results(aggregated, feature_mapping)

    # 10. Create visualizations
    selector.visualize_results(aggregated)

    # Print summary
    print("\n" + "=" * 60)
    print("FEATURE SELECTION COMPLETE")
    print("=" * 60)
    print(f"Features selected: {len(final_features)}")
    print(f"Reports saved to: {REPORTS_DIR}")
    print(f"Models saved to: {MODELS_DIR}")
    print("\nTop 10 selected features:")
    for i, feat in enumerate(final_features[:10]):
        print(f"  {i + 1:2d}. {feat}")
    print("=" * 60)

    return selector


if __name__ == "__main__":
    selector = main()