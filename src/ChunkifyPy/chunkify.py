"""ChunkifyPy is a python library that chunks a list of items into smaller
chunks based on the max size of each chunk.
"""
import copy
import json
import sys
from json import JSONEncoder
from typing import Iterable, Optional

from more_itertools import chunked

DEFAULT_BATCH_SIZE = 1000


def calculate_batch_size(
    items: list[dict], json_encode_class: JSONEncoder = JSONEncoder
) -> float:
    """Calculate the size of feed in MB."""
    item_size = sys.getsizeof(json.dumps(items, cls=json_encode_class)) / (1024 * 1024)
    return item_size


def optimal_items(weights: list[int], values: list[float], capacity: int) -> list[int]:
    """Find the optimal items to select based on the weights and values.

    :param weights: weights of the items
    :param values: values of the items
    :param capacity: max capacity of the items
    :return:
    """
    value_per_weight = [
        (v / w, idx) for idx, (v, w) in enumerate(zip(values, weights, strict=True))
    ]
    value_per_weight.sort(reverse=True, key=lambda x: x[0])
    max_value = 0
    items_selected = []
    for item, idx in value_per_weight:
        if item > 0 and max_value + item <= capacity:
            max_value += item
            items_selected.append(idx)
    return items_selected


def group_items(items: list[tuple[float, int]], max_item_size: int) -> list[list[int]]:
    """Group items based on the max item size.
    :param items: list of items to group
    :param max_item_size: max item size per group
    :return: list of groups of items where sum of items in each group is less than or
    equal to max_item_size.
    """
    weights = [1] * len(items)  # weights are all 1
    values = [item[0] for item in items]  # values are the item sizes
    capacity = max_item_size
    groups = []
    while True:
        items_selected = optimal_items(weights, values, capacity)
        if not items_selected:
            break
        # add items to groups
        groups.append(items_selected)
        # remove items that are selected
        for idx in items_selected:
            values[idx] = 0
        if all(v == 0 for v in values):
            break
    return groups


def chunkify(
    iterable: list,
    chunk_size: float = 1,
    json_dump_cls: Optional[JSONEncoder] = JSONEncoder,
) -> Iterable:
    """Returns a generator that yields chunks of the given iterable
     with the given chunk size.
    :param iterable: list of items to chunk
    :param chunk_size: size of each chunk. In Megabytes.
    :param json_dump_cls: JSONEncoder class to use for json.dumps.
    """
    if not iterable:
        yield []
    default_batch_size = copy.deepcopy(DEFAULT_BATCH_SIZE)
    while True:
        devices_copy = list(chunked(iterable, default_batch_size))
        item_size_list = [
            calculate_batch_size(items=item, json_encode_class=json_dump_cls)
            for item in devices_copy
        ]
        if len(item_size_list) < 1:
            raise ValueError("chunk_size is too small")
        if max(item_size_list) > chunk_size:
            default_batch_size //= 2
        else:
            break
    item_size_list = [
        (calculate_batch_size(item), idx)
        for idx, item in enumerate(list(chunked(iterable, default_batch_size)))
    ]
    iterable = list(chunked(iterable, default_batch_size))
    indexes = group_items(items=item_size_list, max_item_size=chunk_size)
    for idx, index in enumerate(indexes):
        batch: list[list] = [iterable[idx] for idx in index]
        # flatten the batch
        batch: list = [item for sublist in batch for item in sublist]
        yield batch
