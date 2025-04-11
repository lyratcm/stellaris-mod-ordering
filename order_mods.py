import ast
import os.path
import re
import tkinter as tk
import sqlite3
import json
from pathlib import Path
import webbrowser
import time
from multiprocessing import Process
import threading
import json5
import zipfile


#needs to be tracked in multiple functions trigger by buttons so not return
load_order_loc = ""
dependencies = []
dependencies_tracker = 0
exclusive_tracker = 0
mod_filtering_process = Process()
meta_data_location = []
exclusive = []

def create_table():
    db_cursor.execute('CREATE TABLE IF NOT EXISTS sortingDB(displayName TEX, enabled INTEGER, position INTEGER, steamId INTEGER PRIMARY KEY, dependency TEX, exclusive_with TEX, priority TEX, load_after TEX, load_before TEX)')
    # db_cursor.execute('CREATE TABLE IF NOT EXISTS sortingorderDB(idno INTEGER PRIMARY KEY,datestamp TEXT, firstname TEXT, surname TEXT, age INTEGER)')


def mod_filtering_func():
    #recrate the conn link as tkinter doesn't allow it to be passed through
    dab_name = 'mod sorting.db'
    connection_link = sqlite3.connect(dab_name)
    global meta_data_location
    global exclusive
    last_list = []
    # print(f"sorted: {sorted_list}")
    patch_mod_letters = ["-", "+"]
    last_load_letters = ["!"]
    priority_order = []
    patch_list = []
    main_list = []
    for char in meta_data_location:
        if char['priority'][0] != 100000:
            priority_order.append(char)
        else:
            if any(value in char['displayName'] for value in last_load_letters):
                last_list.append(char)
            if any(value in char['displayName'] for value in patch_mod_letters) and not any(value in char['displayName'] for value in last_load_letters):
                patch_list.append(char)
            if not any(value in char['displayName'] for value in last_load_letters) and not any(value in char['displayName'] for value in patch_mod_letters):
                main_list.append(char)
    priority_order = sorted(priority_order, key=lambda s: s['priority'][0])
    #take out the mods that should be last, that are patches and all other mods to order them
    main_list.sort(key = lambda x: x['displayName'], reverse=True)
    patch_list.sort(key = lambda x: x['displayName'],reverse=True)
    for i in range(len(patch_list)):
        main_list.append(patch_list[i])
    # sort based on ! due to stellaris loading
    last_list = sorted(last_list, key=lambda s: s['displayName'].count('!'))
    for i in range(len(last_list)):
        main_list.append(last_list[i])
    for i in range(len(main_list)):
        priority_order.append(main_list[i])

    #make the position match the order in the list
    for i in range(len(main_list)):
        main_list[i][2] = i+1
    print(main_list)


def mod_ordering_func():
    global meta_data_location
    # print(meta_data_location)
    global dependencies
    dependencies = []
    global exclusive
    exclusive_temp = []
    #grab a list of all dependency's
    for dicts in meta_data_location:
        try:
            if dicts['dependency'][0][0] != 100000 and (dicts['dependency'][0][0] != ""):
                # dependencies.append(dicts['dependency'])
                for meta in dicts['dependency']:
                    dependencies.append(meta)
            if (dicts['exclusive_with'][0][0] != 100000) and (dicts['exclusive_with'][0][0] != ""):
                for meta in dicts['exclusive_with']:
                    exclusive.append(meta)
                # print(dicts['exclusive_with'])
            # elif (dicts['exclusive_with'][0][0] != 100000) and (dicts['exclusive_with'][0][0] != ""):
            #     exclusive.append(dicts['exclusive_with'])
            #     print(dicts['exclusive_with'])
            #     if exclusive[-1][0][2] != "":
            #         #move the mod name to the name field to treat the mod like a self overwrite
            #         exclusive[-1][0][0] = exclusive[-1][0][2]
            elif 'exclusive_with' in dicts and dicts['exclusive_with'][0][0] != 100000:
                #fall back to catch missed metadata
                print(dicts['exclusive_with'])
        except KeyError:
            print(dicts)
    # print(dependencies)
    #try to find the mod name in the mod list so the dependency is fill and remove it from the list
    # print(meta_data_location)
    for char in meta_data_location:
        for dependant in dependencies:
            if char["name"][0] == dependant[0]:
                # print(f"{dependant}, {char["name"]}")
                dependencies.remove(dependant)
            if char["name"][0] in dependant[0]:
                exclusive_temp.append(dependant)
    exclusive = exclusive_temp
    # print(exclusive_temp)
    global dependencies_tracker
    dependencies_tracker = len(dependencies)
    global exclusive_tracker
    exclusive_tracker = len(exclusive)
    #opens an ui to
    print(exclusive)
    try:
        missing_mod_lbl.config(text=f"Mod {dependencies[-dependencies_tracker][0]} is missing but is required by a mod in the play set because \n {dependencies[-dependencies_tracker][2]}")
    except IndexError:
        print(dependencies)
    reuq_action_tbl.deiconify()
    main_menu_tbl.withdraw()
    global mod_filtering_process
    # mod_filtering_process = Process(target=mod_filtering_func)
    mod_filtering_process = threading.Thread(target=mod_filtering_func)

