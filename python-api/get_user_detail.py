#!/usr/bin/env python3
"""
get_user_detail.py

Fetch full user details and resolved permissions for a Collate/OpenMetadata
user or bot, to validate what a token can actually do.

Usage:
  python get_user_detail.py <username_or_displayname>

Environment variables (same as other scripts):
  TOKEN     OpenMetadata JWT (required)
  API_BASE  e.g. https://your-org.getcollate.io/api/v1 (required)
"""
import sys
import json
import urllib.parse
from om_client import OpenMetadataClient


# ── User lookup ───────────────────────────────────────────────────────────────

def fetch_all_users(client: OpenMetadataClient) -> list[dict]:
    """Page through /users to get all users (up to 10k)."""
    all_users = []
    after = None
    while True:
        params = "limit=100&fields=roles,teams,profile"
        if after:
            params += f"&after={urllib.parse.quote(after)}"
        resp = client._make_request("GET", f"/users?{params}")
        if resp is None or resp.status_code != 200:
            break
        body  = resp.json()
        page  = body.get("data", [])
        all_users.extend(page)
        after = body.get("paging", {}).get("after")
        if not after or not page:
            break
    return all_users


def fetch_user(client: OpenMetadataClient, search_term: str) -> dict | None:
    """
    Lookup order:
      1. GET /users/name/<term>  (exact name, fastest)
      2. Case-insensitive scan on 'name'
      3. Case-insensitive scan on 'displayName' — stops with error if >1 match
    """
    # 1. Direct name lookup by name
    encoded = urllib.parse.quote(search_term)
    resp = client._make_request(
        "GET", f"/users/name/{encoded}?fields=roles,teams,profile,personas"
    )
    if resp is not None and resp.status_code == 200:
        return resp.json()

    print(f"⚠️  Direct name lookup failed (HTTP {resp.status_code if resp else 'n/a'}), scanning user list...")

    all_users = fetch_all_users(client)
    if not all_users:
        print("❌ Could not retrieve user list.")
        return None

    term_lower = search_term.lower()

    # 2. Case-insensitive name match
    by_name = [u for u in all_users if u.get("name", "").lower() == term_lower]
    if len(by_name) == 1:
        # Re-fetch with full fields by id so we get roles/teams
        return fetch_user_by_id(client, by_name[0]["id"])
    if len(by_name) > 1:
        # Shouldn't happen (names are unique) but handle it anyway
        print(f"❌ Multiple users share the name '{search_term}':")
        for u in by_name:
            print(f"   id={u['id']}  name={u['name']}  displayName={u.get('displayName', '')}")
        sys.exit(1)

    # 3. Case-insensitive displayName match
    by_display = [u for u in all_users if u.get("displayName", "").lower() == term_lower]
    if len(by_display) == 1:
        return fetch_user_by_id(client, by_display[0]["id"])
    if len(by_display) > 1:
        print(f"❌ Multiple users share the displayName '{search_term}' — be more specific:")
        for u in by_display:
            print(f"   id={u['id']}  name={u['name']}  displayName={u.get('displayName', '')}")
        sys.exit(1)

    return None


def fetch_user_by_id(client: OpenMetadataClient, user_id: str) -> dict | None:
    resp = client._make_request(
        "GET", f"/users/{user_id}?fields=roles,teams,profile,personas"
    )
    if resp is not None and resp.status_code == 200:
        return resp.json()
    return None


# ── Role / Policy resolution ──────────────────────────────────────────────────

def fetch_role_by_id(client: OpenMetadataClient, role_id: str) -> dict | None:
    resp = client._make_request("GET", f"/roles/{role_id}?fields=policies")
    if resp is not None and resp.status_code == 200:
        return resp.json()
    return None


def fetch_policy_by_id(client: OpenMetadataClient, policy_id: str) -> dict | None:
    resp = client._make_request("GET", f"/policies/{policy_id}?fields=rules")
    if resp is not None and resp.status_code == 200:
        return resp.json()
    return None


