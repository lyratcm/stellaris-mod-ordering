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


#needs to be tracked in multiple functions trigger by buttons so not return
load_order_loc = ""
dependencies = []
dependencies_tracker = 0
exclusive_tracker = 0
mod_filtering_process = Process()
sorted_list = []
exclusive = []

def create_table():
    db_cursor.execute('CREATE TABLE IF NOT EXISTS sortingDB(displayName TEX, enabled INTEGER, position INTEGER, steamId INTEGER PRIMARY KEY, dependency TEX, exclusive_with TEX, priority TEX, load_after TEX, load_before TEX)')
    # db_cursor.execute('CREATE TABLE IF NOT EXISTS sortingorderDB(idno INTEGER PRIMARY KEY,datestamp TEXT, firstname TEXT, surname TEXT, age INTEGER)')


def mod_filtering_func():
    #recrate the conn link as tkinter doesn't allow it to be passed through
    dab_name = 'mod sorting.db'
    connection_link = sqlite3.connect(dab_name)
    global sorted_list
    global exclusive
    last_list = []
    # print(f"sorted: {sorted_list}")
    patch_mod_letters = ["-", "+"]
    last_load_letters = ["!"]
    priority_order = []
    patch_list = []
    main_list = []
    for char in sorted_list:
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
    # print(f"priority: {priority_order}")
    #take out the mods that should be last, that are patches and all other mods to order them
    # last_list = [char for char in sorted_list ]
    # patch_list = [char for char in sorted_list ]
    # main_list = [char for char in sorted_list ]
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
    # print(main_list)
    # connection_link.execute('DELETE FROM sortingDB')
    # connection_link.commit()
    # for mod in main_list:
    #     displayName = mod[0]
    #     enabled = mod[1]
    #     position = mod[2]
    #     steamId = mod[3]
    #     connection_link.execute("INSERT INTO sortingDB (displayName, enabled, position, steamId) VALUES (?, ?, ?, ?)", (displayName, enabled, position, steamId))
    # connection_link.commit()


def mod_ordering_func():
    global sorted_list
    global dependencies
    dependencies = []
    global exclusive
    exclusive_temp = []
    #grab a list of all dependency's
    for char in sorted_list:
        if char['dependency'][0] != 100000 and (char['dependency'][0] != ""):
            dependencies.append(json.loads(char['dependency']))
        if (char['exclusive_with'][0] != 100000) and (char['exclusive_with'][0] != "") and (char['exclusive_with'][0] != "*"):
            exclusive.append(json.loads(char['exclusive_with']))
        elif (char['exclusive_with'][0] != 100000) and (char['exclusive_with'][0] != ""):
            exclusive.append(json.loads(char['exclusive_with']))
            if exclusive[-1][2] != "":
                #move the mod name to the name field to treat the mod like a self overwrite
                exclusive[-1][0] = exclusive[-1][2]
    #try to find the mod name in the mod list so the dependency is fill and remove it from the list
    for char in sorted_list:
        if [0] in dependencies:
            dependencies.remove(json.loads(char[4]))
        if [0] in exclusive:
            exclusive_temp.append(json.loads(char[5]))
    exclusive = exclusive_temp
    # print(dependencies)
    global dependencies_tracker
    dependencies_tracker = len(dependencies)
    global exclusive_tracker
    exclusive_tracker = len(exclusive)
    #opens an ui to
    missing_mod_lbl.config(text=f"Mod {dependencies[-dependencies_tracker][0]} is missing  but is required by a mod in the play set because \n {dependencies[-dependencies_tracker][2]}")
    reuq_action_tbl.deiconify()
    main_menu_tbl.withdraw()
    global mod_filtering_process
    # mod_filtering_process = Process(target=mod_filtering_func)
    mod_filtering_process = threading.Thread(target=mod_filtering_func)



