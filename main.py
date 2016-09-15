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

from os import stat, getuid, path, getcwd
from subprocess import Popen, PIPE
from time import sleep

from gi import require_version
require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, Gdk

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
        ems(["--format"], [], "An error occurred while formatting the cartridge!")
        
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
    
    for page in range(1, 3):
        output = ems(["--bank", str(page), "--title"], [],
                     "An error occurred while scanning the cartridge contents!")
        data = output.decode("utf-8")
        columns = data.split("\n")[0]
        index_bank  = columns.find("Bank")
        index_title = columns.find("Title")
        index_size  = columns.find("Size")
        index_enhancements = columns.find("Enhancements")
        
        titles_data = data[:-79].split("\n")
        titles_data.pop(0)

        occupied_space = 0.0
        target_store = list_stores[page - 1]
        for entry in titles_data:
            if len(entry) > 0:
                digits = ""
                for char in entry[index_size:index_enhancements]:
                    if char in "0123456789":
                        digits += char
                
                size = int(digits)
                occupied_space += size
                
                target_store.append((entry[index_title:index_size],
                                     size,
                                     "On cartridge",
                                     "N/A",
                                     entry[index_bank:index_title],
                                     "#FFAAFF"))

        if occupied_space > 0:
            space_bars[page - 1].set_text(str('%.2f' % (32 - occupied_space / 1024)) + \
                                          "MB remaining")
            space_bars[page - 1].set_fraction(32 / (occupied_space / 1024))

# When flashing the cartridge
def flash_cartridge(additions, removals):
    output_0 = None
    output_1 = None
    for page in range(1, 3):
        if removals[page -1]:
            output_0 = ems(["--bank", str(page), "--delete"], removals[page - 1],
                           "An error occurred while deleting titles from page " + \
                           str(page) + "!")
            
        if additions[page - 1]:
            output_1 = ems(["--bank", str(page), "--write"], additions[page - 1],
                           "An error occurred while flashing titles to page " + \
                           str(page) + "!\n" + "Perhaps one of the ROMs you are" + \
                           "flashing is already on the cartridge?")
    
    if output_0 == None and output_1 == None:
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                   "Changes successfully flashed!")
        
        dialog.run()
        dialog.destroy()
    
    scan_cartridge()

# When using the flashing utility
def ems(commands, queue, error_message):
    sleep(1) # Wait for the cartridge to become available
    process = Popen(["ems-flasher"] + commands + queue, stdout = PIPE)
    output, error = process.communicate()
    exit_code = process.wait()
    
    # Check if the command was executed successfully
    if exit_code != 0:
        dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.ERROR,
                                   Gtk.ButtonsType.OK, error_message)
        
        dialog.run()
        dialog.destroy()
            
    return output
        
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

# Header bar
header_bar = Gtk.HeaderBar()
header_bar.set_show_close_button(True)
header_bar.props.title = "GB USB Smart Card Flasher"
header_bar.pack_start(stack_switcher_pages)
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
