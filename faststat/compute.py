from numpy import mean, std, loadtxt, where
from io import BytesIO
import base64
import os
import urllib
from scipy import stats
from statsmodels.graphics.factorplots import interaction_plot
import statistics
import matplotlib.pyplot as plt
import pandas as pd

from faststat.dataparse import bin_dataframe_generator, bins_subset, DataSet


def check_outliers(filtered, unfiltered):
    comparison = unfiltered.data_set == filtered.data_set

    if False in comparison:
        return where(comparison is False)


def display_stat_info(dataset):
    """Displays basic statistic information for a data series: means, standard deviation,
    s.e.m., medians and quantiles.

    Arguments:
    ---
    dataset: DataSet type

    Returns:
    ---
    str in HTML format with results."""

    if dataset.data_set.empty:
        return None

    else:

        stat_info = "<h3>Statistical Info</h3> <br/>"
        stat_info += f"Dataset: '{dataset.name}'<br />"
        stat_info += f'No. of samples: {dataset.sampling_size()}<br />'

        if dataset.isnormal():
            stat_info += f'Mean: {dataset.mean_value()}<br />'
            stat_info += f'Standard deviation: {dataset.std_value()}<br />'
            stat_info += f'Standard error of the mean: {dataset.sem_value()}\n<br />'
        else:
            stat_info += f'Median: {dataset.median_value()}<br />'
            stat_info += f'Quantile 25%: {dataset.quantile25_value()}<br />'
            stat_info += f'Quantile 75%: {dataset.quantile75_value()}\n<br />'

    return stat_info


def null_hypothesis_tests(dataset_a, dataset_b):
    """Checks for normality of data. If the data are normally 
    distributed, performs Student's t-test. Else, performs 
    Student's t-test and Wilcoxon rank-sum to assess null 
    hypothesis for two data sets.

    Arguments:
    ---
    dataset_a, b: two DataSet type objects

    Returns:
    ---
    str in HTML with results of normality tests"""

    stat_info = "<h3>Null Hypothesis Tests</h3> <br/>"
    if dataset_a.isnormal() and dataset_b.isnormal():
        t_t_test, p_t_test = stats.ttest_ind(dataset_a.data_set, dataset_b.data_set)
        stat_info += f"Student's t-test results: t = {t_t_test}, P = {p_t_test}\n<br/>"

    else:
        t_t_test, p_t_test = stats.ttest_ind(dataset_a.data_set,
                                             dataset_b.data_set)  # performs t-test even if not normal
        u_rank_sums, p_rank_sums = stats.ranksums(dataset_a.data_set, dataset_b.data_set)
        stat_info += f"Student's t-test results: t = {t_t_test}, P = {p_t_test}<br/>"
        stat_info += f"Wilcoxon rank-sum results: u = {u_rank_sums}, P = {p_rank_sums}<br/>"
    return stat_info


def normality_tests(dataset_a, dataset_b):
    """Performs Shapiro-Wilk for each data set as input. and Levene 
    tests to assess equality variance between them.

    Arguments:
    ---
    dataset_a, b: two DataSet type objects
    
    Returns:
    ---
    str in HTML with results of normality tests"""

    stat_info = "<h3>Normality Tests</h3> <br/>"
    w_shapiro_wilk_a, p_shapiro_wilk_a = stats.shapiro(dataset_a.data_set)
    stat_info += "Shapiro-Wilk test results for dataset {0}: <br/> W = {1}, P = {2}".format(dataset_a.name,
                                                                                            w_shapiro_wilk_a,
                                                                                            p_shapiro_wilk_a) + "<br/>"

    w_shapiro_wilk_b, p_shapiro_wilk_b = stats.shapiro(dataset_b.data_set)
    stat_info += "Shapiro-Wilk test results for dataset {0}: <br/> W = {1}, P = {2}".format(dataset_b.name,
                                                                                            w_shapiro_wilk_b,
                                                                                            p_shapiro_wilk_b) + "<br/>"

    w_levene, p_levene = stats.levene(dataset_a.data_set, dataset_b.data_set)
    stat_info += f"Levene test results: <br/> W = {w_levene}, P = {p_levene}<br/>"

    if p_shapiro_wilk_a < 0.05:
        stat_info += f"Data set '{dataset_a.name}' failed Shapiro-Wilk test.<br/>"
        dataset_a._isnormal = False

    if p_shapiro_wilk_b < 0.05:
        stat_info += f"Data set '{dataset_b.name}' failed Shapiro-Wilk test.<br/>"
        dataset_b._isnormal = False

    if p_levene < 0.05:
        stat_info += "Data sets failed Levene normality test.\n<br/>"
        dataset_a._isnormal = False
        dataset_b._isnormal = False

    return stat_info


