from atb_api import API

# Send an email to the ATB administrators to request an API token
api = API(api_token='<ATB API TOKEN>', api_format='yaml', debug=True, timeout=60)


def get_molecule_info(molid):
    print(api.Molecules.molid(molid=molid))


def get_submitted_pdb(molid):
    api.Molecules.download_file(atb_format="")


def search_by_common_name(common_name):
    print("Searching for: {}".format(common_name))
    molecules = api.Molecules.search(common_name=common_name, match_partial=False)

    molecule = molecules[0]
    print(molecule.inchi)
    return molecule.download_file(atb_format='pdb_aa')


def submit_existing_molecule(pdb_str, net_charge):
    # This will and should fail, as we are trying to resubmit a molecule already in the database.
    print(api.Molecules.submit(pdb=pdb_str, netcharge=net_charge, moltype='heteromolecule', public=True))


if __name__ == "__main__":
    get_molecule_info(21)
    get_submitted_pdb(21)
    pdb_str = search_by_common_name('Piracetam')
    submit_existing_molecule(pdb_str, 0)
