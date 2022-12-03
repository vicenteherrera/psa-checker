#!/bin/sh

# From: https://github.com/release-lab/install

set -e

executable_folder=${INSTALL_DIR:-"/usr/local/bin"} # Eventually, the executable file will be placed here
target="vicenteherrera/psa-checker"
owner="vicenteherrera"
repo="psa-checker"
exe_name="psa-checker"
githubUrl="https://github.com"
version=""

get_arch() {
    # darwin/amd64: Darwin axetroydeMacBook-Air.local 20.5.0 Darwin Kernel Version 20.5.0: Sat May  8 05:10:33 PDT 2021; root:xnu-7195.121.3~9/RELEASE_X86_64 x86_64
    # linux/amd64: Linux test-ubuntu1804 5.4.0-42-generic #46~18.04.1-Ubuntu SMP Fri Jul 10 07:21:24 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
    a=$(uname -m)
    case ${a} in
        "x86_64" | "amd64" )
            echo "amd64"
        ;;
        "i386" | "i486" | "i586")
            echo "386"
        ;;
        "aarch64" | "arm64" | "arm")
            echo "arm64"
        ;;
        "mips64el")
            echo "mips64el"
        ;;
        "mips64")
            echo "mips64"
        ;;
        "mips")
            echo "mips"
        ;;
        *)
            echo ${NIL}
        ;;
    esac
}

get_os(){
    # darwin: Darwin
    echo $(uname -s | awk '{print tolower($0)}')
}

if [ ! -d "$executable_folder" ]; then
    echo "**Error: install directory $executable_folder doesn't exist"
fi

os=$(get_os)
arch=$(get_arch)
file_name="${exe_name}_${os}_${arch}.tar.gz" # the file name should be download


# if version is empty
if [ -z "$version" ]; then
    asset_path=$(
        command curl -sSf https://api.github.com/repos/${owner}/${repo}/releases/latest |
        command grep -o "/${owner}/${repo}/releases/download/.*/${file_name}" |
        command head -n 1
    )
    if [ -z "$asset_path" ]; then echo "${file_name} not found in $asset_path"; exit 1; fi
    asset_uri="${githubUrl}${asset_path}"
else
    asset_uri="${githubUrl}/${owner}/${repo}/releases/download/${version}/${file_name}"
fi

echo "[1/3] Download ${asset_uri} and extract to ${executable_folder}/${exe_name}"
curl -fsSL "${asset_uri}" | tar -xz -C ${executable_folder} ${exe_name}

echo "[2/3] Make ${exe_name} executable"
chmod +x ${executable_folder}/${exe_name}

echo "[3/3] Check executable is in path"
echo "${exe_name} was installed successfully to ${exe}"
if command -v $exe_name version >/dev/null; then
    echo "Run '$exe_name --help' to get started"
else
    echo "Manually add the directory to your \$HOME/.bash_profile (or similar)"
    echo "  export PATH=${executable_folder}:\$PATH"
    echo "Run '$exe_name --help' to get started"
fi

exit 0