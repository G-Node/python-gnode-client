"""
Proxy object are used as a mechanism for lazy loading.
"""


def lazy_value_loader(location, store, result_driver):

    def do_lazy_load():
        obj = store.get(location, False)
        res = result_driver.to_result(obj)
        return res

    return do_lazy_load


def lazy_list_loader(locations, store, result_driver):

    def do_lazy_load():
        results = []

        for location in locations:
            obj = store.get(location, False)
            res = result_driver.to_result(obj)
            results.append(res)

        return results

    return do_lazy_load

