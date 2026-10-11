# NEYROLOC for iOS

Нативная iOS-оболочка для защищённого подключения к remote-интерфейсу
NEYROLOC NEW.

## Возможности

- ввод адреса вручную или сканирование QR-кода из desktop-приложения;
- нормализация локальных HTTP-адресов на порт `8765` и публичных HTTPS-доменов;
- отказ от схем, отличных от HTTP/HTTPS, userinfo, fragments и неверных портов;
- WKWebView, ограниченный scheme/host/effective-port исходного сервера;
- открытие внешней HTTP(S)-ссылки только после явного нажатия пользователя;
- локальное хранение адреса, чатов и интерфейсных настроек;
- deployment target iOS 16.

## Сборка и тесты

Откройте `NEYROLOC.xcodeproj` в Xcode или выполните сборку для симулятора:

```bash
xcodebuild -project NEYROLOC.xcodeproj -scheme NEYROLOC \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17,OS=26.1' \
  build CODE_SIGNING_ALLOWED=NO
```

Unit tests покрывают нормализацию адресов и same-origin policy. Для установки
на реальное устройство или публикации в App Store нужны собственная Apple
signing team, release archive и проверка на целевом устройстве. Сертификаты,
provisioning profiles и пользовательские Xcode-файлы не хранятся в Git.
