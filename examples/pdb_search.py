import pathlib
from atb_api import API

PDB_FILES = pathlib.Path("./example_pdbs")

api = API(api_token='<ATB API TOKEN>', api_format='yaml', timeout=60)

matches = []
missing = []
for pdb_file in PDB_FILES.glob("*.pdb"):
    print(f"Searching for: {pdb_file.name}")
    with open(pdb_file) as fh:
        response = api.Molecules.structure_search(structure_format='pdb', structure=fh.read(), netcharge='*')
        if len(response["matches"]) == 0:
            print("Molecule not found")
            missing.append(pdb_file.name)
        else:
            print("Molecule(s) found: {0}".format(", ".join([f"molid={match['molid']}" for match in response["matches"]])))
            matches.append(", ".join([pdb_file.name] + [str(match['molid']) for match in response['matches']]))
    print()

print("Matches")
print("\n".join(matches))
print()
print("Missing")
print("\n".join(missing))