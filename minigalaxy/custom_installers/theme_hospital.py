import os


def start(game):
    err_msg = ""
    create_save_dir(game)
    change_language_to_en(game)
    create_start_script(game)
    return err_msg


def create_save_dir(game):
    hospital_saves_dir = os.path.join(game.install_dir, "SAVE")
    if not os.path.isdir(hospital_saves_dir):
        os.makedirs(hospital_saves_dir)


def change_language_to_en(game):
    hospital_cfg_file = os.path.join(game.install_dir, "HOSPITAL.CFG")
    if os.path.isfile(hospital_cfg_file):
        cfg_file = open(hospital_cfg_file, "r")
        cfg_content = cfg_file.readlines()
        cfg_file.close()
        cfg_content_mod = []
        for cfg_line in cfg_content:
            if "LANGUAGE=" in cfg_line:
                cfg_content_mod.append("LANGUAGE=EN\n")
            else:
                cfg_content_mod.append(cfg_line)
        cfg_file = open(hospital_cfg_file, "w")
        for cfg_line in cfg_content_mod:
            cfg_file.write(cfg_line)
        cfg_file.close()


def create_start_script(game):
    hospital_start_file = os.path.join(game.install_dir, "minigalaxy-start.sh")
    start_script = '#!/bin/bash\ndosbox  "{}/HOSPITAL.EXE" -exit -fullscreen'.format(game.install_dir)
    start_file = open(hospital_start_file, "w")
    start_file.write(start_script)
    start_file.close()
    os.chmod(hospital_start_file, 0o775)