def resolve_operations(client: OpenMetadataClient, role: dict) -> tuple[list[str], list[dict]]:
    """
    For each policy reference in the role, fetch the full policy by ID
    and collect allow-listed operations.
    Returns (sorted ops list, list of resolved policy dicts).
    """
    ops: set[str] = set()
    resolved_policies = []

    for policy_ref in role.get("policies", []):
        policy_id = policy_ref.get("id")
        if not policy_id:
            continue
        policy = fetch_policy_by_id(client, policy_id)
        if not policy:
            print(f"     ⚠️  Could not fetch policy id={policy_id} name={policy_ref.get('name', '?')}")
            continue
        resolved_policies.append(policy)
        for rule in policy.get("rules", []):
            if rule.get("effect", "").lower() == "allow":
                for op in rule.get("operations", []):
                    ops.add(op)

    return sorted(ops), resolved_policies


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        print("Usage: python get_user_detail.py <username_or_displayname>")
        sys.exit(1)

    search_term = sys.argv[1]
    client = OpenMetadataClient()

    print(f"\n🔍 Looking up user: {search_term}")
    print("─" * 60)

    user = fetch_user(client, search_term)
    if not user:
        print(f"❌ User '{search_term}' not found (tried name and displayName).")
        sys.exit(1)

    # ── User summary ──────────────────────────────────────────────────────────
    roles_refs = user.get("roles", [])
    teams_refs = user.get("teams", [])

    summary = {
        "id":          user.get("id"),
        "name":        user.get("name"),
        "displayName": user.get("displayName"),
        "email":       user.get("email"),
        "isAdmin":     user.get("isAdmin", False),
        "isBot":       user.get("isBot", False),
        "deleted":     user.get("deleted", False),
        "teams":       [{"id": t.get("id"), "name": t.get("name")} for t in teams_refs],
        "roles":       [{"id": r.get("id"), "name": r.get("name")} for r in roles_refs],
    }

    print("\n👤 User Details")
    print(json.dumps(summary, indent=2))

    # ── Roles → Policies (fetched by ID) → Operations ─────────────────────────
    if not roles_refs:
        if summary["isAdmin"]:
            print("\n🔑 Permissions: Admin — all operations allowed")
        else:
            print("\n⚠️  No roles assigned to this user.")
        return

    print("\n🔐 Roles & Permissions")
    print("─" * 60)

    all_ops: set[str] = set()

    for role_ref in roles_refs:
        role_id   = role_ref.get("id")
        role_name = role_ref.get("name", role_id)
        role      = fetch_role_by_id(client, role_id)

        if not role:
            print(f"\n  ⚠️  Could not fetch role name={role_name} id={role_id}")
            continue

        ops, resolved_policies = resolve_operations(client, role)
        all_ops.update(ops)

        print(f"\n  📋 Role: {role_name}  (id={role_id})")
        if resolved_policies:
            for pol in resolved_policies:
                print(f"     Policy: {pol.get('name', '?')}  (id={pol.get('id', '?')})")
                pol_ops = []
                for rule in pol.get("rules", []):
                    if rule.get("effect", "").lower() == "allow":
                        pol_ops.extend(rule.get("operations", []))
                if pol_ops:
                    for op in sorted(set(pol_ops)):
                        print(f"       ✅ {op}")
                else:
                    print("       ⚠️  No allow rules in this policy")
        else:
            print("     ⚠️  No policies resolved for this role")

        if not ops:
            print("     ⚠️  No explicit allow operations found across all policies")

    # ── Aggregate ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print(f"📊 Aggregate allowed operations across all roles ({len(all_ops)} total):")
    for op in sorted(all_ops):
        print(f"  ✅ {op}")

    print()
    if "AuditLogs" in all_ops or "All" in all_ops:
        print("🟢 AuditLogs: GRANTED")
    else:
        print("🔴 AuditLogs: NOT GRANTED — add AuditLogs operation to a role's policy in")
        print("   Settings → Access Control → Policies → <policy> → Rules")


if __name__ == "__main__":
    main()
