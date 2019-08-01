#!/usr/bin/env python3

import os
import sys
from json2dat import encode_data_to_dat
import re
import json

# Workaround to make it possible to build on Windows
if hasattr(sys, 'frozen'):
    os.environ['PATH'] = sys._MEIPASS + ";" + os.environ['PATH']
if True:  # Dirty trick to make PyQt imports appear after if statement
    from design import Ui_MainWindow  # Importing our generated file
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication  # For quitting the program
    from PyQt5.QtCore import pyqtProperty, Qt, QVariant  # For setting colors
    from PyQt5.QtGui import QColor  # For setting colors
    from PyQt5 import QtWidgets


condition = ['at', 'carried', 'counter_eq', 'counter_gt', 'counter_le', 'exists', 'flag', 'here', 'loaded', 'moved', 'not_at',
             'not_carried', 'not_exists', 'not_flag', 'not_here', 'not_loaded', 'not_moved', 'not_present', 'present', 'parameter']
command = ['add_to_counter', 'clear', 'clear_dark', 'clear_flag', 'clear_flag0', 'continue', 'dec_counter', 'destroy', 'die', 'drop', 'game_over', 'get', 'goto', 'inventory', 'look', 'pause', 'print_counter', 'print_noun', 'println',
           'println_noun', 'put', 'put_with', 'refill_lamp', 'save_game', 'score', 'select_counter', 'set_counter', 'set_dark', 'set_flag', 'set_flag0', 'subtract_from_counter', 'superget', 'swap', 'swap_room', 'swap_specific_room', 'message', 'no_operation']
condition_argument_type = ['r', 'o', 'i', 'i', 'i', 'o', 'f', 'o',
                           '-', 'o', 'r', 'o', 'o', 'f', 'o', '-', 'o', 'o', 'o', 's', ]
command_argument_type = [['i'], [], [], ['f'], [], [], [], ['o'], [], ['o'], [], ['o'], ['r'], [], [], [], [], [], [
], [], ['o', 'r'], ['o', 'o'], [], [], [], ['i'], ['i'], [], ['f'], [], ['i'], ['o'], ['o', 'o'], [], ['i'], [], [], ]
action_data_type = {
    'a': 'action',
    'c': 'counter',  # Used in action command parameter
    'f': 'flag',    # Used in action command parameter
    'i': 'integer',  # Used in action command parameter
    'm': 'message',
    'n': 'noun',
    'o': 'object',  # Used in action command parameter
    'r': 'room',    # Used in action command parameter
    's': 'command_stack',  # Used to pass values from conditions to commands
    'v': 'verb',
    '-': 'nothing',  # Used when a condition doesn't take a parameter
}