def replace_text(text, replace:list, replace_to:str = ""):
    for ch in replace:
        if ch in text:
            text = text.replace(ch,replace_to )
    return text


def strip_useful_mod_info(data_location:str):
    lowest_prio = 100000
    global meta_data_location
    global load_order_loc
    meta_data_location = []
    mod_names = []
    if data_location != "":
        load_order_loc = data_location
    else:
        load_order_loc = "C:\\Users\\dan20\\OneDrive\\stellaris mod ordering\\op(for testing code)_backup.json"
    file_location = open(load_order_loc, "r+")
    meta_data_location = [{"name":[],"supported_version":[],"path":[]}]
    for mod_strip in file_location:
        # add a - between each of the dicts so they can be split on without removing the {} which no longer leaves them in a dict format to be converted
        mod_strip = mod_strip.replace("},{", "},-{")
        mod_strip = mod_strip.split(",-")
        # remove some of the start and end of file info
        mod_strip[0] = mod_strip[0][28:]
        mod_strip[-1] = mod_strip[-1][0:-14]
        for jsons in range(len(mod_strip)):
            mod_strip[jsons] = json.loads(mod_strip[jsons])
        # print(mod_strip)
        for mod_name in mod_strip:
            mod_names.append(mod_name["displayName"])
        # print(mod_names)
        mod_folder = Path(os.path.expanduser(f"~\\Documents\\Paradox Interactive\\Stellaris\\mod"))
        # iterate through the mod folder open every file (not folder) all should be mod files
        # extract the mod name, supported version (for future stuff) and file location which can be used to grab mods metadata
        for file in os.listdir(mod_folder):
            descriptor_file = os.path.join(mod_folder, file)
            if os.path.isfile(descriptor_file):
            # if any(value[5:-2] in mod_names for value in open(descriptor_file, "r+", encoding='UTF-8').read()):
                for desc_line in open(descriptor_file, "r+", encoding='UTF-8'):
                    if desc_line.startswith("name="):
                        if "name" in meta_data_location[-1].keys():
                            meta_data_location.append({"name":[replace_text(desc_line, ['"',"\n","name="])]})
                        else:
                            meta_data_location[-1]["name"] = [replace_text(desc_line, ['"',"\n","name="])]
                    if desc_line.startswith("supported_version="):
                        if "supported_version" in meta_data_location[-1].keys():
                            meta_data_location.append({"name":[replace_text(desc_line, ['"',"\n","supported_version="])]})
                        else:
                            meta_data_location[-1]["supported_version"] = [replace_text(desc_line, ['"',"\n","supported_version="])]
                    if desc_line.startswith("path=") or desc_line.startswith("archive="):
                        if "path" in meta_data_location[-1].keys() or "archive" in meta_data_location[-1].keys():
                            meta_data_location.append({"path":[replace_text(replace_text(desc_line, ['"',"\n","path=","archive="]),["_-_"]," - ")]})
                        else:
                            meta_data_location[-1]["path"] = [replace_text(replace_text(desc_line, ['"',"\n","path=","archive="]),["_-_"]," - ")]
                if "path" not in meta_data_location[-1].keys():
                    meta_data_location[-1]["path"] = [""]
                if "supported_version" not in meta_data_location[-1].keys():
                    meta_data_location[-1]["supported_version"] = [""]
                if "name" not in meta_data_location[-1].keys():
                    meta_data_location[-1]["name"] = [""]
                # print(f"{type(meta_data_location[-1]["name"][0])}{type(mod_names[0])}")
                if meta_data_location[-1]["name"][0] not in mod_names:
                    del meta_data_location[-1]
                else:
                    # if there is a metadata file or there is a zip (which indicates that there's a zipped mod)
                    if Path(os.path.join(meta_data_location[-1]["path"][0], "meta_data.json5")).is_file() or Path(meta_data_location[-1]["path"][0]).is_file():
                        #handeling for mods being stored as a zip
                        # iterate through the zip find the metadata if it exsists else use fall back values
                        if Path(meta_data_location[-1]["path"][0]).is_file():
                            archive = zipfile.ZipFile(meta_data_location[-1]["path"][0], 'r')
                            if any(x.startswith("%s/" % "meta_data.json5".rstrip("/")) for x in archive.namelist()):
                                meta = archive.read("meta_data.json5")
                                meta_data = json5.loads(str(meta))
                                meta_data_location[-1] = meta_data_location[-1] | meta_data
                                #fill the field if the mod author wasn't using them set prio to 10k as that is the value of mods that don't care about order
                                if "exclusive_with" not in meta_data:
                                    meta_data_location[-1]["exclusive_with"] = [[ lowest_prio, "", "", 0]]
                                if "dependency" not in meta_data:
                                    meta_data_location[-1]["dependency"] = [[ lowest_prio, "", "" ]]
                                if "priority" not in meta_data:
                                    meta_data_location[-1]["priority"] = [[ lowest_prio, "" ]]
                                if "load_after" not in meta_data:
                                    meta_data_location[-1]["load_after"] = [lowest_prio]
                                if "load_before" not in meta_data:
                                    meta_data_location[-1]["load_before"] = [lowest_prio]
                            else:
                                meta_data_location[-1]["priority"] = [[ lowest_prio, "" ]]
                                meta_data_location[-1]["dependency"] = [[ lowest_prio, "", "" ]]
                                meta_data_location[-1]["exclusive_with"] = [[ lowest_prio, "", "", 0 ]]
                                meta_data_location[-1]["load_after"] = [lowest_prio]
                                meta_data_location[-1]["load_before"] = [lowest_prio]
                        else:
                            meta = open(os.path.join(meta_data_location[-1]["path"][0], "meta_data.json5"), "r", encoding='UTF-8').read()
                            meta_data = json5.loads(meta)
                            meta_data_location[-1] = meta_data_location[-1] | meta_data
                            #fill the field if the mod author wasn't using them set prio to 10k as that is the value of mods that don't care about order
                            if "exclusive_with" not in meta_data:
                                meta_data_location[-1]["exclusive_with"] = [[ lowest_prio, "", "", 0]]
                            if "dependency" not in meta_data:
                                meta_data_location[-1]["dependency"] = [[ lowest_prio, "", "" ]]
                            if "priority" not in meta_data:
                                meta_data_location[-1]["priority"] = [[ lowest_prio, "" ]]
                            if "load_after" not in meta_data:
                                meta_data_location[-1]["load_after"] = [lowest_prio]
                            if "load_before" not in meta_data:
                                meta_data_location[-1]["load_before"] = [lowest_prio]
                    else:
                        meta_data_location[-1]["priority"] = [[ lowest_prio, "" ]]
                        meta_data_location[-1]["dependency"] = [[ lowest_prio, "", "" ]]
                        meta_data_location[-1]["exclusive_with"] = [[ lowest_prio, "", "", 0]]
                        meta_data_location[-1]["load_after"] = [lowest_prio]
                        meta_data_location[-1]["load_before"] = [lowest_prio]
    del(meta_data_location[0])
    # tracker = 0
    # for meta_data in range(len(meta_data_location)):
    #     if meta_data_location[meta_data-tracker]["name"][0] not in mod_names:
    #         # print(meta_data_location[meta_data-tracker]["name"])
    #         del meta_data_location[meta_data-tracker]
    #         tracker +=1
    # print(meta_data_location)




