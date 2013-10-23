from __future__ import print_function, absolute_import, division

import os
import shutil
import appdirs

try:
    # python > 3.1 has not module cPickle
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import urlparse
except ImportError:
    # python > 3.1 has not module urlparse
    import urllib.parse as urlparse

import gnodeclient.util.helper as helper


class Cache(object):
    """
    A file system based cache that uses pickle to store python objects and file data.
    """

    DEFAUTL_BASE_DIR = 'gnodeclient'
    FILE_DIR = 'files'
    FILE_DIR_TMP = 'files_tmp'
    OBJ_DIR = 'objects'
    OBJ_DIR_TMP = 'objects_tmp'

    def __init__(self, location=None, base_dir=DEFAUTL_BASE_DIR):
        """
        Cache initialisation

        :param location: The location of the base directory, by default a suitable location is chosen.
        :type location: str
        :param base_dir: The name of the base directory.
        :type base_dir: str
        """
        if location is None:
            self.__base_dir = appdirs.user_cache_dir(base_dir)
        else:
            self.__base_dir = os.path.join(location, base_dir)

        self.__file_dir = os.path.join(self.base_dir, Cache.FILE_DIR)
        self.__file_dir_tmp = os.path.join(self.base_dir, Cache.FILE_DIR_TMP)
        self.__obj_dir = os.path.join(self.base_dir, Cache.OBJ_DIR)
        self.__obj_dir_tmp = os.path.join(self.base_dir, Cache.OBJ_DIR_TMP)

        self.ensure_dirs()

    #
    # Properties
    #

    @property
    def base_dir(self):
        """
        The path to the base directory.
        """
        return self.__base_dir

    @property
    def file_dir(self):
        """
        The path to the directory where cached files are stored.
        """
        return self.__file_dir

    @property
    def obj_dir(self):
        """
        The path to the directory where cached objects are stored.
        """
        return self.__obj_dir

    @property
    def file_dir_tmp(self):
        """
        The path to the directory where temporarily cached files are stored.
        """
        return self.__file_dir_tmp

    @property
    def obj_dir(self):
        """
        The path to the directory where cached objects are stored.
        """
        return self.__obj_dir

    @property
    def obj_dir_tmp(self):
        """
        The path to the directory where temporarily cached objects are stored.
        """
        return self.__obj_dir_tmp

    #
    # Methods
    #

    def set(self, location, data, temporary=False):
        """
        Caches some object under a certain identifier. The identifier is extracted from the given
        location.

        Example locations:
            "http://host/foo/identifier?param=val"
            "/foo/identifier"
            "identifier"

        :param location: An url or path that ends with a unique identifier or the identifier itself.
        :type location: str
        :param data: Some object that can be serialized by pickle.
        :type data: object
        """
        ident = helper.id_from_location(location)
        f_name = self.obj_cache_path(ident, temporary)

        all_data = self._secure_read(f_name, {})
        all_data[ident] = data
        self._secure_write(f_name, all_data)

    def get(self, location, temporary=False):
        """
        Get an object form the cache.

        :param location: An url or path that ends with a unique identifier or the identifier itself.
        :type location: str

        :returns: The cached object or None if not found.
        :rtype: object
        """
        result = None
        ident = helper.id_from_location(location)

        if len(ident) > 0:
            f_name = self.obj_cache_path(ident, temporary)

            all_data = self._secure_read(f_name, {})

            if ident in all_data:
                result = all_data[ident]

        return result

    def delete(self, location, temporary=False):
        """
        Delete an object form the cache.

        :param location: An url or path that ends with a unique identifier or the identifier itself.
        :type location: str

        :returns: True if the object was deleted, False if not found.
        :rtype: bool
        """
        ident = helper.id_from_location(location)
        f_name = self.obj_cache_path(ident, temporary)

        all_data = self._secure_read(f_name, {})

        if ident in all_data:
            del all_data[ident]
            self._secure_write(f_name, all_data)
            return True
        else:
            return False

    def set_file(self, location, data, temporary=False):
        """
        Write file data to the cache.

        :param location: An url or path that ends with a unique identifier or the identifier itself.
        :type location: str
        :param data: A byte-string that will be stored in a file.
        :type data: str
        """
        ident = helper.id_from_location(location)
        f_name = self.file_cache_path(ident, temporary)

        self._secure_write(f_name, data, False)

    def get_file(self, location, temporary=False):
        """
        Get file data form the cache.

        :param location: An url or path that ends with a unique identifier or the identifier itself.
        :type location: str

        :returns: The cached file data or None if not found.
        :rtype: str
        """
        ident = helper.id_from_location(location)
        f_name = self.file_cache_path(ident, temporary)

        if os.path.isfile(f_name):
            data = self._secure_read(f_name, serialize=False)
            return data
        else:
            return None

    def delete_file(self, location, temporary=False):
        """
        Delete file data form the cache.

        :param location: An url or path that ends with a unique identifier or the identifier itself.
        :type location: str

        :returns: True if the file was deleted, False if not found.
        :rtype: bool
        """
        ident = helper.id_from_location(location)
        f_name = self.file_cache_path(ident, temporary)

        if os.path.isfile(f_name):
            os.remove(f_name)
            return True
        else:
            return False

    def clear(self, temporary=False):
        """
        Erase all data from the cache.
        """
        if temporary:
            dirs = (self.file_dir_tmp, self.obj_dir_tmp)
        else:
            dirs = (self.file_dir, self.obj_dir, self.file_dir_tmp, self.obj_dir_tmp)

        for d in dirs:
            if os.path.exists(d):
                shutil.rmtree(d)

        self.ensure_dirs()

    def obj_cache_path(self, ident, temporary):
        prefix = ident[0:2]
        if temporary:
            return os.path.join(self.obj_dir_tmp, prefix)
        else:
            return os.path.join(self.obj_dir, prefix)

    def file_cache_path(self, ident, temporary):
        if temporary:
            return os.path.join(self.file_dir_tmp, ident)
        else:
            return os.path.join(self.file_dir, ident)

    def ensure_dirs(self):
        dirs = (self.base_dir, self.file_dir, self.obj_dir, self.file_dir_tmp, self.obj_dir_tmp)
        for d in dirs:
            if not os.path.isdir(d):
                os.makedirs(d, 0o0750)
            else:
                os.chmod(d, 0o0750)

    #
    # Helper methods
    #

    def _secure_read(self, f_name, default=None, serialize=True):
        f_handle = None
        f_name_tmp = os.path.join(self.base_dir, helper.random_str(20, "tmp"))

        try:
            if os.path.exists(f_name):
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

        except Exception as e:
            if f_handle is not None and not f_handle.closed:
                f_handle.close()
            if os.path.exists(f_name_tmp):
                if os.path.exists(f_name):
                    os.remove(f_name)
                os.rename(f_name_tmp, f_name)
            raise e

        else:
            if f_handle is not None and not f_handle.closed:
                f_handle.close()
            if os.path.exists(f_name_tmp):
                os.remove(f_name_tmp)

        return data

    def _secure_write(self, f_name, data, serialize=True):
        f_handle = None
        f_name_tmp = os.path.join(self.base_dir, helper.random_str(20, "tmp"))

        try:
            if os.path.exists(f_name):
                shutil.copy2(f_name, f_name_tmp)
            f_handle = open(f_name, "wb")

            if serialize:
                pickle.dump(data, f_handle)
            else:
                f_handle.write(data)

        except Exception as e:
            if f_handle is not None and not f_handle.closed:
                f_handle.close()
            if os.path.exists(f_name_tmp):
                if os.path.exists(f_name):
                    os.remove(f_name)
                os.rename(f_name_tmp, f_name)
            raise e

        else:
            f_handle.close()
            if os.path.exists(f_name_tmp):
                os.remove(f_name_tmp)
