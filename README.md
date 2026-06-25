# Enctypted_vpn_project
Model selection about best new vpn protocols detector.

## Сценарии трафика

Браузер без VPN (Chrome, Opera) |	Non-VPN |	Базовый легитимный трафик
Подключение к серверу OpenVPN |	VPN |	Явный VPN-туннель
Shadowsocks-клиент (ss-local) с ProxyChains или Firefox |	VPN |	Обфусцированный прокси-туннель
Обход DPI: Shadowsocks через нестандартный порт |	VPN |	Имитация устойчивого обхода блокировок
C2-подобный канал через VPN (curl или ping с паузами) |	VPN	| Симуляция скрытого beaconing-поведения
C2-подобный канал без VPN (curl напрямую к серверу) |	Non-VPN |	Имитация внешнего взаимодействия без туннеля
Discord или Telegram Web без VPN |	Non-VPN |	Проверка зашифрованного трафика без туннелирования, UDP
Torrent, Steam, браузерные обновления |	Non-VPN	| Фоновый шумовой трафик 
Exfiltration over VPN — отправка файлов на внешние хосты через туннель | VPN |	Проверка устойчивости модели к эксфильтрации данных
