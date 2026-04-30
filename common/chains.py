"""Shared service registry and chain definitions for the simulator."""

from __future__ import annotations

SERVICE_SPECS = [
    {"name": "T.Data", "script": "T_Data_service.py", "port": 8001, "path": "/a"},
    {"name": "IDP-IDM", "script": "IDP-IDM_service.py", "port": 8002, "path": "/b"},
    {"name": "(FED) - TDICE", "script": "FED_TDICE_service.py", "port": 8003, "path": "/c"},
    {"name": "ABPT", "script": "ABPT_service.py", "port": 8004, "path": "/d"},
    {"name": "Amp-MM - Invenio", "script": "Amp_MM_Invenio_service.py", "port": 8015, "path": "/e"},
    {"name": "ECO Suite", "script": "ECO Suite_service.py", "port": 8006, "path": "/f"},
    {"name": "GRP-ICAP", "script": "GRP_ICAP_server.py", "port": 8007, "path": "/g"},
    {"name": "IDP-Commerce-ES", "script": "IDP_Commerce_ES.py", "port": 8008, "path": "/h"},
    {"name": "IDP-Order Graph Cloud", "script": "IDP_Order Graph_Cloud_service.py", "port": 8009, "path": "/i"},
    {"name": "IDP_Platform", "script": "IDP_Platform_service.py", "port": 8010, "path": "/j"},
    {"name": "SHM", "script": "SHM_service.py", "port": 8011, "path": "/shm"},
    {"name": "TDICE", "script": "TDICE_service.py", "port": 8012, "path": "/tdice"},
    {"name": "TRiP", "script": "TRiP_service.py", "port": 8013, "path": "/trip"},
    {"name": "ISBUS", "script": "ISBUS_service.py", "port": 8014, "path": "/isbus"},
    {"name": "Nimbus", "script": "Nimbus_service.py", "port": 8016, "path": "/nimbus"},

        # New services for Lookup Customer chain
        {"name": "CCSF", "script": "CCSF_service.py", "port": 8020, "path": "/ccsf"},
        {"name": "CCMULE", "script": "CCMULE_service.py", "port": 8021, "path": "/ccmule"},
        {"name": "IDP-Cloud-CG", "script": "IDP_Cloud_CG_service.py", "port": 8022, "path": "/idp-cloud-cg"},
        {"name": "DPG - Sales & Sunrise", "script": "DPG_Sales_Sunrise_service.py", "port": 8023, "path": "/dpg-sales-sunrise"},
        {"name": "Platform Support ATTFEDGOV1", "script": "Platform_Support_ATTFEDGOV1_service.py", "port": 8024, "path": "/platform-support-attfedgov1"},
        {"name": "eTRACS", "script": "eTRACS_service.py", "port": 8025, "path": "/etracs"},
]

SERVICE_BY_NAME = {spec["name"]: spec for spec in SERVICE_SPECS}
ENTRY_SERVICE_NAME = "ABPT"


