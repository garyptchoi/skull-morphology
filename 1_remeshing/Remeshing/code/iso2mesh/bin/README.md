MeshFix is installed here by `setup_remeshing` from the official
[iso2mesh binaries](https://github.com/fangq/iso2mesh/tree/4a0ca5b65d5d292b83b40fd0fdcb742625e573a6/bin).

The setup chooses the binary for the current MATLAB architecture and sets its
executable permission on macOS/Linux. For an offline installation, copy the
matching binary here and run `setup_remeshing('DownloadMeshFix', false)`.
On Windows, save `meshfix_x86-64.exe` as `meshfix.exe`.

MeshFix is by Marco Attene. Its corresponding source is maintained in
[fangq/meshfix](https://github.com/fangq/meshfix). See the upstream license and
publication information before redistributing it.
