# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'create_account_widget.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CreateAccountDialog(object):
    def setupUi(self, CreateAccountDialog):
        CreateAccountDialog.setObjectName("CreateAccountDialog")
        CreateAccountDialog.resize(423, 194)
        self.main_layout = QtWidgets.QVBoxLayout(CreateAccountDialog)
        self.main_layout.setObjectName("main_layout")
        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setObjectName("form_layout")
        self.name_label = QtWidgets.QLabel(CreateAccountDialog)
        self.name_label.setObjectName("name_label")
        self.form_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.name_label)
        self.name_line_edit = QtWidgets.QLineEdit(CreateAccountDialog)
        self.name_line_edit.setObjectName("name_line_edit")
        self.form_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.name_line_edit)
        self.color_label = QtWidgets.QLabel(CreateAccountDialog)
        self.color_label.setObjectName("color_label")
        self.form_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.color_label)
        self.change_color_button = QtWidgets.QPushButton(CreateAccountDialog)
        self.change_color_button.setObjectName("change_color_button")
        self.form_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.change_color_button)
        self.money_label = QtWidgets.QLabel(CreateAccountDialog)
        self.money_label.setObjectName("money_label")
        self.form_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.money_label)
        self.money_spinbox = QtWidgets.QDoubleSpinBox(CreateAccountDialog)
        self.money_spinbox.setMinimum(-100000000.0)
        self.money_spinbox.setMaximum(100000000.0)
        self.money_spinbox.setProperty("value", 0.0)
        self.money_spinbox.setObjectName("money_spinbox")
        self.form_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.money_spinbox)
        self.currency_label = QtWidgets.QLabel(CreateAccountDialog)
        self.currency_label.setObjectName("currency_label")
        self.form_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.currency_label)
        self.currency_combobox = QtWidgets.QComboBox(CreateAccountDialog)
        self.currency_combobox.setObjectName("currency_combobox")
        self.form_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.currency_combobox)
        self.main_layout.addLayout(self.form_layout)
        spacerItem = QtWidgets.QSpacerItem(20, 33, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.main_layout.addItem(spacerItem)
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.setObjectName("buttons_layout")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.buttons_layout.addItem(spacerItem1)
        self.add_button = QtWidgets.QPushButton(CreateAccountDialog)
        self.add_button.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_button.sizePolicy().hasHeightForWidth())
        self.add_button.setSizePolicy(sizePolicy)
        self.add_button.setObjectName("add_button")
        self.buttons_layout.addWidget(self.add_button)
        self.cancel_button = QtWidgets.QPushButton(CreateAccountDialog)
        self.cancel_button.setObjectName("cancel_button")
        self.buttons_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(self.buttons_layout)

        self.retranslateUi(CreateAccountDialog)
        QtCore.QMetaObject.connectSlotsByName(CreateAccountDialog)

    def retranslateUi(self, CreateAccountDialog):
        _translate = QtCore.QCoreApplication.translate
        CreateAccountDialog.setWindowTitle(_translate("CreateAccountDialog", "Dialog"))
        self.name_label.setText(_translate("CreateAccountDialog", "Название:"))
        self.color_label.setText(_translate("CreateAccountDialog", "Цвет:"))
        self.change_color_button.setText(_translate("CreateAccountDialog", "Изменить цвет"))
        self.money_label.setText(_translate("CreateAccountDialog", "Начальная сумма:"))
        self.currency_label.setText(_translate("CreateAccountDialog", "Валюта:"))
        self.add_button.setText(_translate("CreateAccountDialog", "Создать"))
        self.cancel_button.setText(_translate("CreateAccountDialog", "Отменить"))
