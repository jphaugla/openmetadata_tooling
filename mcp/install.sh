# Create a dedicated directory and virtual environment
mkdir om-mcp-workspace && cd om-mcp-workspace
python3 -m venv venv
source venv/bin/activate

# Install the MCP SDK and Google GenAI library
pip install mcp google-genai jupyterlab