CHAIN_DEFINITIONS = {
    "test_scenario_1": ["ABPT", "T.Data", "IDP-IDM", "(FED) - TDICE", "Amp-MM - Invenio", "ECO Suite", "TDICE"],
    "test_scenario_2": ["ABPT", "GRP-ICAP", "IDP-Commerce-ES", "IDP-Order Graph Cloud", "SHM", "TRiP", "TDICE"],
    "test_scenario_3": ["ABPT", "Nimbus", "ISBUS", "IDP_Platform", "IDP-IDM", "ECO Suite", "TDICE"],
    "test_scenario_4": ["ABPT", "T.Data", "GRP-ICAP", "Amp-MM - Invenio", "IDP-Commerce-ES", "SHM", "TRiP", "TDICE"],
    # test_scenario_5 is now handled by FORKED_CHAIN_DEFINITIONS (dynamic/randomized)
    "test_scenario_6": ["ABPT", "IDP-IDM", "SHM", "IDP-Commerce-ES", "TRiP", "GRP-ICAP", "Nimbus", "TDICE"],
    "test_scenario_7": ["ABPT", "ECO Suite", "Amp-MM - Invenio", "IDP-Order Graph Cloud", "T.Data", "ISBUS", "IDP_Platform", "GRP-ICAP", "TDICE"],
    "test_scenario_8": ["ABPT", "Nimbus", "IDP-Commerce-ES", "(FED) - TDICE", "SHM", "IDP-IDM", "TRiP", "Amp-MM - Invenio", "TDICE"],
    "test_scenario_9": ["ABPT", "ISBUS", "IDP_Platform", "ECO Suite", "T.Data", "GRP-ICAP", "IDP-Order Graph Cloud", "Nimbus", "TDICE"],
    "test_scenario_10": ["ABPT", "T.Data", "TDICE"],
    "test_scenario_11": ["ABPT", "(FED) - TDICE", "ECO Suite", "Nimbus", "ISBUS", "IDP_Platform", "T.Data", "IDP-IDM", "GRP-ICAP", "TDICE"],
    "test_scenario_12": ["ABPT", "IDP-Order Graph Cloud", "SHM", "Amp-MM - Invenio", "TRiP", "IDP-Commerce-ES", "Nimbus", "ECO Suite", "IDP_Platform", "TDICE"],
    "test_scenario_13": ["ABPT", "GRP-ICAP", "T.Data", "IDP-Commerce-ES", "Nimbus", "Amp-MM - Invenio", "ISBUS", "IDP-IDM", "ECO Suite", "IDP-Order Graph Cloud", "TDICE"],
    "test_scenario_14": ["ABPT", "SHM", "IDP_Platform", "(FED) - TDICE", "TRiP", "IDP-IDM", "GRP-ICAP", "Amp-MM - Invenio", "Nimbus", "ECO Suite", "TDICE"],
    "test_scenario_15": ["ABPT", "Nimbus", "ISBUS", "Amp-MM - Invenio", "ECO Suite", "T.Data", "IDP-Order Graph Cloud", "IDP-Commerce-ES", "SHM", "GRP-ICAP", "TDICE"],
    "test_scenario_16": ["ABPT", "T.Data", "GRP-ICAP", "IDP-IDM", "Amp-MM - Invenio", "IDP-Commerce-ES", "SHM", "IDP-Order Graph Cloud", "ECO Suite", "TRiP", "Nimbus", "TDICE"],
    "test_scenario_17": ["ABPT", "(FED) - TDICE", "IDP_Platform", "ISBUS", "IDP-Commerce-ES", "T.Data", "Nimbus", "IDP-IDM", "GRP-ICAP", "TRiP", "ECO Suite", "TDICE"],
    "test_scenario_18": ["ABPT", "IDP-Order Graph Cloud", "SHM", "Amp-MM - Invenio", "Nimbus", "IDP-IDM", "ECO Suite", "TRiP", "IDP_Platform", "GRP-ICAP", "ISBUS", "TDICE"],
    "test_scenario_19": ["ABPT", "IDP-Commerce-ES", "T.Data", "GRP-ICAP", "IDP-Order Graph Cloud", "Amp-MM - Invenio", "SHM", "Nimbus", "TRiP", "ECO Suite", "IDP-IDM", "TDICE"],
    "test_scenario_20": ["ABPT", "TDICE"],

        # Custom chain for Lookup Customer scenario
        "lookup_customer_chain": [
            "CCSF",
            "CCMULE",
            "IDP-Cloud-CG",
            "DPG - Sales & Sunrise",
            "Platform Support ATTFEDGOV1",
            "eTRACS"
        ],
}

# chain_20 is a fork-join path:
# ABPT fans out to two service branches, then joins at TDICE.

# chain_5 (simulation 5) is a dynamic, randomized 4-branch fork-join with nested gateway support.
# Each run randomly chooses paths through the branches, resulting in different execution sequences.
# Minimum chain length: 12 (ABPT + 10 unique services + TDICE).

FORKED_CHAIN_DEFINITIONS = {
    "test_scenario_5": {
        "entry": "ABPT",
        "branches": [
            # Branch 1: 10 services (supports minimum chain length 12 = ABPT+10+TDICE)
            ["T.Data", "IDP-IDM", "GRP-ICAP", "Nimbus", "ECO Suite", "Amp-MM - Invenio", "IDP-Order Graph Cloud", "SHM", "IDP-Commerce-ES", "TRiP"],
            # Branch 2: 8 services
            ["IDP_Platform", "(FED) - TDICE", "ISBUS", "T.Data", "GRP-ICAP", "Nimbus", "ECO Suite", "Amp-MM - Invenio"],
            # Branch 3: 9 services
            ["Amp-MM - Invenio", "IDP-Order Graph Cloud", "SHM", "IDP-IDM", "TRiP", "IDP_Platform", "ISBUS", "Nimbus", "ECO Suite"],
            # Branch 4: 8 services
            ["(FED) - TDICE", "IDP-Commerce-ES", "T.Data", "IDP-IDM", "GRP-ICAP", "Amp-MM - Invenio", "IDP-Order Graph Cloud", "SHM"],
        ],
        "join": "TDICE",
        "dynamic": True,  # Flag for randomized path selection
    },
    "test_scenario_20": {
        "entry": "ABPT",
        "branches": [
            ["Nimbus", "ECO Suite", "IDP_Platform", "T.Data"],
            ["IDP-Commerce-ES", "Amp-MM - Invenio", "ISBUS", "TRiP", "GRP-ICAP", "IDP-IDM"],
        ],
        "join": "TDICE",
    }
}

# chain_10 branches after the second service (T.Data):
# ABPT -> T.Data -> (branch_1 with 3 services + branch_2 with 1 service) -> joined tail of 5 services.

