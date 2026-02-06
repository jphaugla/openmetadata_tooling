#!/bin/bash
rm -rf colat-env
VERSION=3.11
pyenv local ${VERSION}
python -m venv colat-env
source colat-env/bin/activate
pip install -r requirements.txt
if [ -f ~/.collate/setEnv.sh ]; then
    source ~/.collate/setEnv.sh
    echo "API_COLLATE_BASE=$API_COLLATE_BASE" > .env
    echo "TOKEN=$TOKEN" >> .env
    echo "✅ Credentials cached in .env"
fi
# this adds this to the jupyter
python -m ipykernel install --user --name=colat-env --display-name "Python (${VERSION}) just using api"
echo "🚀 SUCCESS. Restart Jupyter and use Python (${VERSION} just using api"
