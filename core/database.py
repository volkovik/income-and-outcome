from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor


# Утилиты
def hex_to_rgb(hex_color):
    """
    Преобразует цвет из HEX в RGB (три числа)

    :param hex_color: Строка в виде HEX числа
    :return: кортеж из трёх чисел характеризующие цветовые каналы RGB
    """
    return tuple(int(hex_color[x:x + 2], 16) for x in range(0, 6, 2))


# Классы, ориентированные на данные из базы данных. Сделаны они для удобного использования данных из базы данных
class Currency:
    """Данные о валюте"""

    def __init__(self, name, short_name):
        self.short_name = short_name
        self.name = name


class Account:
    """Данные о счёте"""

    def __init__(self, id, name, color, currency, money):
        self.id = id
        self.name = name
        if type(color) is str:
            self.color = QColor(*hex_to_rgb(color))
        else:
            self.color = color
        self.currency = currency
        self.money = money

    def __copy__(self):
        return Account(self.id, self.name, self.color, self.currency, self.money)


class Category:
    """Данные о категории транзакции"""

    def __init__(self, id, name, color):
        self.id = id
        self.name = name
        if type(color) is str:
            self.color = QColor(*hex_to_rgb(color))
        else:
            self.color = color


class Transaction:
    """Данные о транзакции"""

    def __init__(self, id, account_id, category_id, money, date):
        self.id = id
        self.account_id = account_id
        self.category_id = category_id
        self.money = money
        if type(date) is str:
            self.date = QDate.fromString(date, "dd.MM.yyyy")
        else:
            self.date = date