def output_mod_list():
    output_mod_file_loc = export_data_txtb.get()
    if output_mod_file_loc == '':
        output_mod_file_loc = load_order_loc
    load_order_file = open(output_mod_file_loc, "w")
    output_mod_file = ['{"game":"stellaris","mods":[']
    with connection_link:
        db_cursor.execute("SELECT * FROM sortingDB")
        rows = db_cursor.fetchall()
        for row in rows:
            list(row)
            output_mod_file.append(list(row))
    # output_mod_file.append(db_cursor.execute("SELECT * FROM sortingDB"))
    output_mod_file.append([',"name":"op"}'])
    output_mod_file[1] = str(output_mod_file[1])
    # print(output_mod_file)
    output_mod_file = ''.join(output_mod_file)
    # print(output_mod_file)
    load_order_file.write(output_mod_file)


def close_link_ui():
    global dependencies_tracker
    global mod_filtering_process
    global dependencies
    global exclusive_tracker
    global exclusive
    global meta_data_location
    if dependencies_tracker != 0:
        webbrowser.open(f"{dependencies[-dependencies_tracker][1]}", autoraise=True)
        # print("browser open")
        dependencies_tracker -= 1
    elif exclusive_tracker != 0:
        if exclusive[-exclusive_tracker][0] != "*":
            del meta_data_location[exclusive[-exclusive_tracker]]
        exclusive_tracker -= 1
    if dependencies_tracker != 0:
        missing_mod_lbl.config(text=f"Mod {dependencies[-dependencies_tracker][0]} is missing but is required by a mod in the play set because {dependencies[-dependencies_tracker][2]}")
        reuq_action_tbl.deiconify()
        reuq_action_tbl.iconify()
    elif exclusive_tracker != 0:
        missing_mod_lbl.config(text=f"Mod {exclusive[-exclusive_tracker][0]} is incompatible with a mod in the play set because {exclusive[-exclusive_tracker][1]}")
        reuq_action_tbl.deiconify()
        reuq_action_tbl.iconify()
    else:
        reuq_action_tbl.withdraw()
        main_menu_tbl.deiconify()
        mod_filtering_process.start()
        # print(sorted_list)

