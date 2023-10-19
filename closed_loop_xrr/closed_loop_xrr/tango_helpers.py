#!/usr/bin/env python
# --encoding: utf-8--


def att_group_to_dict(dev, prefix=None):
    attr_list = dev.get_ml_attribute_list()
    tmp = dict()
    if prefix is None:
        for x in attr_list:
            tmp[k] = getattr(dev, x)
    else:
        for x in attr_list:
            p, k = x.split("_", 1)
            if p == prefix:
                tmp[k] = getattr(dev, x)
    return tmp


def get_predictions(dev):
    return att_group_to_dict(dev, "prediction")
