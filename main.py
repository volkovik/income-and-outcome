import sqlite3
import sys
from copy import deepcopy

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QAction, QColorDialog, QMessageBox

from core.widgets import *
from core.database import *
from ui.main_page import Ui_MainPage as MainPageUi
from ui.add_transaction_dialog import Ui_Dialog as AddTransactionDialogUi
from ui.create_account_widget import Ui_CreateAccountDialog as CreateAccountDialogUi

# Когда категория не была выбрана, искользуется именно  этот вид записи
no_category = Category(None, "Без категории", default_color)


# Утилиты
def get(iteration, key, no_result=None):
    """
    Возвращает элемент списка, если он соотвествует условию

    :param iteration: итерируемый объект
    :param key: функция, которая возвращает True или False и получает аргумент в виде элемента итерируемого объекта
    :param no_result: если элемент не был найден по условию, поставленного в функции, то вернуть None, либо что-то ещё
    """
    for i in iteration:
        if key(i):
            return i
    else:
        return no_result


# Виджеты, диалоги
class MainPage(QWidget, MainPageUi):
    def __init__(self, db, accounts, categories, currencies):
        """
        Основная страница приложения. Здесь отображается состояние определённого счёта и его история транзакций

        :param db: подключение к базе данных
        :param accounts: список счетов
        :param categories: список категорий транзакций
        """
        super(MainPage, self).__init__()
        self.setupUi(self)

        # Освновные переменные
        self.db = db
        self.accounts = accounts
        self.categories = categories
        self.currencies = currencies

        self.account = self.accounts[0]

        # Виджеты, которые не были добавлены изначально
        self.account_info_widget = AccountInfo(self.account)
        self.header_layout.insertWidget(0, self.account_info_widget)

        self.transactions_history_layout = QHBoxLayout(self)
        self.page_layout.addLayout(self.transactions_history_layout)

        self.income_history = TransactionList()
        self.transactions_history_layout.addWidget(self.income_history)

        self.outcome_history = TransactionList()
        self.transactions_history_layout.addWidget(self.outcome_history)

        # Ставим последние транзакции в каждую колонку
        self.set_transactions()

        # Добавляем счета в выпадающий список
        for account in self.accounts:
            self.accounts_combobox.addItem(account.name, account.id)

        # Подключаем функции к элементам интерфейса
        self.accounts_combobox.currentIndexChanged.connect(self.account_changed)
        self.add_transaction_button.clicked.connect(self.add_transaction)

    def set_transactions(self):
        """Вывести последние транзакции поставленного счёта"""
        cursor = self.db.cursor()

        # Для удобства создана отдельная функция, чтобы повторять одно и то же действие дважды
        def fun(transaction_list, statement):
            # Получаем последние 50 транзакции, которые связанные с определённым счётом и подходит под условие
            result = cursor.execute(
                f"SELECT * FROM 'transaction' WHERE account_id=? AND {statement} "
                f"ORDER BY STRFTIME('%d.%m.%Y', date) LIMIT 50",
                (self.account.id,)
            ).fetchall()

            transactions = []

            # Обрабатываем транзакции из базы данных и ставим элементы для взаимодействия историей транзакций
            for transaction in result:
                transaction = Transaction(*transaction)
                category = get(self.categories, lambda c: c.id == transaction.category_id, no_category)
                transaction_info = TransactionInfoButton(transaction, self.account, category)
                transaction_info.clicked.connect(partial(
                    self.edit_transaction, transaction.id, self.account.id, category.id, transaction.money,
                    transaction.date
                ))
                transactions.append(transaction_info)

            # Сортируем транзакции. Транзакции с ближайшей датов - выше, а более давние или без даты - вниз
            transactions_with_date = sorted(filter(lambda t: t.date, transactions), key=lambda t: t.date)
            transactions = list(filter(lambda t: not t.date, transactions))
            transactions.extend(transactions_with_date)

            transaction_list.set_transactions(transactions)

        # Ставим транзакции для расходов и доходов
        fun(self.income_history, "money > 0")
        fun(self.outcome_history, "money < 0")

    def account_changed(self, index):
        """Когда пользователь выберает другой счёт из выпадающего списка"""
        self.account = get(self.accounts, lambda a: a.id == self.accounts_combobox.itemData(index))
        self.account_info_widget.change_account(self.account)  # Изменяем информацию о счёте

        self.set_transactions()  # Ставим историю транзакций для выбранного счёта

    def add_transaction(self):
        """Когда пользователь добавляет транзакцию"""
        dialog = AddTransactionDialog(self.accounts, self.categories, self.account.id)

        # Если диалоговое окно завершило работу с успехом
        if dialog.exec_():
            account = dialog.account
            transaction = dialog.transaction
            category = dialog.category

            # Делаем изменения в базу данных
            cursor = self.db
            cursor.execute(
                "INSERT INTO 'transaction'(account_id, category_id, money, date) VALUES (?, ?, ?, ?)",
                (account.id, category.id, transaction.money,
                 transaction.date.toString("dd.MM.yyyy") if transaction.date else None)
            )
            cursor.execute(
                "UPDATE account SET money = money + ? WHERE id = ?",
                (transaction.money, account.id)
            )
            self.db.commit()

            # Ищем счёт, на котором было сделано изменение
            for i in range(len(self.accounts)):
                if self.accounts[i].id == account.id:
                    # Изменяем количество денег на счету
                    self.accounts[i].money = account.money + transaction.money

                    # Если изменения были сделаны на текущем счету, то поставить изменения на главной странице
                    if self.account.id == account.id:
                        self.account = self.accounts[i]
                        self.account_info_widget.set_money(self.account.money)
                        self.set_transactions()
                    break

    def edit_transaction(self, transaction_id, account_id, category_id, money, date):
        """Когда пользователь изменяет трназкцию"""
        # Находит аккаунт, на котором проходила транзакция и приводим в тот внешний вид, который был до этой транзакции
        accounts = deepcopy(self.accounts)
        for i in range(len(accounts)):
            if accounts[i].id == account_id:
                # Изменяем количество денег на счету
                accounts[i].money = accounts[i].money - money
                break

        dialog = EditTransactionDialog(accounts, self.categories, account_id, category_id, money, date)

        # Если диалоговое окно завершило работу с успехом
        if dialog.exec_():
            original_account = get(accounts, lambda a: a.id == account_id)
            edited_account = dialog.account
            transaction = dialog.transaction
            category = dialog.category

            cursor = self.db.cursor()

            # Если пользователь нажал на кнопку удалить
            if dialog.deleted:
                # Удаляем транзакцию и изменяем количество денег на счету в базе данных
                cursor.execute("DELETE FROM 'transaction' WHERE id=?", (transaction_id,))
                cursor.execute("UPDATE account SET money=? WHERE id=?", (edited_account.money, edited_account.id))

                money = 0
            else:
                # Обновляем данные о транзакции и итогое количество денег на счету в базе данных
                cursor.execute(
                    "UPDATE 'transaction' SET account_id=?, category_id=?, money=?, date=? WHERE id=?",
                    (edited_account.id, category.id, transaction.money,
                     transaction.date.toString("dd.MM.yyyy") if transaction.date else None, transaction_id)
                )
                cursor.execute(
                    "UPDATE account SET money=? WHERE id=?",
                    (edited_account.money + transaction.money, edited_account.id)
                )
                if original_account.id != edited_account.id:
                    # Если был перенос транзакции с одного счёта на другой, то поставить исходную сумму счёта, где
                    # проводился изначально транзакция
                    cursor.execute(
                        "UPDATE account SET money=? WHERE id=?",
                        (original_account.money, original_account.id)
                    )

                money = transaction.money

            self.db.commit()
            # Обновить список транзакций
            self.set_transactions()

            # Ищем аккаунт, который был изменён из-за редактирования транзакции, и изменяем в нём данные
            for i in range(len(self.accounts)):
                # Аккаунт, на котором сделана транзакция
                if self.accounts[i].id == edited_account.id:
                    self.accounts[i].money = edited_account.money + money

                # Если транзакция была перенесена на другой счёт, то поставить прежнюю сумму денег
                if self.accounts[i].id == original_account.id and original_account.id != edited_account.id:
                    self.accounts[i].money = original_account.money

            # Если текущий выбранный аккаунт в главном меню выбранный для изменения, то транзакция будет изменена, то
            # количество денег на счету изменится
            if original_account.id == edited_account.id:
                self.account_info_widget.set_money(original_account.money + money)
            else:
                self.account_info_widget.set_money(original_account.money)

    def create_account(self):
        """Когда пользователь создаёт счёт"""
        dialog = CreateAccountDialog(self.accounts, self.currencies)

        # Если диалоговое окно завершило работу с успехом
        if dialog.exec_():
            account = dialog.account

            cursor = self.db.cursor()
            # Добавляем информацию о счёте в базу данных
            cursor.execute(
                "INSERT INTO account(name, color, currency, money) VALUES (?, ?, ?, ?)",
                (account.name, account.color.name()[1:], account.currency, account.money)
            )
            self.db.commit()

            # Получаем ID, который сгенерировала база данных
            account.id = cursor.lastrowid

            # Обновляем данные в программе
            self.accounts.append(account)
            self.accounts.sort(key=lambda a: a.name)
            self.accounts_combobox.addItem(account.name, account.id)
            self.accounts_combobox.model().sort(0, Qt.AscendingOrder)

    def accounts_list(self):
        """Когда пользователь открывает список счетов"""
        dialog = ListAccountsDialog(self.db, self.accounts, self.currencies)
        dialog.exec_()  # Открываем диалоговое окно

        # Расчитываем на то, что счета были изменены
        edited_accounts = dialog.accounts
        self.accounts = edited_accounts

        # Ищем счёт, который выбран на главной странице и изменяем его
        for i in range(len(edited_accounts)):
            if edited_accounts[i].id == self.account.id:
                self.account = edited_accounts[i]
                break
        else:
            # Если аккаунт не был найден, то будет поставлен первый по списку
            self.account = edited_accounts[0]
            self.set_transactions()

        # Меняем информацию на главном экране
        self.account_info_widget.change_account(self.account)

        # Перед тем как почистить все элементы combobox, мы отключаем привязанную функцию, которая отвечает за
        # динамическое изменение информации о счёте на главной странице программы. Делаем это для устранения ошибки,
        # связанной с пустым combobox
        self.accounts_combobox.currentIndexChanged.disconnect()
        self.accounts_combobox.clear()
        # Обновляем combobox актуальным списком счетов и подключаем фукнцию, отключённую ранее
        for account in self.accounts:
            self.accounts_combobox.addItem(account.name, account.id)
        self.accounts_combobox.currentIndexChanged.connect(self.account_changed)


