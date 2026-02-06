#!/bin/bash
# 1. Environment Setup
rm -rf colat-env
pyenv local 3.10
python -m venv colat-env
source colat-env/bin/activate

# 2. Upgrade Pip
pip install --upgrade pip

# 3. Step 1: Install the SDK and base dependencies
# This handles the bulk, but might mess up the lineage namespace
pip install -r requirements.txt

# 4. THE FIX: Surgical Force-Reinstall of the Lineage Fork
# We uninstall ANY version and then force-install our fork WITHOUT dependencies
# This ensures our files are the ones Python finds during 'import sqllineage'
pip uninstall -y sqllineage collate-sqllineage
pip install --no-deps --no-cache-dir "collate-sqllineage==2.0.1"

# THE BRIDGE: Force the sqllineage namespace to point to our fork
SITE_PACKAGES="colat-env/lib/python3.10/site-packages"
if [ -d "$SITE_PACKAGES/collate_sqllineage" ] && [ ! -d "$SITE_PACKAGES/sqllineage" ]; then
    echo "🔗 Creating namespace bridge: sqllineage -> collate_sqllineage"
    # Create a simple __init__.py bridge
    mkdir -p "$SITE_PACKAGES/sqllineage"
    echo "from collate_sqllineage import *" > "$SITE_PACKAGES/sqllineage/__init__.py"
fi

# 5. Cache credentials for Jupyter
if [ -f ~/.collate/setEnv.sh ]; then
    source ~/.collate/setEnv.sh
    echo "API_COLLATE_BASE=$API_COLLATE_BASE" > .env
    echo "TOKEN=$TOKEN" >> .env
    echo "✅ Credentials cached in .env"
fi

# 6. Register Kernel
python -m ipykernel install --user --name=colat-env --display-name "Python (Collate-1.11.7-Final)"

# 7. Comprehensive Integrity Check
echo "--- FINAL INTEGRITY CHECK ---"
python -c "import pydantic; print('✅ Pydantic:', pydantic.__version__)"
python -c "import sqllineage; print('✅ Lineage Parser: FOUND')"
python -c "import cachetools; print('✅ Cachetools: FOUND')"
echo "🚀 SUCCESS. Restart Jupyter and use 'Collate-1.11.7-Final'."
