# Automated Topology Builder (ATB) API Version 0.1

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