def one_way_anova(data_frame, bin_var):
    """Performs regular one-way ANOVA for a given feature measured over variables with multiple bins.

    Arguments
    ---
    data_frame: pandas.DataFrame
        Input data, in the case of FastStat, it is called from a previously
        filtered DataSet object.

    bin_var: str 
        Name of bin variable

    Returns
    ---
    pandas.DataFrame:
        A table with ANOVA information"""

    # counts number of bins for given bin variable
    bin_num = data_frame.columns.str.contains(bin_var + ' bin ').sum()
    subdataset = DataSet(data_frame,
                         data_frame.columns[data_frame.columns.get_loc(bin_var + ' bin 1') + bin_num])
    anova_dataset = bin_dataframe_generator(bins_subset(data_frame, bin_var),
                                            bin_var)
    bin_list = anova_dataset['bin'].unique()
    bin_size = [anova_dataset[anova_dataset['bin'] == b][bin_var].shape[0] for b in bin_list]
    bin_avg_size = statistics.mean(bin_size)
    bin_size.insert(0, 0)
    bin_mean = [anova_dataset[anova_dataset['bin'] == b][bin_var].mean() for b in bin_list]
    bin_mean.insert(0, 0)

    # Number of samples and mean of all samples
    n = len(anova_dataset[bin_var])
    grand_mean = anova_dataset[bin_var].mean()

    # Degrees of freedom - df
    df_within = sum(bin_size) - bin_num
    df_between = bin_num - 1

    # Calculating properties between groups
    ms_within = sum([sum((anova_dataset[anova_dataset['bin'] == b][bin_var] -
                       bin_mean[b])**2)/(bin_size[b]-1) for b in bin_list]) / bin_num
    ss_within = ms_within * df_within

    ss_tot = sum([sum((anova_dataset[anova_dataset['bin'] == b][bin_var]**2))
                  for b in bin_list]) - n * grand_mean**2
    ss_between = ss_tot - ss_within


    anova_list = [anova_dataset[anova_dataset['bin'] == b][bin_var] for b in bin_list]
    f_one_way_anova, p_one_way_anova = stats.f_oneway(*anova_list)

    results = {'SS': [ss_between, ss_within, ss_tot],
               'DF': [df_between, df_within, ''],
               'F': [f_one_way_anova, '', ''],
               'P': [p_one_way_anova, '', '']}
    columns = ['SS', 'DF', 'F', 'P']

    anova_table = pd.DataFrame(results, columns=columns, index=['Between',
                                                                'Within', 'Total'])

    return anova_table


