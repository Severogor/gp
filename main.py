#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re, json
import os, sys
from ModelInterface import *


################
# Model Interface
# ~S.
################


path = os.path.abspath(os.path.dirname(sys.argv[0]))

def metal(value, model, dicts, default = None):
    """Trivial metal dictionary fixer
        value: fixed values list
        model: validation model of appropriate type
        dicts: word token dictionary
        default: default value for not-found keys
    """

    data = []
    for item in value:
        instance = {}
        for d in dicts:
            for v in model.model:
                for w in dicts[d]:
                    if w in str(item[v]).lower():
                        instance[d] = dicts[d][w]
                        break
                if instance.get(d):
                    break
            if not instance.get(d):
                instance[d] = default

        data.append(instance)

    return data



def as_is(value):
    """Dummy function"""

    return value



def split(value, key, delimiter, model):
    """Split value by delimiter
        value: parsed list value
        key: field to split by
        delimiter: regex pattern
        model: validation model of appropriate type
    """

    instances = []
    for v in value:
        for s in [x.strip() for x in delimiter.split(v[key]) if x.strip()]:
            i = model.parse(v)
            i[key] = s
            instances.append(i)

    return instances



def match(value, field, token):
    """Get fuzzy values identified by word tokens
        value: parsed list value
        field: destination value[field]
        token: regex pattern
    """

    for v in value:
        s = token.search(v["insertion"])
        try:
            v[field] = s.group(0)
            v["insertion"] = v["insertion"].replace(s.group(0), '')

        except AttributeError:
            pass

    return value



# Модель блока металлов
mm = model({
    'metal': parse_str,
    'sample': parse_int,
    'color': parse_str
})

# Словарь по металлам
dictpath = os.path.join(path, "metaldict.json")
print()
print("Loading dictionaries from %r" % (dictpath,))
try:
    with open(dictpath) as f:
        mdict = json.load(f)
        print("Done")

except OSError as ex:
    mdict = {}
    print(ex)

# Модель блока размеров
dm = model({
    'size': parse_float,
    'weight': parse_float,
    'length': parse_float,
    'height': parse_float,
    'currency': parse_str,
    'first_price': parse_float,
    'last_price': parse_float,
    'width': parse_float
})

# Модель блока вставок
im = model({
    'carat': parse_float,
    'color': parse_int,
    'count': parse_int,
    'cut': parse_str,
    'cut_count': parse_int,
    'form': parse_str,
    'insertion': parse_str,
    'purity': parse_int,
    'type': parse_str
})

# Интерфейс основной модели
i = interface("provider_name", {
    "nebo": {},
    "adamas": {
        "insertion_group_list": (
            (split, {"key": "insertion", "delimiter": re.compile('\s*;\s*'), "model": im}),
            (match, {"field": "count", "token": re.compile(r'([0-9]+)\s*шт(?:ук)?[.]*', re.IGNORECASE)}),
            (match, {"field": "carat", "token": re.compile(r'((?:[0-9]*[,.])?[0-9]+)\s*кар(?:ат)?[.]*', re.IGNORECASE)}),
        )
    }
})

# Основная модель
bm = model({
    "stuff_list": (blocklist, {"model": model({
        'brand': parse_str,
        'crucifixion': parse_bool,
        'dimensions': (blocklist, {"model": dm}),
        'insertion_group_list': (blocklist, {"model": im}),
        'insertion_count': parse_int,
        'is_child': parse_bool,
        'lock': parse_list,
        'metal': (trigger, {"tlist": [(metal, {"model": mm, "dicts": mdict}), (blocklist, {"model": mm})]}),
        'metal_count': parse_int,
        'name': parse_str,
        'product_type': parse_str,
        'provider': parse_str,
        'provider_images': parse_list,
        'provider_name': parse_str,
        'provider_url': parse_str,
        'religion': parse_bool,
        'sex': parse_str,
        'soroka_images': parse_list,
        'style': parse_list,
        'vendor_code': parse_str,
        'weaving': parse_str
    }, i)})
})


# Чтение
srcpath = os.path.join(path, 'sample-data.json')
print("Reading data from file %r" % (srcpath,))
try:
    with open(srcpath) as f:
        data = json.load(f)
        print("Done")

except OSError as ex:
    exit(ex)

# Запись
respath = os.path.join(path, 'result.json')
print("Writing data to file %r" % (respath,))
try:
    with open(respath, 'w') as f:
        json.dump(bm.parse(data), f, ensure_ascii = False, indent = 2)
        print("Done")
        print()

except OSError as ex:
    exit(ex)

