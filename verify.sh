#!/bin/bash
set -e
echo "Running Data Model Architect Verification Battery..."
python -m pytest tests/ -v
echo "All 22/22 Unit, Pipeline & DuckDB Tests Passed! Ready Out of the Box!"
