#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re



class InterfaceError(KeyError):
    """Basic interface errors generalize to KeyError anyway"""

    pass



class InterfaceNotFoundError(InterfaceError):
    """Interface is not defined for selector identifier"""

    pass



class BadInterfaceError(InterfaceError):
    """Interface<->model incompatibility"""

    pass



def trigger(value, tlist):
    """Multifunction trigger
        value: parsed value
        tlist: trigger list, i.e.

        (
          simpletrigger,
          (trigger, {"parameter": value, ...}),
          ...
        )

        Every trigger function must have at least one parameter (value) which is modified and returned
    """

    for t in tlist:
        if callable(t):
           # Простой вызов -- вызываемый объект (функция) с одним параметром
            value = t(value)
        else:
            # Вызов функции/метода с несколькими параметрами в виде (f, {"parameter": value, ...})
            value = t[0](value, **t[1])

    return value



def blocklist(value, model):
    """Block list parser
        value: parsed list of blocks with structure defined by model
        model: value items model
    """

    data = []
    for v in value:
        # Кладём в контейнер все объекты, сверенные с моделью-эталоном
        data.append(model.parse(v))

    return data



class model:
    """Base model class"""

    def __init__(self, model, interface = None):
        """Initialize model with possible interface
            model: a mapping object, i.e.

            {
              "a": int,
              "b": str,
              "c": (trigger, (("custom_func1", {...}), ...)),
              ...
            }

            interface: an interface-like object with mapping dict and match method
        """

        self.model = model
        self.interface = None

        if interface:
            self.setinterface(interface)


    def setinterface(self, interface):
        """Check object usability and model-conformance
            interface: interface-like object with "mapping" mapping dict and "match" match method
        """

        # Проверка наличия необходимых свойств объекта
        for t in ((type, "mapping", dict), (callable, "match", True)):
            if t[0](getattr(interface, t[1], None)) is not t[2]:
                raise AttributeError('Interface-like object required with "mapping" dictionary and "match" method')

                return

        # Проход и проверка на соответствие полей интерфейса используемой модели
        model_set = set(self.model)
        for i in interface.mapping:
            if not set(interface.mapping[i]) <= model_set:
                raise BadInterfaceError("Interface %r must be a (sub)set of model, but has extra keys (%s)" % (i, ", ".join([repr(v) for v in set(interface.mapping[i]) - set(self.model)])))

                return

        # Установить предположительно подходящий интерфейс
        self.interface = interface


    def match(self, value):
        """Match/clean value according to a predefined model
            value: matching value
        """

        data = {}
        # Проход по определению модели
        for m in self.model:

            try:
                if callable(self.model[m]):
                    data[m] = self.model[m](value[m])
                else:
                    data[m] = self.model[m][0](value[m], **self.model[m][1])

            # Неполный источник
            except KeyError:
                data[m] = None

            # Неправильное определение вызова
            except TypeError as ex:
                print(ex)
                data[m] = None

        return data


    def parse(self, value):
        """Start model validation
            value: matching value
        """

        # Проход по интерфейсу, если он есть
        # По принципу от частного (интерфейса) -- к общему (модели)
        if self.interface:
            self.interface.match(value)

        # Проход по модели и возврат значения
        return self.match(value)



class interface:
    """Model interface"""

    def __init__(self, selector, mapping):
        """Interface object constructor:
            selector: source identifier field name
            mapping: interface dictionary
                {"id-key": {"field": ((<function object> f, <params> {}), ...), ...}, ...}
        """

        self.id = None
        self.selector = selector
        self.mapping = mapping


    def match(self, source):
        """Match source data to interface:
            source: data dictionary

            returns: modified source
        """

        # Выбрать ключ-селектор блока данных для использования к нему соответствующего интерфейса
        try:
            self.id = source[self.selector]

        except KeyError:
            # Если ключ селектора отсутствует -- вызвать исключение
            raise InterfaceError("Inconsistent data: interface selector key %r not found in data" % (self.selector,))
            self.id = None

        # Если по данному значению селектора не задан интерфейс
        if self.id not in self.mapping:
            raise InterfaceNotFoundError("Interface for identifier %r is not found in mapping definition" % (self.id,))

        # Проход по полям блока интерфейса, соответствующего выбранному ранее значению селектора
        for k in self.mapping[self.id]:
            # Проход по обработчикам поля
            for f in self.mapping[self.id][k]:
                # Запуск обработчиков (обработка и изменение источника)
                source[k] = f[0](source[k], **f[1])

        return source



def parse_float(value):
    """Parse float value given in arbitrary format"""

    try:
        return float(re.search(r"([-]?(?:[0-9]*[,.])?[0-9]+)", str(value)).group(0).replace(',', '.'))

    except AttributeError as ex:
        return None



def parse_int(value):
    """Parse integer value given in arbitrary format"""

    try:
        return int(float(re.search(r"([-]?(?:[0-9]*[,.])?[0-9]+)", str(value)).group(0).replace(',', '.')))

    except AttributeError as ex:
        return None



def parse_str(value):
    """Parse string value except None"""

    try:
        return [str(value), None][value is None]

    except UnicodeEncodeError as ex:
        return None



def parse_bool(value):
    """Parse boolean value given in arbitrary format"""

    value = str(value)[:6].strip().title()
    s = set(['1', 'True', '0', 'False'])

    try:
        if value not in s:
            raise ValueError("unexpected value out of set (expected %s, got \"%s\")" % (tuple(s), value,))

    except ValueError as ex:
        return None

    return [False, True][value in ['1', 'True']]



def parse_list(value):
    """Parse simple string list"""

    try:
        return [str(v) for v in value]

    except TypeError as ex:
        return None


