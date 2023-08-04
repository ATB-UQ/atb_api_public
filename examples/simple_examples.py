from atb_api_public.atb_api import API

# Send an email to the ATB administrators to request an API token
api = API(api_token='<ATB API TOKEN>', api_format='yaml', debug=True, timeout=60)

print(api.Molecules.molid(molid=21))

molecules = api.Molecules.search(common_name='Pterostilbene', match_partial=False)

for molecule in molecules:
    print(molecule.inchi)
    pdb_path = '{molid}.pdb'.format(molid=molecule.molid)
    molecule.download_file(fnme=pdb_path, atb_format='pdb_aa')

    with open(pdb_path) as fh:
        pdb_str = fh.read()

print(api.Molecules.structure_search(structure_format='pdb', structure=pdb_str, netcharge='*'))

# This will and should fail, as we are trying to resubmit a molecule already in the database.
print(api.Molecules.submit(pdb=pdb_str, netcharge=0, moltype='heteromolecule', public=True))

