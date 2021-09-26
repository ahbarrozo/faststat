import pandas as pd
from scipy import stats
from outliers import smirnov_grubbs as grubbs


def read_data(input_file):
    """Opens MS Excel spreadsheet and converts it to a pandas DataFrame
    :arg input_file: xls or xlsx file
    :return pd.DataFrame"""

    input_data = pd.read_excel(input_file)

    renamed_columns = list(input_data.columns)
    bin_count = 1

    for i in range(len(renamed_columns)):
        """rename 'Unnamed' columns that are formed from merged cells. These will form bins for analysis"""
        if renamed_columns[i].find("Unnamed") >= 0:
            bin_count += 1
            renamed_columns[i] = renamed_columns[i-bin_count+1] + ' bin ' + str(bin_count)
            if renamed_columns[i+1].find("Unnamed") < 0:
                renamed_columns[i-bin_count+1] += ' bin 1'
        else:
            bin_count = 1
    print(renamed_columns)      
    return pd.DataFrame(input_data.values, columns=pd.Index(renamed_columns))


def filter_numeric_data(data_frame, parameter):
    """Removes NaN and performs Grubbs' test to check for outliers, removing them. By
    default, it uses alpha=0.05 for removal of outliers.
    :arg data_frame: pd.DataFrame to be parsed
    :arg parameter: name of parameter to be checked
    :return result from Grubbs' test, telling about outliers removed"""

    if parameter not in data_frame.columns:
        raise AttributeError(f"Could not find {parameter} in data frame.")

    filter_nan = data_frame[pd.notnull(data_frame[parameter])]     # filtering NaN data
    data_series = pd.Series(filter_nan[parameter])
    data_series.reset_index(drop=True, inplace=True)               # index must be reset to work

    try:
        data = pd.to_numeric(data_series) # conversion necessary to use Grubbs' test

    except ValueError:
        raise ValueError("Grubbs' test cannot be performed due to non-numeric data. Please check your data.")
        return -1
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


# prototype of function for data frame to handle bins

def bin_dataframe_generator(data_set, bin_param, num__bins):
 
    bin_data_set = pd.DataFrame()  # empty declaration to perform concatenation
    for i in range(1, num__bins + 1):
        bin_subset = bins_subset(data_set, bin_param, i).dropna()
        bin_subset = pd.DataFrame(filter_numeric_data(bin_subset, bin_param + ' bin ' + str(i)))
        bin_subset['bin'] = i
        bin_data_set = bin_data_set.append(bin_subset)
    
    bin_data_set.reset_index(inplace=True)
    bin_data_set.fillna(0, inplace=True)
    bin_data_set[bin_param] = bin_data_set[bin_param + ' bin 1']  # preparing new column with results from bin 1
    del bin_data_set[bin_param + ' bin 1']
    
    for binIndex in range(2, num__bins + 1):  # merging all the bins in a single one
        bin_data_set[bin_param] = bin_data_set[bin_param] + bin_data_set[bin_param + ' bin ' + str(binIndex)]
        del bin_data_set[bin_param + ' bin ' + str(binIndex)]

    return bin_data_set


class DataSet:
    def __init__(self, df, events, **kwargs):
        self._data_frame = df
        self._name = ""
        if kwargs is not None:
            for key, value in kwargs.items():
                self._data_frame,  self._param_name = subset_data(self._data_frame, key, value)
                self._name += str(self._param_name) + " "
        try:
            self._data_set = filter_numeric_data(self._data_frame, events)
        except ValueError:
            self._data_set = pd.Series() # returns an empty seriees
            pass
        self._isnormal = True  # data is assumed to be normal.
        self._events = events

    @property
    def data_name(self):
        if self._data_set.empty:
            return ""
        else:
            return str(self._name) + " : " + str(self._data_set.name)

    @data_name.setter
    def data_name(self, name):
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
