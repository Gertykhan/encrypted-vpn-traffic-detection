import pandas as pd
import numpy as np
import glob
import os
import re

def safe(series, index=0, func='mean'):
    s = series.dropna()
    if s.empty: return 0
    if func == 'mean': return s.mean()
    if func == 'max': return s.max()
    if func == 'std': return s.std()
    return s.iloc[index] if index < len(s) else 0

def make_bidirectional_flow_id(proto, ip1, ip2, port1, port2):
    key = sorted([(ip1, port1), (ip2, port2)])
    return f"{proto}_{key[0][0]}_{key[0][1]}_{key[1][0]}_{key[1][1]}"


all_features = []

# Все .csv в папке flows
file_list = glob.glob('flows/traffic_data_*.csv')

for filepath in file_list:
    df = pd.read_csv(filepath)

    # Извлекаем номер сценария из имени файла, например "traffic_data_002.csv"
    filename = os.path.basename(filepath)
    match = re.search(r'traffic_data_(\d+)', filename)
    scenario_id = int(match.group(1)) if match else -1

    # Присваиваем сценарий и метку VPN/Non-VPN
    df['scenario'] = scenario_id
    df['label'] = 'VPN' if scenario_id in [2, 3, 4, 5, 10] else 'Non-VPN'

    df.columns = [c.strip() for c in df.columns]

    df['protocol'] = np.where(df['tcp.srcport'].notna(), 'TCP',
                              np.where(df['udp.srcport'].notna(), 'UDP', 'OTHER'))
    df = df[df['protocol'].isin(['TCP', 'UDP'])]

    df['src_port'] = df['tcp.srcport'].fillna(df['udp.srcport'])
    df['dst_port'] = df['tcp.dstport'].fillna(df['udp.dstport'])
    df['size'] = np.where(
        df['protocol'] == 'TCP',
        df['tcp.len'].fillna(0) + df['tcp.hdr_len'].fillna(0),
        df['udp.length'].fillna(0)
    )
    df['timestamp'] = df['frame.time_relative']
    df['ip.src'] = df['ip.src'].astype(str)
    df['ip.dst'] = df['ip.dst'].astype(str)

    df['flow_id'] = df.apply(lambda row: make_bidirectional_flow_id(row['protocol'], row['ip.src'], row['ip.dst'], row['src_port'], row['dst_port']), axis=1)

    for flow_id, group in df.groupby('flow_id'):
        group = group.sort_values('timestamp')
        if group.shape[0] < 2:
            continue



        src_ip = group['ip.src'].iloc[0]
        dst_ip = group['ip.dst'].iloc[0]
        src_port = group['src_port'].iloc[0]
        dst_port = group['dst_port'].iloc[0]

        # Клиент → Сервер
        src_df = group[
            (group['ip.src'] == src_ip) &
            (group['ip.dst'] == dst_ip) &
            (group['src_port'] == src_port) &
            (group['dst_port'] == dst_port)
        ]

        # Сервер → Клиент
        dst_df = group[
            (group['ip.src'] == dst_ip) &
            (group['ip.dst'] == src_ip) &
            (group['src_port'] == dst_port) &
            (group['dst_port'] == src_port)
        ]

        iat = group['timestamp'].diff().dropna()
        fiat = src_df['timestamp'].diff().dropna()
        biat = dst_df['timestamp'].diff().dropna()

        idle_threshold = 1.0
        idle_periods = iat[iat > idle_threshold]
        active_periods = iat[iat <= idle_threshold]

        duration = group['timestamp'].iloc[-1] - group['timestamp'].iloc[0]
        ttl = group['ip.ttl'].iloc[0] if 'ip.ttl' in group.columns else 0

        all_features.append({
            'scenario': scenario_id,
            'label': 'VPN' if scenario_id in [2, 3, 4, 5, 10] else 'Non-VPN',
            'src_port': group['src_port'].iloc[0],           # Номер порта клиента
            'dst_port': group['dst_port'].iloc[0],           # Номер порта сервера
            'mean_src': src_df['size'].mean(),               # Средний размер пакетов, отправленных клиентом
            'mean_dst': safe(dst_df['size'], func='mean'),               # Средний размер пакетов, отправленных сервером
            'qty_src': len(src_df),                          # Число пакетов от клиента
            'pld_src': src_df['size'].sum(),                 # Общая нагрузка от клиента (сумма всех size)
            'var_data': group['size'].std(),                 # Стд. отклонение размера пакетов по потоку
            'var_src': src_df['size'].std(),                 # Стд. отклонение размера пакетов от клиента
            'frst_src': src_df['size'].iloc[0],              # Размер первого пакета клиента
            'scd_src': src_df['size'].iloc[1] if len(src_df) > 1 else 0,  # Размер второго пакета клиента
            'frst_dst': safe(dst_df['size'], 0), # Размер первого пакета сервера
            'scd_dst': safe(dst_df['size'], 1),  # Размер второго пакета сервера
            'max_src': src_df['size'].max(),                 # Максимальный размер пакета клиента
            'min_src': src_df['size'].min(),                 # Минимальный размер пакета клиента
            'max_dst': safe(dst_df['size'], func='max'), # Максимальный размер пакета сервера
            'ttl_src': ttl,                                  # TTL первого пакета от клиента
            'duration': duration,                            # Длительность потока
            'flowPktsPerSecond': len(group) / duration if duration > 0 else 0,  # Пакеты/сек
            'flowBytesPerSecond': group['size'].sum() / duration if duration > 0 else 0,  # Байт/сек
            'mean_flowiat': iat.mean(),                      # Среднее межпакетное время (IAT) по потоку
            'std_flowiat': iat.std(),                        # Стд. отклонение IAT
            'min_flowiat': iat.min(),                        # Мин. IAT
            'max_flowiat': iat.max(),                        # Макс. IAT
            'packet_size_mean': group['size'].mean(),        # Средний размер пакета
            'packet_size_std': group['size'].std(),          # Стд. отклонение размера пакета
            'total_fiat': fiat.sum() if not fiat.empty else 0,  # Сумма IAT в прямом направлении
            'total_biat': biat.sum() if not biat.empty else 0,  # Сумма IAT в обратном направлении
            'min_fiat': fiat.min() if not fiat.empty else 0,    # Мин. IAT от клиента
            'max_fiat': fiat.max() if not fiat.empty else 0,    # Макс. IAT от клиента
            'mean_fiat': fiat.mean() if not fiat.empty else 0,  # Средняя IAT от клиента
            'min_biat': biat.min() if not biat.empty else 0,    # Мин. IAT от сервера
            'max_biat': biat.max() if not biat.empty else 0,    # Макс. IAT от сервера
            'mean_biat': biat.mean() if not biat.empty else 0,  # Средняя IAT от сервера
            'min_active': active_periods.min() if not active_periods.empty else 0, # Мин. активная фаза
            'mean_active': active_periods.mean() if not active_periods.empty else 0, # Средняя активная фаза
            'max_active': active_periods.max() if not active_periods.empty else 0, # Макс. активная фаза
            'std_active': active_periods.std() if not active_periods.empty else 0, # Стд. отклонение активных фаз
            'min_idle': idle_periods.min() if not idle_periods.empty else 0,     # Мин. пауза между активностями
            'mean_idle': idle_periods.mean() if not idle_periods.empty else 0,   # Средняя пауза между активностями
            'max_idle': idle_periods.max() if not idle_periods.empty else 0,     # Макс. пауза между активностями
            'std_idle': idle_periods.std() if not idle_periods.empty else 0      # Стд. отклонение пауз
        })

# Финальная сборка всех потоков в таблицу
df_features = pd.DataFrame(all_features)
df_features.to_csv('flows/Features_full.csv', index=False)

print(df_features.describe())
