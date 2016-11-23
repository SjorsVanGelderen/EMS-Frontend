#!/usr/bin/python3

"""
EMS Front-end - GTK3 front-end for EMS flasher
Copyright (C) 2016  Sjors van Gelderen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re

from os import stat, getuid, path, getcwd
from subprocess import Popen, PIPE
from threading import Thread
from time import sleep

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, Gdk, GLib

# When the search key-combination is pressed
def on_key_search(widget, event = None):
    keyval = event.keyval
    name   = Gdk.keyval_name(keyval)

    mod = Gtk.accelerator_get_label(keyval, event.state)
    if mod == "Ctrl+F" or mod == "Ctrl+Mod2+F":
        search_bar.set_search_mode(not search_bar.get_search_mode())

# When the search button is pressed
def on_button_search(button):
    search_bar.set_search_mode(not search_bar.get_search_mode())

def on_button_refresh(button):
    scan_cartridge()
    
# When the flash button is pressed
def on_button_flash(button):
    dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.INFO,
                               Gtk.ButtonsType.YES_NO,
                               "Flash")
    
    dialog.format_secondary_text("Flash the changes to the cartridge?")
    response = dialog.run()
    dialog.destroy()
    
    if response == Gtk.ResponseType.YES:
        additions = [[], []]
        removals  = [[], []]
        for store in range(0, 2):
            for entry in list_stores[store]:
                if entry[2] == "To be removed":
                    removals[store].append(entry[4])
                    list_stores[store].remove(entry.iter)
                elif entry[2] == "To be flashed":
                    additions[store].append(entry[4])
                    list_stores[store].remove(entry.iter)
                elif entry[2] == "On cartridge":
                    list_stores[store].remove(entry.iter)
        
        flash_cartridge(additions, removals)
                    
# When the add button is pressed
def on_button_add(button):
    dialog = Gtk.FileChooserDialog("Select ROM files", window, Gtk.FileChooserAction.OPEN,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                    Gtk.STOCK_OPEN,   Gtk.ResponseType.OK))
    
    filter_roms = Gtk.FileFilter()
    filter_roms.set_name("GB/GBC ROM files")
    filter_roms.add_pattern("*.gb")
    filter_roms.add_pattern("*.gbc")
    dialog.add_filter(filter_roms)
    
    dialog.set_select_multiple(True)
    response = dialog.run()
    
    page_id = stack_pages.get_visible_child_name()
    target_store = list_stores[0] if page_id  == "page_1" else list_stores[1]
    if response == Gtk.ResponseType.OK:
       for path in dialog.get_filenames():
           filename = path.split("/")
           filename = filename[len(filename) - 1]
           
           duplicate = False
           for store in list_stores:
               for entry in store:
                   if entry[2] == filename:
                       duplicate = True
                       break

           if not duplicate:
               target_store.append((filename,
                                    int(stat(path).st_size / 1024),
                                    "To be flashed",
                                    "N/A",
                                    path,
                                    "#BDECB6"))
           
    dialog.destroy()

# When the remove button is pressed
def on_button_remove(button):
    page_id = stack_pages.get_visible_child_name()
    target_store = list_stores[0] if page_id  == "page_1" else list_stores[1]
    target_tree_view = tree_views[0] if page_id == "page_1" else tree_views[1]
    model, paths = target_tree_view.get_selection().get_selected_rows()
    for path in paths:
        iter = model.get_iter(path)
        if target_store[iter][2] == "On cartridge":
            target_store[iter][2] = "To be removed"
        else:
            model.remove(iter)

# When the format button is pressed
def on_button_format(button):
    dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.INFO,
                               Gtk.ButtonsType.YES_NO,
                               "Format")
    
    dialog.format_secondary_text("Are you sure you wish to format the cartridge?")
    response = dialog.run()
    dialog.destroy()

    if response == Gtk.ResponseType.YES:
        ems([{"command":  ["--bank", "1", "--format"],
              "callback": None,
              "error":    "An error occurred while formatting page 1!"},
             {"command":  ["--bank", "2", "--format"],
              "callback": None,
              "error":    "An error occurred while formatting page 2!"}])
    
        for store in list_stores:
            for entry in store:
                if entry[2] == "To be removed" or entry[2] == "On cartridge":
                    store.remove(entry.iter)

# When scanning the cartridge contents
def scan_cartridge():
    for store in list_stores:
        for entry in store:
            if entry[2] == "On cartridge":
                store.remove(entry.iter)
    
    ems([{"command":  ["--bank", "1", "--title"],
          "callback": process_scanned_data,
          "error":    "An error occurred while scanning page 1!"},
         {"command":  ["--bank", "2", "--title"],
          "callback": process_scanned_data,
          "error":    "An error occurred while scanning page 2!"}])

# When processing scanned data
def process_scanned_data(data):
    match_bank  = re.search("Bank",         data)
    match_title = re.search("Title",        data)
    match_size  = re.search("Size",         data)
    match_enh   = re.search("Enhancements", data)
    match_page  = re.search("Page: ",       data)
    
    titles_data = data[:-79].split("\n")
    titles_data.pop(0)
    
    page = int(data[match_page.end()]) - 1
    occupied_space = 0.0
    target_store = list_stores[page]
    for entry in titles_data:
        if len(entry) > 0:
            size_string   = entry[match_size.start():match_enh.start()]
            digits_string = re.search("[\d]+", size_string)
            size = int(digits_string.group())
            occupied_space += size
            
            target_store.append((entry[match_title.start():match_size.start()],
                                 size,
                                 "On cartridge",
                                 "N/A",
                                 entry[match_bank.start():match_title.start()],
                                 "#FFAAFF"))
            
    if occupied_space > 0:
        space_bars[page].set_text(str('%.2f' % (32 - occupied_space / 1024)) + \
                                  "MB remaining")
        space_bars[page].set_fraction(1 - 32 / (occupied_space / 1024))

# When flashing the cartridge
def flash_cartridge(additions, removals):
    chain = []
    
    for page in range(0, 2):
        if len(removals[page]) > 0:
            chain.append({"command":  ["--bank", str(page + 1), "--delete"] + \
                                      removals[page],
                          "callback": None,
                          "error":    "An error occurred while deleting titles from " + \
                                      "page " + str(page + 1) + "!"})

    for page in range(0, 2):
        if len(additions[page]) > 0:
            chain.append({"command":  ["--bank", str(page + 1), "--write"] + \
                                      additions[page],
                          "callback": None,
                          "error":    "An error occurred while flashing titles to " + \
                                      "page " + str(page + 1) + "!\n"               + \
                                      "Perhaps one of the ROMs you are "            + \
                                      "flashing is already on the cartridge?"})
    
    if len(removals[0])  > 0 or \
       len(removals[1])  > 0 or \
       len(additions[0]) > 0 or \
       len(additions[1]) > 0:
        ems(chain)
        scan_cartridge()

# When using the flashing utility
def ems(chain):
    def cleanup(thread_id):
        threads[thread_id].join()
        threads.pop(thread_id)

        if not threads:
            spinner.stop()
            button_add.set_sensitive(True)
            button_flash.set_sensitive(True)
            button_format.set_sensitive(True)
            button_refresh.set_sensitive(True)
            button_remove.set_sensitive(True)
            button_search.set_sensitive(True)
    
    def ems_thread(operation, thread_id):
        exit_code = -1
        for i in range(0, 3): # Perform 3 attempts
            sleep(1) # Wait for the cartridge to become available
            process = Popen(["ems-flasher"] + operation["command"], stdout = PIPE)
            output, error = process.communicate()
            exit_code = process.wait()
            
            # Check if the command was executed successfully
            if exit_code == 0:
                break

        if exit_code != 0:
            GLib.idle_add(raise_error, operation["error"])
        elif operation["callback"] != None:
            GLib.idle_add(operation["callback"], output.decode("utf-8"))
            
        GLib.idle_add(cleanup, thread_id)
    
    button_add.set_sensitive(False)
    button_flash.set_sensitive(False)
    button_format.set_sensitive(False)
    button_refresh.set_sensitive(False)
    button_remove.set_sensitive(False)
    button_search.set_sensitive(False)
    spinner.start()
            
    threads = {}
    for i in range(len(chain)):
        t = Thread(target = ems_thread, args = (chain[i], i))
        threads[i] = t
        t.start()

# When an error message should be triggered
def raise_error(message):
    dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR,
                               Gtk.ButtonsType.OK, message)
    dialog.run()
    dialog.destroy()
            
        
# ROM lists
rom_lists = []

# List stores
list_stores = []

for i in range(0, 2):
    list_stores.append(Gtk.ListStore(str, int, str, str, str, str))

# Tree views
tree_views = []

for i in range(0, 2):
    tree_views.append(Gtk.TreeView(list_stores[i]))
    tree_views[i].get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    for o, column_title in enumerate(["Title", "Size(KB)", "Status"]):
        renderer = Gtk.CellRendererText()
        column   = Gtk.TreeViewColumn(column_title, renderer, text = o, background = 5)
        column.set_sort_column_id(o)
        column.set_resizable(True)
        column.set_expand(True)
        tree_views[i].append_column(column)

# Tree lists
tree_lists = []

for i in range(0, 2):
    tree_lists.append(Gtk.ScrolledWindow())
    tree_lists[i].set_vexpand(True)
    tree_lists[i].add(tree_views[i])

# Space bars
space_bars = []

for i in range(0, 2):
    space_bars.append(Gtk.ProgressBar())
    space_bars[i].set_text("32MB remaining")
    space_bars[i].set_fraction(0.0)
    space_bars[i].set_show_text(True)
    space_bars[i].set_tooltip_text("Space remaining on this page of the cartridge")

# Page layout boxes
layout_boxes = []

for i in range(0, 2):
    layout_boxes.append(Gtk.Box())
    layout_boxes[i].set_orientation(Gtk.Orientation.VERTICAL)
    layout_boxes[i].add(tree_lists[i])
    layout_boxes[i].add(space_bars[i])

# Page stack
stack_pages = Gtk.Stack()
stack_pages.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
stack_pages.set_transition_duration(250)
stack_pages.add_titled(layout_boxes[0], "page_1", "Data page 1")
stack_pages.add_titled(layout_boxes[1], "page_2", "Data page 2")

# Page stack switcher
stack_switcher_pages = Gtk.StackSwitcher()
stack_switcher_pages.set_stack(stack_pages)
stack_switcher_pages.set_tooltip_text("Press to switch to the corresponding page")

# Search bar
search_entry = Gtk.SearchEntry()
search_bar   = Gtk.SearchBar()
search_bar.connect_entry(search_entry)
search_bar.add(search_entry)
search_bar.set_tooltip_text("Enter text here to search this page")

# Search button
icon_search   = Gio.ThemedIcon(name = "search")
image_search  = Gtk.Image.new_from_gicon(icon_search, Gtk.IconSize.BUTTON)
button_search = Gtk.Button()
button_search.connect("clicked", on_button_search)
button_search.add(image_search)
button_search.set_tooltip_text("Search this page")

# Main vertical layout box
layout_box_main = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)
layout_box_main.add(search_bar)
layout_box_main.add(stack_pages)

# Flash button
icon_flash   = Gio.ThemedIcon(name = "document-send")
image_flash  = Gtk.Image.new_from_gicon(icon_flash, Gtk.IconSize.BUTTON)
button_flash = Gtk.Button()
button_flash.connect("clicked", on_button_flash)
button_flash.add(image_flash)
button_flash.set_tooltip_text("Flash changes to the cartridge")

# Add button
icon_add   = Gio.ThemedIcon(name = "list-add")
image_add  = Gtk.Image.new_from_gicon(icon_add, Gtk.IconSize.BUTTON)
button_add = Gtk.Button()
button_add.connect("clicked", on_button_add)
button_add.add(image_add)
button_add.set_tooltip_text("Open a file picker to add new ROMs to this page")

# Refresh button
icon_refresh   = Gio.ThemedIcon(name = "view-refresh")
image_refresh  = Gtk.Image.new_from_gicon(icon_refresh, Gtk.IconSize.BUTTON)
button_refresh = Gtk.Button()
button_refresh.connect("clicked", on_button_refresh)
button_refresh.add(image_refresh)
button_refresh.set_tooltip_text("Re-read cartridge contents")

# Remove button
icon_remove   = Gio.ThemedIcon(name = "list-remove")
image_remove  = Gtk.Image.new_from_gicon(icon_remove, Gtk.IconSize.BUTTON)
button_remove = Gtk.Button()
button_remove.connect("clicked", on_button_remove)
button_remove.add(image_remove)
button_remove.set_tooltip_text("Remove selected ROMs from this page")

# Format button
icon_format   = Gio.ThemedIcon(name = "edit-clear")
image_format  = Gtk.Image.new_from_gicon(icon_format, Gtk.IconSize.BUTTON)
button_format = Gtk.Button()
button_format.connect("clicked", on_button_format)
button_format.add(image_format)
button_format.set_tooltip_text("Format the cartridge")

# Spinner
spinner = Gtk.Spinner()
spinner.set_tooltip_text("Indicates cartridge access")

# Header bar
header_bar = Gtk.HeaderBar()
header_bar.set_show_close_button(True)
header_bar.props.title = "GB USB Smart Card Flasher"
header_bar.pack_start(stack_switcher_pages)
header_bar.pack_start(spinner)
header_bar.pack_end(button_search)
header_bar.pack_end(Gtk.VSeparator())
header_bar.pack_end(button_remove)
header_bar.pack_end(button_add)
header_bar.pack_end(Gtk.VSeparator())
header_bar.pack_end(button_format)
header_bar.pack_end(button_flash)
header_bar.pack_end(button_refresh)

# Window
window = Gtk.Window()
window.set_icon_from_file("Game-Boy-Color-Game.png")
window.set_border_width(10)
window.set_default_size(1024, 768)
window.set_titlebar(header_bar)
window.add(layout_box_main)
window.connect("key-press-event", on_key_search)
window.connect("delete-event", Gtk.main_quit)

# Initialize the program
scan_cartridge()
window.show_all()
Gtk.main()
