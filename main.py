#!/usr/bin/python

"""
EMS Frontend - GTK3 frontend for EMS flasher
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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, Gdk

from os import stat

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

# When the add button is pressed
def on_button_add(button):
    dialog = Gtk.FileChooserDialog("Select ROM files",
                                   window, Gtk.FileChooserAction.OPEN,
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
       for filename in dialog.get_filenames():
           target_store.append((filename,
                                "{} bytes".format(str(stat(filename).st_size)),
                                "Ready to flash", "#BDECB6"))
           
    dialog.destroy()

# When the remove button is pressed
def on_button_remove(button):
    page_id = stack_pages.get_visible_child_name()
    target_tree_view = tree_views[0] if page_id == "page_1" else tree_views[1]
    model, paths = target_tree_view.get_selection().get_selected_rows()
    for path in paths:
        iter = model.get_iter(path)
        model.remove(iter)

# When the flash button is pressed
def on_button_flash(button):
    dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.INFO,
                               Gtk.ButtonsType.OK,
                               "Flashing to smart card...")
    
    dialog.format_secondary_text("Please wait until the operation is finished.")
    dialog.run()
    dialog.destroy()

# ROM lists
rom_lists = []

# List stores
list_stores = []

for i in range(0, 2):
    list_stores.append(Gtk.ListStore(str, str, str, str))
    
    # for rom in rom_lists[i]:
    #     list_stores[i].append(list(rom))

# Tree views
tree_views = []

for i in range(0, 2):
    tree_views.append(Gtk.TreeView(list_stores[i]))
    tree_views[i].get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
    for o, column_title in enumerate(["Title", "Size", "Status"]):
        renderer = Gtk.CellRendererText()
        column   = Gtk.TreeViewColumn(column_title, renderer, text = o, background = 3)
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
    space_bars[i].set_text("16MB remaining")
    space_bars[i].set_fraction(0.5)
    space_bars[i].set_show_text(True)
    space_bars[i].set_tooltip_text("Shows the space remaining on this page of the cartridge")

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

# Add button
icon_add   = Gio.ThemedIcon(name = "list-add")
image_add  = Gtk.Image.new_from_gicon(icon_add, Gtk.IconSize.BUTTON)
button_add = Gtk.Button()
button_add.connect("clicked", on_button_add)
button_add.add(image_add)
button_add.set_tooltip_text("Open a file picker to add new ROMs to this page")

# Remove button
icon_remove   = Gio.ThemedIcon(name = "list-remove")
image_remove  = Gtk.Image.new_from_gicon(icon_remove, Gtk.IconSize.BUTTON)
button_remove = Gtk.Button()
button_remove.connect("clicked", on_button_remove)
button_remove.add(image_remove)
button_remove.set_tooltip_text("Remove selected ROMs from this page")

# Flash button
icon_flash   = Gio.ThemedIcon(name = "document-send")
image_flash  = Gtk.Image.new_from_gicon(icon_flash, Gtk.IconSize.BUTTON)
button_flash = Gtk.Button()
button_flash.connect("clicked", on_button_flash)
button_flash.add(image_flash)
button_flash.set_tooltip_text("Flash changes to the cartridge")

# Header bar
header_bar = Gtk.HeaderBar()
header_bar.set_show_close_button(True)
header_bar.props.title = "GB USB Smart Card Flasher"
header_bar.pack_start(stack_switcher_pages)
header_bar.pack_end(button_search)
header_bar.pack_end(button_add)
header_bar.pack_end(button_remove)
header_bar.pack_end(button_flash)

# Spinner
# spinner = Gtk.Spinner()
# spinner.start()

# Window
window = Gtk.Window()
window.set_border_width(10)
window.set_default_size(800, 600)
window.set_titlebar(header_bar)
window.add(layout_box_main)
window.connect("key-press-event", on_key_search)
window.connect("delete-event", Gtk.main_quit)
window.show_all()
Gtk.main()
