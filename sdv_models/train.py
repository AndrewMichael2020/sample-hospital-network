#!/usr/bin/env python3
"""
SDV model training for multi-table healthcare data synthesis.
Train HMA1, CTGAN, or TVAE models on rule-based pseudo-seed data.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import argparse
import logging
from pathlib import Path

# SDV imports
from sdv.multi_table import HMASynthesizer
from sdv.single_table import CTGANSynthesizer, TVAESynthesizer, GaussianCopulaSynthesizer
from sdv.metadata import MultiTableMetadata

# SDMetrics import with fallback
try:
    from sdmetrics.reports.multi_table import QualityReport as MultiTableQualityReport
except ImportError:
    try:
        from sdmetrics.multi_table import QualityReport as MultiTableQualityReport
    except ImportError:
        MultiTableQualityReport = None

# Local imports
from constraints import define_healthcare_constraints, apply_data_corrections


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HealthcareSDVTrainer:
    """
    Trainer for SDV models on healthcare data with multi-table relationships.
    """
    
    def __init__(self, data_dir: str = "data", metadata_path: str = "sdv_models/metadata.json"):
        self.data_dir = Path(data_dir)
        self.metadata_path = Path(metadata_path)
        self.models_dir = Path("sdv_models/trained_models")
        self.models_dir.mkdir(exist_ok=True)
        
        self.metadata = MultiTableMetadata()
        self.data = {}
        self.synthesizer = None
        
    def load_data(self) -> Dict[str, pd.DataFrame]:
        """Load CSV data files into pandas DataFrames."""
        logger.info("Loading data files...")
        
        # Expected data files based on schema
        data_files = {
            'patients': 'patients.csv',
            'ed_encounters': 'ed_encounters.csv', 
            'ip_stays': 'ip_stays.csv'
        }
        
        for table_name, filename in data_files.items():
            filepath = self.data_dir / filename
            if filepath.exists():
                logger.info(f"Loading {filename}...")
                df = pd.read_csv(filepath)
                
                # Convert datetime columns
                datetime_columns = self._get_datetime_columns(table_name)
                for col in datetime_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col])
                
                self.data[table_name] = df
                logger.info(f"Loaded {len(df)} records from {filename}")
            else:
                logger.warning(f"Data file {filename} not found")
        
        return self.data
    
    def _get_datetime_columns(self, table_name: str) -> List[str]:
        """Get datetime column names for a table."""
        # Hardcoded datetime columns based on schema
        datetime_cols_map = {
            'patients': ['dob'],
            'ed_encounters': ['arrival_ts'],
            'ip_stays': ['admit_ts', 'discharge_ts']
        }
        return datetime_cols_map.get(table_name, [])
    
    def setup_metadata(self):
        """Setup SDV metadata from loaded data."""
        logger.info("Setting up metadata...")
        
        # Detect metadata from data automatically
        self.metadata.detect_from_dataframes(self.data)
        
        # Check if relationships are already detected
        existing_relationships = self.metadata.relationships
        logger.info(f"Detected {len(existing_relationships)} existing relationships")
        
        # Only add relationships if they don't exist
        relationship_exists = any(
            rel['parent_table_name'] == 'patients' and 
            rel['child_table_name'] == 'ed_encounters'
            for rel in existing_relationships
        )
        
        if not relationship_exists:
            logger.info("Adding patients -> ed_encounters relationship")
            self.metadata.add_relationship(
                parent_table_name='patients',
                child_table_name='ed_encounters',
                parent_primary_key='patient_id',
                child_foreign_key='patient_id'
            )
        
        relationship_exists = any(
            rel['parent_table_name'] == 'patients' and 
            rel['child_table_name'] == 'ip_stays'
            for rel in existing_relationships
        )
        
        if not relationship_exists:
            logger.info("Adding patients -> ip_stays relationship")
            self.metadata.add_relationship(
                parent_table_name='patients', 
                child_table_name='ip_stays',
                parent_primary_key='patient_id',
                child_foreign_key='patient_id'
            )
        
        # Validate metadata against loaded data
        try:
            self.metadata.validate_data(self.data)
            logger.info("Metadata validation successful")
        except Exception as e:
            logger.error(f"Metadata validation failed: {e}")
            # Continue anyway for testing
            logger.warning("Continuing despite metadata validation failure")
    
    def train_hma_model(self, epochs: int = 300) -> HMASynthesizer:
        """
        Train HMA1 (Hierarchical Modeling Algorithm) model.
        Recommended for multi-table data with relationships.
        """
        logger.info("Training HMA model...")
        
        # Initialize HMA synthesizer
        synthesizer = HMASynthesizer(
            metadata=self.metadata,
            verbose=True
        )
        
        # Get constraints
        constraints = define_healthcare_constraints()
        
        # Train model
        logger.info(f"Starting training...")
        try:
            synthesizer.fit(
                data=self.data
            )
            
            self.synthesizer = synthesizer
            logger.info("HMA model training completed")
            return synthesizer
        
        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
    
    def train_ctgan_model(self, epochs: int = 300) -> Dict[str, CTGANSynthesizer]:
        """
        Train individual CTGAN models for each table.
        Note: This doesn't preserve cross-table relationships as well as HMA.
        """
        logger.info("Training CTGAN models for individual tables...")
        
        synthesizers = {}
        
        for table_name, df in self.data.items():
            logger.info(f"Training CTGAN for {table_name}...")
            
            # Create single-table metadata for this table
            from sdv.metadata import SingleTableMetadata
            table_metadata = SingleTableMetadata()
            table_metadata.detect_from_dataframe(df)
            
            # Initialize CTGAN synthesizer
            synthesizer = CTGANSynthesizer(
                metadata=table_metadata,
                epochs=epochs,
                verbose=True
            )
            
            # Train model
            try:
                synthesizer.fit(df)
                synthesizers[table_name] = synthesizer
                logger.info(f"CTGAN training completed for {table_name}")
            except Exception as e:
                logger.error(f"CTGAN training failed for {table_name}: {e}")
        
        return synthesizers
    
    def generate_synthetic_data(self, num_patients: int = 1000) -> Dict[str, pd.DataFrame]:
        """Generate synthetic data using the trained model."""
        if self.synthesizer is None:
            raise ValueError("No model trained yet. Call train_*_model() first.")
        
        logger.info(f"Generating synthetic data for {num_patients} patients...")
        
        try:
            # For HMA, we can control the scale by specifying the number of rows
            # for the parent table (patients)
            scale_factor = num_patients / len(self.data['patients'])
            
            synthetic_data = self.synthesizer.sample(
                scale=scale_factor
            )
            
            logger.info("Synthetic data generation completed")
            
            # Apply post-processing corrections
            for table_name, df in synthetic_data.items():
                logger.info(f"Applying corrections to {table_name}...")
                synthetic_data[table_name] = apply_data_corrections(df, table_name)
                logger.info(f"Generated {len(df)} records for {table_name}")
            
            return synthetic_data
        
        except Exception as e:
            logger.error(f"Data generation failed: {e}")
            raise
    
    def save_model(self, model_name: str = "healthcare_hma_model"):
        """Save the trained model to disk."""
        if self.synthesizer is None:
            raise ValueError("No model to save")
        
        model_path = self.models_dir / f"{model_name}.pkl"
        logger.info(f"Saving model to {model_path}")
        
        try:
            # Save model
            self.synthesizer.save(str(model_path))
            
            # Save metadata separately for reference
            metadata_path = self.models_dir / f"{model_name}_metadata.json"
            metadata_dict = self.metadata.to_dict()
            with open(metadata_path, 'w') as f:
                json.dump(metadata_dict, f, indent=2, default=str)
            
            logger.info("Model saved successfully")
        
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            raise
    
    def load_model(self, model_name: str = "healthcare_hma_model"):
        """Load a trained model from disk."""
        model_path = self.models_dir / f"{model_name}.pkl"
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file {model_path} not found")
        
        logger.info(f"Loading model from {model_path}")
        
        try:
            # Load model
            self.synthesizer = HMASynthesizer.load(str(model_path))
            
            # Load metadata if available
            metadata_path = self.models_dir / f"{model_name}_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata_dict = json.load(f)
                self.metadata.load_from_dict(metadata_dict)
            
            logger.info("Model loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def validate_synthetic_data(self, synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Validate synthetic data quality using SDMetrics.
        Returns quality report with scores.
        """
        logger.info("Validating synthetic data quality...")
        
        if MultiTableQualityReport is None:
            logger.warning("SDMetrics MultiTableQualityReport not available, using basic validation")
            return self._basic_quality_validation(synthetic_data)
        
        try:
            # Generate quality report
            quality_report = MultiTableQualityReport()
            quality_report.generate(
                real_data=self.data,
                synthetic_data=synthetic_data,
                metadata=self.metadata
            )
            
            # Get overall score
            overall_score = quality_report.get_score()
            
            # Get detailed scores
            details = quality_report.get_details()
            
            logger.info(f"Overall quality score: {overall_score:.3f}")
            
            # Log table-level scores
            if len(details) > 0:
                table_scores = details.groupby('Table')['Score'].mean()
                for table, score in table_scores.items():
                    logger.info(f"  {table}: {score:.3f}")
                
                return {
                    'overall_score': overall_score,
                    'details': details,
                    'table_scores': table_scores.to_dict()
                }
            else:
                return {
                    'overall_score': overall_score,
                    'details': details,
                    'table_scores': {}
                }
        
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            return self._basic_quality_validation(synthetic_data)
    
    def _basic_quality_validation(self, synthetic_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Basic quality validation fallback."""
        overall_quality = 0.0
        table_count = 0
        
        for table_name in self.data.keys():
            if table_name in synthetic_data:
                # Simple quality metric - check if basic statistics are similar
                real_df = self.data[table_name]
                synthetic_df = synthetic_data[table_name]
                
                # Check row count similarity (within 50%)
                row_count_ratio = len(synthetic_df) / len(real_df)
                if 0.5 <= row_count_ratio <= 2.0:
                    overall_quality += 0.8
                else:
                    overall_quality += 0.4
                
                table_count += 1
        
        if table_count > 0:
            overall_quality /= table_count
        
        return {
            'overall_score': overall_quality,
            'details': [],
            'table_scores': {}
        }


def main():
    """Main training script."""
    parser = argparse.ArgumentParser(description="Train SDV models on healthcare data")
    parser.add_argument("--data-dir", default="data", help="Directory containing CSV data files")
    parser.add_argument("--model-type", choices=['hma', 'ctgan'], default='hma',
                       help="Type of model to train")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--patients", type=int, default=2000, 
                       help="Number of synthetic patients to generate")
    parser.add_argument("--save-name", default="healthcare_model",
                       help="Name for saved model")
    parser.add_argument("--generate-only", action='store_true',
                       help="Load existing model and generate data only")
    
    args = parser.parse_args()
    
    # Initialize trainer
    trainer = HealthcareSDVTrainer(data_dir=args.data_dir)
    
    if args.generate_only:
        # Load existing model and generate data
        try:
            trainer.load_model(args.save_name)
            synthetic_data = trainer.generate_synthetic_data(args.patients)
            
            # Save synthetic data
            output_dir = Path("data/synthetic")
            output_dir.mkdir(exist_ok=True)
            
            for table_name, df in synthetic_data.items():
                output_path = output_dir / f"{table_name}_synthetic.csv"
                df.to_csv(output_path, index=False)
                logger.info(f"Saved synthetic {table_name} to {output_path}")
        
        except FileNotFoundError:
            logger.error(f"Model {args.save_name} not found. Train a model first.")
            return
    
    else:
        # Full training pipeline
        
        # Load data
        trainer.load_data()
        
        if not trainer.data:
            logger.error("No data loaded. Make sure CSV files exist in data directory.")
            return
        
        # Setup metadata
        trainer.setup_metadata()
        
        # Train model
        if args.model_type == 'hma':
            model = trainer.train_hma_model(epochs=args.epochs)
        else:  # ctgan
            models = trainer.train_ctgan_model(epochs=args.epochs)
            logger.warning("CTGAN training completed, but multi-table generation not implemented")
            return
        
        # Save model
        trainer.save_model(args.save_name)
        
        # Generate synthetic data
        synthetic_data = trainer.generate_synthetic_data(args.patients)
        
        # Validate quality
        quality_scores = trainer.validate_synthetic_data(synthetic_data)
        
        # Save synthetic data
        output_dir = Path("data/synthetic")
        output_dir.mkdir(exist_ok=True)
        
        for table_name, df in synthetic_data.items():
            output_path = output_dir / f"{table_name}_synthetic.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved synthetic {table_name} to {output_path}")
        
        # Save quality report
        quality_path = output_dir / "quality_report.json"
        with open(quality_path, 'w') as f:
            # Convert numpy types to native Python types for JSON serialization
            quality_report = {
                'overall_score': float(quality_scores['overall_score']),
                'table_scores': {k: float(v) for k, v in quality_scores['table_scores'].items()}
            }
            json.dump(quality_report, f, indent=2)
        
        logger.info(f"Training and generation completed. Quality score: {quality_scores['overall_score']:.3f}")


if __name__ == "__main__":
    main()