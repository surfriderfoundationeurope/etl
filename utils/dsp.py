import pandas as pd
from scipy.interpolate import interp1d


def uniform_sampling(data, sampling_rate, interpolation_kind='zero'):
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
        raise ValueError('Cannot resample an empty dataframe')

    period_ns, fract = divmod(1e9, sampling_rate)
    if fract != 0:
        raise ValueError('Refusing to interpolate under nanosecond scale')

    # the new, uniformly sampled index
    index_new = pd.date_range(data.index[0], data.index[-1], freq=f'{period_ns}N')
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
