import pandas as pd
from scipy.interpolate import interp1d


def custom_sampling(
        data: pd.DataFrame, output_index: pd.Index, interpolation_kind: str = "linear"):
    """ Interpolate data to infer values on custom sampling

    Parameters
    ----------
    data: DataFrame with scalar values
    ouptut_index: Desired time index on which to estimate values
    interpolation_kind: Interpolation method. See interp1d documentation

    Returns
    -------
    output_data: DataFrame with index `output_index` and interpolated data

    Examples
    --------
    > data

                              longitude   latitude  elevation
        time
        2018-01-24 19:27:58 -117.327168  33.126515    -17.228
        2018-01-24 19:27:59 -117.327153  33.126543    -18.199
        2018-01-24 19:28:12 -117.325690  33.126616    -18.440
        2018-01-24 19:28:13 -117.327072  33.126540    -19.161
        2018-01-24 19:28:14 -117.327218  33.126539    -18.472
        2018-01-24 19:28:15 -117.327250  33.126544    -18.429
        2018-01-24 19:28:16 -117.327248  33.126550    -18.678
        2018-01-24 19:28:17 -117.327258  33.126558    -19.163
        2018-01-24 19:28:18 -117.327263  33.126566    -19.362
        2018-01-24 19:28:19 -117.327270  33.126579    -19.731
        2018-01-24 19:28:20 -117.327282  33.126588    -19.876
    > output_index
        DatetimeIndex([   '2018-01-24 19:27:58.500000',
                          '2018-01-24 19:27:58.750000128',
                          '2018-01-24 19:27:59',
                          '2018-01-24 19:27:59',
                          '2018-01-24 19:28:00.249999872',
                          '2018-01-24 19:28:00.500000',
                          '2018-01-24 19:28:00.750000128',
                          '2018-01-24 19:28:01',
                          '2018-01-24 19:28:03',
                          '2018-01-24 19:28:03.500000',
                          '2018-01-24 19:28:03.500000',
                          '2018-01-24 19:28:03.750000128',
                          '2018-01-24 19:28:04',
                          '2018-01-24 19:28:04'],
        dtype='datetime64[ns]',
        freq=None)
    > output_data

                                      longitude   latitude  elevation
        2018-01-24 19:27:58.500000000 -117.327168  33.126515 -17.228000
        2018-01-24 19:27:58.750000128 -117.327164  33.126522 -17.470750
        2018-01-24 19:27:59.000000000 -117.327160  33.126529 -17.713500
        2018-01-24 19:27:59.000000000 -117.327160  33.126529 -17.713500
        2018-01-24 19:28:00.249999872 -117.327069  33.126547 -18.212904
        2018-01-24 19:28:00.500000000 -117.327040  33.126548 -18.217538
        2018-01-24 19:28:00.750000128 -117.327012  33.126550 -18.222173
        2018-01-24 19:28:01.000000000 -117.326984  33.126551 -18.226808
        2018-01-24 19:28:03.000000000 -117.326759  33.126562 -18.263885
        2018-01-24 19:28:03.500000000 -117.326703  33.126565 -18.273154
        2018-01-24 19:28:03.500000000 -117.326703  33.126565 -18.273154
        2018-01-24 19:28:03.750000128 -117.326675  33.126566 -18.277788
        2018-01-24 19:28:04.000000000 -117.326647  33.126568 -18.282423
        2018-01-24 19:28:04.000000000 -117.326647  33.126568 -18.282423

    """
    index_input = data.index

    t_input = (index_input - index_input[0]).total_seconds()
    t_output = (output_index - output_index[0]).total_seconds()

    values = data.values
    f_interp = interp1d(t_input, values.T, kind=interpolation_kind)
    values = f_interp(t_output).T
    output_data = pd.DataFrame(values, columns=data.columns, index=output_index)
    import pdb;
    pdb.set_trace()
    return output_data


