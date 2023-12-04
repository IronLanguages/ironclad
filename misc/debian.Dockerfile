FROM mcr.microsoft.com/devcontainers/dotnet:0-6.0
#                                           ^ == bullseye

SHELL ["bash", "-c"]

# Install IronPython
RUN sudo -u vscode -i dotnet tool install --global ironpython.console --version 3.4.1

# Install Python and other build tools
RUN apt update && apt upgrade -y
RUN \
    apt install -y lsb-release wget software-properties-common gnupg git && \
    apt install -y python3-pip && \
    apt install -y python-is-python3 && \
    apt install -y scons && \
    apt install -y castxml python3-pygccxml && \
    apt install -y nasm && \
    true

# Install Clang/LLVM ver. 13, which is the newest on Debian Bullseye
RUN ver=13 && \
    apt install -y clang-${ver} lld-${ver} && \
    update-alternatives --install  /usr/bin/llvm-config  llvm-config  /usr/lib/llvm-${ver}/bin/llvm-config  ${ver}0  && \
    shopt -s extglob && \
    cd /usr/lib/llvm-${ver}/bin && \
    declare -a progs=($(ls !(llvm-config))) && \
    declare -a sublinks && \
    for prog in ${progs[@]}; do  \
        sublinks+=(--slave  /usr/bin/${prog}  ${prog}  /usr/lib/llvm-${ver}/bin/${prog});  \
    done && \
    update-alternatives --install  /usr/bin/llvm-config  llvm-config  /usr/lib/llvm-${ver}/bin/llvm-config  ${ver}0 ${sublinks[@]}  && \
    true

# Install CPython build prerequisites, based on https://github.com/pyenv/pyenv/wiki#suggested-build-environment
RUN apt install -y \
        build-essential curl openssl make \
        libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    && true

# Compile and install CPython 3.4
# pip/ensurepip refuses to install due to mismatch of libssl-dev version
RUN \
    cd /usr/src && \
    wget https://www.python.org/ftp/python/3.4.4/Python-3.4.4.tgz && \
    tar -xzf Python-3.4.4.tgz && \
    rm Python-3.4.4.tgz && \
    cd Python-3.4.4 && \
    ./configure && \
    make && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.4.4 && \
    true