BRANCHED_CHAIN_DEFINITIONS = {
    "test_scenario_10": {
        "fork_at": "T.Data",
        "branches": [
            ["IDP-IDM", "Amp-MM - Invenio"],
            ["GRP-ICAP"],
        ],
        "joined_tail": ["IDP-Commerce-ES", "SHM", "IDP-Order Graph Cloud", "TRiP", "Nimbus", "TDICE"],
    }
}

LONG_CHAIN_ID = "test_scenario_19"


def get_service_url(service_name: str) -> str:
    spec = SERVICE_BY_NAME[service_name]
    return f"http://localhost:{spec['port']}{spec['path']}"


def get_possible_downstream_names(service_name: str) -> list[str]:
    downstream_names = []
    for chain in CHAIN_DEFINITIONS.values():
        for index, current_name in enumerate(chain[:-1]):
            if current_name == service_name:
                next_name = chain[index + 1]
                if next_name not in downstream_names:
                    downstream_names.append(next_name)

    for forked_chain in FORKED_CHAIN_DEFINITIONS.values():
        entry = forked_chain["entry"]
        join = forked_chain["join"]
        branches = forked_chain["branches"]

        if service_name == entry:
            for branch in branches:
                if branch and branch[0] not in downstream_names:
                    downstream_names.append(branch[0])
            if join not in downstream_names:
                downstream_names.append(join)
            continue

        for branch in branches:
            for index, current_name in enumerate(branch[:-1]):
                if current_name == service_name:
                    next_name = branch[index + 1]
                    if next_name not in downstream_names:
                        downstream_names.append(next_name)

    for branched_chain in BRANCHED_CHAIN_DEFINITIONS.values():
        fork_at = branched_chain["fork_at"]
        branches = branched_chain["branches"]
        joined_tail = branched_chain["joined_tail"]

        if service_name == fork_at:
            for branch in branches:
                if branch and branch[0] not in downstream_names:
                    downstream_names.append(branch[0])
            continue

        for branch in branches:
            if not branch:
                continue
            for index, current_name in enumerate(branch[:-1]):
                if current_name == service_name:
                    next_name = branch[index + 1]
                    if next_name not in downstream_names:
                        downstream_names.append(next_name)
            if service_name == branch[-1] and joined_tail:
                join_target = joined_tail[0]
                if join_target not in downstream_names:
                    downstream_names.append(join_target)

        for index, current_name in enumerate(joined_tail[:-1]):
            if current_name == service_name:
                next_name = joined_tail[index + 1]
                if next_name not in downstream_names:
                    downstream_names.append(next_name)

    return downstream_names


def get_possible_downstream_urls(service_name: str) -> list[str]:
    return [get_service_url(name) for name in get_possible_downstream_names(service_name)]


def get_next_service_name(service_name: str, chain_id: str | None) -> str | None:
    """Get the next service in the chain, with support for randomized dynamic paths."""
    import random
    
    chain = CHAIN_DEFINITIONS.get(chain_id or "")
    if chain and service_name in chain:
        index = chain.index(service_name)
        if index == len(chain) - 1:
            return None
        return chain[index + 1]

    # Handle forked chains (including dynamic ones like test_scenario_5)
    forked_chain = FORKED_CHAIN_DEFINITIONS.get(chain_id or "")
    if forked_chain:
        entry = forked_chain["entry"]
        branches = forked_chain["branches"]
        join = forked_chain["join"]
        is_dynamic = forked_chain.get("dynamic", False)
        
        if service_name == entry:
            # Entry point: randomly choose one or more branches (or deterministic for non-dynamic)
            if is_dynamic:
                # For dynamic chains, randomly pick 1–2 branches to follow
                num_branches_to_follow = random.randint(1, 2)
                selected_branches = random.sample(branches, min(num_branches_to_follow, len(branches)))
                # Return the first service of a randomly selected branch
                first_branch = selected_branches[0]
                return first_branch[0] if first_branch else None
            else:
                # Non-dynamic: return first service of first branch
                return branches[0][0] if branches and branches[0] else None
        
        # Check if service is in any branch
        for branch in branches:
            if service_name in branch:
                idx = branch.index(service_name)
                if idx < len(branch) - 1:
                    # Return next service in the same branch
                    return branch[idx + 1]
                else:
                    # End of branch: proceed to join
                    return join
        
        # If all branches are exhausted, return the join service
        if service_name != join:
            return join
        return None

    branched_chain = BRANCHED_CHAIN_DEFINITIONS.get(chain_id or "")
    if branched_chain:
        joined_tail = branched_chain["joined_tail"]
        if service_name in joined_tail:
            idx = joined_tail.index(service_name)
            return joined_tail[idx + 1] if idx < len(joined_tail) - 1 else None
        for branch in branched_chain["branches"]:
            if service_name in branch:
                idx = branch.index(service_name)
                return branch[idx + 1] if idx < len(branch) - 1 else None

    return None