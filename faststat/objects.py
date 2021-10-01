from werkzeug.utils import secure_filename
import pandas as pd

class FastStat:
    """A class to handle user inputs within FastStat, from the spreadsheet to
    the choice of analysis to be performed.

    Attributes
    ---

    data_frame : pandas.DataFrame
        Used to store all the data from the uploaded spreadsheet

    file_name : str
        The uploaded spreasheet file name

    parm_names : list
        A list containing all the column names extracted from the spreasheet. 
        Those must be added manually by the spreasheet creator. Specific 
        format needs to be followed particularly when handling variables with 
        multiple bins. In this case, all the bins of a given property should be
        named in a single merged cell. Following from it, an 'Average' or
        'Total' kind of property of those bins must follow. See 'example'
        folder for a sample file.

    parms : dict
        A dictionary that stores the choice of parameters the user wishes to
        use to define a subset for analysis. Keys are the spreasheet column 
        name, and values are the name/id extracted from the cells in the
        column.

    stat_func : str
        Name of the statistical function to be used in the analysis. This
        includes: Basic Statistics, Normality Test, Null-Hypothesis Test, 
        One- and Two-way ANOVA 

    stat_property : str
        Name of the parameter to be analyzed statistically.

    template : str
        HTML template to be rendered
    """

    def __init__(self, file = None):
        if file is None:
            self._data_frame = None
            self._file_name = None
            self._parm_names = None

        else:
            self._file_name = secure_filename(file.filename)
            self._data_frame = self.read_data(file)
            self._parm_names = self.data_frame.columns.values.tolist()

        self._parms = {}
        self._stat_func = None
        self._stat_property = None
        self._template = "view_input.html"


    def read_data(self, input_file, num_bin = 3):
        """Opens MS Excel spreadsheet and converts it to a pandas 
        DataFrame

        Arguments
        ---

        input_file: str 
            Path to a xls or xlsx file

        num_bin : int
            Number of bins used in this spreadsheet. Use 3 by default

        Returns
        ---
            pd.DataFrame format of the spreadsheet"""

        input_data = pd.read_excel(input_file)
        renamed_columns = list(input_data.columns)

        for i in range(len(renamed_columns)):
            """Rename 'Unnamed' columns that are formed from merged 
            cells. These will form bins for analysis"""
            if renamed_columns[i].find("Unnamed") >= 0:
                for b in range(num_bin - 1): 
                    renamed_columns[i+b] = renamed_columns[i-1] + f' bin {b+2}'

                renamed_columns[i-1] += ' bin 1'

        return pd.DataFrame(input_data.values, columns=pd.Index(renamed_columns))



    def reset(self, hard_reset=False):
        if hard_reset:
            self.__init__()
        else:
            self._parms = {}
            self._stat_func = None
            self._stat_property = None
            self._template = "view_input.html"


    # First three parameters have no setters. Those must be 
    # initialized via self.__init__ for consistency.
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

