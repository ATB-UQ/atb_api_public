# Automated Topology Builder (ATB) API Version 0.1

Public Python client (import name `atb_api`, distribution `atb_api`) for the ATB **v0.1** web API.
**Status: legacy.** The current client is [`atb_client`](https://github.com/ATB-UQ/atb_client) for API v1;
this package stays for existing user scripts and for platform siblings that still import it. Python 3.9-3.13,
dependencies `requests`, `pyyaml`; no tests.


## Installation

The ATB API can be installed directly from this remote repository using pip:

```pip install git+https://github.com/ATB-UQ/atb_api_public.git```

Or by cloning this repository and installing from the within the source directory:

```pip install .```


## Example use

```
from atb_api import API
# Send an email to the ATB administrators to request an API token
api = API(api_token='<your_api_token_here>')
molecules = api.Molecules.search(common_name='Pterostilbene', match_partial=False)

for molecule in molecules:
    print(molecule.inchi)
    pdb_path = '{molid}.pdb'.format(molid=molecule.molid)
    molecule.download_file(fnme=pdb_path, atb_format='pdb_aa') # Get All-Atom (aa) PDB
```
		
More detailed example use is provided in the `examples` folder.

## The three ATB client libraries

| Package (import name) | Talks to | Status | Who uses it |
|---|---|---|---|
| `atb_client` (`atb_client`) | API **v1** (`/api/v1`, keyed, JSON, typed) | **Current.** New code goes here. Includes `atb_client.legacy.API`, an `atb_api`-compatible shim on v1 | `website` (API docs), `pipeline`, `compute_tasks`, `atb_submission_targets`, `dihedral_gap_service`, `dihedral_scan_service`, `atb_microstates`, `rotamer_ladder`, `atb_api_job_pipeline` (v1 mode) |
| `atb_api_public` (`atb_api`) | API **v0.1** (token in query string, YAML/JSON/pickle) | **Public legacy.** The package users `pip install` from GitHub; frozen except for fixes the platform needs | `atb_api_job_pipeline` (v0.1 mode), `dihedral_fragments`, `gromos_job_wrapper`, `amber_converter`, `pyscf_interface`, `xTB_interface`, `dihedral_scan_service` (tests), `orbmol_interface` |
| `API_client` (`API_client`) | API **v0.1** | **Internal legacy fork** of `atb_api` with extra namespaces (`Users`, `Events`, `Validations`, `Compounds`, `Fragments`, `Dihedrals`, solvation free energies) and the internal-token header. Not for users | `website/website/tasks/*`, `compute_tasks`, `pipeline`, `core` (tests), `solvation_fe_ti`, `gromos_job_wrapper`, `atb_condensed_phase`, `atb_submission_targets`, `dihedral_*`, `fragment_merger`, `Blind_RMSD` |

`atb_api` and `API_client` are the same code base (~460 differing lines, the fork being the larger one)
and are both API v0.1 clients; v0.1 is kept running for them while callers move to v1. Several
platform callers choose at run time: with a service key in the keyring (`atb_server_settings.secrets.service_api_key`)
they use `atb_client` on v1, without one they fall back to `API_client`/`atb_api` and the internal token
(`pipeline/api_v1.py`, `atb_api_job_pipeline/api.py`). `atb_client` is import-name-independent of the two,
so all three install side by side. Migration path for an `atb_api` script: change the import to
`atb_client.legacy`, then to `ATBClient` (`atb_client` docs, "Migrating from atb_api").
Checked 2026-10-07 by grep over the sibling checkouts; scripts under `old/` and `.worktrees/` excluded.

## Notes for platform use

- `API(host=..., api_token=..., internal_token=None, api_format='yaml', timeout=45, maximum_attempts=1)`;
  `internal_token` sends `X-ATB-Internal-Token` for ATB's own server-side callers.
- Only `API` is re-exported from `atb_api`; `HTTPError` and `API_Timeout` must be imported from `atb_api.atb_api`.
- Namespaces: `Molecules`, `QM_Calculations`, `Jobs`, `RMSD`, `Statistics`, all in `src/atb_api/atb_api.py`.
- Remote: `ATB-UQ/atb_api_public`; the sibling checkout directory is `atb_api_public`.
