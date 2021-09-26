from werkzeug.utils import secure_filename

from faststat.dataparse import read_data


class FastStat:
    def __init__(self, file = None):
        if file is None:
            self._data_frame = None
            self._file_name = None
            self._parm_names = None

        else:
            self._file_name = secure_filename(file.filename)
            self._data_frame = read_data(file)
            self._parm_names = self.data_frame.columns.values.tolist()

        self._parms = {}
        self._values = []
        self._parm_values = []
        self._stat_func = None
        self._stat_property = None
        self._template = "view_input.html"

    def reset(self, hard_reset=False):
        if hard_reset:
            self.__init__()
        else:
            self._parms = {}
            self._values = []
            self._parm_values = []
            self._stat_func = None
            self._stat_property = None
            self._template = "view_input.html"


    @property
    def data_frame(self):
        return self._data_frame

    @property
    def file_name(self):
        return self._file_name


    @property
    def parm_names(self):
        return self._parm_names

    @property
    def parms(self):
        return self._parms

    @parms.setter
    def parms(self, parmlist):
        self._parms = parmlist

    @property
    def parm_values(self):
        return self._parm_values

    @parm_values.setter
    def parms_values(self, parmvalues):
        self._parm_values = parmvalues

    @property
    def stat_func(self):
        return self._stat_func

    @stat_func.setter
    def stat_func(self, func_name):
        self._stat_func = func_name

    @property
    def stat_property(self):
        return self._stat_property

    @stat_property.setter
    def stat_property(self, stat_prop):
        self._stat_property = stat_prop

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, temp_html):
        self._template = temp_html

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, parmlist):
        self._parms = parmlist

