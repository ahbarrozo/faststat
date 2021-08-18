from numpy import mean, std, loadtxt, where
import os
import urllib
from scipy import stats
from statsmodels.graphics.factorplots import interaction_plot
import statistics
import matplotlib.pyplot as plt
import pandas as pd
from dataparse import bin_dataframe_generator, bins_subset, DataSet


def compute_mean_std(filename=None):
    data = loadtxt(os.path.join('uploads', filename))
    return """
Data from file <tt>%s</tt>:
<p>
<table border=1>
<tr><td> mean    </td><td> %.3g </td></tr>
<tr><td> st.dev. </td><td> %.3g </td></tr>
""" % (filename, mean(data), std(data))


def check_outliers(filtered, unfiltered):
    comparison = unfiltered.data_set == filtered.data_set

    if False in comparison:
        return where(comparison is False)


def display_stat_info(dataset):
    """Displays basic statistic information for a data series: means, standard deviation,
    s.e.m., medians and quantiles.
    :arg dataset: DataSet type
    :return str"""

    stat_info = "<h3>Statistical Info</h3> <br/>"
    stat_info += f"Dataset: '{dataset.data_name}'<br />"
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
    """Checks for normality of data. If the data are normally distributed, performs
    Student's t-test. Else, performs Student's t-test and Wilcoxon rank-sum to assess
    null hypothesis for two data sets.
    :arg dataset_a: DataSet type
    :arg dataset_b: DataSet type
    :return str"""

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
    """Performs Shapiro-Wilk for each data set as input. and Levene tests to assess equality
    variance between them.
    :arg dataset_a: DataSet type
    :arg dataset_b: DataSet type
    :return: str"""

    stat_info = "<h3>Normality Tests</h3> <br/>"
    w_shapiro_wilk_a, p_shapiro_wilk_a = stats.shapiro(dataset_a.data_set)
    stat_info += "Shapiro-Wilk test results for dataset {0}: <br/> W = {1}, P = {2}".format(dataset_a.data_name,
                                                                                            w_shapiro_wilk_a,
                                                                                            p_shapiro_wilk_a) + "<br/>"

    w_shapiro_wilk_b, p_shapiro_wilk_b = stats.shapiro(dataset_b.data_set)
    stat_info += "Shapiro-Wilk test results for dataset {0}: <br/> W = {1}, P = {2}".format(dataset_b.data_name,
                                                                                            w_shapiro_wilk_b,
                                                                                            p_shapiro_wilk_b) + "<br/>"

    w_levene, p_levene = stats.levene(dataset_a.data_set, dataset_b.data_set)
    stat_info += f"Levene test results: <br/> W = {w_levene}, P = {p_levene}<br/>"

    if p_shapiro_wilk_a < 0.05:
        stat_info += f"Data set '{dataset_a.data_name}' failed Shapiro-Wilk test.<br/>"
        dataset_a._isnormal = False

    if p_shapiro_wilk_b < 0.05:
        stat_info += f"Data set '{dataset_b.data_name}' failed Shapiro-Wilk test.<br/>"
        dataset_b._isnormal = False

    if p_levene < 0.05:
        stat_info += "Data sets failed Levene normality test.\n<br/>"
        dataset_a._isnormal = False
        dataset_b._isnormal = False

    return stat_info


