#!/bin/bash
set -e
echo "Running Data Model Architect Verification Battery..."
python -m pytest tests/ -v
echo "All 23/23 Unit, Pipeline, Multi-Branch & DuckDB Tests Passed! Ready Out of the Box!"
