
import json
import os

file_path = "/Users/jasonhaugland/gits/openmetadata_tooling/mcp/mcp_om.ipynb"

with open(file_path, "r") as f:
    nb = json.load(f)

# The new source code with TOOL INTEGRATION
new_source = [
    "import os\n",
    "import httpx\n",
    "from google import genai\n",
    "from google.genai import types\n",
    "from mcp import ClientSession\n",
    "from mcp.client.streamable_http import streamable_http_client\n",
    "\n",
    "# Variables\n",
    "OM_PAT = os.getenv(\"TOKEN\")\n",
    "OM_BASE_URL = os.getenv(\"API_BASE\", \"http://localhost:8585/api/v1\")\n",
    "GEMINI_KEY = os.getenv(\"GEMINI_APIKEY\")\n",
    "MCP_URL = \"http://localhost:8585/mcp\"\n",
    "timeout = httpx.Timeout(90, read=None)\n",
    "\n",
    "async def ask_metadata(prompt):\n",
    "    headers = {\"Authorization\": f\"Bearer {OM_PAT}\"}\n",
    "    async with httpx.AsyncClient(timeout=timeout, headers=headers) as http_client:\n",
    "        async with streamable_http_client(url=MCP_URL, http_client=http_client) as (read, write, _):\n",
    "            async with ClientSession(read, write) as session:\n",
    "                await session.initialize()\n",
    "                \n",
    "                # 1. List Available Tools from MCP\n",
    "                result = await session.list_tools()\n",
    "                mcp_tools = result.tools\n",
    "                \n",
    "                # 2. Convert MCP Tools to Gemini Tools\n",
    "                gemini_tools = []\n",
    "                for tool in mcp_tools:\n",
    "                    # Basic conversion - Gemini expects 'function_declarations'\n",
    "                    # Note: We are simplifying the schema for compatibility\n",
    "                    gemini_tool = types.Tool(function_declarations=[])\n",
    "                    if tool.inputSchema: # Ensure schema exists\n",
    "                         # Clean up schema properties that might confuse Gemini if needed\n",
    "                         # For now, pass mostly as-is but ensure type is object\n",
    "                         pass \n",
    "                    \n",
    "                    gemini_tools.append(types.Tool(\n",
    "                        function_declarations=[types.FunctionDeclaration(\n",
    "                            name=tool.name,\n",
    "                            description=tool.description,\n",
    "                            parameters=tool.inputSchema\n",
    "                        )]\n",
    "                    ))\n",
    "                \n",
    "                # 3. Initialize Gemini Client with Tools\n",
    "                client = genai.Client(api_key=GEMINI_KEY)\n",
    "                chat = client.chats.create(model=\"gemini-2.0-flash\")\n",
    "                \n",
    "                # 4. Send Initial Message\n",
    "                response = chat.send_message(prompt, config=types.GenerateContentConfig(tools=gemini_tools))\n",
    "                \n",
    "                # 5. Tool Execution Loop\n",
    "                # Loop while the model wants to call functions\n",
    "                while response.function_calls:\n",
    "                    parts = []\n",
    "                    for part in response.function_calls:\n",
    "                         print(f\"Calling tool: {part.name} with args: {part.args}\")\n",
    "                         \n",
    "                         # Execute the tool via MCP session\n",
    "                         tool_result = await session.call_tool(part.name, arguments=part.args)\n",
    "                         \n",
    "                         # Convert MCP result to text/JSON for Gemini\n",
    "                         # MCP returns 'content' list (TextContent or ImageContent)\n",
    "                         result_text = \"\"\n",
    "                         if tool_result.content:\n",
    "                             for content in tool_result.content:\n",
    "                                 if content.type == 'text':\n",
    "                                     result_text += content.text + \"\\n\"\n",
    "                                 else:\n",
    "                                     result_text += str(content) + \"\\n\"\n",
    "                         else:\n",
    "                             result_text = \"Success\"\n",
    "                             \n",
    "                         parts.append(types.Part.from_function_response(\n",
    "                             name=part.name,\n",
    "                             response={\"result\": result_text} \n",
    "                         ))\n",
    "                    \n",
    "                    # Send the tool outputs back to the model\n",
    "                    response = chat.send_message(parts)\n",
    "\n",
    "                return response.text\n",
    "\n",
    "# Test it!\n",
    "await ask_metadata(\"Looking in the Cockroach_movr database service, what tables do you see\")"
]

found = False
for cell in nb["cells"]:
    if cell["id"] == "43527e5f-691b-4ad8-91b6-b2e3e1191cb0":
        cell["source"] = new_source
        cell["outputs"] = [] # Clear outputs
        found = True
        break

if not found:
    print("Error: Cell not found")
    exit(1)

with open(file_path, "w") as f:
    json.dump(nb, f, indent=1)

print("Notebook updated successfully.")