def one_way_anova(stat_data, dataset, bin_var):
    """Performs regular one-way ANOVA for a given feature measured over variables with multiple bins.
    :arg stat_data: pandas.DataFrame
    :arg dataset: DataSet type
    :arg bin_var: str representing name of bin variable
    :return pandas.DataFrame with ANOVA information"""

    # counts number of bins for given bin variable
    bin_num = dataset.data_frame.columns.str.contains(bin_var + ' bin ').sum()
    subdataset = DataSet(dataset.data_frame,
                         dataset.data_frame.columns[dataset.data_frame.columns.get_loc(bin_var +
                                                                                           ' bin 1') + bin_num])
    anova_dataset = bin_dataframe_generator(bins_subset(subdataset.data_frame, bin_var), bin_var, 3)
    bin_list = anova_dataset['bin'].unique()
    bin_size = [anova_dataset[anova_dataset['bin'] == b][bin_var].shape[0] for b in bin_list]
    bin_avg_size = statistics.mean(bin_size)
    bin_size.insert(0, 0)
    bin_mean = [anova_dataset[anova_dataset['bin'] == b][bin_var].mean() for b in bin_list]
    bin_mean.insert(0, 0)

    # Degrees of freedom - df
    n = len(anova_dataset[bin_var])
    grand_mean = anova_dataset[bin_var].mean()

    df_err = sum(bin_size) - bin_num
    ms_err = sum([sum((anova_dataset[anova_dataset['bin'] == b][bin_var] -
                       bin_mean[b])**2)/(bin_size[b]-1) for b in bin_list]) / bin_num
    ss_err = ms_err * df_err

    ss_means = sum([(bin_mean[b] - grand_mean) ** 2 for b in bin_list])
    ms_between = ss_means / (bin_num - 1) * bin_avg_size

    df_groups = bin_num - 1
    ss_groups = ms_between * n / bin_num
    f_one_way_anova = ms_between / ms_err

    anova_list = [anova_dataset[anova_dataset['bin'] == b][bin_var] for b in bin_list]
    f_one_way_anova, p_one_way_anova = stats.f_oneway(*anova_list)

    results = {'sum_sq': [ss_groups, ss_err, ss_groups + ss_err],
               'df': [df_groups, df_err, ''],
               'F': [f_one_way_anova, '', ''],
               'P': [p_one_way_anova, '', '']}
    columns = ['sum_sq', 'df', 'F', 'P']

    anova_table = pd.DataFrame(results, columns=columns, index=['group', 'error', 'total'])

    return anova_table


# WARNING: THIS HASN'T BEEN IMPLEMENTED YET!!!
# prototype for one-way ANOVA with repeated measures to be finished

def one_way_anova_rep_msr(stat_data, dataset, control_var, bin_var):
    """Performs one-way ANOVA with repeated measures for a given feature measured over bins, controlling over bins.
    :arg stat_data: pandas.DataFrame
    :arg dataset: DataSet type
    :arg control_var: str representing the name of the control variable
    :arg bin_var: str representing the name of the bin variable
    :return pandas.DataFrame with ANOVA information"""

    # counts number of bins for given bin variable
    bin_num = dataset.data_frame.columns.str.contains(bin_var + ' bin ').sum()
    subdataset = DataSet(dataset.data_frame,
                         dataset.data_frame.columns[dataset.data_frame.columns.get_loc(bin_var +
                                                                                           ' bin 1') + bin_num])
    anova_dataset = bin_dataframe_generator(bins_subset(subdataset.data_frame, bin_var), bin_var, 3)
    id_list = anova_dataset.index
    id_size = len(id_list)
    bin_list = anova_dataset['bin'].unique()
    bin_size = [anova_dataset[anova_dataset['bin'] == b][bin_var].shape[0] for b in bin_list]
    bin_avg_size = statistics.mean(bin_size)
    bin_size.insert(0, 0)
    bin_mean = [anova_dataset[anova_dataset['bin'] == b][bin_var].mean() for b in bin_list]
    bin_mean.insert(0, 0)

    # Degrees of freedom - df
    n = len(anova_dataset[bin_var])
    grand_mean = anova_dataset[bin_var].mean()

    df_tot = n-1
    ms_tot = sum((anova_dataset[bin_var] - grand_mean)**2) / n
    ss_tot = ms_tot * df_tot

    df_within = sum(bin_size) - bin_num
    ms_within = sum([sum((anova_dataset[anova_dataset['id'] == i][bin_var] -
                          bin_mean[i])**2)/(id_size[i]-1) for i in id_list]) / id_size
    ss_within = sum([sum((anova_dataset[anova_dataset['id'] == i][bin_var] -
                          bin_mean[i])**2)*(id_size[i]-1)/id_size[i] for i in id_list])

    df_err = sum(bin_size) - bin_num
    ms_err = sum([sum((anova_dataset[anova_dataset['bin'] == b][bin_var] -
                       bin_mean[b])**2)/(bin_size[b]-1) for b in bin_list]) / bin_num
    ss_err = ms_err * df_err

    ss_means = sum([(bin_mean[b] - grand_mean) ** 2 for b in bin_list])
    ms_between = ss_means / (bin_num - 1) * bin_avg_size

    df_groups = bin_num - 1
    ss_groups = ms_between * n / bin_num
    f_one_way_anova = ms_between / ms_err

    anova_list = [anova_dataset[anova_dataset['bin'] == b][bin_var] for b in bin_list]
    f_one_way_anova, p_one_way_anova = stats.f_oneway(*anova_list)

    results = {'sum_sq': [ss_groups, ss_err, ss_groups + ss_err],
               'df': [df_groups, df_err, ''],
               'F': [f_one_way_anova, '', ''],
               'P': [p_one_way_anova, '', '']}
    columns = ['sum_sq', 'df', 'F', 'P']

    anova_table = pd.DataFrame(results, columns=columns, index=['group', 'error', 'total'])

    return anova_table


