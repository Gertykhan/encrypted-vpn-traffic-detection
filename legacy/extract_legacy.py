import pandas as pd
import numpy as np
import glob
import os

filenames = glob.glob('flows/traffic_data_???.csv')

df_feature = pd.DataFrame(columns=[
    'src_port',           # Номер порта клиента
    'dst_port',           # Номер порта сервера
    'mean_src',           # Средний размер пакетов, отправленных клиентом
    'mean_dst',           # Средний размер пакетов, отправленных сервером
    'qty_src',            # Число пакетов от клиента
    'pld_src',            # Общая нагрузка от клиента (сумма всех size)
    'var_data',           # Стд. отклонение размера пакетов по потоку
    'var_src',            # Стд. отклонение размера пакетов от клиента
    'frst_src',           # Размер первого пакета клиента
    'scd_src',            # Размер второго пакета клиента
    'frst_dst',           # Размер первого пакета сервера
    'scd_dst',            # Размер второго пакета сервера
    'max_src',            # Максимальный размер пакета клиента
    'min_src',            # Минимальный размер пакета клиента
    'max_dst',            # Максимальный размер пакета сервера
    'ttl_src',            # TTL первого пакета от клиента
    'duration',           # Длительность потока
    'flowPktsPerSecond',  # Пакеты/сек
    'flowBytesPerSecond', # Байт/сек
    'mean_flowiat',       # Среднее время между любыми двумя пакетами
    'std_flowiat',        # Стд. отклонение iat
    'min_flowiat',        # Мин. iat
    'max_flowiat',        # Макс. iat
    'packet_size_mean',   # Средний размер пакета
    'packet_size_std',    # Стд. отклонение размера пакета
    'total_fiat',         # Сумма IAT в прямом направлении (src → dst)
    'total_biat',         # Сумма IAT в обратном направлении (dst → src)
    'min_fiat',           # Мин. IAT от клиента
    'max_fiat',           # Макс. IAT от клиента
    'mean_fiat',          # Средняя IAT от клиента
    'min_biat',           # Мин. IAT от сервера
    'max_biat',           # Макс. IAT от сервера
    'mean_biat',          # Средняя IAT от сервера
    'min_active',         # Мин. активная фаза (бурст трафика)
    'mean_active',        # Средняя активная фаза
    'max_active',         # Макс. активная фаза
    'std_active',         # Стд. отклонение активных фаз
    'min_idle',           # Мин. время простоя
    'mean_idle',          # Среднее время простоя
    'max_idle',           # Макс. время простоя
    'std_idle'            # Стд. отклонение простоя
])

for i, value in enumerate(filenames):
    df = pd.read_csv(value)
    df.columns = [c.strip() for c in df.columns]

    if df.shape[0] < 2 or not {'Source', 'Destination', 'Source Port', 'Destination Port', 'Time', 'Time to Live'}.issubset(df.columns):
        continue

    ip_src = df['Source'].iloc[0]
    ip_dst = df['Destination'].iloc[0]

    if 'TCP Segment Len' in df.columns and 'TCP Header' in df.columns:
        df['size'] = df['TCP Segment Len'].fillna(0) + df['TCP Header'].fillna(0)
    elif 'Length' in df.columns:
        df['size'] = df['Length']
    else:
        df['size'] = 0

    df['timestamp'] = df['Time']
    duration = df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]
    iat = df['timestamp'].diff().dropna()

    src_df = df[df['Source'] == ip_src]
    dst_df = df[df['Source'] == ip_dst]

    fiat = src_df['timestamp'].diff().dropna()
    biat = dst_df['timestamp'].diff().dropna()

    idle_threshold = 1.0
    idle_periods = iat[iat > idle_threshold]
    active_periods = iat[iat <= idle_threshold]

    # direction = 1 if df['Time to Live'].iloc[0] >= 64 else 0

    df_feature.loc[f'{i+1}', :] = [
        df['Source Port'].iloc[0],                             # src_port
        df['Destination Port'].iloc[0],                        # dst_port
        src_df['size'].mean(),                                 # mean_src
        dst_df['size'].mean(),                                 # mean_dst
        len(src_df),                                           # qty_src
        src_df['size'].sum(),                                  # pld_src
        df['size'].std(),                                      # var_data
        src_df['size'].std(),                                  # var_src
        src_df['size'].iloc[0],                                # frst_src
        src_df['size'].iloc[1] if len(src_df) > 1 else 0,      # scd_src
        dst_df['size'].iloc[0],                                # frst_dst
        dst_df['size'].iloc[1] if len(dst_df) > 1 else 0,      # scd_dst
        src_df['size'].max(),                                  # max_src
        src_df['size'].min(),                                  # min_src
        dst_df['size'].max(),                                  # max_dst
        df['Time to Live'].iloc[0],                            # ttl_src
        duration,                                              # duration
        len(df) / duration if duration > 0 else 0,             # flowPktsPerSecond
        df['size'].sum() / duration if duration > 0 else 0,    # flowBytesPerSecond
        iat.mean(),                                            # mean_flowiat
        iat.std(),                                             # std_flowiat
        iat.min(),                                             # min_flowiat
        iat.max(),                                             # max_flowiat
        df['size'].mean(),                                     # packet_size_mean
        df['size'].std(),                                      # packet_size_std
        fiat.sum() if not fiat.empty else 0,                   # total_fiat
        biat.sum() if not biat.empty else 0,                   # total_biat
        fiat.min() if not fiat.empty else 0,                   # min_fiat
        fiat.max() if not fiat.empty else 0,                   # max_fiat
        fiat.mean() if not fiat.empty else 0,                  # mean_fiat
        biat.min() if not biat.empty else 0,                   # min_biat
        biat.max() if not biat.empty else 0,                   # max_biat
        biat.mean() if not biat.empty else 0,                  # mean_biat
        active_periods.min() if not active_periods.empty else 0, # min_active
        active_periods.mean() if not active_periods.empty else 0,# mean_active
        active_periods.max() if not active_periods.empty else 0, # max_active
        active_periods.std() if not active_periods.empty else 0, # std_active
        idle_periods.min() if not idle_periods.empty else 0,     # min_idle
        idle_periods.mean() if not idle_periods.empty else 0,    # mean_idle
        idle_periods.max() if not idle_periods.empty else 0,     # max_idle
        idle_periods.std() if not idle_periods.empty else 0      # std_idle
    ]

df_feature.to_csv('flows/Features_full.csv', index=False)
print(df_feature.head())
