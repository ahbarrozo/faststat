import pandas as pd
from scipy import stats
from outliers import smirnov_grubbs as grubbs


def filter_numeric_data(data_frame, parameter):
    """Removes NaN from any pandas Data Frame and performs 
    Grubbs' test to check for outliers, removing them. By
    default, it uses alpha=0.05 for removal of outliers.

    Arguments
    ---

    data_frame : pd.DataFrame 
        Data frame to be parsed

    parameter : str
        Name of column in data_frame to be checked

    Returns
    ---

    grubbs.test : pd.Series
        Result from Grubbs' test, telling about outliers removed"""

    if parameter not in data_frame.columns:
        raise AttributeError(f"Could not find {parameter} in data frame.")

    filter_nan = data_frame[pd.notnull(data_frame[parameter])]     # filtering NaN data
    data_series = pd.Series(filter_nan[parameter])
    data_series.reset_index(drop=True, inplace=True)               # index must be reset to work

    try:
        data = pd.to_numeric(data_series) # conversion necessary to use Grubbs' test

    except ValueError:
        raise ValueError("Grubbs' test cannot be performed due to non-numeric data. Please check your data.")

    # There seems to be an issue with the smirnov_grubbs.py when handling
    # certain large outliers, and I could not figure out why. This is an error
    # handling to cope with this issue
    try:
        return grubbs.test(data, alpha=0.05) 

    except KeyError:
        raise KeyError("""Grubbs' test cannot be performed due to input data. Try
                       removing manually any outlier that is largely deviating
                       from the distribution""")


def subset_data(data_frame, parameter, subset_val):
    """Extracts subset of data frame where 'parameters' is 'subset_val'"""
    return data_frame[data_frame[parameter] == subset_val], subset_val


def bins_subset(data_frame, parameter, bin_num=None):
    if not bin_num:
        return data_frame.filter(like=parameter + ' bin')
    else:
        return data_frame.filter(like=parameter + ' bin ' + str(bin_num))


def bin_dataframe_generator(data_frame, bin_parm):
    """Creates a nenw data frame from an input to handle bins to be used in
    ANOVA calculations.

    Arguments
    ---

    data_frame : pd.DataFrame 
        Data frame to be parsed

    bin_param : str
        Name of bin column group in data_frame 

    Returns
    ---

    grubbs.test : pd.Series
        Result from Grubbs' test, telling about outliers removed"""

    bin_num = data_frame.columns.str.contains(bin_parm + ' bin ').sum()
    bin_dataframe = pd.DataFrame()  # empty declaration to perform concatenation
    for i in range(1, bin_num + 1):
        bin_subset = bins_subset(data_frame, bin_parm, i).dropna()
        bin_subset = pd.DataFrame(filter_numeric_data(bin_subset, bin_parm + ' bin ' + str(i)))
        bin_subset['bin'] = i
        bin_subset.rename(columns={f'{bin_parm} bin {i}': f'{bin_parm}'}, inplace=True)
        bin_dataframe = bin_dataframe.append(bin_subset)
    
    bin_dataframe.reset_index(inplace=True)
    bin_dataframe.fillna(0, inplace=True)

    return bin_dataframe


class DataSet:
    def __init__(self, df, events, **parms):
        self._data_frame = df
        self._name = ""

        # parms is a dictionary that is passes all the chosen parameters and
        # their values to create a smaller data frame.
        if parms is not None:
            for key, value in parms.items():
                self._data_frame,  self._parm_name = subset_data(self._data_frame, key, value)
                self._name += str(self._parm_name) + " "
        try:
            self._data_set = filter_numeric_data(df, events)
        except ValueError:
            self._data_set = pd.Series() # returns an empty seriees
            pass
        self._isnormal = True  # data is assumed to be normal.
        self._events = events

    @property
    def name(self):
        if self._data_set.empty:
            return ""
        else:
            return str(self._name) + " : " + str(self._data_set.name)

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def data_frame(self):
        return self._data_frame

    @data_frame.setter
    def data_frame(self, df):
        self._data_frame = df

    @property
    def data_set(self):
        return self._data_set

    @data_set.setter
    def data_set(self, dataset):
        self._data_set = dataset

    def isnormal(self):
        return self._isnormal

    def data_events(self):
        return self._events

    def sampling_size(self):
        return len(self._data_set)   

    def mean_value(self):
        return self._data_set.mean()

    def median_value(self):
        return self._data_set.median()

    def quantile25_value(self):
        return self._data_set.quantile(.25)

    def quantile75_value(self):
        return self._data_set.quantile(.75)
    
    def std_value(self):
        return self._data_set.std()

    def sem_value(self):
        return stats.sem(self._data_set) 