def strip_useful_mod_info(data_location):
    lowest_prio = 100000

    # connection_link.execute("DELETE FROM sortingDB")
    # connection_link.commit()
    global sorted_list
    global load_order_loc
    sorted_list = []
    if data_location != "":
        load_order_loc = data_location
    else:
        load_order_loc = "C:\\Users\\dan20\\OneDrive\\stellaris mod ordering\\op(for testing code)_backup.json"
    file_location = open(load_order_loc, "r+")
    meta_data_location = []
    meta_data = {}
    for mod_strip in file_location:
        # add a - between each of the dicts so they can be split on without removing the {} which no longer leaves them in a dict format to be converted
        mod_strip = mod_strip.replace("},{", "},-{")
        mod_strip = mod_strip.split(",-")
        # remove some of the start and end of file info
        mod_strip[0] = mod_strip[0][28:]
        mod_strip[-1] = mod_strip[-1][0:-14]
        mod_folder = Path(os.path.expanduser(f"~\\Documents\\Paradox Interactive\\Stellaris\\mod"))
        # iterate through the mod folder open every file (not folder) all should be mod files
        # extract the mod name, supported version (for future stuff) and file location which can be used to grab mods metadata
        for file in os.listdir(mod_folder):
            descriptor_file = os.path.join(mod_folder, file)
            if os.path.isfile(descriptor_file):
                for descriptor in open(descriptor_file, "r+", encoding='UTF-8'):
                    # meta_data_location.append(descriptor)
                    if descriptor.startswith("name="):
                        meta_data_location.append({"name":f"{(descriptor[5:].replace('"', "")).replace("\n","")}"})
                    if descriptor.startswith("supported_version="):
                        meta_data_location[-1]["supported_version"] = (descriptor[18:].replace('"', "")).replace("\n","")
                    if descriptor.startswith("path="):
                        meta_data_location[-1]["path"] = ((descriptor[5:].replace('"', "")).replace("\n","")).replace("_-_"," - ")
                if "path" not in meta_data_location[-1]:
                    meta_data_location[-1]["path"] = ""
                    # meta_data_location[-1]["path"] = meta_data_location[-1]["path"].replace("/", "\\\\")
                if "supported_version" not in meta_data_location[-1]:
                    meta_data_location[-1]["supported_version"] = ""
                if "name" not in meta_data_location[-1]:
                    meta_data_location[-1]["name"] = ""
                # print(f"{meta_data_location[-1]["path"]}")
                if Path(os.path.join(meta_data_location[-1]["path"], "meta_data.json5")).is_file():
                    meta = open(os.path.join(meta_data_location[-1]["path"], "meta_data.json5"), "r", encoding='UTF-8').read()
                    meta_data = json5.loads(meta)
                    for key in meta_data:
                        meta_data[key] = meta_data[key][1:-2]
                    meta_data_location[-1] = meta_data_location[-1] | meta_data
                    # for mod_info in open(os.path.join(meta_data_location[-1]["path"], "descriptor.mod"), "r", encoding='UTF-8'):
                    #     if mod_info.startswith("name="):
                    #         mod_info = mod_info[5:-2]
                    #         meta_data["name"] = mod_info
                    # print(meta_data)
                    #fill the field if the mod author wasn't using them set prio to 10k as that is the value of mods that don't care about order
                    if "exclusive_with" not in meta_data:
                        meta_data_location[-1]["exclusive_with"] = [ lowest_prio, "", "" ]
                    if "dependency" not in meta_data:
                        meta_data_location[-1]["dependency"] = [ lowest_prio, "", "" ]
                    if "priority" not in meta_data:
                        meta_data_location[-1]["priority"] = [ lowest_prio, "" ]
                    if "load_after" not in meta_data:
                        meta_data_location[-1]["load_after"] = lowest_prio
                    if "load_before" not in meta_data:
                        meta_data_location[-1]["load_before"] = lowest_prio
                    # print(mod_info["dependency"])
                else:
                    # for mod_info in open(os.path.join(mod_data_location["path"], "descriptor.mod"), "r", encoding='UTF-8'):
                    #     if mod_info.startswith("name="):
                    #         mod_info = mod_info[5:-2]
                    #         meta_data["name"] = mod_info
                    meta_data_location[-1]["priority"] = [ lowest_prio, "" ]
                    meta_data_location[-1]["dependency"] = [ lowest_prio, "", "" ]
                    meta_data_location[-1]["exclusive_with"] = [ lowest_prio, "", "" ]
                    meta_data_location[-1]["load_after"] = lowest_prio
                    meta_data_location[-1]["load_before"] = lowest_prio

            # print(meta_data_location)
        # for mod_data_location in meta_data_location:
        #     # find the mod file use it to locate the mod folder, find the meta_data and extract the info to be used later for ordering
        #     # error handling incase someone is sorting for mods they don't have
        #     # print(f"{mod_data_location["path"]}/meta_data.json5")
        #     if Path(os.path.join(mod_data_location["path"], "meta_data.json5")).is_file():
        #         meta = open(os.path.join(mod_data_location["path"], "meta_data.json5"), "r", encoding='UTF-8').read()
        #         meta_data = json5.loads(meta)
        #         for mod_info in open(os.path.join(mod_data_location["path"], "descriptor.mod"), "r", encoding='UTF-8'):
        #             if mod_info.startswith("name="):
        #                 mod_info = mod_info[5:-2]
        #                 meta_data["name"] = mod_info
        #         # print(meta_data)
        #         #fill the field if the mod author wasn't using them set prio to 10k as that is the value of mods that don't care about order
        #         if "exclusive_with" not in meta_data:
        #             meta_data["exclusive_with"] = [ lowest_prio, "", "" ]
        #         if "dependency" not in meta_data:
        #             meta_data["dependency"] = [ lowest_prio, "", "" ]
        #         if "priority" not in meta_data:
        #             meta_data["priority"] = [ lowest_prio, "" ]
        #         if "load_after" not in meta_data:
        #             meta_data["load_after"] = lowest_prio
        #         if "load_before" not in meta_data:
        #             meta_data["load_before"] = lowest_prio
        #         # print(mod_info["dependency"])
        #     else:
        #         # for mod_info in open(os.path.join(mod_data_location["path"], "descriptor.mod"), "r", encoding='UTF-8'):
        #         #     if mod_info.startswith("name="):
        #         #         mod_info = mod_info[5:-2]
        #         #         meta_data["name"] = mod_info
        #         # meta_data["name"] =
        #         meta_data["priority"] = [ lowest_prio, "" ]
        #         meta_data["dependency"] = [ lowest_prio, "", "" ]
        #         meta_data["exclusive_with"] = [ lowest_prio, "", "" ]
        #         meta_data["load_after"] = lowest_prio
        #         meta_data["load_before"] = lowest_prio
        #     # for data in meta_data_location:
        #     #     if data["name"] == meta_data["name"]:
        #     #         meta_data["supported_version"] = data["supported_version"]
        #     #         meta_data["path"] = data["path"]
        #     #get list of names, then iterate over those names. 1 iteration for finding them then an iteration per dict
        #     # meta_data_out = []
        #     # meta_data.extend(meta_data_location)
        #     # for myDict in meta_data:
        #     #     if myDict not in meta_data_out:
        #     #         meta_data_out.append(myDict)
        #
        #     # meta_data["supported_version"] = (meta_data["name"] in meta_data_location) == True
        #     # meta_data["supported_version"] = meta_data_location[meta_data_location.index()][["supported_version"]]
        #     sorted_list.append(meta_data)
        #     # print(meta_data)
    meta_info = []
    for meta_data in meta_data_location:
        if meta_data["path"] == "C:/Users/dan20/Documents/Paradox Interactive/Stellaris/mod/megacorp metamod":
            meta_info.append(meta_data)
    # print(meta_data_location)
    print(meta_info)


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
    global sorted_list
    if dependencies_tracker != 0:
        webbrowser.open(f"{dependencies[-dependencies_tracker][1]}", autoraise=True)
        # print("browser open")
        dependencies_tracker -= 1
    elif exclusive_tracker != 0:
        if exclusive[-exclusive_tracker][0] != "*":
            del sorted_list[exclusive[-exclusive_tracker]]
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