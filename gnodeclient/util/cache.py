"""
A file based cache that uses pickle to store dict objects
"""

import os
import shutil
import random
import string
import urlparse
from os import path
import cPickle as pickle
import appdirs

DEFAUTL_BASE_DIR = 'gnodeclient'
FILE_DIR = 'files'
OBJ_DIR = 'objects'


class Cache(object):

    def __init__(self, location=None, base_dir=DEFAUTL_BASE_DIR):
        if location is None:
            self.__base_dir = appdirs.user_cache_dir(base_dir)
        else:
            self.__base_dir = path.join(location, base_dir)

        self.__file_dir = path.join(self.base_dir, FILE_DIR)
        self.__obj_dir = path.join(self.base_dir, OBJ_DIR)

        dirs = (self.base_dir, self.file_dir, self.obj_dir)
        for d in dirs:
            if not path.isdir(d):
                os.mkdir(d, 0750)
            else:
                os.chmod(d, 0750)

    #
    # Properties
    #

    @property
    def base_dir(self):
        return self.__base_dir

    @property
    def file_dir(self):
        return self.__file_dir

    @property
    def obj_dir(self):
        return self.__obj_dir

    #
    # Methods
    #

    def set(self, location, data):
        ident = urlparse.urlparse(location).path.split("/")[-1].lower()
        f_name = self.obj_cache_path(ident)

        all_data = self.secure_read(f_name, {})
        all_data[ident] = data
        self.secure_write(f_name, all_data)

    def get(self, location):
        ident = urlparse.urlparse(location).path.split("/")[-1].lower()
        f_name = self.obj_cache_path(ident)

        all_data = self.secure_read(f_name, {})

        if ident in all_data:
            return all_data[ident]
        else:
            return None

    def delete(self, location):
        ident = urlparse.urlparse(location).path.split("/")[-1].lower()
        f_name = self.obj_cache_path(ident)

        all_data = self.secure_read(f_name, {})

        if ident in all_data:
            del all_data[ident]
            return True
        else:
            return False

    def set_file(self, location, data):
        ident = urlparse.urlparse(location).path.split("/")[-1].lower()
        f_name = self.file_cache_path(ident)

        self.secure_write(f_name, data, False)

    def get_file(self, location):
        ident = urlparse.urlparse(location).path.split("/")[-1].lower()
        f_name = self.file_cache_path(ident)

        if path.isfile(f_name):
            data = self.secure_read(f_name, serialize=False)
            return data
        else:
            return None

    def delete_file(self, location):
        ident = urlparse.urlparse(location).path.split("/")[-1].lower()
        f_name = self.file_cache_path(ident)

        if path.isfile(f_name):
            os.remove(f_name)
            return True
        else:
            return False

    def clear(self):
        dirs = (self.base_dir, self.file_dir, self.obj_dir)
        for d in dirs:
            if path.exists(d):
                shutil.rmtree(d)
            os.mkdir(d, 0750)

    #
    # Helper methods
    #

    def obj_cache_path(self, ident):
        prefix = ident[0:2]
        return path.join(self.obj_dir, prefix)

    def file_cache_path(self, ident):
        return path.join(self.file_dir, ident)

    def secure_read(self, f_name, default=None, serialize=True):
        f_handle = None
        f_name_tmp = path.join(self.base_dir, "temp_" + "".join(random.choice(string.lowercase) for _ in range(20)))

        try:
            if path.exists(f_name):
                shutil.copy2(f_name, f_name_tmp)
                f_handle = open(f_name, "rb")

                if serialize:
                    try:
                        data = pickle.load(f_handle)
                    except EOFError:
                        data = default
                else:
                    data = f_handle.read()

            else:
                data = default

        except Exception, e:
            if f_handle is not None and not f_handle.closed:
                f_handle.close()
            if path.exists(f_name_tmp):
                if path.exists(f_name):
                    os.remove(f_name)
                os.rename(f_name_tmp, f_name)
            raise e

        else:
            if f_handle is not None and not f_handle.closed:
                f_handle.close()
            if path.exists(f_name_tmp):
                os.remove(f_name_tmp)

        return data

    def secure_write(self, f_name, data, serialize=True):
        f_handle = None
        f_name_tmp = path.join(self.base_dir, "temp_" + "".join(random.choice(string.lowercase) for _ in range(20)))

        try:
            if path.exists(f_name):
                shutil.copy2(f_name, f_name_tmp)
            f_handle = open(f_name, "wb")

            if serialize:
                pickle.dump(data, f_handle)
            else:
                f_handle.write(data)

        except Exception, e:
            if f_handle is not None and not f_handle.closed:
                f_handle.close()
            if path.exists(f_name_tmp):
                if path.exists(f_name):
                    os.remove(f_name)
                os.rename(f_name_tmp, f_name)
            raise e

        else:
            f_handle.close()
            if path.exists(f_name_tmp):
                os.remove(f_name_tmp)



