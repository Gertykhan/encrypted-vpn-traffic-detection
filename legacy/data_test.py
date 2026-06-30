import pandas as pd

df = pd.read_csv('flows/traffic_data_002.csv')
df.columns = [c.strip() for c in df.columns]

# Найдём одну пару клиент-сервер
client_ip = '192.168.1.4'
server_ip = '13.68.233.9'
client_port = 50571
server_port = 443

# Пакеты от сервера
server_packets = df[
    (df['ip.src'] == server_ip) &
    (df['ip.dst'] == client_ip) &
    (df['tcp.srcport'] == server_port) &
    (df['tcp.dstport'] == client_port)
]

# Посмотреть, какие там значения size, tcp.len, tcp.hdr_len
print(server_packets[['tcp.len', 'tcp.hdr_len', 'frame.time_relative']].head(10))
