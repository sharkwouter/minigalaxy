import os
import shutil
import subprocess
import requests
import hashlib

from minigalaxy.paths import CACHE_DIR
from minigalaxy.constants import SESSION
from minigalaxy.paths import DXVK_DIR, VKD3D_DIR


# Get the latest version of DXVK available
def get_info_dxvk():
    request_url = "https://api.github.com/repos/doitsujin/dxvk/releases/latest"
    response = SESSION.get(request_url)
    response_params = response.json()
    return response_params["tag_name"][1:]


# Get the latest version of vkd3d available
def get_info_vkd3d():
    request_url = "https://api.github.com/repos/HansKristian-Work/vkd3d-proton/releases/latest"
    response = SESSION.get(request_url)
    response_params = response.json()
    return response_params["tag_name"][1:]


# Check if a new dxvk version is available
def download_latest_dxvk():
    version = get_info_dxvk()
    dxvk_archive = os.path.join(DXVK_DIR, "dxvk-{}.tar.gz".format(version))

    if not os.path.exists(dxvk_archive):
        url = "https://github.com/doitsujin/dxvk/releases/download/v{}/dxvk-{}.tar.gz".format(version, version)
        r = requests.get(url, allow_redirects=True)
        open('{}/dxvk-{}.tar.gz'.format(DXVK_DIR, version), 'wb').write(r.content)

    shutil.unpack_archive(dxvk_archive, DXVK_DIR)

    # Remove the archive and keep only DXVK folder
    os.remove(dxvk_archive)


# Check if a new vkd3d-proton version is available
def download_latest_vkd3d():
    version = get_info_vkd3d()
    vkd3d_archive_zst = os.path.join(VKD3D_DIR, "vkd3d-proton-{}.tar.zst".format(version))
    vkd3d_archive_tar = vkd3d_archive_zst[:-4]

    if not os.path.exists(vkd3d_archive_zst):
        url = "https://github.com/HansKristian-Work/vkd3d-proton/releases/download/v{}/vkd3d-proton-{}.tar.zst".format(
            version, version)
        r = requests.get(url, allow_redirects=True)
        open('{}/vkd3d-proton-{}.tar.zst'.format(VKD3D_DIR, version), 'wb').write(r.content)

    # Use check_call to be sure that the command is finished before to continue.
    subprocess.check_call(['unzstd', vkd3d_archive_zst])
    shutil.unpack_archive(vkd3d_archive_tar, VKD3D_DIR)

    # Remove both archive and keep only vkd3d-proton folder.
    os.remove(vkd3d_archive_zst)
    os.remove(vkd3d_archive_tar)


# Remove old DXVK version
def remove_old_dxvk():
    version = get_info_dxvk()
    if not len(os.listdir(DXVK_DIR)) == '0':
        for directory in os.listdir(DXVK_DIR):
            if directory[5:] != version:
                shutil.rmtree(os.path.join(DXVK_DIR, directory))


# Remove old VKD3D version
def remove_old_vkd3d():
    version = get_info_vkd3d()
    if not len(os.listdir(VKD3D_DIR)):
        for directory in os.listdir(VKD3D_DIR):
            if directory[13:] != version:
                shutil.rmtree(os.path.join(VKD3D_DIR, directory))


# Install DXVK
def install_uninstall_dxvk(state, game):
    dxvk_version = get_info_dxvk()
    dxvk_folder = os.path.join(DXVK_DIR, "dxvk-{}".format(dxvk_version))
    setup_dxvk = os.path.join(dxvk_folder, "setup_dxvk.sh")

    prefix = os.path.join(game.install_dir, "prefix")
    os.environ["WINEPREFIX"] = prefix

    # Download DXVK
    if not os.path.exists(dxvk_folder):
        download_latest_dxvk()

    # Remove old version DXVK directory
    remove_old_dxvk()

    # Retrieve d3d9.dll hash
    d3d9_prefix = hashlib.md5(
        open((os.path.join(prefix, "dosdevices/c:/windows/system32/d3d9.dll")), 'rb').read()).hexdigest()
    d3d9_dxvk = hashlib.md5(open((os.path.join(dxvk_folder, "x64/d3d9.dll")), 'rb').read()).hexdigest()

    # DXVK is installed/uninstalled each time the user clicks on button_properties_ok.
    # Even if DXVK are already installed.
    # These conditions check if dxvk/vkd3d are installed in the prefix and avoid this issue.
    if d3d9_prefix != d3d9_dxvk and state == "install":
        subprocess.Popen([setup_dxvk, 'install'])
    if d3d9_prefix == d3d9_dxvk and state == "uninstall":
        subprocess.Popen([setup_dxvk, 'uninstall'])


# Install VKD3D
def install_uninstall_vkd3d(state, game):
    vkd3d_version = get_info_vkd3d()
    vkd3d_folder = os.path.join(VKD3D_DIR, "vkd3d-proton-{}".format(vkd3d_version))
    setup_vkd3d = os.path.join(vkd3d_folder, "setup_vkd3d_proton.sh")

    prefix = os.path.join(game.install_dir, "prefix")
    os.environ["WINEPREFIX"] = prefix

    # Download VKD3D-Proton
    if not os.path.exists(vkd3d_folder):
        download_latest_vkd3d()

    # Remove old version vkd3d directory
    remove_old_vkd3d()

    # Retrieve d3d12.dll hash
    d3d12_prefix = hashlib.md5(
        open((os.path.join(prefix, "dosdevices/c:/windows/system32/d3d12.dll")), 'rb').read()).hexdigest()
    d3d12_vkd3d = hashlib.md5(open((os.path.join(vkd3d_folder, "x64/d3d12.dll")), 'rb').read()).hexdigest()

    # DXVK/VKD3D are installed/uninstalled each time the user clicks on button_properties_ok.
    # Even if DXVK/VKD3D are already installed.
    # These conditions check if dxvk/vkd3d are installed in the prefix and avoid this issue.
    if d3d12_prefix != d3d12_vkd3d and state == "install":
        subprocess.Popen([setup_vkd3d, 'install'])
    if d3d12_prefix == d3d12_vkd3d and state == "uninstall":
        subprocess.Popen([setup_vkd3d, 'uninstall'])
