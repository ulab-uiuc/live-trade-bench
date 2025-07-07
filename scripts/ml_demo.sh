#!/usr/bin/env bash

# === Configuration ===
DATA_DIR="../data"    # e.g. ~/projects/data
MODELS_DIR="../models"  # Directory for saved models
RESULTS_DIR="../results"  # Directory for results
TICKER="AAPL"
TRAIN_START="2023-01-01"
TRAIN_END="2025-01-01"
TEST_START="2025-01-01"
TEST_END="2025-06-01"
EVAL_DELAY=5
RESOLUTION="D"

# === Create directories ===
mkdir -p "${DATA_DIR}"
mkdir -p "${MODELS_DIR}"
mkdir -p "${RESULTS_DIR}"

echo "=== Machine Learning Trading Demo ==="
echo "Ticker: ${TICKER}"
echo "Training Period: ${TRAIN_START} to ${TRAIN_END}"
echo "Testing Period: ${TEST_START} to ${TEST_END}"
echo ""

# === Option 1: Train and test a single model ===
echo "=== Training Random Forest Model ==="
python ../examples/ml_demo.py \
  --ticker "${TICKER}" \
  --train_start "${TRAIN_START}" \
  --train_end "${TRAIN_END}" \
  --test_start "${TEST_START}" \
  --test_end "${TEST_END}" \
  --model_type random_forest \
  --eval_delay "${EVAL_DELAY}" \
  --resolution "${RESOLUTION}" \
  --output_dir "${RESULTS_DIR}"

echo ""
echo "=== Training Logistic Regression Model ==="
python ../examples/ml_demo.py \
  --ticker "${TICKER}" \
  --train_start "${TRAIN_START}" \
  --train_end "${TRAIN_END}" \
  --test_start "${TEST_START}" \
  --test_end "${TEST_END}" \
  --model_type logistic_regression \
  --eval_delay "${EVAL_DELAY}" \
  --resolution "${RESOLUTION}" \
  --output_dir "${RESULTS_DIR}"

echo ""
echo "=== Training SVM Model ==="
python ../examples/ml_demo.py \
  --ticker "${TICKER}" \
  --train_start "${TRAIN_START}" \
  --train_end "${TRAIN_END}" \
  --test_start "${TEST_START}" \
  --test_end "${TEST_END}" \
  --model_type svm \
  --eval_delay "${EVAL_DELAY}" \
  --resolution "${RESOLUTION}" \
  --output_dir "${RESULTS_DIR}"

# === Option 2: Compare all models at once ===
echo ""
echo "=== Comparing All Models ==="
python ../examples/ml_demo.py \
  --ticker "${TICKER}" \
  --train_start "${TRAIN_START}" \
  --train_end "${TRAIN_END}" \
  --test_start "${TEST_START}" \
  --test_end "${TEST_END}" \
  --eval_delay "${EVAL_DELAY}" \
  --resolution "${RESOLUTION}" \
  --compare_models \
  --output_dir "${RESULTS_DIR}"

# === Option 3: Cross-validation ===
echo ""
echo "=== Running Cross-Validation ==="
python ../examples/ml_demo.py \
  --ticker "${TICKER}" \
  --train_start "${TRAIN_START}" \
  --test_end "${TEST_END}" \
  --model_type random_forest \
  --cross_validate \
  --output_dir "${RESULTS_DIR}"

echo ""
echo "=== Demo Complete ==="
echo "Results saved in: ${RESULTS_DIR}"
echo "Models saved in: ${MODELS_DIR}"
echo "Data saved in: ${DATA_DIR}" 