class AddTransactionDialog(QDialog, AddTransactionDialogUi):
    def __init__(self, accounts, categories, account_id=0, *args, **kwargs):
        """
        Диалоговое окно для добавления транзакции

        :param accounts: список, содержащий все доступные счета
        :param categories: список, содержащий все доступные категории
        :param account_id: ID аккаунта, который будет поставлен по умолчанию при запуске окна
        """
        super(AddTransactionDialog, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setWindowTitle("Добавить транзакцию")

        # Основные переменные
        self.accounts = accounts
        self.categories = categories

        self.account = get(accounts, lambda a: a.id == account_id, self.accounts[0])
        self.category = no_category

        self.transaction = Transaction(0, self.account.id, 0, 0, QDate.currentDate())

        # Виджеты, которые не были добавлены изначально

        # Показываем, как будет выглядить количество денег на счету после транзакции
        self.main_layout.insertWidget(0, QLabel("Счёт после транзакции:"))
        self.account_info = AccountInfo(self.account)
        self.main_layout.insertWidget(1, self.account_info)

        # Информация о транзакции
        self.main_layout.insertWidget(2, QLabel("Транзакция:"))
        self.transaction_info = TransactionInfo(self.transaction, self.account, self.category)
        self.main_layout.insertWidget(3, self.transaction_info)

        # Ставим дату транзакции
        self.date_edit.setDate(self.transaction.date)
        self.date_edit.setMaximumDate(self.transaction.date)

        # Ставим элементы выпадающих списков

        # Список аккаунтов
        for account in self.accounts:
            self.account_combobox.addItem(account.name, account.id)
        self.account_combobox.setCurrentIndex(self.account_combobox.findData(self.account.id))

        # Список категорий транзакций
        self.category_combobox.addItem(no_category.name, no_category.id)
        for category in categories:
            self.category_combobox.addItem(category.name, category.id)

        # Подключаем функции к элементам интерфейса
        self.add_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.money_spinbox.valueChanged.connect(self.money_changed)
        self.category_combobox.currentIndexChanged.connect(self.category_changed)
        self.account_combobox.currentIndexChanged.connect(self.account_changed)
        self.date_edit.dateChanged.connect(self.date_changed)
        self.date_checkbox.stateChanged.connect(self.date_checkbox_state_changed)

    def check_data(self):
        """Проверяем данные формы. Если данные недействительны, то кнопка 'Добавить' будет выключена"""
        if self.transaction.money != 0:
            state = False
        else:
            state = True

        self.add_button.setDisabled(state)

    def money_changed(self, value):
        """Когда мы изменяем количество денег в транзакции"""
        self.transaction.money = value

        self.transaction_info.set_money(value)
        self.account_info.set_money(self.account.money + value)

        self.check_data()

    def category_changed(self, index):
        """Когда мы изменяем категорию"""
        self.category = get(self.categories, lambda c: c.id == self.category_combobox.itemData(index), no_category)
        self.transaction_info.set_category(self.category)
        self.transaction.category_id = self.category.id

        self.check_data()

    def account_changed(self, index):
        """Когда мы изменяем счёт"""
        account = get(self.accounts, lambda a: a.id == self.account_combobox.itemData(index))
        self.account = account
        self.account_info.change_account(self.account)
        self.account_info.set_money(self.account.money + self.transaction.money)

        self.check_data()

    def date_changed(self, date):
        """Когда мы изменяем дату"""
        self.transaction.date = date
        self.transaction_info.set_date(date)

        self.check_data()

    def date_checkbox_state_changed(self, state):
        """Когда мы выключаем или включаем дату"""
        date = None if not state else self.date_edit.date()

        self.date_edit.setDisabled(not state)
        self.transaction_info.set_date(date)
        self.transaction.date = date

        self.check_data()


class EditTransactionDialog(AddTransactionDialog):
    def __init__(self, accounts, categories, account_id=0, category_id=0, money=0, date=None,
                 *args, **kwargs):
        """
        Диалоговое окно для редактирования транзакции

        :param accounts: список, содержащий все доступные счета
        :param categories: список, содержащий все доступные категории
        :param account_id: ID аккаунта, который будет поставлен по умолчанию
        :param category_id: ID категории, который будет поставлен по умолчанию
        :param money: количетсво денег в транзакции, которая будет поставлена по умолчанию
        :param date: дата транзакции, которая будет поставлена по умолчанию (если None, то дата не поставлена)
        """
        super(EditTransactionDialog, self).__init__(accounts, categories, account_id, *args, **kwargs)

        # Каждый раз при изменении каких-либо данных, введёные данные будут сравниваться отсюда
        self.default_settings = {
            "account_id": account_id,
            "category_id": category_id,
            "money": money,
            "date": date
        }

        # Ставим соотвествующие название кнопки и окна диалога
        self.setWindowTitle("Редактировать транзакцию")
        self.add_button.setText("Сохранить")

        # Изменяем данные в соотвествии с данными транзакции
        self.transaction_info.set_money(money)
        self.transaction_info.set_date(date)
        self.money_spinbox.setValue(money)
        if date is None:
            self.date_checkbox.setChecked(False)
        else:
            self.date_edit.setDate(date)
        self.category = get(categories, lambda c: c.id == category_id, no_category)
        self.category_combobox.setCurrentIndex(self.category_combobox.findData(self.category.id))

        # Переменная, которая указывает, что транзакцию должна быть удаленна
        self.deleted = False

        # Добавляем допольнительную кнопку - удалить транзакцию
        self.delete_button = QPushButton("Удалить", self)
        self.delete_button.clicked.connect(self.set_as_deleted)
        self.buttons_layout.insertWidget(0, self.delete_button)

    def check_data(self):
        """Проверяем данные формы. Если данные недействительны, то кнопка 'Сохранить' будет выключена"""
        state = True

        if self.transaction.money != 0:
            if self.default_settings["money"] != self.transaction.money:
                state = False
            elif not self.default_settings["category_id"] == self.category.id:
                state = False
            elif self.account.id != self.default_settings["account_id"]:
                state = False
            elif self.transaction.date != self.default_settings["date"]:
                state = False

        self.add_button.setDisabled(state)

    def set_as_deleted(self):
        """Когда пользователь хочет удалить транзакцию"""
        dialog = QMessageBox.warning(
            self,
            "Удаление транзакции",
            "Вы точно хотите удалить данную транзакцию?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Yes
        )

        # Если пользователь решил, что транзакцию нужно удалить, то пометим это и закроем окно
        if dialog == QMessageBox.Yes:
            self.deleted = True
            self.accept()


class CreateAccountDialog(QDialog, CreateAccountDialogUi):
    def __init__(self, accounts, currencies, *args, **kwargs):
        """
        Виджет предназначенный для создания нового счёта

        :param accounts: список, содержащий все доступные счета
        :param categories: список, содержащий все доступные категории
        """
        super(CreateAccountDialog, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowIcon(QIcon("icon.ico"))
        self.setWindowTitle("Создать счёт")

        # Основные переменные
        self.accounts = accounts
        self.currencies = currencies

        self.account = Account(0, None, default_color, currencies[0].short_name, 0)

        # Показываем, как будет выглядить счёт после создания
        self.account_info = AccountInfo(self.account)
        self.account_info.set_name("Без названия")
        self.main_layout.insertWidget(0, self.account_info)

        for currency in self.currencies:
            self.currency_combobox.addItem(currency.name, currency.short_name)

        # Подключаем функции к элементам интерфейса
        self.add_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.money_spinbox.valueChanged.connect(self.money_changed)
        self.name_line_edit.textChanged.connect(self.name_changed)
        self.currency_combobox.currentIndexChanged.connect(self.currency_changed)
        self.change_color_button.clicked.connect(self.change_color)

    def check_data(self):
        """Проверяем данные формы. Если данные недействительны, то кнопка 'Добавить' будет выключена"""
        state = True

        # Ищем, чтобы имя нового счёта не совпадало с другими именами счетов
        if self.account.name is not None:
            for account in self.accounts:
                if account.name == self.account.name:
                    break
            else:
                state = False

        self.add_button.setDisabled(state)

    def money_changed(self, value):
        """Когда мы изменяем начальное количество денег на счёте"""
        self.account_info.set_money(value)
        self.account.money = value

        self.check_data()

    def name_changed(self, value):
        """Когда мы изменяем название счёта"""
        # Если поле не пустое
        if value:
            self.account_info.set_name(value)
            self.account.name = value
        else:
            self.account_info.set_name("Нет названия")
            self.account.name = None

        self.check_data()

    def currency_changed(self, index):
        """Когда мы изменяем валюту счёта"""
        currency = get(self.currencies, lambda c: c.short_name == self.currency_combobox.itemData(index))
        self.account.currency = currency.short_name
        self.account_info.set_currency(currency.short_name)

        self.check_data()

    def change_color(self):
        """Когда мы изменяем цвет счёта"""
        color = QColorDialog.getColor(self.account.color)
        if color.isValid():
            self.account.color = color
            self.account_info.set_color(color)

        self.check_data()


class EditAccountDialog(CreateAccountDialog):
    def __init__(self, accounts, currencies, name, color, money, currency, *args, **kwargs):
        """
        Виджет предназначенный для создания нового счёта

        :param accounts: список, содержащий все доступные счета
        :param categories: список, содержащий все доступные категории
        :param name: название счёта, которое будет поставлено по умолчанию
        :param color: QColor цвет, который будет поставлен по умолчанию
        :param money: количество денег на счету, которое будет поставлено по умолчанию
        :param currency: валюта счёта, которая будет поставлена по умолчанию
        """
        super(EditAccountDialog, self).__init__(accounts, currencies, *args, **kwargs)

        # Ставим соотвествующие название кнопки и окна диалога
        self.setWindowTitle("Редактировать транзакцию")
        self.add_button.setText("Сохранить")
        self.money_label.setText("Сумма:")

        # Настройки счёта, которые были в момент открытия окна диалога. По этим настройкам будет идти сравнение, изменил
        # ли пользователь что-то или нет
        self.default_settings = {
            "name": name,
            "color": color,
            "money": money,
            "currency": currency
        }

        # Переменная, которая указывает, что транзакцию должна быть удаленна
        self.deleted = False

        # Добавляем допольнительную кнопку - удалить транзакцию
        self.delete_button = QPushButton("Удалить", self)
        self.delete_button.clicked.connect(self.set_as_deleted)
        self.buttons_layout.insertWidget(0, self.delete_button)

        # Если у пользователя всего один счёь, то выключаем кнопку "Удалить". У пользователя должен быть как минимум
        # один счёт
        if len(accounts) == 1:
            self.delete_button.setDisabled(True)

        # Вставляем в формы информацию о счёте
        self.name_line_edit.setText(name)
        self.currency_combobox.setCurrentIndex(self.currency_combobox.findData(currency))
        self.account.color = color
        self.account_info.set_color(color)
        self.money_spinbox.setValue(money)

        self.account_info.change_account(self.account)

    def check_data(self):
        """Проверяем данные формы. Если данные недействительны, то кнопка 'Сохранить' будет выключена"""
        state = True

        # Ищем, чтобы имя нового счёта не совпадало с другими именами счетов
        if self.account.name is not None and self.account.name != self.default_settings["name"] and \
                self.account.name not in [x.name for x in self.accounts]:
            state = False
        elif self.account.money != self.default_settings["money"]:
            state = False
        elif self.account.color != self.default_settings["color"]:
            state = False
        elif self.account.currency != self.default_settings["currency"]:
            state = False

        self.add_button.setDisabled(state)

    def set_as_deleted(self):
        dialog = QMessageBox.warning(
            self,
            "Удаление счёта",
            "Вы точно хотите удалить данный счёт?",
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Yes
        )

        # Если пользователь решил, что транзакцию нужно удалить, то пометим это и закроем окно
        if dialog == QMessageBox.Yes:
            self.deleted = True
            self.accept()


class ListAccountsDialog(QDialog):
    def __init__(self, db, accounts, currencies, *args, **kwargs):
        """
        Диалог, который показывает список счетов, которые есть у пользователя

        :param db: подключение к базе данных
        :param accounts: список, содержащий все доступные счета
        :param categories: список, содержащий все доступные категории
        """
        super(ListAccountsDialog, self).__init__(*args, **kwargs)
        self.resize(423, 194)
        self.setWindowTitle("Список счетов")
        self.setWindowIcon(QIcon("icon.ico"))

        # Ставим основные переменные
        self.db = db
        self.accounts = accounts
        self.currencies = currencies

        # Создаем виджет для вывода списка счетов на данный момент
        self.main_layout = QHBoxLayout(self)
        self.accounts_list_widget = AccountsList(self)
        self.main_layout.addWidget(self.accounts_list_widget)

        # Ставим счета
        self.set_accounts()

    def set_accounts(self):
        """Сортируем счета по алфавитному порядку и ставим их в списке"""
        sorted_accounts = sorted(self.accounts, key=lambda a: a.name, reverse=True)
        self.accounts_list_widget.set_accounts(sorted_accounts, self.edit_account)

    def edit_account(self, original_account):
        """Когда пользователь редактирует счёт"""
        dialog = EditAccountDialog(self.accounts, self.currencies, original_account.name, original_account.color,
                                   original_account.money, original_account.currency)

        if dialog.exec_():
            account = dialog.account
            account.id = original_account.id

            cursor = self.db.cursor()

            # Если пользотель нажал на кнопку "удалить"
            if dialog.deleted:
                # # Удаляем транзакции связанные со счётом и удаляем сам счёт
                cursor.execute("DELETE FROM 'transaction' WHERE account_id = ?", (account.id,))
                cursor.execute("DELETE FROM account WHERE id = ?", (account.id,))

                # Находим счёт в списке счетов и удаляем его
                for index in range(len(self.accounts)):
                    if self.accounts[index].id == account.id:
                        del self.accounts[index]
                        break
            else:
                # Делаем изменения в базе данных
                cursor.execute(
                    "UPDATE account SET name = ?, color = ?, currency = ?, money = ? WHERE id = ?",
                    (account.name, account.color.name()[1:] if account.color else None, account.currency, account.money,
                     account.id)
                )

                # Находим счёт в списке счетов и изменяем его
                for index in range(len(self.accounts)):
                    if self.accounts[index].id == account.id:
                        self.accounts[index].name = account.name
                        self.accounts[index].color = account.color
                        self.accounts[index].currency = account.currency
                        self.accounts[index].money = account.money

            self.db.commit()

            # Обновляем список аккаунтов в диалоге
            self.set_accounts()


class Main(QMainWindow):
    def __init__(self):
        """
        Основной класс программы. Здесь происходит подключение к базе данный, запуск основной страницы программы и
        генерация меню
        """
        super(Main, self).__init__()
        self.resize(650, 450)
        self.setWindowTitle("Мои доходы и расходы")
        self.setWindowIcon(QIcon("icon.ico"))

        # Подключение к базе данных
        self.db = sqlite3.connect("db.sqlite")

        cursor = self.db.cursor()

        # Получить все доступные счета из базы данных
        self.accounts = []
        for row in cursor.execute("SELECT * FROM account").fetchall():
            self.accounts.append(Account(*row))
        self.accounts.sort(key=lambda a: a.name)

        # Получить все доступные категории транзакции из базы данных
        self.categories = []
        for row in cursor.execute("SELECT * FROM category").fetchall():
            self.categories.append(Category(*row))
        self.categories.sort(key=lambda c: c.name, reverse=True)

        # Получить все доступные валюты
        self.currencies = []
        for row in cursor.execute("SELECT * FROM currency").fetchall():
            self.currencies.append(Currency(*row))
        self.currencies.sort(key=lambda c: c.name, reverse=True)

        main_page = MainPage(self.db, self.accounts, self.categories, self.currencies)
        self.setCentralWidget(main_page)

        # Создаём меню, в котором мы сможем редактировать счета
        create_account_action = QAction("Создать счёт", self)
        create_account_action.triggered.connect(main_page.create_account)
        accounts_list_actions = QAction("Список счетов", self)
        accounts_list_actions.triggered.connect(main_page.accounts_list)

        menu = self.menuBar()
        accounts_menu = menu.addMenu("Счета")
        accounts_menu.addAction(create_account_action)
        accounts_menu.addAction(accounts_list_actions)

    def closeEvent(self, event):
        self.db.close()  # Закрыть подключение с базой данных при закрытии программы


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    sys.exit(app.exec())
