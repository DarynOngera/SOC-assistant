#!/usr/bin/env python3
"""
CSV File Processing and Anomaly Detection
Handles CSV file uploads, validation, processing, and report generation
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
import uuid
import io
import base64
from pathlib import Path

# Set matplotlib backend for headless environments
import matplotlib
matplotlib.use('Agg')

def json_serializer(obj):
    """Custom JSON serializer for numpy data types"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    return str(obj)

class CSVProcessor:
    """
    Handles CSV file processing for anomaly detection
    """
    
    def __init__(self, detector=None, upload_dir="uploads", reports_dir="reports"):
        self.detector = detector
        self.upload_dir = Path(upload_dir)
        self.reports_dir = Path(reports_dir)
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Supported file formats
        self.supported_formats = ['.csv']
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_rows = 100000  # Maximum rows to process
        
    def validate_csv_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate uploaded CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return False, f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({self.max_file_size / 1024 / 1024:.1f}MB)"
            
            # Check file extension
            if not file_path.lower().endswith('.csv'):
                return False, "File must be a CSV file"
            
            # Try to read the CSV file
            try:
                df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows to validate
                if df.empty:
                    return False, "CSV file is empty"
                
                # Check minimum columns
                if len(df.columns) < 5:
                    return False, "CSV file must have at least 5 columns for meaningful analysis"
                    
            except pd.errors.EmptyDataError:
                return False, "CSV file is empty or corrupted"
            except pd.errors.ParserError as e:
                return False, f"CSV parsing error: {str(e)}"
            except Exception as e:
                return False, f"Error reading CSV file: {str(e)}"
            
            return True, "File is valid"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def preprocess_csv_data(self, file_path: str, sample_size: Optional[int] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Preprocess CSV data for anomaly detection
        
        Args:
            file_path: Path to the CSV file
            sample_size: Optional limit on number of rows to process
            
        Returns:
            Tuple of (processed_dataframe, metadata)
        """
        print(f"Preprocessing CSV file: {file_path}")
        
        # Load data with chunked reading for large files
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        if file_size_mb > 50:  # Use chunked reading for files > 50MB
            chunks = []
            chunk_size = 10000
            rows_read = 0
            
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                chunks.append(chunk)
                rows_read += len(chunk)
                
                if sample_size and rows_read >= sample_size:
                    break
                if rows_read >= self.max_rows:
                    break
                    
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(file_path)
            
        # Apply sampling if needed
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            
        # Limit to max_rows
        if len(df) > self.max_rows:
            df = df.head(self.max_rows)
            
        original_shape = df.shape
        
        # Basic preprocessing
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Fill missing values
        for col in numeric_cols:
            df[col] = df[col].fillna(df[col].median())
            
        for col in categorical_cols:
            mode_val = df[col].mode()
            fill_val = mode_val.iloc[0] if not mode_val.empty else 'unknown'
            df[col] = df[col].fillna(fill_val)
        
        # Convert categorical to numeric (simple label encoding)
        for col in categorical_cols:
            if col.lower() not in ['label', 'attack_cat', 'timestamp']:
                try:
                    df[col] = pd.Categorical(df[col]).codes
                except:
                    # If conversion fails, keep as is
                    pass
        
        # Create metadata
        metadata = {
            'original_shape': original_shape,
            'processed_shape': df.shape,
            'numeric_columns': list(numeric_cols),
            'categorical_columns': list(categorical_cols),
            'file_size_mb': file_size_mb,
            'preprocessing_timestamp': datetime.now().isoformat()
        }
        
        print(f"Preprocessed data shape: {df.shape}")
        return df, metadata
    
    def detect_anomalies(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform anomaly detection on the processed data
        
        Args:
            df: Preprocessed DataFrame
            metadata: Preprocessing metadata
            
        Returns:
            Dictionary containing anomaly detection results
        """
        print("Performing anomaly detection...")
        
        results = {
            'total_records': len(df),
            'anomalies_detected': 0,
            'anomaly_percentage': 0.0,
            'predictions': [],
            'anomaly_scores': [],
            'feature_importance': {},
            'detection_timestamp': datetime.now().isoformat(),
            'model_used': 'mock' if not self.detector else 'trained'
        }
        
        try:
            if self.detector and hasattr(self.detector, 'models') and self.detector.models:
                # Use trained models for prediction
                results.update(self._detect_with_trained_models(df))
            else:
                # Use mock detection for demonstration
                results.update(self._detect_with_mock_model(df))
                
        except Exception as e:
            print(f"Error in anomaly detection: {e}")
            # Fallback to mock detection
            results.update(self._detect_with_mock_model(df))
            results['error'] = str(e)
        
        return results
    
    def _detect_with_trained_models(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform anomaly detection using trained ML models via shared detector instance
        
        Args:
            df: Preprocessed DataFrame
            
        Returns:
            Dictionary with detection results
        """
        try:
            # Use the detector's batch prediction method for consistency with live data
            batch_results = self.detector.predict_batch(df)
            
            predictions = batch_results['predictions']
            anomaly_scores = batch_results['anomaly_scores']
            confidences = batch_results.get('confidences', [])
            
            # Calculate statistics
            total_records = len(predictions)
            anomalies_detected = sum(predictions)
            anomaly_percentage = (anomalies_detected / total_records) * 100
            
            # Get anomaly indices and scores
            anomaly_indices = [i for i, pred in enumerate(predictions) if pred == 1]
            anomaly_records = df.iloc[anomaly_indices].to_dict('records') if anomaly_indices else []
            
            # Add confidence scores to anomaly records
            for i, record in enumerate(anomaly_records):
                if i < len(anomaly_indices):
                    idx = anomaly_indices[i]
                    record['anomaly_score'] = anomaly_scores[idx] if idx < len(anomaly_scores) else 0.5
                    record['confidence'] = confidences[idx] if idx < len(confidences) else 0.5
            
            # Calculate severity distribution based on anomaly scores
            severity_distribution = self._calculate_severity_distribution(anomaly_scores, predictions)
            
            return {
                'method': 'trained_models',
                'model_info': {
                    'model_used': batch_results.get('model_used', 'unknown'),
                    'feature_importance': batch_results.get('feature_importance', {}),
                    'total_features': len(df.columns),
                    'model_ready': True
                },
                'total_records': total_records,
                'anomalies_detected': anomalies_detected,
                'anomaly_percentage': round(anomaly_percentage, 2),
                'normal_records': total_records - anomalies_detected,
                'anomaly_indices': anomaly_indices,
                'anomaly_scores': anomaly_scores,
                'confidences': confidences,
                'predictions': predictions,
                'severity_distribution': severity_distribution,
                'anomaly_records': anomaly_records[:10],  # Limit to first 10 for report
                'average_confidence': round(sum(confidences) / len(confidences), 3) if confidences else 0.5
            }
            
        except Exception as e:
            print(f"Error in trained model detection: {e}")
            # Fallback to mock detection
            return self._detect_with_mock_model(df)
    
    def _detect_with_mock_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform mock anomaly detection for demonstration purposes
        
        Args:
            df: Preprocessed DataFrame
            
        Returns:
            Dictionary with mock detection results
        """
        try:
            total_records = len(df)
            
            # Generate mock predictions (simulate ~5-15% anomaly rate)
            np.random.seed(42)  # For reproducible results
            anomaly_rate = np.random.uniform(0.05, 0.15)
            num_anomalies = int(total_records * anomaly_rate)
            
            # Create predictions array
            predictions = [0] * total_records
            anomaly_indices = np.random.choice(total_records, num_anomalies, replace=False)
            for idx in anomaly_indices:
                predictions[idx] = 1
            
            # Generate mock anomaly scores
            anomaly_scores = []
            for i in range(total_records):
                if predictions[i] == 1:
                    # Anomalies get higher scores (0.5-1.0)
                    score = np.random.uniform(0.5, 1.0)
                else:
                    # Normal records get lower scores (0.0-0.6)
                    score = np.random.uniform(0.0, 0.6)
                anomaly_scores.append(float(score))
            
            # Generate mock confidences
            confidences = [np.random.uniform(0.6, 0.95) for _ in range(total_records)]
            
            # Get anomaly records
            anomaly_records = df.iloc[list(anomaly_indices)].to_dict('records') if num_anomalies > 0 else []
            
            # Add scores to anomaly records
            for i, record in enumerate(anomaly_records):
                if i < len(anomaly_indices):
                    idx = anomaly_indices[i]
                    record['anomaly_score'] = anomaly_scores[idx]
                    record['confidence'] = confidences[idx]
            
            # Calculate severity distribution
            severity_distribution = self._calculate_severity_distribution(anomaly_scores, predictions)
            
            return {
                'method': 'mock_detection',
                'model_info': {
                    'model_used': 'mock',
                    'feature_importance': self._generate_mock_feature_importance(df.columns),
                    'total_features': len(df.columns),
                    'model_ready': False
                },
                'total_records': total_records,
                'anomalies_detected': num_anomalies,
                'anomaly_percentage': round((num_anomalies / total_records) * 100, 2),
                'normal_records': total_records - num_anomalies,
                'anomaly_indices': list(anomaly_indices),
                'anomaly_scores': anomaly_scores,
                'confidences': confidences,
                'predictions': predictions,
                'severity_distribution': severity_distribution,
                'anomaly_records': anomaly_records[:10],  # Limit to first 10
                'average_confidence': round(sum(confidences) / len(confidences), 3) if confidences else 0.5
            }
            
        except Exception as e:
            print(f"Error in mock detection: {e}")
            # Return minimal results if even mock detection fails
            return {
                'method': 'fallback',
                'total_records': len(df),
                'anomalies_detected': 0,
                'anomaly_percentage': 0.0,
                'predictions': [0] * len(df),
                'anomaly_scores': [0.1] * len(df),
                'error': str(e)
            }
    
    def _calculate_severity_distribution(self, anomaly_scores: List[float], predictions: List[int]) -> Dict[str, int]:
        """Calculate severity distribution based on anomaly scores"""
        high_severity = 0
        medium_severity = 0
        low_severity = 0
        
        for i, score in enumerate(anomaly_scores):
            if predictions[i] == 1:  # Only count actual anomalies
                if score >= 0.8:
                    high_severity += 1
                elif score >= 0.6:
                    medium_severity += 1
                else:
                    low_severity += 1
        
        return {
            'high': high_severity,
            'medium': medium_severity,
            'low': low_severity
        }
    
    def _generate_mock_feature_importance(self, columns: List[str]) -> Dict[str, float]:
        """Generate mock feature importance scores"""
        importance = {}
        np.random.seed(42)
        
        for col in columns:
            # Generate random importance scores
            importance[str(col)] = float(np.random.uniform(0.1, 1.0))
        
        return importance
    
    def generate_report(self, file_info: Dict[str, Any], preprocessing_metadata: Dict[str, Any], 
                       detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive anomaly detection report
        
        Args:
            file_info: Information about the uploaded file
            preprocessing_metadata: Data preprocessing metadata
            detection_results: Anomaly detection results
            
        Returns:
            Dictionary containing the complete report
        """
        print("Generating anomaly detection report...")
        
        report_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Create visualizations
        visualizations = self._create_visualizations(detection_results, report_id)
        
        # Generate summary statistics
        summary_stats = self._generate_summary_stats(detection_results)
        
        # Create detailed analysis
        detailed_analysis = self._create_detailed_analysis(detection_results, preprocessing_metadata)
        
        # Compile final report
        report = {
            'report_id': report_id,
            'timestamp': timestamp.isoformat(),
            'file_info': file_info,
            'preprocessing_metadata': preprocessing_metadata,
            'detection_results': detection_results,
            'summary_statistics': summary_stats,
            'detailed_analysis': detailed_analysis,
            'visualizations': visualizations,
            'recommendations': self._generate_recommendations(detection_results),
            'report_version': '1.0'
        }
        
        # Save report to file
        report_path = self.reports_dir / f"anomaly_report_{report_id}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=json_serializer)
        
        print(f"Report saved to: {report_path}")
        return report
    
    def _create_visualizations(self, detection_results: Dict[str, Any], report_id: str) -> Dict[str, str]:
        """Create visualization plots and return base64 encoded images"""
        visualizations = {}
        
        try:
            # Set style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # 1. Anomaly Score Distribution
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Anomaly Detection Analysis', fontsize=16, fontweight='bold')
            
            scores = detection_results['anomaly_scores']
            predictions = detection_results['predictions']
            
            # Anomaly score histogram
            axes[0, 0].hist(scores, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 0].axvline(x=0.5, color='red', linestyle='--', label='Threshold (0.5)')
            axes[0, 0].set_xlabel('Anomaly Score')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].set_title('Distribution of Anomaly Scores')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Anomaly vs Normal counts
            labels = ['Normal', 'Anomaly']
            counts = [len(scores) - sum(predictions), sum(predictions)]
            colors = ['lightgreen', 'lightcoral']
            axes[0, 1].pie(counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            axes[0, 1].set_title('Normal vs Anomaly Distribution')
            
            # Feature importance (top 10)
            if detection_results['feature_importance']:
                feature_imp = detection_results['feature_importance']
                top_features = sorted(feature_imp.items(), key=lambda x: x[1], reverse=True)[:10]
                if top_features:
                    features, importance = zip(*top_features)
                    y_pos = np.arange(len(features))
                    axes[1, 0].barh(y_pos, importance, color='lightblue')
                    axes[1, 0].set_yticks(y_pos)
                    axes[1, 0].set_yticklabels(features)
                    axes[1, 0].set_xlabel('Importance Score')
                    axes[1, 0].set_title('Top 10 Feature Importance')
                    axes[1, 0].grid(True, alpha=0.3)
            else:
                axes[1, 0].text(0.5, 0.5, 'Feature importance\nnot available', 
                               ha='center', va='center', transform=axes[1, 0].transAxes)
                axes[1, 0].set_title('Feature Importance')
            
            # Time series of anomaly scores (if we have enough data points)
            if len(scores) > 10:
                sample_indices = np.linspace(0, len(scores)-1, min(100, len(scores)), dtype=int)
                sampled_scores = [scores[i] for i in sample_indices]
                axes[1, 1].plot(sample_indices, sampled_scores, marker='o', markersize=3, alpha=0.7)
                axes[1, 1].axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Threshold')
                axes[1, 1].set_xlabel('Sample Index')
                axes[1, 1].set_ylabel('Anomaly Score')
                axes[1, 1].set_title('Anomaly Scores Over Samples')
                axes[1, 1].legend()
                axes[1, 1].grid(True, alpha=0.3)
            else:
                axes[1, 1].text(0.5, 0.5, 'Insufficient data\nfor time series', 
                               ha='center', va='center', transform=axes[1, 1].transAxes)
                axes[1, 1].set_title('Anomaly Scores Over Time')
            
            plt.tight_layout()
            
            # Save plot to base64
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close()
            
            visualizations['main_analysis'] = img_base64
            
            # Save plot file
            plot_path = self.reports_dir / f"anomaly_analysis_{report_id}.png"
            with open(plot_path, 'wb') as f:
                f.write(base64.b64decode(img_base64))
            
        except Exception as e:
            print(f"Error creating visualizations: {e}")
            visualizations['error'] = str(e)
        
        return visualizations
    
    def _generate_summary_stats(self, detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics"""
        scores = detection_results['anomaly_scores']
        predictions = detection_results['predictions']
        
        return {
            'total_records_analyzed': detection_results['total_records'],
            'anomalies_detected': detection_results['anomalies_detected'],
            'anomaly_rate_percentage': detection_results['anomaly_percentage'],
            'normal_records': detection_results['total_records'] - detection_results['anomalies_detected'],
            'score_statistics': {
                'mean_score': float(np.mean(scores)),
                'median_score': float(np.median(scores)),
                'std_score': float(np.std(scores)),
                'min_score': float(np.min(scores)),
                'max_score': float(np.max(scores)),
                'percentile_95': float(np.percentile(scores, 95)),
                'percentile_99': float(np.percentile(scores, 99))
            },
            'model_performance': {
                'model_used': detection_results['model_used'],
                'detection_threshold': 0.5,
                'high_confidence_anomalies': int(np.sum(np.array(scores) > 0.8)),
                'medium_confidence_anomalies': int(np.sum((np.array(scores) > 0.5) & (np.array(scores) <= 0.8))),
                'low_confidence_anomalies': int(np.sum((np.array(scores) > 0.3) & (np.array(scores) <= 0.5)))
            }
        }
    
    def _create_detailed_analysis(self, detection_results: Dict[str, Any], 
                                 preprocessing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed analysis section"""
        return {
            'data_quality_assessment': {
                'original_records': preprocessing_metadata['original_shape'][0],
                'processed_records': preprocessing_metadata['processed_shape'][0],
                'features_analyzed': preprocessing_metadata['processed_shape'][1],
                'data_completeness': 'Good' if preprocessing_metadata['processed_shape'][0] > 100 else 'Limited'
            },
            'anomaly_patterns': {
                'distribution_type': 'Skewed towards normal' if detection_results['anomaly_percentage'] < 10 else 'High anomaly rate',
                'score_concentration': 'Low scores dominant' if np.mean(detection_results['anomaly_scores']) < 0.3 else 'Mixed distribution',
                'potential_attack_indicators': detection_results['anomalies_detected'] > 0
            },
            'model_insights': {
                'detection_method': detection_results['model_used'],
                'confidence_level': 'High' if detection_results['model_used'] != 'mock' else 'Demo Mode',
                'feature_utilization': len(detection_results['feature_importance']) if detection_results['feature_importance'] else 0
            }
        }
    
    def _generate_recommendations(self, detection_results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        anomaly_rate = detection_results['anomaly_percentage']
        total_anomalies = detection_results['anomalies_detected']
        
        if anomaly_rate > 20:
            recommendations.append("High anomaly rate detected (>20%). Consider investigating data source or adjusting detection thresholds.")
        elif anomaly_rate > 10:
            recommendations.append("Moderate anomaly rate detected (>10%). Review flagged records for potential security incidents.")
        elif anomaly_rate < 1:
            recommendations.append("Very low anomaly rate (<1%). Data appears mostly normal, but verify detection sensitivity.")
        
        if total_anomalies > 0:
            recommendations.append(f"Investigate {total_anomalies} flagged anomalies for potential security threats.")
            recommendations.append("Prioritize high-confidence anomalies (score > 0.8) for immediate review.")
        
        if detection_results['model_used'] == 'mock':
            recommendations.append("Currently using demo detection mode. Train ML models with your data for improved accuracy.")
        
        recommendations.append("Consider correlating results with other security tools and threat intelligence.")
        recommendations.append("Implement automated alerting for high-confidence anomalies in production.")
        
        return recommendations
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a saved report by ID"""
        report_path = self.reports_dir / f"anomaly_report_{report_id}.json"
        
        if not report_path.exists():
            return None
        
        try:
            with open(report_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading report {report_id}: {e}")
            return None
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """List all available reports"""
        reports = []
        
        for report_file in self.reports_dir.glob("anomaly_report_*.json"):
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                    reports.append({
                        'report_id': report['report_id'],
                        'timestamp': report['timestamp'],
                        'file_name': report['file_info']['filename'],
                        'total_records': report['detection_results']['total_records'],
                        'anomalies_detected': report['detection_results']['anomalies_detected'],
                        'anomaly_percentage': report['detection_results']['anomaly_percentage']
                    })
            except Exception as e:
                print(f"Error reading report file {report_file}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        reports.sort(key=lambda x: x['timestamp'], reverse=True)
        return reports
    
    def cleanup_old_files(self, days_old: int = 30):
        """Clean up old uploaded files and reports"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Clean upload directory
        for file_path in self.upload_dir.glob("*"):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                try:
                    file_path.unlink()
                    print(f"Deleted old upload: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        # Clean reports directory
        for file_path in self.reports_dir.glob("*"):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                try:
                    file_path.unlink()
                    print(f"Deleted old report: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
