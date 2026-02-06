#!/bin/bash
# 1. Environment Refresh
rm -rf dq-lean-env
python3.10 -m venv dq-lean-env
source dq-lean-env/bin/activate

# 2. Base Dependencies (Standard for 1.11.8)
pip install --upgrade pip
pip install "chardet==4.0.0" "pydantic>=2.7.0,<2.12"

# 3. Targeted Collate Install
# We include 'pyarrow' as requested
pip install "openmetadata-ingestion[profiler,pandas,postgres,pyarrow]==1.11.8"
pip install ipykernel==6.29.0 IPython==8.20.0 python-dotenv==1.0.0 cachetools>=5.3.0 sqlparse==0.5.3 collate-sqllineage==2.0.1

# 4. THE NAMESPACE BRIDGE (Crucial for Lineage)
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
if [ -d "$SITE_PACKAGES/collate_sqllineage" ] && [ ! -d "$SITE_PACKAGES/sqllineage" ]; then
    echo "🔗 Creating sqllineage bridge..."
    mkdir -p "$SITE_PACKAGES/sqllineage"
    echo "from collate_sqllineage import *" > "$SITE_PACKAGES/sqllineage/__init__.py"
fi

# 5. Register Kernel
python -m ipykernel install --user --name=dq-lean-env --display-name "Python (Collate-1.11.8-DQ-Lean)"

# 6. FIXED INTEGRITY CHECK
echo "--- FINAL DQ LEAN INTEGRITY CHECK ---"
python -c "import pandas; print(f'✅ Pandas: {pandas.__version__}')"
python -c "import dotenv; print('✅ Dotenv: FOUND')"
python -c "import sqllineage; print('✅ Lineage Parser: FOUND')"
python -c "
try:
    from metadata.sdk.data_quality.dataframes.dataframe_validator import DataFrameValidator
    print('✅ DQ SDK: READY (DataFrame Validator Found)')
except ImportError as e:
    print(f'❌ ERROR: Validator not found. {e}')
"