def skip_link_ui():
    reuq_action_tbl.withdraw()
    main_menu_tbl.deiconify()
    mod_filtering_process.start()

if "__main__" == __name__:
    dab_name = 'mod sorting.db'
    connection_link = sqlite3.connect(dab_name)
    db_cursor = connection_link.cursor()

    create_table()

    main_menu_tbl = tk.Tk()
    main_menu_tbl.geometry("700x600")

    main_menu_txtb = tk.Label(main_menu_tbl, text="Mod list ordering tool", background="red", fg="white")
    main_menu_txtb.grid(row=3, column=1)
    main_menu_tbl.title("Mod list ordering tool that allows for customised ordering")

    load_data_lbl = tk.Label(main_menu_tbl, text="Insert link to mod list:")
    load_data_txtb = tk.Entry(main_menu_tbl, relief="raised")
    load_data_lbl.grid(row=8, column=0, padx=15, pady=15)
    load_data_txtb.grid(row=8, column=1)
    load_data_submit_btn = tk.Button(main_menu_tbl, text="Submit", command= lambda :strip_useful_mod_info(data_location = load_data_txtb.get()))
    load_data_submit_btn.grid(columnspan=2)

    order_mods_btn = tk.Button(main_menu_tbl, text="Sort submitted mods", command=mod_ordering_func)
    order_mods_btn.grid(row=11, column=0, padx=50, pady=15)

    export_data_lbl = tk.Label(main_menu_tbl, text="File location to output output ordered list to (if null will take input file):")
    export_data_txtb = tk.Entry(main_menu_tbl, relief="raised")
    export_data_lbl.grid(row=12, column=0, padx=15, pady=15)
    export_data_txtb.grid(row=12, column=1)
    export_data_submit_btn = tk.Button(main_menu_tbl, text="Submit", command=output_mod_list)
    export_data_submit_btn.grid(row=13, columnspan=2)

    reuq_action_tbl = tk.Tk()
    reuq_action_tbl.geometry("1000x600")

    missing_mod_lbl = tk.Label(reuq_action_tbl, text=f"Mod dependencies[dependencies_tracker][0] is missing but is required by a mod in the play set")
    missing_mod_lbl.grid(row=1, column=2, padx=15, pady=15)
    sub_to_mod_btn = tk.Button(reuq_action_tbl, text="Click here to go to mod page", command=close_link_ui)
    sub_to_mod_btn.grid(row=2, column=1)
    skip_sub_btn = tk.Button(reuq_action_tbl, text="Skip subscribing", command=skip_link_ui)
    skip_sub_btn.grid(row=2, column=2)
    #hide for later
    reuq_action_tbl.withdraw()
    main_menu_tbl.mainloop() #run form by default


# add ui to show dependency to download, show a single link then have button to show next incrating counter global