def two_way_anova(dataframe_a, dataframe_b, parameter, parm_val_a, parm_val_b, bin_var):
    """Performs regular two-way ANOVA for a given feature measured over bins.

    Arguments
    ---
    dataframe_a,b: pandas DataFrame
        Spreadsheet input, in the FastStat case coming from a filtered data
        frame from DataSet object.

    parameter: str 
        Name of the variable for the two-way measurement

    parm_val_a, b: str 
        Value for the chosen parameter
    :arg bin_var: str representing name of bin variable

    Returns
    ---
    pandas.DataFrame with ANOVA information"""

    # counts number of bins for given bin variable
    bin_num = dataframe_a.columns.str.contains(bin_var + ' bin ').sum() 

    subdataset_a = DataSet(dataframe_a,
                           dataframe_a.columns[dataframe_a.columns.get_loc(bin_var + ' bin 1') + bin_num])
    subdataset_b = DataSet(dataframe_b,
                           dataframe_b.columns[dataframe_b.columns.get_loc(bin_var + ' bin 1') + bin_num])
    bin_dataset_a = bin_dataframe_generator(bins_subset(subdataset_a.data_frame, bin_var),
                            bin_var)

    bin_dataset_b = bin_dataframe_generator(bins_subset(subdataset_b.data_frame, bin_var),
                            bin_var)
    bin_dataset_a[parameter] = parm_val_a
    bin_dataset_b[parameter] = parm_val_b
    anova_dataset = bin_dataset_a.append(bin_dataset_b)

    fig = interaction_plot(anova_dataset['bin'],
                           anova_dataset[parameter],
                           anova_dataset[bin_var],
                           colors=['red', 'blue'],
                           markers=['D', '^'], ms=10)

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())

    # Degrees of freedom - df

    n = len(anova_dataset[bin_var])
    df_a = len(anova_dataset['bin'].unique()) - 1
    df_b = len(anova_dataset[parameter].unique()) - 1
    dfaxb = df_a * df_b
    df_within = n - (len(anova_dataset['bin'].unique()) * len(anova_dataset[parameter].unique()))

    # Sum of squares - ssq (factors A, B and total)

    grand_mean = anova_dataset[bin_var].mean()
    ssq_a = sum([(anova_dataset[anova_dataset[parameter] == l][bin_var].mean() - grand_mean) ** 2 for l in
                anova_dataset[parameter]])
    ssq_b = sum(
        [(anova_dataset[anova_dataset['bin'] == l][bin_var].mean() -
          grand_mean) ** 2 for l in anova_dataset['bin']])
    ssq_total = sum((anova_dataset[bin_var] - grand_mean) ** 2)

    # Sum of Squares Within (error/residual)

    bin_means_a = [bin_dataset_a[bin_dataset_a['bin'] == d][bin_var].mean() for d in bin_dataset_a['bin']]
    bin_means_b = [bin_dataset_b[bin_dataset_b['bin'] == d][bin_var].mean() for d in bin_dataset_b['bin']]
    ssq_within = sum((bin_dataset_b[bin_var] - bin_means_b) ** 2) + sum((bin_dataset_a[bin_var] - bin_means_a) ** 2)

    # Sum of Squares Interaction

    ssqaxb = ssq_total - ssq_a - ssq_b - ssq_within

    # Mean Squares

    ms_a = ssq_a / df_a
    ms_b = ssq_b / df_b
    ms_ax_b = ssqaxb / dfaxb
    ms_within = ssq_within / df_within

    # F-ratio

    f_a = ms_a / ms_within
    f_b = ms_b / ms_within
    faxb = ms_ax_b / ms_within

    # Obtaining p-values

    p_a = stats.f.sf(f_a, df_a, df_within)
    p_b = stats.f.sf(f_b, df_b, df_within)
    paxb = stats.f.sf(faxb, dfaxb, df_within)

    # table with results from ANOVA

    results = {'SS': [ssq_a, ssq_b, ssqaxb, ssq_within],
               'DF': [df_a, df_b, dfaxb, df_within],
               'F': [f_a, f_b, faxb, ''],
               'PR(>F)': [p_a, p_b, paxb, '']}
    columns = ['SS', 'DF', 'F', 'PR(>F)']

    return pd.DataFrame(results, columns=columns,
                        index=[parameter, 'bin',
                               parameter + ':bin', 'Residual']), urllib.parse.quote(figdata_png)

