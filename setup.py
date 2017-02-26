from cx_Freeze import setup, Executable

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    code_license = f.read()

include_files = ['README.rst', 'changelog.txt']
includes = [
    'lxml._elementpath'
]
packages = []

setup(
    name='dsda_command_line',
    version='0.3.2',
    description='DSDA command line client',
    long_description=readme,
    author='4shockblast',
    license=code_license,
    options={'build_exe': {'include_files': include_files, 'includes': includes}},
    executables=[Executable('dsda_client/dsda_command_line.py', base="Console")]
)
