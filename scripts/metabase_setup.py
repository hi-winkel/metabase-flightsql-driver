#!/usr/bin/env python3
"""
Metabase Automated Setup and Testing Script

This script automates:
1. Initial Metabase setup (admin user creation)
2. Database connection creation (GizmoSQL and Spice)
3. API key generation
4. Card/Question and Dashboard creation
"""

import os
import sys
import json
import time
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MetabaseConfig:
    """Configuration for Metabase connection"""
    base_url: str = "http://localhost:3000"
    admin_email: str = "admin@metabase.local"
    admin_password: str = "Metabase123!"
    admin_first_name: str = "Admin"
    admin_last_name: str = "User"
    site_name: str = "Metabase FlightSQL Test"


class MetabaseClient:
    """Client for interacting with Metabase API"""

    def __init__(self, config: MetabaseConfig):
        self.config = config
        self.session = requests.Session()
        self.session_token: Optional[str] = None
        self.api_key: Optional[str] = None

    def _headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        elif self.session_token:
            headers["X-Metabase-Session"] = self.session_token
        return headers

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                 expected_status: Optional[int] = None) -> Dict:
        """Make an API request"""
        url = f"{self.config.base_url}/api/{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url, headers=self._headers())
            elif method == "POST":
                response = self.session.post(url, headers=self._headers(), json=data)
            elif method == "PUT":
                response = self.session.put(url, headers=self._headers(), json=data)
            elif method == "DELETE":
                response = self.session.delete(url, headers=self._headers())
            else:
                raise ValueError(f"Unknown method: {method}")

            # Accept 200, 201, 202 as success
            success_codes = [200, 201, 202]
            if expected_status:
                success_codes = [expected_status]

            if response.status_code not in success_codes and response.status_code >= 400:
                print(f"Warning: {method} {endpoint} returned {response.status_code}")
                print(f"Response: {response.text[:500]}")

            if response.text:
                content_type = response.headers.get('content-type', '')
                if content_type.startswith('application/json'):
                    return response.json()
                else:
                    return {"text": response.text, "status_code": response.status_code}
            return {"status_code": response.status_code}
        except requests.exceptions.ConnectionError:
            print(f"Error: Cannot connect to Metabase at {self.config.base_url}")
            return {"error": "Connection error"}
        except json.JSONDecodeError:
            return {"text": response.text, "status_code": response.status_code}

    # ==================== Health & Status ====================

    def wait_for_ready(self, timeout: int = 120) -> bool:
        """Wait for Metabase to be ready"""
        print("Waiting for Metabase to be ready...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = self.session.get(f"{self.config.base_url}/api/health")
                if response.status_code == 200:
                    print("Metabase is ready!")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(2)
        print("Timeout waiting for Metabase")
        return False

    def get_session_properties(self) -> Dict:
        """Get session properties including setup token"""
        return self._request("GET", "session/properties")

    def is_setup_complete(self) -> bool:
        """Check if initial setup is complete"""
        props = self.get_session_properties()
        return props.get("has-user-setup", False) and not props.get("setup-token")

    def get_setup_token(self) -> Optional[str]:
        """Get the setup token for initial configuration"""
        props = self.get_session_properties()
        return props.get("setup-token")

    # ==================== Setup & Authentication ====================

    def setup(self) -> bool:
        """Perform initial Metabase setup"""
        token = self.get_setup_token()
        if not token:
            print("No setup token available - setup may already be complete")
            return False

        print(f"Performing initial setup with token: {token[:8]}...")

        setup_data = {
            "token": token,
            "prefs": {
                "site_name": self.config.site_name,
                "site_locale": "en",
                "allow_tracking": False
            },
            "user": {
                "first_name": self.config.admin_first_name,
                "last_name": self.config.admin_last_name,
                "email": self.config.admin_email,
                "password": self.config.admin_password
            }
        }

        result = self._request("POST", "setup", setup_data)
        if result.get("id"):
            self.session_token = result["id"]
            print(f"Setup complete! Session ID: {self.session_token[:8]}...")
            return True
        print(f"Setup failed: {result}")
        return False

    def login(self) -> bool:
        """Login with admin credentials"""
        print(f"Logging in as {self.config.admin_email}...")
        result = self._request("POST", "session", {
            "username": self.config.admin_email,
            "password": self.config.admin_password
        })
        if result.get("id"):
            self.session_token = result["id"]
            print(f"Login successful! Session: {self.session_token[:8]}...")
            return True
        print(f"Login failed: {result}")
        return False

    def set_api_key(self, api_key: str):
        """Set API key for authentication"""
        self.api_key = api_key
        self.session_token = None

    # ==================== API Key Management ====================

    def get_api_keys(self) -> List[Dict]:
        """Get list of existing API keys"""
        return self._request("GET", "api-key")

    def create_api_key(self, name: str = "automation-key") -> Optional[str]:
        """Create a new API key"""
        print(f"Creating API key: {name}...")

        # Get admin group ID
        groups = self._request("GET", "permissions/group")
        admin_group = next((g for g in groups if g.get("name") == "Administrators"), None)
        if not admin_group:
            print("Could not find Administrators group")
            return None

        result = self._request("POST", "api-key", {
            "name": name,
            "group_id": admin_group["id"]
        })

        if result.get("unmasked_key"):
            key = result["unmasked_key"]
            print(f"API key created: {key[:20]}...")
            return key
        print(f"Failed to create API key: {result}")
        return None

    # ==================== Database Management ====================

    def get_databases(self) -> List[Dict]:
        """Get list of databases"""
        return self._request("GET", "database")

    def find_database(self, name: str) -> Optional[Dict]:
        """Find a database by name"""
        databases = self.get_databases()
        if isinstance(databases, dict) and "data" in databases:
            databases = databases["data"]
        for db in databases:
            if db.get("name") == name:
                return db
        return None

    def create_database(self, name: str, engine: str, details: Dict) -> Optional[Dict]:
        """Create a new database connection"""
        print(f"Creating database: {name} ({engine})...")

        # Check if already exists
        existing = self.find_database(name)
        if existing:
            print(f"Database '{name}' already exists (ID: {existing['id']})")
            return existing

        result = self._request("POST", "database", {
            "name": name,
            "engine": engine,
            "details": details,
            "auto_run_queries": True,
            "is_full_sync": True,
            "is_on_demand": False,
            "schedules": {}
        })

        if result.get("id"):
            print(f"Database created! ID: {result['id']}")
            return result
        print(f"Failed to create database: {result}")
        return None

    def sync_database(self, db_id: int) -> bool:
        """Trigger database schema sync"""
        print(f"Syncing database {db_id}...")
        result = self._request("POST", f"database/{db_id}/sync_schema")
        return result.get("status") == "ok"

    def get_database_metadata(self, db_id: int) -> Dict:
        """Get database metadata including tables and fields"""
        return self._request("GET", f"database/{db_id}/metadata")

    # ==================== Predefined Database Configs ====================

    def create_gizmosql_connection(self, host: str = "gizmosql", port: int = 31337,
                                    username: str = "gizmosql",
                                    password: str = "gizmosql_password") -> Optional[Dict]:
        """Create GizmoSQL database connection"""
        return self.create_database(
            name="gizmo",
            engine="arrow-flight-sql",
            details={
                "host": host,
                "port": port,
                "username": username,
                "password": password,
                "useEncryption": False,
                "disableCertificateVerification": True
            }
        )

    def create_spice_connection(self, host: str = "spiced-container",
                                 port: int = 50051,
                                 token: str = "1234567890") -> Optional[Dict]:
        """Create Spice database connection"""
        return self.create_database(
            name="flight",
            engine="arrow-flight-sql",
            details={
                "host": host,
                "port": port,
                "token": token,  # Spice API key authentication
                "useEncryption": False,
                "disableCertificateVerification": True
            }
        )

    # ==================== Card/Question Management ====================

    def create_native_card(self, name: str, database_id: int, query: str,
                           collection_id: Optional[int] = None,
                           display: str = "table") -> Optional[Dict]:
        """Create a native SQL card/question"""
        print(f"Creating card: {name}...")

        card_data = {
            "name": name,
            "display": display,
            "dataset_query": {
                "database": database_id,
                "type": "native",
                "native": {
                    "query": query
                }
            },
            "visualization_settings": {}
        }
        if collection_id:
            card_data["collection_id"] = collection_id

        result = self._request("POST", "card", card_data)
        if result.get("id"):
            print(f"Card created! ID: {result['id']}")
            return result
        print(f"Failed to create card: {result}")
        return None

    def get_cards(self) -> List[Dict]:
        """Get list of cards/questions"""
        return self._request("GET", "card")

    def run_card(self, card_id: int) -> Dict:
        """Run a card and get results"""
        return self._request("POST", f"card/{card_id}/query")

    # ==================== Dashboard Management ====================

    def create_dashboard(self, name: str, description: str = "",
                         collection_id: Optional[int] = None) -> Optional[Dict]:
        """Create a new dashboard"""
        print(f"Creating dashboard: {name}...")

        dashboard_data = {
            "name": name,
            "description": description
        }
        if collection_id:
            dashboard_data["collection_id"] = collection_id

        result = self._request("POST", "dashboard", dashboard_data)
        if result.get("id"):
            print(f"Dashboard created! ID: {result['id']}")
            return result
        print(f"Failed to create dashboard: {result}")
        return None

    def add_card_to_dashboard(self, dashboard_id: int, card_id: int,
                               row: int = 0, col: int = 0,
                               size_x: int = 8, size_y: int = 6) -> Optional[Dict]:
        """Add a card to a dashboard using PUT /api/dashboard/:id"""
        print(f"Adding card {card_id} to dashboard {dashboard_id}...")

        # First get the current dashboard state
        dashboard = self._request("GET", f"dashboard/{dashboard_id}")
        if not dashboard.get("id"):
            print(f"Failed to get dashboard: {dashboard}")
            return None

        # Get existing dashcards
        existing_dashcards = dashboard.get("dashcards", [])

        # Create new dashcard entry
        new_dashcard = {
            "id": -1,  # Negative ID for new cards
            "card_id": card_id,
            "row": row,
            "col": col,
            "size_x": size_x,
            "size_y": size_y,
            "parameter_mappings": [],
            "visualization_settings": {}
        }

        # Update dashboard with new dashcard
        updated_dashcards = existing_dashcards + [new_dashcard]
        result = self._request("PUT", f"dashboard/{dashboard_id}", {
            "dashcards": updated_dashcards
        })

        if result.get("id"):
            print(f"Card added to dashboard!")
            return result
        print(f"Failed to add card: {result}")
        return None

    def get_dashboards(self) -> List[Dict]:
        """Get list of dashboards"""
        return self._request("GET", "dashboard")

    # ==================== Query Execution ====================

    def run_query(self, database_id: int, query: str) -> Dict:
        """Run a native SQL query"""
        return self._request("POST", "dataset", {
            "database": database_id,
            "type": "native",
            "native": {"query": query}
        })


def save_env_file(api_key: str, env_path: str = ".env"):
    """Save API key to .env file"""
    env_file = Path(env_path)
    content = f"METABASE_API_KEY={api_key}\n"

    if env_file.exists():
        existing = env_file.read_text()
        if "METABASE_API_KEY=" in existing:
            # Replace existing key
            lines = existing.split("\n")
            lines = [l for l in lines if not l.startswith("METABASE_API_KEY=")]
            lines.insert(0, f"METABASE_API_KEY={api_key}")
            content = "\n".join(lines)
        else:
            content = f"METABASE_API_KEY={api_key}\n{existing}"

    env_file.write_text(content)
    print(f"API key saved to {env_path}")


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """Load environment variables from .env file"""
    env_file = Path(env_path)
    env_vars = {}
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
    return env_vars


def main():
    """Main setup and test function"""
    print("=" * 60)
    print("Metabase Automated Setup & Testing")
    print("=" * 60)

    # Load .env file first
    env_vars = load_env_file()
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value

    config = MetabaseConfig()
    client = MetabaseClient(config)

    # Step 1: Wait for Metabase
    if not client.wait_for_ready():
        sys.exit(1)

    # Step 2: Check setup status and perform setup or login
    props = client.get_session_properties()
    has_user = props.get("has-user-setup", False)

    # Try to use existing API key from env first
    env_key = os.environ.get("METABASE_API_KEY")
    if env_key:
        print(f"\n--- Using API key from .env: {env_key[:20]}... ---")
        client.set_api_key(env_key)
        # Verify the key works
        dbs = client.get_databases()
        if isinstance(dbs, dict) and "API" not in str(dbs.get("text", "")):
            print("API key is valid!")
        elif isinstance(dbs, list) or (isinstance(dbs, dict) and "data" in dbs):
            print("API key is valid!")
        else:
            print(f"API key invalid, will try login...")
            client.api_key = None

    if not client.api_key:
        if not has_user:
            print("\n--- Performing Initial Setup ---")
            if not client.setup():
                print("Setup failed!")
                sys.exit(1)
        else:
            print("\n--- Metabase already configured, logging in ---")
            if not client.login():
                print("Login failed! Please check credentials or set METABASE_API_KEY in .env")
                sys.exit(1)

    # Step 3: Create or verify API key
    print("\n--- API Key Management ---")
    api_keys = client.get_api_keys()
    if isinstance(api_keys, list) and len(api_keys) > 0:
        print(f"Found {len(api_keys)} existing API key(s)")
        # Check if automation key exists
        auto_key = next((k for k in api_keys if k.get("name") == "automation-key"), None)
        if auto_key:
            print(f"Automation key already exists (ID: {auto_key['id']})")
    else:
        # Create new API key
        new_key = client.create_api_key("automation-key")
        if new_key:
            save_env_file(new_key)
            client.set_api_key(new_key)

    # Step 4: Create database connections
    print("\n--- Database Connections ---")

    gizmo = client.create_gizmosql_connection()
    spice = client.create_spice_connection()

    # Step 5: Sync databases
    print("\n--- Syncing Databases ---")
    if gizmo:
        client.sync_database(gizmo["id"])
        time.sleep(5)  # Wait for sync
        meta = client.get_database_metadata(gizmo["id"])
        tables = meta.get("tables", [])
        print(f"GizmoSQL: {len(tables)} tables synced")

    if spice:
        client.sync_database(spice["id"])
        time.sleep(5)  # Wait for sync
        meta = client.get_database_metadata(spice["id"])
        tables = meta.get("tables", [])
        print(f"Spice: {len(tables)} tables synced")

    # Step 6: Test queries
    print("\n--- Testing Queries ---")
    if gizmo:
        result = client.run_query(gizmo["id"], "SELECT COUNT(*) as cnt FROM hr.departments")
        if result.get("status") == "completed":
            rows = result.get("data", {}).get("rows", [])
            print(f"GizmoSQL query OK: {rows}")
        else:
            print(f"GizmoSQL query failed: {result.get('error', 'Unknown error')}")

    if spice:
        result = client.run_query(spice["id"], "SELECT COUNT(*) as cnt FROM yellow_taxis")
        if result.get("status") == "completed":
            rows = result.get("data", {}).get("rows", [])
            print(f"Spice query OK: {rows}")
        else:
            print(f"Spice query failed: {result.get('error', 'Unknown error')}")

    # Step 7: Create sample dashboard (optional demo)
    print("\n--- Creating Sample Dashboard ---")
    if gizmo:
        # Create a card
        card = client.create_native_card(
            name="Department Budgets",
            database_id=gizmo["id"],
            query="SELECT department_name, budget FROM hr.departments ORDER BY budget DESC",
            display="bar"
        )

        if card:
            # Create a dashboard
            dashboard = client.create_dashboard(
                name="FlightSQL Demo Dashboard",
                description="Automated test dashboard for Arrow Flight SQL driver"
            )

            if dashboard:
                client.add_card_to_dashboard(dashboard["id"], card["id"])
                print(f"\nDashboard URL: {config.base_url}/dashboard/{dashboard['id']}")

    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print(f"Metabase URL: {config.base_url}")
    print(f"Admin Email: {config.admin_email}")
    print(f"Admin Password: {config.admin_password}")
    if client.api_key:
        print(f"API Key: {client.api_key[:30]}...")
    print("=" * 60)


if __name__ == "__main__":
    main()