class ExampleApp(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(ExampleApp, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Disable UI before we have data loaded
        self.ui.centralwidget.setEnabled(False)

        # Widget arrays
        self.room_exit_combobox = [self.ui.comboBox_room_exit_north, self.ui.comboBox_room_exit_south, self.ui.comboBox_room_exit_east,
                                   self.ui.comboBox_room_exit_west, self.ui.comboBox_room_exit_up, self.ui.comboBox_room_exit_down]
        self.room_combobox = self.room_exit_combobox + \
            [self.ui.comboBox_object_room, self.ui.comboBox_start_room,
                self.ui.comboBox_treasure_room]

        self.condition_combobox = [self.ui.comboBox_condition_code_1, self.ui.comboBox_condition_code_2,
                                   self.ui.comboBox_condition_code_3, self.ui.comboBox_condition_code_4, self.ui.comboBox_condition_code_5]
        self.condition_argument_spinbox = [self.ui.spinBox_condition_argument_1, self.ui.spinBox_condition_argument_2,
                                           self.ui.spinBox_condition_argument_3, self.ui.spinBox_condition_argument_4, self.ui.spinBox_condition_argument_5]
        self.condition_argument_combobox = [self.ui.comboBox_condition_argument_1, self.ui.comboBox_condition_argument_2,
                                            self.ui.comboBox_condition_argument_3, self.ui.comboBox_condition_argument_4, self.ui.comboBox_condition_argument_5]

        self.command_code_combobox = [self.ui.comboBox_command_code_1, self.ui.comboBox_command_code_2,
                                      self.ui.comboBox_command_code_3, self.ui.comboBox_command_code_4]
        self.command_message_combobox = [self.ui.comboBox_command_message_1, self.ui.comboBox_command_message_2,
                                         self.ui.comboBox_command_message_3, self.ui.comboBox_command_message_4]
        self.item_listwidget = [self.ui.listWidget_action, self.ui.listWidget_verb, self.ui.listWidget_noun,
                                self.ui.listWidget_message, self.ui.listWidget_room, self.ui.listWidget_object]

        self.header_spinbox = [self.ui.spinBox_max_objects_carried, self.ui.spinBox_treasures, self.ui.spinBox_word_length,
                               self.ui.spinBox_time_limit, self.ui.spinBox_version_number, self.ui.spinBox_adventure_number]
        self.header_combobox = [
            self.ui.comboBox_start_room, self.ui.comboBox_treasure_room]

        # Callback arrays
        self.populate_item_list = [self.populate_action_list, self.populate_verb_list, self.populate_noun_list,
                                   self.populate_message_list, self.populate_room_list, self.populate_object_list]

        self.find_item_in_item = [self.find_action_in_items,
                                  self.find_verb_in_items,
                                  self.find_noun_in_items,
                                  self.find_message_in_items,
                                  self.find_room_in_items,
                                  self.find_object_in_items]

        # Misc translation arrays
        self.listwidget_type = ['action', 'verb',
                                'noun', 'message', 'room', 'object']
        self.empty_item = [
            lambda: {'title': '',
                     'precondition': [0, 0],
                     'condition': ["parameter", "parameter", "parameter", "parameter", "parameter"],
                     'condition_argument': [0, 0, 0, 0, 0],
                     'command': ["no_operation", "no_operation", "no_operation", "no_operation"]
                     },
            lambda: '',
            lambda: '',
            lambda: '',
            lambda: {'description': '', 'exit': [0, 0, 0, 0, 0, 0]},
            lambda: {'description': '', 'noun': '', 'starting_location': 0}
        ]
        self.header_spinbox_type = ['max_objects_carried', 'number_of_treasures',
                                    'word_length', 'time_limit', 'adventure_version', 'adventure_number']
        self.header_combobox_type = ['starting_room', 'treasure_room_id']

        # Menus
        self.ui.actionOpen.triggered.connect(self.browse_open_json_file)
        self.ui.actionNew.triggered.connect(self.new_file)
        self.ui.actionSave_As.triggered.connect(self.browse_save_as_json_file)
        self.ui.actionSave.triggered.connect(self.save_json_file)
        self.ui.actionQuit.triggered.connect(QCoreApplication.instance().quit)
        self.ui.actionExport_As.triggered.connect(
            self.browse_export_as_dat_file)

        # Verbs
        self.ui.listWidget_verb.itemSelectionChanged.connect(self.select_verb)
        self.ui.lineEdit_verb.textChanged.connect(self.update_verb_text)
        self.ui.checkBox_verb_synonym.stateChanged.connect(
            self.update_verb_synonym)

        # Nouns
        self.ui.listWidget_noun.itemSelectionChanged.connect(self.select_noun)
        self.ui.lineEdit_noun.textChanged.connect(self.update_noun_text)
        self.ui.checkBox_noun_synonym.stateChanged.connect(
            self.update_noun_synonym)

        # Messages
        self.ui.listWidget_message.itemSelectionChanged.connect(
            self.select_message)
        self.ui.plainTextEdit_message.textChanged.connect(
            self.update_message_text)

        # Rooms
        self.ui.listWidget_room.itemSelectionChanged.connect(self.select_room)
        self.ui.plainTextEdit_room_description.textChanged.connect(
            self.update_room_description_text)
        for exit_index, _ in enumerate(self.room_exit_combobox):
            self.room_exit_combobox[exit_index].currentIndexChanged.connect(
                self.update_room_exits)

        # Objects
        self.ui.listWidget_object.itemSelectionChanged.connect(
            self.select_object)
        self.ui.plainTextEdit_object_description.textChanged.connect(
            self.update_object_text)
        self.ui.checkBox_object_treasure.stateChanged.connect(
            self.update_object_treasure)
        self.ui.lineEdit_object_noun.textChanged.connect(
            self.update_object_noun)
        self.ui.checkBox_object_carriable.stateChanged.connect(
            self.update_object_carriable)
        self.ui.comboBox_object_room.currentIndexChanged.connect(
            self.update_object_room)

        # Actions
        self.ui.listWidget_action.itemSelectionChanged.connect(
            self.select_action)
        self.ui.lineEdit_action_comment.textChanged.connect(
            self.update_action_comment)

        # Action preconditions
        self.ui.radioButton_precondition_verb_noun.toggled.connect(
            self.select_precondition_verb_noun)
        self.ui.radioButton_precondition_auto.toggled.connect(
            self.select_precondition_auto)
        self.ui.radioButton_precondition_subroutine.toggled.connect(
            self.select_precondition_subroutine)

        self.ui.comboBox_precondition_verb.currentIndexChanged.connect(
            self.select_precondition_verb)
        self.ui.comboBox_precondition_noun.currentIndexChanged.connect(
            self.select_precondition_noun)
        self.ui.horizontalSlider_precondition_chance.valueChanged.connect(
            self.change_horizontalSlider_precondition_chance)
        self.ui.spinBox_precondition_chance.valueChanged.connect(
            self.change_spinBox_precondition_chance)

        # Action conditions
        for condition_index, _ in enumerate(self.condition_combobox):
            self.condition_combobox[condition_index].currentIndexChanged.connect(
                self.change_condition_code)

        for condition_index, _ in enumerate(self.condition_argument_spinbox):
            self.condition_argument_spinbox[condition_index].valueChanged.connect(
                self.change_condition_spinbox)

        for condition_index, _ in enumerate(self.condition_argument_combobox):
            self.condition_argument_combobox[condition_index].currentIndexChanged.connect(
                self.change_condition_combobox)

        # Action commands
        for command_index, _ in enumerate(self.command_code_combobox):
            self.command_code_combobox[command_index].currentIndexChanged.connect(
                self.change_command_code_combobox)

        for command_index, _ in enumerate(self.command_message_combobox):
            self.command_message_combobox[command_index].currentIndexChanged.connect(
                self.change_command_message_combobox)

        # Toolbuttons
        self.ui.toolButton_Move_Up.clicked.connect(self.move_up)
        self.ui.toolButton_Move_Down.clicked.connect(self.move_down)
        self.ui.toolButton_Add_Above.clicked.connect(self.add_above)
        self.ui.toolButton_Add_Below.clicked.connect(self.add_below)
        self.ui.toolButton_Remove.clicked.connect(self.remove)

        # Header
        for combobox in self.header_combobox:
            combobox.currentIndexChanged.connect(self.change_header_combobox)
        for spinbox in self.header_spinbox:
            spinbox.valueChanged.connect(self.change_header_spinbox)

    # Header fields

    def change_header_combobox(self):
        for header_item in self.header_combobox:
            header_item.blockSignals(True)
        for header_index, header_item in enumerate(self.header_combobox):
            value = header_item.currentIndex()
            field_name = self.header_combobox_type[header_index]
            self.data['header'][field_name] = value
        for header_item in self.header_combobox:
            header_item.blockSignals(False)

    def change_header_spinbox(self):
        for header_item in self.header_spinbox:
            header_item.blockSignals(True)
        for header_index, header_item in enumerate(self.header_spinbox):
            value = header_item.value()
            field_name = self.header_spinbox_type[header_index]
            self.data['header'][field_name] = value
        for header_item in self.header_spinbox:
            header_item.blockSignals(False)

    # Toolbar buttons

    def remove(self):
        tab_index = self.ui.tabWidget.currentIndex()
        item_type = self.listwidget_type[tab_index]
        old_index = self.item_listwidget[tab_index].currentRow()

        dependencies = self.find_item_in_item[tab_index](old_index)
        # Only allow removing of the item if it isn't referenced anywhere
        if len(dependencies) == 0:
            # Don't remove "Room 0"
            if not(item_type == 'room' and old_index == 0):
                # Only remove if the list isn't empty
                if len(self.data[item_type]) > 0:
                    del self.data[item_type][old_index]

                    dependency_list = []
                    for index, _ in enumerate(self.data[item_type]):
                        dependency_list.append(
                            self.find_item_in_item[tab_index](index))
                    for index, value in enumerate(dependency_list):
                        for item_value in value:
                            if index > old_index:
                                self.decrement_terminal(self.data, item_value)

        self.populate_item_list[tab_index]()
        # Decrease index of selected row, if it's the last one
        if len(self.data[item_type]) == old_index:
            self.item_listwidget[tab_index].setCurrentRow(old_index - 1)
        else:
            self.item_listwidget[tab_index].setCurrentRow(old_index)
        self.update_item_combobox_contents(tab_index)

    def move_up(self):
        tab_index = self.ui.tabWidget.currentIndex()
        item_type = self.listwidget_type[tab_index]
        old_index = self.item_listwidget[tab_index].currentRow()

        # Don't allow moving up if the item is the first in the list
        if old_index > 0:
            # Don't allow moving down a room to swap with "Room 0"
            if not(item_type == 'room' and old_index == 1):
                swap_with = self.data[item_type][old_index]
                self.data[item_type][old_index] = self.data[item_type][old_index - 1]
                self.data[item_type][old_index - 1] = swap_with

                to_move_down = self.find_item_in_item[tab_index](old_index - 1)
                to_move_up = self.find_item_in_item[tab_index](old_index)
                for item_value in to_move_down:
                    self.increment_terminal(self.data, item_value)
                for item_value in to_move_up:
                    self.decrement_terminal(self.data, item_value)

                self.populate_item_list[tab_index]()
                self.item_listwidget[tab_index].setCurrentRow(old_index - 1)
        self.update_item_combobox_contents(tab_index)

    def move_down(self):
        tab_index = self.ui.tabWidget.currentIndex()
        item_type = self.listwidget_type[tab_index]
        old_index = self.item_listwidget[tab_index].currentRow()

        # Don't allow moving down, if item is the last in the list
        if (old_index + 1) < len(self.data[item_type]):
            # Don't allow moving down "Room 0"
            if not(item_type == 'room' and old_index == 0):
                swap_with = self.data[item_type][old_index]
                self.data[item_type][old_index] = self.data[item_type][old_index + 1]
                self.data[item_type][old_index + 1] = swap_with

                to_move_down = self.find_item_in_item[tab_index](old_index)
                to_move_up = self.find_item_in_item[tab_index](old_index + 1)
                for item_value in to_move_down:
                    self.increment_terminal(self.data, item_value)
                for item_value in to_move_up:
                    self.decrement_terminal(self.data, item_value)

                self.populate_item_list[tab_index]()
                self.item_listwidget[tab_index].setCurrentRow(old_index + 1)
                self.update_item_combobox_contents(tab_index)

    def add_below(self):
        tab_index = self.ui.tabWidget.currentIndex()
        item_type = self.listwidget_type[tab_index]
        old_index = self.item_listwidget[tab_index].currentRow()
        self.data[item_type].insert(
            old_index + 1, self.empty_item[tab_index]())
        dependency_list = []
        for index, _ in enumerate(self.data[item_type]):
            dependency_list.append(self.find_item_in_item[tab_index](index))
        for index, value in enumerate(dependency_list):
            for item_value in value:
                if index >= old_index + 1:
                    self.increment_terminal(self.data, item_value)
        self.populate_item_list[tab_index]()
        self.item_listwidget[tab_index].setCurrentRow(old_index + 1)
        self.update_item_combobox_contents(tab_index)

    def add_above(self):
        tab_index = self.ui.tabWidget.currentIndex()
        item_type = self.listwidget_type[tab_index]
        old_index = self.item_listwidget[tab_index].currentRow()
        # Don't allow adding above "Room 0"
        if not(item_type == 'room' and old_index == 0):
            self.data[item_type].insert(
                old_index, self.empty_item[tab_index]())

            dependency_list = []
            for index, _ in enumerate(self.data[item_type]):
                dependency_list.append(
                    self.find_item_in_item[tab_index](index))
            for index, value in enumerate(dependency_list):
                for item_value in value:
                    if index >= old_index:
                        self.increment_terminal(self.data, item_value)

            self.populate_item_list[tab_index]()

            self.item_listwidget[tab_index].setCurrentRow(old_index)
            self.update_item_combobox_contents(tab_index)
            self.select_object()

    # Dependency resolution working through recursion
    def decrement_terminal(self, data_structure, path):
        current_address_item = path.pop(0)
        if len(path) > 0:
            self.decrement_terminal(
                data_structure[current_address_item], path)
        else:
            m = re.search('message_(\d+)',
                          str(data_structure[current_address_item]))
            if m:
                data_structure[current_address_item] = "message_%d" % (
                    int(m.group(1)) - 1)
            else:
                data_structure[current_address_item] -= 1

    def increment_terminal(self, data_structure, path):
        current_address_item = path.pop(0)
        if len(path) > 0:
            self.increment_terminal(
                data_structure[current_address_item], path)
        else:
            m = re.search('message_(\d+)',
                          str(data_structure[current_address_item]))
            if m:
                data_structure[current_address_item] = "message_%d" % (
                    int(m.group(1)) + 1)
            else:
                data_structure[current_address_item] += 1

    def update_item_combobox_contents(self, item_type):
        if item_type == 0:  # Action
            pass
        elif item_type == 1:  # Verb
            pass
        elif item_type == 2:  # Noun
            pass
        elif item_type == 3:  # Message
            for combobox in self.command_message_combobox:
                combobox.blockSignals(True)
                combobox.clear()
                for index, value in enumerate(self.data['message']):
                    message_text = value.replace('\n', ' ').replace('\r', '')
                    combobox.addItem("%d: %s" % (index, message_text))
                combobox.blockSignals(False)
            self.select_action()  # Update values in on-screen action
        elif item_type == 4:  # Room
            self.populate_room_comboboxes()
        elif item_type == 5:  # Object
            self.change_condition_code()  # Update all the text in condition comboboxes
        # Attempt to manually repaint listwidget after update, to make it work on MacOSX
        self.item_listwidget[item_type].repaint()

    # Action commands
    def change_command_message_combobox(self):
        if len(self.ui.listWidget_action.selectedIndexes()) > 0:
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            for command_combobox_index, _ in enumerate(self.command_message_combobox):
                if "message_" in self.data['action'][index]['command'][command_combobox_index]:
                    value = self.command_message_combobox[command_combobox_index].currentIndex(
                    )
                    self.data['action'][index]['command'][command_combobox_index] = "message_%d" % value

    def change_command_code_combobox(self):
        if len(self.ui.listWidget_action.selectedIndexes()) > 0:
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            for command_combobox_index, _ in enumerate(self.command_code_combobox):
                if self.command_code_combobox[command_combobox_index].isEnabled:
                    value = self.command_code_combobox[command_combobox_index].currentIndex(
                    )
                    # Message?
                    if value == 35:
                        message_index = self.command_message_combobox[command_combobox_index].currentIndex(
                        )
                        self.data['action'][index]['command'][command_combobox_index] = "message_%d" % message_index
                    else:
                        self.data['action'][index]['command'][command_combobox_index] = command[value]
            self.refresh_command_combobox_statuses()
            self.change_condition_code()

    def refresh_command_combobox_statuses(self):
        index = self.ui.listWidget_action.selectedIndexes()[0].row()
        for command_index, value in enumerate(self.data['action'][index]['command']):
            if "message_" in value:
                command_code_index = command.index("message")
                self.command_message_combobox[command_index].setDisabled(False)
                message_index = int(re.sub("message_", "", value))
                self.command_message_combobox[command_index].blockSignals(True)
                self.command_message_combobox[command_index].setCurrentIndex(
                    message_index)
                self.command_message_combobox[command_index].blockSignals(
                    False)
            else:
                command_code_index = command.index(value)
                self.command_message_combobox[command_index].setDisabled(True)
            self.command_code_combobox[command_index].blockSignals(True)
            self.command_code_combobox[command_index].setCurrentIndex(
                command_code_index)
            self.command_code_combobox[command_index].blockSignals(False)

    # Action conditions
    def change_condition_combobox(self):
        if len(self.ui.listWidget_action.selectedIndexes()) > 0:
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            for condition_combobox_index, _ in enumerate(self.condition_argument_combobox):
                if self.condition_argument_combobox[condition_combobox_index].isEnabled:
                    value = self.condition_argument_combobox[condition_combobox_index].currentIndex(
                    )
                    if value < 0:
                        value = 0
                    self.data['action'][index]['condition_argument'][condition_combobox_index] = value

    def change_condition_spinbox(self):
        index = self.ui.listWidget_action.selectedIndexes()[0].row()
        for condition_spinbox_index, _ in enumerate(self.condition_argument_spinbox):
            if self.condition_argument_spinbox[condition_spinbox_index].isEnabled:
                value = self.condition_argument_spinbox[condition_spinbox_index].value(
                )
                if value < 0:
                    value = 0
                self.data['action'][index]['condition_argument'][condition_spinbox_index] = value

    def change_condition_code(self):
        if len(self.ui.listWidget_action.selectedIndexes()) > 0:
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            for val in self.condition_argument_spinbox:
                val.blockSignals(True)
            for val in self.condition_argument_combobox:
                val.blockSignals(True)
            # Populate parameter command datatype queue
            command_queue = []
            for command_data in self.data['action'][index]['command']:
                if not "message_" in command_data:
                    command_entry_index = command.index(command_data)
                    for token in command_argument_type[command_entry_index]:
                        command_queue.append(token)
            # Pad the command token queue with 'no data type' at the end, to disable undeclared parameter conditions
            command_queue = command_queue + ['-'] * 5

            for condition_index, _ in enumerate(self.condition_combobox):
                combobox_index = self.condition_combobox[condition_index].currentIndex(
                )
                self.data['action'][index]['condition'][condition_index] = condition[combobox_index]

                # "parameter" condition?
                if combobox_index == 19:
                    argument_type = command_queue.pop(0)
                else:
                    argument_type = condition_argument_type[combobox_index]
                self.condition_input_control(
                    condition_index, combobox_index, argument_type)
            for val in self.condition_argument_spinbox:
                val.blockSignals(False)
            for val in self.condition_argument_combobox:
                val.blockSignals(False)

    def condition_input_control(self, condition_index, condition_code_index, argument_type):
        if argument_type == 'f':  # Flag
            self.condition_argument_spinbox[condition_index].setDisabled(False)
            self.condition_argument_combobox[condition_index].setDisabled(True)
        elif argument_type == 'i':  # Integer
            self.condition_argument_spinbox[condition_index].setDisabled(False)
            self.condition_argument_combobox[condition_index].setDisabled(True)
        elif argument_type == 'o':  # Object
            self.condition_argument_spinbox[condition_index].setDisabled(True)
            self.condition_argument_combobox[condition_index].setDisabled(
                False)
            self.populate_condition_combobox(condition_index, argument_type)
        elif argument_type == 'r':  # Room
            self.condition_argument_spinbox[condition_index].setDisabled(True)
            self.condition_argument_combobox[condition_index].setDisabled(
                False)
            self.populate_condition_combobox(condition_index, argument_type)
        elif argument_type == 's':  # Stack
            self.condition_argument_spinbox[condition_index].setDisabled(False)
            self.condition_argument_combobox[condition_index].setDisabled(
                False)
        elif argument_type == '-':  # Nothing
            self.condition_argument_spinbox[condition_index].setDisabled(True)
            self.condition_argument_combobox[condition_index].setDisabled(True)
        else:
            print("FAILURE: invalid argument type found!")

    # This should be used to populate an arbitrary action condition combobox
    # Some strange bugs remain
    def populate_condition_combobox(self, condition_index, argument_type):
        index = self.ui.listWidget_action.selectedIndexes()[0].row()
        to_populate_with = []
        if argument_type == 'n':  # Noun
            to_populate_with = self.data['noun']
        elif argument_type == 'o':  # Object
            for object_data in self.data['object']:
                to_populate_with.append(object_data['description'])
        elif argument_type == 'r':  # Room
            for room_data in self.data['room']:
                to_populate_with.append(room_data['description'])
        elif argument_type == 'v':  # Verb
            to_populate_with = self.data['verb']
        combobox = self.condition_argument_combobox[condition_index]
        combobox.clear()
        for combobox_index, item in enumerate(to_populate_with):
            combobox.addItem("%d: %s" % (combobox_index, item))
        combobox.setCurrentIndex(
            self.data['action'][index]['condition_argument'][condition_index])

    # Actions
    def populate_action_list(self):
        self.ui.listWidget_action.clear()
        for index, value in enumerate(self.data['action']):
            self.ui.listWidget_action.addItem(
                "%d: %s" % (index, value['title']))
        self.populate_action_comboboxes()

    def select_action(self):
        if len(self.ui.listWidget_action.selectedIndexes()) > 0:
            for val in self.condition_combobox:
                val.blockSignals(True)
            for val in self.condition_argument_spinbox:
                val.blockSignals(True)
            for val in self.condition_argument_combobox:
                val.blockSignals(True)
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            self.ui.lineEdit_action_comment.setText(
                self.data['action'][index]['title'])
            self.ui.groupBox_action.setTitle("Action " + str(index))

            self.set_precondition(self.data['action'][index]['precondition']
                                  [0], self.data['action'][index]['precondition'][1])
            # Colorize "Anything" noun if "verb-noun" action type
            if self.data['action'][index]['precondition'][0] > 0 and self.data['action'][index]['precondition'][1] == 0:
                self.set_widget_bg_color(
                    self.ui.comboBox_precondition_noun, Qt.red)
            else:
                self.set_widget_bg_color(
                    self.ui.comboBox_precondition_noun, Qt.white)

            for condition_index, value in enumerate(self.data['action'][index]['condition']):
                condition_argument = self.data['action'][index]['condition_argument'][condition_index]
                condition_code_index = condition.index(value)
                self.condition_combobox[condition_index].setCurrentIndex(
                    condition_code_index)
                self.condition_argument_spinbox[condition_index].setValue(
                    condition_argument)

            self.refresh_command_combobox_statuses()

            for val in self.condition_combobox:
                val.blockSignals(False)
            for val in self.condition_argument_spinbox:
                val.blockSignals(False)
            for val in self.condition_argument_combobox:
                val.blockSignals(False)
            self.change_condition_code()

    def update_action_comment(self):
        # Update text field with upper case version
        index = self.ui.listWidget_action.selectedIndexes()[0].row()
        text = self.ui.lineEdit_action_comment.text().upper()
        cursor_position = self.ui.lineEdit_action_comment.cursorPosition()
        self.ui.lineEdit_action_comment.setText(text)
        self.ui.lineEdit_action_comment.setCursorPosition(cursor_position)
        self.data['action'][index]['title'] = text
        # Update list with new data
        sel_item = self.ui.listWidget_action.selectedItems()[0]
        sel_item.setText("%d: %s" % (index, text))

    # Action preconditions
    def change_spinBox_precondition_chance(self):
        index = self.ui.listWidget_action.selectedIndexes()[0].row()
        chance = self.ui.spinBox_precondition_chance.value()
        self.ui.horizontalSlider_precondition_chance.setValue(chance)
        self.data['action'][index]['precondition'][1] = chance

    def change_horizontalSlider_precondition_chance(self):
        index = self.ui.listWidget_action.selectedIndexes()[0].row()
        chance = self.ui.horizontalSlider_precondition_chance.value()
        self.ui.spinBox_precondition_chance.setValue(chance)
        self.data['action'][index]['precondition'][1] = chance

    def select_precondition_verb(self):
        # Only select if the listWidget has been initialized
        if len(self.ui.listWidget_action.selectedIndexes()) > 0:
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            index_verb = self.ui.comboBox_precondition_verb.currentIndex() + 1
            self.data['action'][index]['precondition'][0] = index_verb

    def select_precondition_noun(self):
        # Only select if the listWidget has been initialized
        if len(self.ui.listWidget_action.selectedIndexes()) > 0:
            index = self.ui.listWidget_action.selectedIndexes()[0].row()

            index_noun = self.ui.comboBox_precondition_noun.currentIndex()
            self.data['action'][index]['precondition'][1] = index_noun
            # Colorize "Anything" noun
            if self.data['action'][index]['precondition'][1] == 0:
                self.set_widget_bg_color(
                    self.ui.comboBox_precondition_noun,  Qt.red)
            else:
                self.set_widget_bg_color(
                    self.ui.comboBox_precondition_noun,  Qt.white)

    def select_precondition_verb_noun(self):
        self.disable_precondition_widgets()
        self.ui.comboBox_precondition_verb.setDisabled(False)
        self.ui.comboBox_precondition_noun.setDisabled(False)
        if self.ui.radioButton_precondition_verb_noun.isChecked():
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            verb = self.data['action'][index]['precondition'][0]
            # Verb can't be "0" in a verb-noun action, since this makes it auto action or subroutine action.
            # If verb is 0, the verb and nouns need to be initialized to valid values.
            if verb == 0:
                self.data['action'][index]['precondition'][0] = 1  # verb
                self.data['action'][index]['precondition'][1] = 0  # noun
                self.set_precondition(
                    self.data['action'][index]['precondition'][0], self.data['action'][index]['precondition'][1])
                # Colorize "Anything" noun
                if self.data['action'][index]['precondition'][1] == 0:
                    self.set_widget_bg_color(
                        self.ui.comboBox_precondition_noun,  Qt.red)
                else:
                    self.set_widget_bg_color(
                        self.ui.comboBox_precondition_noun,  Qt.white)

    def select_precondition_auto(self):
        self.disable_precondition_widgets()
        self.ui.horizontalSlider_precondition_chance.setDisabled(False)
        self.ui.spinBox_precondition_chance.setDisabled(False)
        if self.ui.radioButton_precondition_auto.isChecked():
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            verb = self.data['action'][index]['precondition'][0]
            noun = self.data['action'][index]['precondition'][1]
            if verb > 0 or noun < 1:
                self.data['action'][index]['precondition'][0] = 0
                self.data['action'][index]['precondition'][1] = 100

    def select_precondition_subroutine(self):
        self.disable_precondition_widgets()
        if self.ui.radioButton_precondition_subroutine.isChecked():
            index = self.ui.listWidget_action.selectedIndexes()[0].row()
            verb = self.data['action'][index]['precondition'][0]
            noun = self.data['action'][index]['precondition'][1]
            if verb > 0 or noun > 0:
                self.data['action'][index]['precondition'][0] = 0
                self.data['action'][index]['precondition'][1] = 0

    def disable_precondition_widgets(self):
        self.set_widget_bg_color(self.ui.comboBox_precondition_noun,  Qt.white)
        self.ui.comboBox_precondition_verb.setDisabled(True)
        self.ui.comboBox_precondition_noun.setDisabled(True)
        self.ui.horizontalSlider_precondition_chance.setDisabled(True)
        self.ui.spinBox_precondition_chance.setDisabled(True)

    def set_precondition(self, verb, noun):
        self.disable_precondition_widgets()
        # Verb-noun precondition
        if verb > 0:
            self.ui.comboBox_precondition_verb.setDisabled(False)
            self.ui.comboBox_precondition_noun.setDisabled(False)
            self.ui.radioButton_precondition_verb_noun.setChecked(True)
            # Subtract 1 because we removed the first invalid "AUTO" verb from combobox
            self.ui.comboBox_precondition_verb.setCurrentIndex(verb - 1)
            self.ui.comboBox_precondition_noun.setCurrentIndex(noun)
        # Auto precondition
        elif (verb == 0) and (noun > 0):
            self.ui.horizontalSlider_precondition_chance.setDisabled(False)
            self.ui.spinBox_precondition_chance.setDisabled(False)
            self.ui.radioButton_precondition_auto.setChecked(True)
            self.ui.horizontalSlider_precondition_chance.setValue(noun)
            self.ui.spinBox_precondition_chance.setValue(noun)
        # Subroutine precondition
        else:
            self.ui.radioButton_precondition_subroutine.setChecked(True)

    # Objects
    def populate_object_list(self):
        self.ui.listWidget_object.clear()
        for index, value in enumerate(self.data['object']):
            self.ui.listWidget_object.addItem(
                "%d: %s" % (index, value['description']))

    def update_object_room(self):
        if len(self.ui.listWidget_object.selectedIndexes()) > 0:
            index = self.ui.listWidget_object.selectedIndexes()[0].row()
            # Subtract one to compensate for inventory
            index_room = self.ui.comboBox_object_room.currentIndex() - 1
            self.data['object'][index]['starting_location'] = index_room

    def select_object(self):
        if len(self.ui.listWidget_object.selectedIndexes()) > 0:
            index = self.ui.listWidget_object.selectedIndexes()[0].row()
            self.ui.plainTextEdit_object_description.setPlainText(
                self.data['object'][index]['description'])
            self.ui.lineEdit_object_noun.setText(
                self.data['object'][index]['noun'])
            if len(self.data['object'][index]['noun']) < 1:
                self.ui.checkBox_object_carriable.setEnabled(False)
                self.ui.checkBox_object_carriable.setChecked(False)
            # Add one to compensate for inventory
            self.ui.comboBox_object_room.setCurrentIndex(
                self.data['object'][index]['starting_location'] + 1)
            self.ui.groupBox_object.setTitle("Object " + str(index))

    def update_object_carriable(self):
        if not self.ui.checkBox_object_carriable.isChecked():
            index = self.ui.listWidget_object.selectedIndexes()[0].row()
            self.data['object'][index]['noun'] = ''
            self.ui.lineEdit_object_noun.setText('')
            self.ui.checkBox_object_carriable.setEnabled(False)

    def update_object_noun(self):
        index = self.ui.listWidget_object.selectedIndexes()[0].row()
        text = self.ui.lineEdit_object_noun.text().upper()
        # Write back upper case version to field
        self.ui.lineEdit_object_noun.setText(text)
        self.data['object'][index]['noun'] = text
        if len(text) > 0:
            self.ui.checkBox_object_carriable.setEnabled(True)
            self.ui.checkBox_object_carriable.setChecked(True)
        else:
            self.ui.checkBox_object_carriable.setEnabled(False)

    def update_object_text(self):
        index = self.ui.listWidget_object.selectedIndexes()[0].row()
        text = self.ui.plainTextEdit_object_description.toPlainText()
        self.data['object'][index]['description'] = text
        sel_item = self.ui.listWidget_object.selectedItems()[0]
        sel_item.setText("%d: %s" % (index, text))
        if len(text) > 0:
            self.ui.checkBox_object_treasure.setEnabled(True)
            if text[0] == '*':
                self.ui.checkBox_object_treasure.setChecked(True)
            else:
                self.ui.checkBox_object_treasure.setChecked(False)
        else:
            self.ui.checkBox_object_treasure.setEnabled(False)
            self.ui.checkBox_object_treasure.setChecked(False)

    def update_object_treasure(self):
        text = self.ui.plainTextEdit_object_description.toPlainText()
        if len(text) > 0:
            if self.ui.checkBox_object_treasure.isChecked():
                if text[0] != '*':
                    self.ui.plainTextEdit_object_description.setPlainText(
                        '*' + text)
            elif text[0] == '*':
                self.ui.plainTextEdit_object_description.setPlainText(
                    text[1:])

    # Rooms
    def populate_room_list(self):
        self.ui.listWidget_room.clear()
        for index, value in enumerate(self.data['room']):
            self.ui.listWidget_room.addItem(
                "%d: %s" % (index, value['description']))

    def update_room_exits(self):
        index = self.ui.listWidget_room.selectedIndexes()[0].row()
        for exit_index, combobox in enumerate(self.room_exit_combobox):
            index_room = combobox.currentIndex()
            self.data['room'][index]['exit'][exit_index] = index_room
            if index_room == 0:
                self.set_widget_bg_color(
                    self.room_exit_combobox[exit_index], Qt.red)
            else:
                self.set_widget_bg_color(
                    self.room_exit_combobox[exit_index], Qt.white)

    def select_room(self):
        if len(self.ui.listWidget_room.selectedIndexes()) > 0:
            index = self.ui.listWidget_room.selectedIndexes()[0].row()
            self.ui.plainTextEdit_room_description.setPlainText(
                self.data['room'][index]['description'])
            for combobox in self.room_exit_combobox:
                combobox.blockSignals(True)
            for direction, value in enumerate(self.room_exit_combobox):
                value.setCurrentIndex(
                    self.data['room'][index]['exit'][direction])

            for combobox in self.room_exit_combobox:
                combobox.blockSignals(False)
            self.ui.groupBox_room.setTitle("Room " + str(index))

    def update_room_description_text(self):
        index = self.ui.listWidget_room.selectedIndexes()[0].row()
        text = self.ui.plainTextEdit_room_description.toPlainText()
        self.data['room'][index]['description'] = text
        sel_item = self.ui.listWidget_room.selectedItems()[0]
        sel_item.setText("%d: %s" % (index, text))
        if index > 0:  # If storeroom/no exit, don't change combobox texts
            for combobox_index, combobox in enumerate(self.room_combobox):
                message_text = text.replace('\n', ' ').replace('\r', '')
                if combobox_index == 6:  # Room combobox text is +1
                    combobox.setItemText(index + 1, "%d: %s" %
                                         (index, message_text))
                else:
                    combobox.setItemText(index, "%d: %s" %
                                         (index, message_text))
        self.change_condition_code()  # Update all the text in condition comboboxes

    # Messages
    def populate_message_list(self):
        self.ui.listWidget_message.clear()
        for index, value in enumerate(self.data['message']):
            self.ui.listWidget_message.addItem(
                "%d: %s" % (index, value))

    def select_message(self):
        if len(self.ui.listWidget_message.selectedIndexes()) > 0:
            index = self.ui.listWidget_message.selectedIndexes()[0].row()
            self.ui.plainTextEdit_message.setPlainText(
                self.data['message'][index])
            self.ui.groupBox_message.setTitle("Message " + str(index))

    def update_message_text(self):
        index = self.ui.listWidget_message.selectedIndexes()[0].row()
        text = self.ui.plainTextEdit_message.toPlainText()
        self.data['message'][index] = text
        sel_item = self.ui.listWidget_message.selectedItems()[0]
        sel_item.setText("%d: %s" % (index, text))
        # Update text in command message comboboxes
        for combobox in self.command_message_combobox:
            message_text = text.replace('\n', ' ').replace('\r', '')
            combobox.setItemText(index, "%d: %s" % (index, message_text))

    # Verbs
    def populate_verb_list(self):
        self.ui.listWidget_verb.clear()
        self.ui.comboBox_precondition_verb.blockSignals(True)
        self.ui.comboBox_precondition_verb.clear()
        for index, value in enumerate(self.data['verb']):
            self.ui.listWidget_verb.addItem(
                "%d: %s" % (index, value))
            if index > 0:
                self.ui.comboBox_precondition_verb.addItem(
                    "%d: %s" % (index, value))
        self.ui.comboBox_precondition_verb.blockSignals(False)
        self.select_action()  # Update values in on-screen action

    def select_verb(self):
        if len(self.ui.listWidget_verb.selectedIndexes()) > 0:
            index = self.ui.listWidget_verb.selectedIndexes()[0].row()
            text = self.data['verb'][index]
            self.ui.lineEdit_verb.setText(text)
            if len(text) > 0:
                self.ui.checkBox_verb_synonym.setEnabled(True)
            else:
                self.ui.checkBox_verb_synonym.setEnabled(False)
            self.ui.groupBox_verb.setTitle("Verb " + str(index))

    def update_verb_synonym(self):
        text = self.ui.lineEdit_verb.text()
        if len(text) > 0:
            if self.ui.checkBox_verb_synonym.isChecked():
                if text[0] != '*':
                    self.ui.lineEdit_verb.setText('*' + text)
            else:
                if text[0] == '*':
                    self.ui.lineEdit_verb.setText(text[1:])

    def update_verb_text(self):
        index = self.ui.listWidget_verb.selectedIndexes()[0].row()
        text = self.ui.lineEdit_verb.text().upper()
        cursor_position = self.ui.lineEdit_verb.cursorPosition()
        # Write back upper case version to field
        self.ui.lineEdit_verb.setText(text)
        self.ui.lineEdit_verb.setCursorPosition(cursor_position)
        self.data['verb'][index] = text
        sel_item = self.ui.listWidget_verb.selectedItems()[0]
        sel_item.setText("%d: %s" % (index, text))
        if len(text) > 0:
            self.ui.checkBox_verb_synonym.setEnabled(True)
            if text[0] == '*':
                self.ui.checkBox_verb_synonym.setChecked(True)
            else:
                self.ui.checkBox_verb_synonym.setChecked(False)
        else:
            self.ui.checkBox_verb_synonym.setEnabled(False)
            self.ui.checkBox_verb_synonym.setChecked(False)
        if index > 0:  # If AUT verb, don't change combobox text
            self.ui.comboBox_precondition_verb.setItemText(
                index - 1, "%d: %s" % (index, text))

    # Nouns
    def populate_noun_list(self):
        self.ui.listWidget_noun.clear()
        self.ui.comboBox_precondition_noun.blockSignals(True)
        self.ui.comboBox_precondition_noun.clear()
        for index, value in enumerate(self.data['noun']):
            self.ui.listWidget_noun.addItem(
                "%d: %s" % (index, value))
            if index > 0:
                self.ui.comboBox_precondition_noun.addItem(
                    "%d: %s" % (index, value))
            else:
                self.ui.comboBox_precondition_noun.addItem("Anything")
                self.ui.comboBox_precondition_noun.setItemData(
                    index, QColor("palevioletred"), Qt.BackgroundColorRole)
        self.ui.comboBox_precondition_noun.blockSignals(False)
        self.select_action()  # Update values in on-screen action

    def select_noun(self):
        if len(self.ui.listWidget_noun.selectedIndexes()) > 0:
            index = self.ui.listWidget_noun.selectedIndexes()[0].row()
            self.ui.lineEdit_noun.setText(self.data['noun'][index])
            if len(self.data['noun'][index]) > 0:
                self.ui.checkBox_noun_synonym.setEnabled(True)
            else:
                self.ui.checkBox_noun_synonym.setEnabled(False)
            self.ui.groupBox_noun.setTitle("Noun " + str(index))

    def update_noun_synonym(self):
        text = self.ui.lineEdit_noun.text()
        if len(text) > 0:
            if self.ui.checkBox_noun_synonym.isChecked():
                if text[0] != '*':
                    self.ui.lineEdit_noun.setText('*' + text)
            else:
                if text[0] == '*':
                    self.ui.lineEdit_noun.setText(text[1:])

    def update_noun_text(self):
        index = self.ui.listWidget_noun.selectedIndexes()[0].row()
        text = self.ui.lineEdit_noun.text().upper()
        cursor_position = self.ui.lineEdit_noun.cursorPosition()
        # Write back upper case version to field
        self.ui.lineEdit_noun.setText(text)
        self.ui.lineEdit_noun.setCursorPosition(cursor_position)
        self.data['noun'][index] = text
        sel_item = self.ui.listWidget_noun.selectedItems()[0]
        sel_item.setText("%d: %s" % (index, text))
        if len(text) > 0:
            self.ui.checkBox_noun_synonym.setEnabled(True)
            if text[0] == '*':
                self.ui.checkBox_noun_synonym.setChecked(True)
            else:
                self.ui.checkBox_noun_synonym.setChecked(False)
        else:
            self.ui.checkBox_noun_synonym.setEnabled(False)
            self.ui.checkBox_noun_synonym.setChecked(False)
        if index > 0:  # If ANY verb, don't change combobox text
            self.ui.comboBox_precondition_noun.setItemText(
                index, "%d: %s" % (index, text))

    # Generic
    def set_widget_bg_color(self, w, color):
        p = w.palette()
        p.setColor(w.backgroundRole(), color)
        w.setPalette(p)

    def new_file(self):
        self.ui.centralwidget.setEnabled(False)
        self.data = {
            "action": [],
            "header": {
                "adventure_number": 0,
                "adventure_version": 0,
                "game_bytes": 0,
                "max_objects_carried": 99,
                "number_of_actions": 0,
                "number_of_messages": 0,
                "number_of_objects": 0,
                "number_of_rooms": 0,
                "number_of_treasures": 0,
                "number_of_words": 0,
                "starting_room": 0,
                "time_limit": 32767,
                "treasure_room_id": 0,
                "word_length": 3
            },
            "message": [],
            "noun": ["ANY", "NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"],
            "object": [],
            "room": [{"description": "", "exit": [0, 0, 0, 0, 0, 0]}],
            "verb": ["AUT", "GO", "", "", "", "", "", "", "", "", "GET", "", "", "", "", "", "", "", "DRO"]
        }
        self.populate_ui()
        self.ui.centralwidget.setEnabled(True)
        if hasattr(self, 'json_filename'):
            # Since we have a new file, disable the "Save" functionality
            delattr(self, 'json_filename')

    def browse_open_json_file(self):
        # In case there are any existing elements in the list
        dialog = QtWidgets.QFileDialog

        file_list = dialog.getOpenFileName(self, "Pick a file", ".", "*.json")
        if len(file_list[0]) > 0:  # if user didn't pick a file don't continue
            with open(file_list[0]) as json_file:
                self.data = json.load(json_file)
                self.populate_ui()
                # Enable UI after we have data
                self.ui.centralwidget.setEnabled(True)
                self.json_filename = file_list[0]

    def browse_save_as_json_file(self):
        if hasattr(self, 'data'):  # Only attempt export if data exists
            # In case there are any existing elements in the list
            dialog = QtWidgets.QFileDialog
            file_list = dialog.getSaveFileName(
                self, "Save a file", "default.json",  "*.json")
            if len(file_list[0]) > 0:  # if user didn't pick a file don't continue
                self.json_filename = file_list[0]
                self.save_json_file()

    def save_json_file(self):
        if hasattr(self, 'json_filename'):
            with open(self.json_filename, 'w') as outfile:
                json.dump(self.data, outfile,  sort_keys=True, indent=4)
                outfile.close()

    def browse_export_as_dat_file(self):
        if hasattr(self, 'data'):  # Only attempt export if data exists
            # In case there are any existing elements in the list
            dialog = QtWidgets.QFileDialog
            file_list = dialog.getSaveFileName(
                self, "Export a file", "default.dat",  "*.dat")
            if len(file_list[0]) > 0:  # if user didn't pick a file don't continue
                self.dat_filename = file_list[0]
                self.export_dat_file()

    def export_dat_file(self):
        if hasattr(self, 'dat_filename'):
            with open(self.dat_filename, 'w') as outfile:
                outfile.write(encode_data_to_dat(self.data))
                outfile.close()

    def populate_room_comboboxes(self):
        # Store original combobox indices before refreshing
        original_index = []
        for combobox in self.room_combobox:
            original_index.append(combobox.currentIndex())

        for room_combobox_id, combobox in enumerate(self.room_combobox):
            combobox.blockSignals(True)

            combobox.clear()
            if room_combobox_id == 6:  # Object combobox
                combobox.addItem("-1: Inventory")
            for index, value in enumerate(self.data['room']):
                if index == 0:  # Alter the first room entry text
                    if room_combobox_id < 6:  # If a room exit, set "No exit"
                        combobox.addItem("No exit")
                        combobox.setItemData(index, QColor(
                            "palevioletred"), Qt.BackgroundColorRole)
                    else:  # In all other cases, room 0 is "Storeroom"
                        combobox.addItem("0: Storeroom")
                else:  # Change newline to space because prettier
                    room_text = value['description'].replace(
                        '\n', ' ').replace('\r', '')
                    combobox.addItem("%d: %s" % (index, room_text))
        self.populate_general_data()

        # Restore original combobox indices after refreshing
        for room_combobox_id, combobox in enumerate(self.room_combobox):
            # Only restore to valid, positive number indices
            if original_index[room_combobox_id] >= 0:
                combobox.setCurrentIndex(original_index[room_combobox_id])
        for combobox in self.room_combobox:
            combobox.blockSignals(False)

    def populate_general_data(self):
        for header_item in self.header_combobox:
            header_item.blockSignals(True)
        for header_item in self.header_spinbox:
            header_item.blockSignals(True)
        self.ui.spinBox_max_objects_carried.setValue(
            self.data['header']['max_objects_carried'])
        self.ui.spinBox_treasures.setValue(
            self.data['header']['number_of_treasures'])
        self.ui.spinBox_word_length.setValue(
            self.data['header']['word_length'])
        self.ui.spinBox_time_limit.setValue(
            self.data['header']['time_limit'])
        self.ui.spinBox_version_number.setValue(
            self.data['header']['adventure_version'])
        self.ui.spinBox_adventure_number.setValue(
            self.data['header']['adventure_number'])
        self.ui.comboBox_start_room.setCurrentIndex(
            self.data['header']['starting_room'])
        self.ui.comboBox_treasure_room.setCurrentIndex(
            self.data['header']['treasure_room_id'])
        for header_item in self.header_combobox:
            header_item.blockSignals(False)
        for header_item in self.header_spinbox:
            header_item.blockSignals(False)

    def populate_action_comboboxes(self):
        # Add conditions to comboboxes
        for combobox in self.condition_combobox:
            combobox.clear()
            for index, value in enumerate(condition):
                combobox.addItem(value.replace('_', ' '))
        # Add commands to comboboxes
        for combobox in self.command_code_combobox:
            combobox.clear()
            for index, value in enumerate(command):
                combobox.addItem(value.replace('_', ' '))
        # Add command messages to comboboxes
        for combobox in self.command_message_combobox:
            combobox.clear()
            for index, value in enumerate(self.data['message']):
                message_text = value.replace('\n', ' ').replace('\r', '')
                combobox.addItem("%d: %s" % (index, message_text))

    def populate_ui(self):
        self.ui.listWidget_verb.blockSignals(True)
        self.ui.listWidget_noun.blockSignals(True)
        self.ui.listWidget_message.blockSignals(True)
        self.ui.listWidget_action.blockSignals(True)
        self.ui.listWidget_room.blockSignals(True)
        self.ui.listWidget_object.blockSignals(True)

        for val in self.room_combobox:
            val.blockSignals(True)
        for val in self.condition_combobox:
            val.blockSignals(True)
        for val in self.condition_argument_spinbox:
            val.blockSignals(True)
        for val in self.condition_argument_combobox:
            val.blockSignals(True)

        # Populate room comboboxes
        self.populate_room_comboboxes()

        # Populate general data
        self.populate_general_data()

        for populate in self.populate_item_list:
            populate()

        self.ui.listWidget_verb.blockSignals(False)
        self.ui.listWidget_noun.blockSignals(False)
        self.ui.listWidget_message.blockSignals(False)
        self.ui.listWidget_action.blockSignals(False)
        self.ui.listWidget_room.blockSignals(False)
        self.ui.listWidget_object.blockSignals(False)

        # Set default list entries to 0 to initialize them
        self.ui.listWidget_verb.setCurrentRow(0)
        self.ui.listWidget_noun.setCurrentRow(0)
        self.ui.listWidget_message.setCurrentRow(0)
        self.ui.listWidget_action.setCurrentRow(0)
        self.ui.listWidget_room.setCurrentRow(0)
        self.ui.listWidget_object.setCurrentRow(0)

        for val in self.room_combobox:
            val.blockSignals(False)

        for val in self.condition_combobox:
            val.blockSignals(False)
        for val in self.condition_argument_spinbox:
            val.blockSignals(False)
        for val in self.condition_argument_combobox:
            val.blockSignals(False)

    # Item list manipulation functions below

    # Item dependencies
    # * action - none
    # * verb - precondition
    # * noun - precondition
    # * message - command
    # * room - condition, command, room exits, object, start room, treasure room
    # * object - condition, command

    def find_action_in_items(self, message_index):
        # Dummy function, for consistency
        return []

    def find_verb_in_items(self, verb_index):
        # find verb in preconditions
        found_instances = []
        for action_index, action in enumerate(self.data['action']):
            precondition_verb = action['precondition'][0]
            if (precondition_verb > 0 and verb_index > 0):
                if verb_index == precondition_verb:
                    found_instances.append(
                        ['action', action_index, 'precondition', 0])
        return(found_instances)

    def find_noun_in_items(self, noun_index):
        # Find noun in preconditions
        found_instances = []
        for action_index, action in enumerate(self.data['action']):
            precondition_verb = action['precondition'][0]
            precondition_noun = action['precondition'][1]
            if (precondition_verb > 0 and noun_index > 0):
                if noun_index == precondition_noun:
                    found_instances.append(
                        ['action', action_index, 'precondition', 1])
        return(found_instances)

    def find_message_in_items(self, message_index):
        # Find message in commands
        found_instances = []
        for action_index, action in enumerate(self.data['action']):
            for command_index, command_text in enumerate(action['command']):
                m = re.search('message_(\d+)', command_text)
                if m:
                    found = int(m.group(1))
                    if found == message_index:
                        # The below line needs some more logic down the line since command message structure is "message_123", not an integer
                        found_instances.append(
                            ['action', action_index, 'command', command_index])
        return(found_instances)

    def find_room_in_items(self, room_index):
        # Find room in actions
        found_instances = []
        for action_index, action in enumerate(self.data['action']):
            # Populate parameter command datatype queue
            command_queue = []
            for command_data in self.data['action'][action_index]['command']:
                if not "message_" in command_data:
                    command_entry_index = command.index(command_data)
                    for token in command_argument_type[command_entry_index]:
                        command_queue.append(token)

            # Pad the command token queue with 'no data type' at the end, to disable undeclared parameter conditions
            command_queue = command_queue + ['-'] * 5

            for condition_index, condition_code in enumerate(action['condition']):
                condition_code_index = condition.index(condition_code)

                # "parameter" condition?
                if condition_code_index == 19:
                    argument_type = command_queue.pop(0)
                else:
                    argument_type = condition_argument_type[condition_code_index]

                if argument_type == 'r':  # room

                    if action['condition_argument'][condition_index] == room_index:
                        found_instances.append(
                            ['action', action_index, 'condition_argument', condition_index])

        # Find room in room exits
        for current_room_index, room in enumerate(self.data['room']):
            for exit_index, exit_value in enumerate(room['exit']):
                if exit_value > 0 and exit_value == room_index:
                    found_instances.append(
                        ['room', current_room_index, 'exit', exit_index])

        # Find room in objects
        for current_object_index, object_instance in enumerate(self.data['object']):
            value = object_instance['starting_location']
            if value > 0:
                if self.data['object'][current_object_index]['starting_location'] == room_index:
                    found_instances.append(
                        ['object', current_object_index, 'starting_location'])

        # Find room in header
        if self.data['header']['treasure_room_id'] == room_index:
            found_instances.append(['header', 'treasure_room_id'])
        if self.data['header']['starting_room'] == room_index:
            found_instances.append(['header', 'starting_room'])

        return found_instances

    def find_object_in_items(self, object_index):
        # Find object in actions (conditions and commands)
        found_instances = []
        for action_index, action in enumerate(self.data['action']):
            # Populate parameter command datatype queue
            command_queue = []
            for command_data in self.data['action'][action_index]['command']:
                if not "message_" in command_data:
                    command_entry_index = command.index(command_data)
                    for token in command_argument_type[command_entry_index]:
                        command_queue.append(token)

            # Pad the command token queue with 'no data type' at the end, to disable undeclared parameter conditions
            command_queue = command_queue + ['-'] * 5

            for condition_index, condition_code in enumerate(action['condition']):
                condition_code_index = condition.index(condition_code)

                # "parameter" condition?
                if condition_code_index == 19:
                    argument_type = command_queue.pop(0)
                else:
                    argument_type = condition_argument_type[condition_code_index]

                if argument_type == 'o':  # object

                    if action['condition_argument'][condition_index] == object_index:
                        found_instances.append(
                            ['action', action_index, 'condition_argument', condition_index])
        return found_instances


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ExampleApp()
    main_window.show()
    sys.exit(app.exec_())
