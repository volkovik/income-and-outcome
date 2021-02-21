from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QSizePolicy, QSpacerItem, QLabel, QPushButton, \
    QHBoxLayout

from ui.item_of_list_widget import Ui_Form as ItemOfListWidgetUi


default_color = QColor(217, 217, 217)  # цвет по-умолчанию


class Tag(QLabel):
    def __init__(self, name, color=default_color, **kwargs):
        """
        Виджет, в виде плашки с изменяемым фоном и текстом
        Данный виджет предназначен для обозначение тега

        :param name: строка с названием тега
        :param color: QColor, цвет тега
        """
        super(Tag, self).__init__(**kwargs)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.set_name(name)
        self.set_color(color)

    def set_name(self, name):
        """
        Поменять название тега

        :param name: новое название
        """
        self.setText(name)

    def set_color(self, color: QColor):
        """
        Поменять цвет тега

        :param color: QColor, новый цвет тега
        """
        # Определяем насколько фон тега контрастен к белому тексту
        if (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114) > 186:
            text_color = "#000"
        else:
            text_color = "#FFF"

        self.setStyleSheet(
            f"background-color: {color.name(0)};"
            f"color: {text_color};"
            "padding: 4px;"
            "border-radius: 7px;"
        )


class AccountInfo(QWidget, ItemOfListWidgetUi):
    def __init__(self, account, *args, **kwargs):
        """
        Виджет, который выводит блок информации, а именно: кол-во денег всех счетах или на определённом

        :param account: database.account, класс ориантированный на хранение данных о счёте
        """
        super(AccountInfo, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.set_money(account.money)
        self.set_currency(account.currency)

        # Добавление тега в качестве названия счёта
        self.name = account.name
        self.account_tag = Tag(account.name, account.color)
        self.tags_layout.addWidget(self.account_tag)

    def change_account(self, account):
        """
        Изменить данные об аккаунте

        :param account: database.account, класс ориантированный на хранение данных о счёте
        """
        self.set_money(account.money)
        self.set_currency(account.currency)
        self.account_tag.set_name(account.name)
        self.account_tag.set_color(account.color)

    def set_money(self, value):
        """
        Изменить количество денег на счету

        :param value: новое число характеризующие количество денег на счету
        """
        self.money_label.setText(f"{value:.2f}")

        # Поставить красный цвет шрифта, если сумма меньше нуля
        if value < 0:
            style = "color: red"
        else:
            style = "color: black"

        self.money_label.setStyleSheet(style)
        self.currency_label.setStyleSheet(style)

    def set_currency(self, value):
        """
        Изменить валюту счёта

        :param value: строка с новой валютой аккаунта
        """
        self.currency_label.setText(value)

    def set_name(self, value):
        """
        Поставить название счёта

        :param value: новое название счёта
        """
        self.account_tag.set_name(value)

    def set_color(self, color):
        """
        Поставить цвет для счёта

        :param color: QColor, новый цвет счёта
        """
        self.account_tag.set_color(color)


class TransactionInfo(QWidget, ItemOfListWidgetUi):
    def __init__(self, transaction, account, category, *args, **kwargs):
        """
        Виджет, показывающий информацию о выполненной транзакции

        :param account: database.account, класс ориантированный на хранение данных о счёте
        :param transaction: database.transaction, класс ориантированный на хранение данных о транзакции
        :param category: database.category, класс ориантированный на хранение данных о категории
        """
        super(TransactionInfo, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.set_money(transaction.money)
        self.set_currency(account.currency)

        # Добавление тега в качестве названия категории
        self.category_tag = Tag(category.name, category.color)
        self.tags_layout.addWidget(self.category_tag)

        # Добавление тега в качестве даты траназкции
        self.date = transaction.date
        self.date_tag = Tag(transaction.date.toString("dd.MM.yyyy") if transaction.date else "Без даты")
        self.tags_layout.addWidget(self.date_tag)

    def set_money(self, value):
        """
        Изменить количество денег задействованных в транзакции

        :param value: новое число характеризующие количество денег в транзакции
        """
        text = f"{value:.2f}"

        if value < 0:
            style = "color: red"
        elif value > 0:
            style = "color: green"
            text = "+" + text
        else:
            style = "color: black"

        self.money_label.setText(text)

        self.money_label.setStyleSheet(style)
        self.currency_label.setStyleSheet(style)

    def set_currency(self, value):
        """
        Изменить валюту транзакции

        :param value: строка с новой валютой транзакции
        """
        self.currency_label.setText(value)

    def set_category(self, category):
        """
        Поставть или сбросить категорию

        :param category: database.Category, данные о категории
        """
        self.category_tag.set_name(category.name)
        self.category_tag.set_color(category.color)

    def set_date(self, date=None):
        """
        Изменить или сбросить дату

        :param date: QDate, дата или None, если нужно сбросить дату
        """
        self.date = date
        self.date_tag.set_name(date.toString("dd.MM.yyyy") if date else "Без даты")


class TransactionInfoButton(QPushButton, TransactionInfo):
    def __init__(self, transaction, account, category, *args, **kwargs):
        """
        Виджет, показывающий информацию о выполненной транзакции, а также выполняющий функцию кнопки, при нажатии на
        которую происходит редактирование транзакции

        :param account: database.account, класс ориантированный на хранение данных о счёте
        :param transaction: database.transaction, класс ориантированный на хранение данных о транзакции
        :param category: database.category, класс ориантированный на хранение данных о категории
        """
        super(TransactionInfoButton, self).__init__(transaction, account, category,
                                                    *args, **kwargs)

        self.setObjectName("TransactionInfo")
        self.setStyleSheet(
            "QPushButton#TransactionInfo {"
            "   background-color: none;"
            "   border: none;"
            "}"
            "QPushButton#TransactionInfo:hover {"
            "   background-color: #ebebeb;"
            "   border: 1px solid #dbdbdb;"
            "}"
            "QPushButton#TransactionInfo:pressed {"
            "   background-color: #e3e3e3;"
            "   border: 1px solid #dbdbdb;"
            "}"
        )


class List(QScrollArea):
    def __init__(self, *args, **kwargs):
        """Виджет, который сделан для вывода виджетов в виде списка"""
        super(List, self).__init__(*args, **kwargs)

        # Ставим нужные настройки, чтобы виджеты выводились корректно
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)

        self.content_widget = QWidget()
        self.setWidget(self.content_widget)
        layout = QVBoxLayout(self.content_widget)
        self.items_layout = QVBoxLayout()  # layout, который будет вмещать в себя транзакции
        layout.addLayout(self.items_layout)
        # spacer, который выравнивает элементы списка в самый верх
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))
        

