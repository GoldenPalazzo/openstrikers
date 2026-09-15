# Extract all functions
python extract_functions.py ./report.json

# Filter functions between 50-200 bytes with 20-80% match
python extract_functions.py ./report.json 50 200 20.0 80.0 --csv

# Filter functions larger than 100 bytes (no upper limit)
python extract_functions.py ./report.json 100 None None None

# Filter functions smaller than 50 bytes with low match percentage
python extract_functions.py ./report.json None 50 None 30.0

# Filter functions between 20-100 bytes with high match percentage
python extract_functions.py ./report.json 20 100 70.0 None

# Export all functions (no filters)
python extract_functions.py ./report.json --csv