def uniform_sampling(data: pd.DataFrame, sampling_rate: float, interpolation_kind: str = "zero"):
    """ Resample a signal to a uniform sampling rate
    Uses a zero order interpolator (aka sample-and-hold) to estimate the value
    of the signal on the exact timestamps that correspond to a uniform sampling
    rate.
    Sampling frequencies whose period cannot be represented as a integer
    nanosecond  are not supported. For example, 3Hz is not supported because its
    period is 333333333.333 nanoseconds. Another example: 4096Hz is not
    supported because its period is 244140.625 nanoseconds.
    Parameters
    ----------
    data: pd.DataFrame
        Input dataframe. All columns must be numeric. It must have a
        datetime-like index.
    sampling_rate: float
        Target sampling rate in Hertz.
    interpolation_kind: str | int | None
        If None, no interpolation is performed, ie. timestamps of the input data
        are ignored.
        Else, it specifies the kind of interpolation as a string or an int
        (see documentation of scipy.interpolate.interp1d)
    Returns
    -------
    pd.DataFrame
        A new dataframe with the same columns as the input but the index will
        change to accomodate a uniform sampling.
    Examples
    --------
    >>> import pandas.util.testing as tm
    >>> data =  tm.makeTimeDataFrame(freq='S').head()  # Create a 1Hz dataframe
    >>> data
                         A         B         C         D
    2000-01-01 00:00:00 -0.739572 -0.191162  1.023474  1.663371
    2000-01-01 00:00:01  1.183841 -0.631689  0.412752  1.488323
    2000-01-01 00:00:02  1.683318  2.237185  0.726931 -0.914066
    2000-01-01 00:00:03  0.948706 -1.087019 -0.685658  0.710647
    2000-01-01 00:00:04  1.177724  0.510797 -0.707243 -0.790019
    >>> uniform_sampling(data, 4)  # Resample to 4Hz
                                    A         B         C         D
    2000-01-01 00:00:00.000 -0.739572 -0.191162  1.023474  1.663371
    2000-01-01 00:00:00.250 -0.739572 -0.191162  1.023474  1.663371
    2000-01-01 00:00:00.500 -0.739572 -0.191162  1.023474  1.663371
    2000-01-01 00:00:00.750 -0.739572 -0.191162  1.023474  1.663371
    2000-01-01 00:00:01.000  1.183841 -0.631689  0.412752  1.488323
    2000-01-01 00:00:01.250  1.183841 -0.631689  0.412752  1.488323
    2000-01-01 00:00:01.500  1.183841 -0.631689  0.412752  1.488323
    2000-01-01 00:00:01.750  1.183841 -0.631689  0.412752  1.488323
    2000-01-01 00:00:02.000  1.683318  2.237185  0.726931 -0.914066
    2000-01-01 00:00:02.250  1.683318  2.237185  0.726931 -0.914066
    2000-01-01 00:00:02.500  1.683318  2.237185  0.726931 -0.914066
    2000-01-01 00:00:02.750  1.683318  2.237185  0.726931 -0.914066
    2000-01-01 00:00:03.000  0.948706 -1.087019 -0.685658  0.710647
    2000-01-01 00:00:03.250  0.948706 -1.087019 -0.685658  0.710647
    2000-01-01 00:00:03.500  0.948706 -1.087019 -0.685658  0.710647
    2000-01-01 00:00:03.750  0.948706 -1.087019 -0.685658  0.710647
    2000-01-01 00:00:04.000  1.177724  0.510797 -0.707243 -0.790019
    """

    if data.empty:
        raise ValueError("Cannot resample an empty dataframe")

    period_ns, fract = divmod(1e9, sampling_rate)
    if fract != 0:
        raise ValueError("Refusing to interpolate under nanosecond scale")

    # the new, uniformly sampled index
    index_new = pd.date_range(data.index[0], data.index[-1], freq=f"{period_ns}N")
    data_new = pd.DataFrame(columns=data.columns, index=index_new)

    t_old = (data.index - data.index[0]).total_seconds()
    t_new = (data_new.index - data_new.index[0]).total_seconds()

    values = data.values
    if interpolation_kind is not None:
        f_interp = interp1d(t_old, values.T, kind=interpolation_kind)
        values = f_interp(t_new).T
    else:
        min_length = min(len(index_new), len(values))
        index_new = index_new[:min_length]
        values = values[:min_length, :]
    output_data = pd.DataFrame(values, columns=data.columns, index=index_new)
    return output_data
