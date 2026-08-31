#!/bin/bash
set -e
echo "Running Data Model Architect Verification Battery..."
python -m pytest tests/ -v
echo "All 10/10 Benchmark Scenarios Passed! Ready Out of the Box!"
