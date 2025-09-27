#!/usr/bin/env bash

set -euo pipefail

REPO_URL=${BACKFLIP_REPO_URL:-https://github.com/zZedix/BackFlip}
INSTALL_ROOT=${BACKFLIP_INSTALL_ROOT:-/opt/backflip}

info() {
    printf '\033[0;34m[INFO]\033[0m %s\n' "$1" >&2
}

success() {
    printf '\033[0;32m[SUCCESS]\033[0m %s\n' "$1" >&2
}

error() {
    printf '\033[0;31m[ERROR]\033[0m %s\n' "$1" >&2
}

require_root() {
    if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
        error "This installer must run with root privileges (try sudo)."
        exit 1
    fi
}

require_apt() {
    if ! command -v apt-get >/dev/null 2>&1; then
        error "This installer only supports Ubuntu/Debian systems with apt-get available."
        exit 1
    fi
}

install_packages() {
    info "Updating package index"
    apt-get update >/dev/null
    info "Installing system dependencies"
    DEPS=(python3 python3-venv python3-pip git autossh openssh-client)
    apt-get install -y --no-install-recommends "${DEPS[@]}" >/dev/null
}

ensure_virtualenv() {
    local venv_dir="$1"
    if [[ ! -d "$venv_dir" ]];
    then
        info "Creating Python virtual environment at ${venv_dir}"
        python3 -m venv "$venv_dir"
    else
        info "Reusing existing virtual environment at ${venv_dir}"
    fi
    "${venv_dir}/bin/pip" install --upgrade pip setuptools wheel >/dev/null
}

refresh_source() {
    local checkout_dir="$1"
    if [[ -d "${checkout_dir}/.git" ]]; then
        info "Updating Backflip sources in ${checkout_dir}"
        git -C "$checkout_dir" fetch --depth 1 origin main >/dev/null
        git -C "$checkout_dir" reset --hard origin/main >/dev/null
    else
        info "Cloning Backflip sources from ${REPO_URL}"
        rm -rf "$checkout_dir"
        git clone --depth 1 "$REPO_URL" "$checkout_dir" >/dev/null
    fi
}

resolve_project_root() {
    local candidate

    # 1) If script sits inside a checked-out project, reuse it
    if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
        candidate=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
        if [[ -f "${candidate}/pyproject.toml" ]]; then
            echo "$candidate"
            return
        fi
    fi

    # 2) If current directory already contains the project
    candidate=$(pwd)
    if [[ -f "${candidate}/pyproject.toml" && -d "${candidate}/backflip" ]]; then
        echo "$candidate"
        return
    fi

    # 3) Otherwise fetch/update under INSTALL_ROOT
    local checkout_dir="${INSTALL_ROOT}/src"
    refresh_source "$checkout_dir"
    echo "$checkout_dir"
}

sync_project() {
    local venv_dir="$1"
    local source_dir="$2"
    info "Installing Backflip package inside the virtual environment"
    "${venv_dir}/bin/pip" install --upgrade "${source_dir}" >/dev/null
}

link_binaries() {
    local venv_dir="$1"
    local bin_dir="/usr/local/bin"
    install -d "$bin_dir"
    ln -sf "${venv_dir}/bin/backflip" "${bin_dir}/backflip"
    ln -sf "${venv_dir}/bin/backflip-install" "${bin_dir}/backflip-install"
}

run_installer() {
    local venv_dir="$1"
    local project_root="$2"
    local python_bin="${venv_dir}/bin/python"
    local installer_path="${project_root}/scripts/install.py"
    info "Launching interactive Backflip installer"
    if [[ -t 0 && -t 1 ]]; then
        if ! "${python_bin}" "${installer_path}"; then
            error "Interactive installer failed."
            exit 1
        fi
        return
    fi

    local quoted_cmd
    printf -v quoted_cmd "%q " "${python_bin}" "${installer_path}"
    quoted_cmd="env BACKFLIP_SIMPLE_PROMPT=1 ${quoted_cmd% }"

    if [[ -r /dev/tty ]]; then
        info "Attaching to /dev/tty for interactive prompts"
        if ! env BACKFLIP_SIMPLE_PROMPT=1 "${python_bin}" "${installer_path}" < /dev/tty > /dev/tty 2>&1; then
            error "Interactive installer failed."
            exit 1
        fi
        return
    fi

    if command -v script >/dev/null 2>&1; then
        info "Allocating pseudo-TTY via script(1)"
        if ! script -q -c "${quoted_cmd}" /dev/null; then
            error "Interactive installer failed."
            exit 1
        fi
        return
    fi

    error "No interactive TTY detected. Run this installer from a terminal (e.g. ssh session)."
    exit 1
}

main() {
    require_root
    require_apt

    local venv_dir="${INSTALL_ROOT}/venv"
    install -d "$INSTALL_ROOT"

    install_packages
    ensure_virtualenv "$venv_dir"
    local project_root
    project_root=$(resolve_project_root)
    sync_project "$venv_dir" "$project_root"
    link_binaries "$venv_dir"
    run_installer "$venv_dir" "$project_root"

    success "Backflip installation finished successfully."
    info "Use the backflip command to manage the service."
}

main "$@"
