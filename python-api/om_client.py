import os
import sys
import requests
import urllib.parse
from typing import Optional, Dict, Any, List

class OpenMetadataClient:
    def __init__(self):
        self.token = os.getenv("TOKEN")
        self.api_base = os.getenv("API_BASE")
        
        if not self.token or not self.api_base:
            print("❌ Error: Missing environment variables (TOKEN or API_BASE).")
            print("Please ensure they are set in your environment.")
            sys.exit(1)
            
        # Clean up trailing slashes
        self.api_base = self.api_base.rstrip('/')
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
        """Generic request handler with detailed error reporting."""
        url = f"{self.api_base}{endpoint}"
        
        # Added a default 30s timeout to prevent hangs
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30
            
        print(f"DEBUG: [{method}] {url}")
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            return response
        except Exception as e:
            import traceback
            print(f"❌ Request Error [{method} {url}]: {e}")
            traceback.print_exc()
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = self._make_request("GET", f"/users/{user_id}")
        if response is not None and response.status_code == 200:
            return response.json()
        return None

    def get_service_id(self, service_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        Attempts to find a service by name, checking Database then Search services.
        Returns a tuple: (service_id, service_type) or (None, None)
        """
        encoded_name = urllib.parse.quote(service_name)
        
        # 1. Check Database Services
        response = self._make_request("GET", f"/services/databaseServices/name/{encoded_name}?include=all")
        if response is not None and response.status_code == 200:
            return response.json().get("id"), "databaseService"
            
        # 2. Check Search Services
        response = self._make_request("GET", f"/services/searchServices/name/{encoded_name}?include=all")
        if response is not None and response.status_code == 200:
            return response.json().get("id"), "searchService"
            
        return None, None

    def get_pipelines_for_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Fetches all pipelines and filters by service name."""
        # Using fields=owners,sourceConfig,airflowConfig to match the bash script behavior
        response = self._make_request("GET", "/services/ingestionPipelines?limit=1000&fields=owners,sourceConfig,airflowConfig")
        if response is None or response.status_code != 200:
            return []
            
        data = response.json().get("data", [])
        return [p for p in data if p.get("service", {}).get("name") == service_name]

    def trigger_pipeline(self, pipeline_id: str) -> bool:
        response = self._make_request("POST", f"/services/ingestionPipelines/trigger/{pipeline_id}")
        return response is not None and response.status_code == 200

    def deploy_pipeline(self, pipeline_id: str) -> bool:
        response = self._make_request("POST", f"/services/ingestionPipelines/deploy/{pipeline_id}")
        return response is not None and response.status_code == 200

    def create_pipeline(self, pipeline_data: Dict[str, Any]) -> tuple[bool, Optional[str], str]:
        """Returns success boolean, new pipeline ID (if success), and raw response text."""
        response = self._make_request("POST", "/services/ingestionPipelines", json=pipeline_data)
        if response is not None and response.status_code in [200, 201]:
            return True, response.json().get("id"), response.text
        
        error_msg = response.text if response is not None else "Unknown Error"
        return False, None, error_msg

    def delete_pipeline(self, pipeline_id: str) -> bool:
        response = self._make_request("DELETE", f"/services/ingestionPipelines/{pipeline_id}?hardDelete=true&recursive=true")
        return response is not None and response.status_code == 200

    def patch_pipeline(self, pipeline_id: str, patch_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Applies a JSON patch to a pipeline."""
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json-patch+json"
        
        url = f"{self.api_base}/services/ingestionPipelines/{pipeline_id}"
        try:
            response = requests.patch(url, headers=headers, json=patch_data)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Patch failed: {e}")
        return None