def two_way_anova(stat_data, dataset_a, dataset_b, parameter, parm_val_a, parm_val_b, bin_var):
    """Performs regular two-way ANOVA for a given feature measured over bins.
    :arg stat_data: pandas.DataFrame
    :arg dataset_a: DataSet type
    :arg dataset_b: DataSet type
    :arg parameter: str representing the name of the variable for the two-way measurement
    :arg parm_val_a: str for the value for the chosen parameter for dataset_a
    :arg parm_val_b: str for the value for the chosen parameter for dataset_b
    :arg bin_var: str representing name of bin variable
    :return pandas.DataFrame with ANOVA information"""

    bin_num = dataset_a.data_frame.columns.str.contains(
        bin_var + ' bin ').sum()  # counts number of bins for given bin variable

    subdataset_a = DataSet(dataset_a.data_frame,
                           dataset_a.data_frame.columns[stat_data.columns.get_loc(bin_var + ' bin 1') + bin_num])
    subdataset_b = DataSet(dataset_b.data_frame,
                           dataset_b.data_frame.columns[stat_data.columns.get_loc(bin_var + ' bin 1') + bin_num])
    bin_dataset_a = bin_dataframe_generator(bins_subset(subdataset_a.data_frame, bin_var), bin_var, 3)
    bin_dataset_b = bin_dataframe_generator(bins_subset(subdataset_b.data_frame, bin_var), bin_var, 3)
    bin_dataset_a[parameter] = parm_val_a
    bin_dataset_b[parameter] = parm_val_b
    anovaDataSet = bin_dataset_a.append(bin_dataset_b)

    fig = interaction_plot(anovaDataSet['bin'],
                           anovaDataSet[parameter],
                           anovaDataSet[bin_var],
                           colors=['red', 'blue'],
                           markers=['D', '^'], ms=10)

    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)

    import base64
    figdata_png = base64.b64encode(figfile.getvalue())

    # Degrees of freedom - df

    n = len(anovaDataSet[bin_var])
    df_a = len(anovaDataSet['bin'].unique()) - 1
    df_b = len(anovaDataSet[parameter].unique()) - 1
    dfaxb = df_a * df_b
    df_within = n - (len(anovaDataSet['bin'].unique()) * len(anovaDataSet[parameter].unique()))

    # Sum of squares - ssq (factors A, B and total)

    grand_mean = anovaDataSet[bin_var].mean()
    ssq_a = sum([(anovaDataSet[anovaDataSet[parameter] == l][bin_var].mean() - grand_mean) ** 2 for l in
                anovaDataSet[parameter]])
    ssq_b = sum(
        [(anovaDataSet[anovaDataSet['bin'] == l][bin_var].mean() - grand_mean) ** 2 for l in anovaDataSet['bin']])
    ssq_total = sum((anovaDataSet[bin_var] - grand_mean) ** 2)

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

    results = {'sum_sq': [ssq_a, ssq_b, ssqaxb, ssq_within],
               'df': [df_a, df_b, dfaxb, df_within],
               'F': [f_a, f_b, faxb, ''],
               'PR(>F)': [p_a, p_b, paxb, '']}
    columns = ['sum_sq', 'df', 'F', 'PR(>F)']

    return pd.DataFrame(results, columns=columns,
                        index=[parameter, 'bin',
                               parameter + ':bin', 'Residual']), urllib.parse.quote(figdata_png)