class AccountItem(QWidget):
    def __init__(self, account, edit_function, *args, **kwargs):
        """
        Виджет, который сделан в качестве элемента списка

        :param account: database.Account, счёт, к которому привязан элемент списка
        :param edit_function: функция, которая будет вызываться при нажатии на кпопку 'Ред.' напротив названия счёта
        """
        super(AccountItem, self).__init__(*args, **kwargs)

        layout = QHBoxLayout(self)
        # Название счёта
        layout.addWidget(Tag(account.name, account.color, parent=self))
        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Maximum))
        # Кнопка, при нажатии которой будет открыто окно с редактирование счёта
        button = QPushButton("Ред.", self)
        button.clicked.connect(partial(edit_function, account))
        layout.addWidget(button)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


class AccountsList(List):
    """Виджет ориентирован на показ списка счетов"""

    def set_accounts(self, accounts, edit_function):
        """
        Вставить счета в список

        :param accounts: список, содержащий все доступные счета
        :param edit_function: функция, которая будет вызываться при нажатии на кпопку 'Ред.' напротив названия счёта
        """
        # Если в списке есть какие-то элементы, то они будут удалены
        for i in range(self.items_layout.count()):
            item = self.items_layout.itemAt(i).widget()

            if type(item) is AccountItem:
                item.deleteLater()

        for acc in accounts:
            self.items_layout.insertWidget(0, AccountItem(acc, edit_function))


class TransactionList(List):
    """Виджет ориентирован на показ списка транзакции"""

    def set_transactions(self, transactions):
        """
        Вставить транзакции в список

        :param transactions: спислк, содержащий транзакции счёта
        """
        # Если в списке есть какие-то элементы, то они будут удалены
        for i in range(self.items_layout.count()):
            item = self.items_layout.itemAt(i).widget()

            if type(item) is TransactionInfoButton:
                item.deleteLater()

        for transaction in transactions:
            self.items_layout.insertWidget(0, transaction)
