import pandas as pd
from scipy import stats
from outliers import smirnov_grubbs as grubbs

# prototype of function for reading and preparing input file

def readData(inputFile):

    inputData = pd.read_excel(inputFile) # read the whole excel sheet. Now needs to handle columns unnamed 

    renamedColumns = list(inputData.columns)
    binCount = 1

    for i in range(len(renamedColumns)):
        """rename 'Unnamed' columns that are formed from merged cells. These will form bins for analysis"""
        if renamedColumns[i].find("Unnamed") >= 0:
            binCount += 1
            renamedColumns[i] = renamedColumns[i-binCount+1] + ' bin ' + str(binCount)
            if renamedColumns[i+1].find("Unnamed") < 0:
                renamedColumns[i-binCount+1] += ' bin 1'
        else:
            binCount = 1
          
    return pd.DataFrame(inputData.values, columns=pd.Index(renamedColumns))

# prototype for filtering function: removing NaN's and outliers from Grubbs' test.

def filter_numeric_data(statData, parameter):
 
    if parameter not in statData.columns:
        print("ERROR: Could not find parameter named {}.".format(parameter))
        return 1

    filterNaNData = statData[pd.notnull(statData[parameter])]     # filtering NaN data

    try:
        data = pd.to_numeric(pd.Series(filterNaNData[parameter])) # conversion necessary to use Grubbs' test
    except ValueError:
        print("ERROR: Grubbs' test cannot be performed due to non-numeric data. Please check your data.")
        return 1
    return grubbs.test(data, alpha=0.05) # Grubbs' test
    

# prototype for extracting subgroups

def subset_data(statData, parameter, subsetValue):
    return statData[statData[parameter] == subsetValue], subsetValue # extract subset of data where 'parameter' = 'subsetValue'


def bins_subset(statData, parameter, binNum = None):
    if not binNum:
        return statData.filter(like=parameter + ' bin')
    else:
        return statData.filter(like=parameter + ' bin ' + str(binNum))


# prototype of function for data frame to handle bins

def bin_dataframe_generator(dataSet, binParameter, numBins):
 
    binDataSet = pd.DataFrame() # empty declaration to perform concatenation
    for i in range(1,numBins+1):
        binSubset = bins_subset(dataSet, binParameter, i).dropna()
        binSubset = pd.DataFrame(filter_numeric_data(binSubset, binParameter + ' bin ' + str(i)))
        binSubset['bin'] = i
        binDataSet = binDataSet.append(binSubset)
    
    binDataSet.reset_index(inplace=True)
    binDataSet.fillna(0, inplace=True)
    binDataSet[binParameter] = binDataSet[binParameter + ' bin 1'] # preparing a new column with results from bin 1
    del binDataSet[binParameter + ' bin 1']
    
    for binIndex in range(2,numBins+1): # merging all the bins in a single one
        binDataSet[binParameter] = binDataSet[binParameter] + binDataSet[binParameter + ' bin ' + str(binIndex)]
        del binDataSet[binParameter + ' bin ' + str(binIndex)]

    return binDataSet


# prototype for normality test. Will need to implement a normality attribute
class DataSet:
    def __init__(self, statData, events, **kwargs):
        self._data_frame = statData
        self._name = ""
        if kwargs is not None:
            for key, value in kwargs.items():
                self._data_frame,  self._param_name = subset_data(self._data_frame, key, value)
                self._name += str(self._param_name) + " "
        try:
                self._data_set = filter_numeric_data(self._data_frame, events)
        except ValueError:
            pass
        self._isnormal = True  # setting as True temporarily
        self._events = events
        
    def data_name(self):
        return str(self._name) + " : " + str(self._data_set.name)        

    def data_frame(self):
        return self._data_frame

    def data_set(self):
        return self._data_set

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