def two_way_anova_repmsr(stat_data, dataset_a, dataset_b, parameter, parm_val_a, parm_val_b, bin_var):
    from statsmodels.formula.api import ols
    from statsmodels.stats.anova import anova_lm
    from statsmodels.graphics.factorplots import interaction_plot
    import matplotlib.pyplot as plt
    import pandas as pd
    from dataparse import bin_dataframe_generator, bins_subset, DataSet

    bin_num = dataset_a.data_frame.columns.str.contains(
        bin_var + ' bin ').sum()  # counts number of bins for given bin variable

    subdataset_a = DataSet(dataset_a.data_frame,
                           dataset_a.data_frame.columns[stat_data.columns.get_loc(bin_var + ' bin 1') + bin_num])
    subdataset_b = DataSet(dataset_b.data_frame,
                           dataset_b.data_frame.columns[stat_data.columns.get_loc(bin_var + ' bin 1') + bin_num])
    bin_data_set_a = bin_dataframe_generator(bins_subset(subdataset_a.data_frame, bin_var), bin_var, 3)
    bin_data_set_b = bin_dataframe_generator(bins_subset(subdataset_b.data_frame, bin_var), bin_var, 3)
    bin_data_set_a[parameter] = parm_val_a
    bin_data_set_b[parameter] = parm_val_b
    anova_data_set = bin_data_set_a.append(bin_data_set_b)

    fig = interaction_plot(anova_data_set['bin'],
                           anova_data_set[parameter],
                           anova_data_set[bin_var],
                           colors=['red', 'blue'],
                           markers=['D', '^'], ms=10)

    from io import BytesIO
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)

    import base64
    figdata_png = base64.b64encode(figfile.getvalue())

    # Degrees of freedom - df

    N = len(anova_data_set[bin_var])
    dfA = len(anova_data_set['bin'].unique()) - 1
    dfB = len(anova_data_set[parameter].unique()) - 1
    dfAxB = dfA * dfB
    dfWithin = N - (len(anova_data_set['bin'].unique()) * len(anova_data_set[parameter].unique()))

    # Sum of squares - ssq (factors A, B and total)

    grand_mean = anova_data_set[bin_var].mean()
    ssqA = sum([(anova_data_set[anova_data_set[parameter] == l][bin_var].mean() - grand_mean) ** 2 for l in
                anova_data_set[parameter]])
    ssqB = sum(
        [(anova_data_set[anova_data_set['bin'] == l][bin_var].mean() - grand_mean) ** 2 for l in anova_data_set['bin']])
    ssqTotal = sum((anova_data_set[bin_var] - grand_mean) ** 2)

    # Sum of Squares Within (error/residual)

    bin_meansA = [bin_data_set_a[bin_data_set_a['bin'] == d][bin_var].mean() for d in bin_data_set_a['bin']]
    bin_meansB = [bin_data_set_b[bin_data_set_b['bin'] == d][bin_var].mean() for d in bin_data_set_b['bin']]
    ssqWithin = sum((bin_data_set_b[bin_var] - bin_meansB) ** 2) + sum((bin_data_set_a[bin_var] - bin_meansA) ** 2)

    # Sum of Squares Interaction

    ssqAxB = ssqTotal - ssqA - ssqB - ssqWithin

    # Mean Squares

    msA = ssqA / dfA
    msB = ssqB / dfB
    msAxB = ssqAxB / dfAxB
    msWithin = ssqWithin / dfWithin

    # F-ratio

    fA = msA / msWithin
    fB = msB / msWithin
    fAxB = msAxB / msWithin

    # Obtaining p-values

    pA = stats.f.sf(fA, dfA, dfWithin)
    pB = stats.f.sf(fB, dfB, dfWithin)
    pAxB = stats.f.sf(fAxB, dfAxB, dfWithin)

    # table with results from ANOVA

    results = {'sum_sq': [ssqA, ssqB, ssqAxB, ssqWithin],
               'df': [dfA, dfB, dfAxB, dfWithin],
               'F': [fA, fB, fAxB, 'NaN'],
               'PR(>F)': [pA, pB, pAxB, 'NaN']}
    columns = ['sum_sq', 'df', 'F', 'PR(>F)']

    return pd.DataFrame(results, columns=columns,
                        index=[parameter, 'bin',
                               parameter + ':bin', 'Residual']), urllib.parse.quote(figdata_png), anova_data_set
