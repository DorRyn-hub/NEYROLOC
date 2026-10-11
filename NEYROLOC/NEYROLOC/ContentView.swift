//
//  ContentView.swift
//  NEYROLOC
//
//  Клиент к настольному NEYROLOC: WKWebView поверх мобильного веб-интерфейса,
//  который отдаёт сервер на компьютере (Файл → Удалённый доступ с телефона).
//  Адрес вводится один раз и сохраняется; перед загрузкой — быстрая проверка
//  доступности, чтобы неверный адрес давал понятную ошибку, а не чёрный экран.
//

import Combine
import SwiftUI
import WebKit

enum ServerAddress {
    static func strip(_ value: String) -> String {
        value.replacingOccurrences(of: "http://", with: "")
            .replacingOccurrences(of: "https://", with: "")
    }

    static func normalize(_ raw: String) -> String {
        let value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else { return value }
        let explicitScheme = value.contains("://")
        if explicitScheme
            && !value.lowercased().hasPrefix("http://")
            && !value.lowercased().hasPrefix("https://") {
            return ""
        }

        guard var components = URLComponents(
            string: explicitScheme ? value : "http://" + value
        ), let host = components.host, !host.isEmpty else {
            return ""
        }
        if !explicitScheme {
            let isDomain = host.range(
                of: "^[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$",
                options: .regularExpression
            ) != nil
            components.scheme = isDomain && !isLocalHTTPHost(host) ? "https" : "http"
        }
        if components.scheme?.lowercased() == "http" && components.port == nil {
            components.port = 8765
        }
        return components.string ?? ""
    }

    static func validatedURL(_ raw: String) -> URL? {
        guard let components = URLComponents(string: normalize(raw)),
              let scheme = components.scheme?.lowercased(),
              ["http", "https"].contains(scheme),
              let host = components.host,
              !host.isEmpty,
              components.user == nil,
              components.password == nil,
              isAllowedFragment(components.fragment),
              components.port.map({ (1...65535).contains($0) }) ?? true,
              scheme == "https" || isLocalHTTPHost(host),
              let url = components.url else {
            return nil
        }
        return url
    }

    static func isAllowedFragment(_ fragment: String?) -> Bool {
        guard let fragment, !fragment.isEmpty else { return true }
        let items = URLComponents(string: "?" + fragment)?.queryItems ?? []
        return items.count == 1
            && items[0].name == "code"
            && (items[0].value?.range(
                of: "^[0-9]{6}$",
                options: .regularExpression
            ) != nil)
    }

    static func isLocalHTTPHost(_ host: String) -> Bool {
        let value = host.lowercased().trimmingCharacters(in: CharacterSet(charactersIn: "[]"))
        if value == "localhost" || value.hasSuffix(".local") || value == "::1" {
            return true
        }
        if value.contains(":")
            && (value.hasPrefix("fc") || value.hasPrefix("fd") || value.hasPrefix("fe80:")) {
            return true
        }

        let octets = value.split(separator: ".").compactMap { Int($0) }
        guard octets.count == 4, octets.allSatisfy({ (0...255).contains($0) }) else {
            return false
        }
        switch (octets[0], octets[1]) {
        case (10, _), (127, _), (192, 168), (169, 254):
            return true
        case (172, 16...31), (100, 64...127):
            return true
        default:
            return false
        }
    }

    static func sameOrigin(_ lhs: URL, _ rhs: URL) -> Bool {
        func effectivePort(_ url: URL) -> Int? {
            if let port = url.port { return port }
            return url.scheme?.lowercased() == "https" ? 443 : 80
        }
        return lhs.scheme?.lowercased() == rhs.scheme?.lowercased()
            && lhs.host?.lowercased() == rhs.host?.lowercased()
            && effectivePort(lhs) == effectivePort(rhs)
    }
}

// MARK: - Сохранение адреса сервера

final class ServerStore: ObservableObject {
    @Published var url: String {
        didSet { UserDefaults.standard.set(url, forKey: "server_url") }
    }
    init() {
        if CommandLine.arguments.contains("-resetServer") {
            UserDefaults.standard.removeObject(forKey: "server_url")
        }
        url = UserDefaults.standard.string(forKey: "server_url") ?? ""
    }
}

// MARK: - WKWebView

struct WebView: UIViewRepresentable {
    let url: URL
    let onReady: () -> Void
    let onError: (String) -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(origin: url, onReady: onReady, onError: onError)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()   // сохраняет локальные чаты и настройки
        config.userContentController.add(context.coordinator, name: "neyrolocExport")
        let web = WKWebView(frame: .zero, configuration: config)
        web.navigationDelegate = context.coordinator
        web.uiDelegate = context.coordinator
        web.isOpaque = false
        web.backgroundColor = UIColor(Color.nBg)
        web.scrollView.backgroundColor = UIColor(Color.nBg)
        web.allowsBackForwardNavigationGestures = true
        context.coordinator.requestedURL = url
        web.load(URLRequest(url: url, timeoutInterval: 10))
        return web
    }

    func updateUIView(_ web: WKWebView, context: Context) {
        context.coordinator.onReady = onReady
        context.coordinator.onError = onError
        if context.coordinator.requestedURL != url {
            context.coordinator.origin = url
            context.coordinator.requestedURL = url
            web.load(URLRequest(url: url, timeoutInterval: 10))
        }
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler {
        var origin: URL
        var requestedURL: URL?
        var onReady: () -> Void
        var onError: (String) -> Void

        init(
            origin: URL,
            onReady: @escaping () -> Void,
            onError: @escaping (String) -> Void
        ) {
            self.origin = origin
            self.onReady = onReady
            self.onError = onError
        }

        func webView(
            _ webView: WKWebView,
            decidePolicyFor navigationAction: WKNavigationAction,
            decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
        ) {
            guard let target = navigationAction.request.url else {
                decisionHandler(.cancel)
                return
            }
            if ServerAddress.sameOrigin(origin, target) {
                decisionHandler(.allow)
                return
            }
            if navigationAction.navigationType == .linkActivated,
               ["http", "https"].contains(target.scheme?.lowercased() ?? "") {
                UIApplication.shared.open(target)
            }
            decisionHandler(.cancel)
        }

        func webView(
            _ webView: WKWebView,
            createWebViewWith configuration: WKWebViewConfiguration,
            for navigationAction: WKNavigationAction,
            windowFeatures: WKWindowFeatures
        ) -> WKWebView? {
            guard navigationAction.targetFrame == nil,
                  let target = navigationAction.request.url else { return nil }
            if ServerAddress.sameOrigin(origin, target) {
                webView.load(navigationAction.request)
            } else if ["http", "https"].contains(target.scheme?.lowercased() ?? "") {
                UIApplication.shared.open(target)
            }
            return nil
        }

        func userContentController(
            _ userContentController: WKUserContentController,
            didReceive message: WKScriptMessage
        ) {
            guard message.name == "neyrolocExport",
                  let payload = message.body as? [String: Any],
                  let text = payload["text"] as? String,
                  text.utf8.count <= 16 * 1024 * 1024 else { return }
            let rawName = (payload["filename"] as? String) ?? "neyroloc.md"
            let allowed = CharacterSet.alphanumerics.union(
                CharacterSet(charactersIn: " -_абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")
            )
            let stem = rawName.replacingOccurrences(of: ".md", with: "")
                .unicodeScalars.filter { allowed.contains($0) }
                .prefix(60)
            let filename = (stem.isEmpty ? "neyroloc" : String(stem)) + ".md"
            let url = FileManager.default.temporaryDirectory.appendingPathComponent(filename)
            do {
                try text.write(to: url, atomically: true, encoding: .utf8)
                presentShareSheet(for: url)
            } catch {
                onError("Не удалось подготовить экспорт чата.")
            }
        }

        private func presentShareSheet(for url: URL) {
            guard let scene = UIApplication.shared.connectedScenes
                .compactMap({ $0 as? UIWindowScene }).first,
                  let window = scene.windows.first(where: { $0.isKeyWindow }),
                  let root = window.rootViewController else { return }
            var presenter = root
            while let presented = presenter.presentedViewController { presenter = presented }
            let sheet = UIActivityViewController(activityItems: [url], applicationActivities: nil)
            if let popover = sheet.popoverPresentationController {
                popover.sourceView = presenter.view
                popover.sourceRect = CGRect(
                    x: presenter.view.bounds.midX,
                    y: presenter.view.bounds.maxY - 1,
                    width: 1,
                    height: 1
                )
            }
            presenter.present(sheet, animated: true)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            onReady()
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            report(error)
        }

        func webView(
            _ webView: WKWebView,
            didFailProvisionalNavigation navigation: WKNavigation!,
            withError error: Error
        ) {
            report(error)
        }

        private func report(_ error: Error) {
            let nsError = error as NSError
            guard nsError.code != NSURLErrorCancelled else { return }
            onError(nsError.localizedDescription)
        }
    }
}

// MARK: - Экраны

private enum Screen { case welcome, web }

struct ContentView: View {
    @StateObject private var store = ServerStore()
    @State private var screen: Screen = .welcome
    @State private var draft: String = ""
    @State private var errorText: String?
    /// Адрес для первой загрузки: из QR он приходит вместе с #code=,
    /// чтобы веб-клиент подключился без ввода кода. В store.url код не
    /// сохраняем — там остаётся чистый адрес.
    @State private var loadURL: String = ""
    @State private var webIsReady = false
    @State private var showingScanner = false
    @State private var showingManualSetup = false
    @State private var showManualAfterScanner = false
    @State private var showScannerAfterManual = false
    @State private var didBootstrap = false

    var body: some View {
        ZStack {
            switch screen {
            case .welcome:
                welcomeView
            case .web:
                webScreen
            }
        }
        .font(AppTypography.bodyRegular)
        .onAppear {
            guard !didBootstrap else { return }
            didBootstrap = true
            draft = ServerAddress.strip(store.url)
            if !store.url.isEmpty {
                loadURL = store.url
                connect(store.url)
            }
        }
        .fullScreenCover(isPresented: $showingScanner, onDismiss: {
            guard showManualAfterScanner else { return }
            showManualAfterScanner = false
            showingManualSetup = true
        }) {
            ScanScreen(
                onScanned: { value in
                    showingScanner = false
                    handleScan(value)
                },
                onManual: {
                    showManualAfterScanner = true
                    showingScanner = false
                },
                onCancel: { showingScanner = false }
            )
        }
        .sheet(isPresented: $showingManualSetup, onDismiss: {
            guard showScannerAfterManual else { return }
            showScannerAfterManual = false
            showingScanner = true
        }) {
            manualSetupSheet
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
        }
    }

    // MARK: Aurora welcome

    private var welcomeView: some View {
        ZStack {
            AuroraBackdrop()

            ScrollView {
                VStack(alignment: .leading, spacing: 22) {
                    brandHeader
                    hero
                    connectionPanel
                    workspaceFeatures
                    createdByRdev
                        .frame(maxWidth: .infinity)
                        .padding(.top, 4)
                }
                .padding(.horizontal, 20)
                .padding(.top, 18)
                .padding(.bottom, 30)
            }
        }
        .accessibilityIdentifier("auroraWelcome")
    }

    private var brandHeader: some View {
        HStack(spacing: 12) {
            logo(44)

            VStack(alignment: .leading, spacing: 2) {
                Text("NEYROLOC")
                    .font(AppTypography.headlineBold)
                    .foregroundStyle(AuroraTheme.text)
            }

            Spacer(minLength: 8)

            AuroraStatusPill(
                title: "iPhone",
                systemImage: "iphone",
                tint: AuroraTheme.teal
            )
        }
    }

    private var hero: some View {
        VStack(alignment: .leading, spacing: 13) {
            HStack(spacing: 8) {
                AuroraStatusPill(
                    title: "ЛОКАЛЬНО + ОБЛАКО",
                    systemImage: "sparkles",
                    tint: AuroraTheme.secondaryText
                )
                AuroraStatusPill(
                    title: "ПРИВАТНО",
                    systemImage: "lock.fill",
                    tint: AuroraTheme.success
                )
            }

            Text("Ваше ИИ-пространство\nна iPhone")
                .font(AppTypography.largeTitleBold)
                .foregroundStyle(AuroraTheme.text)
                .fixedSize(horizontal: false, vertical: true)

            Text("Подключайтесь к моделям на компьютере, продолжайте диалоги и управляйте генерацией из единого пространства NEYROLOC.")
                .font(AppTypography.calloutRegular)
                .foregroundStyle(AuroraTheme.secondaryText)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    private var connectionPanel: some View {
        AuroraPanel {
            VStack(alignment: .leading, spacing: 15) {
                Label("ПОДКЛЮЧЕНИЕ", systemImage: "bolt.horizontal.circle.fill")
                    .font(AppTypography.captionBold)
                    .tracking(0.8)
                    .foregroundStyle(AuroraTheme.teal)

                Text("Один QR-код — и всё готово")
                    .font(AppTypography.title2Bold)
                    .foregroundStyle(AuroraTheme.text)

                Text("Откройте на компьютере «Файл → Удалённый доступ с телефона» и наведите камеру на код.")
                    .font(AppTypography.subheadlineRegular)
                    .foregroundStyle(AuroraTheme.secondaryText)

                if let errorText {
                    Label(errorText, systemImage: "exclamationmark.triangle.fill")
                        .font(AppTypography.captionRegular)
                        .foregroundStyle(AuroraTheme.danger)
                        .fixedSize(horizontal: false, vertical: true)
                }

                Button {
                    errorText = nil
                    showingScanner = true
                } label: {
                    Label("Сканировать QR-код", systemImage: "qrcode.viewfinder")
                }
                .buttonStyle(AuroraPrimaryButtonStyle())
                .accessibilityIdentifier("scanQRCodeButton")

                Button {
                    draft = ServerAddress.strip(store.url)
                    showingManualSetup = true
                } label: {
                    Label("Ввести адрес вручную", systemImage: "network")
                }
                .buttonStyle(AuroraSecondaryButtonStyle())
                .accessibilityIdentifier("manualAddressButton")

                if !store.url.isEmpty {
                    Button {
                        loadURL = store.url
                        connect(store.url)
                    } label: {
                        HStack {
                            Image(systemName: "clock.arrow.circlepath")
                            VStack(alignment: .leading, spacing: 2) {
                                Text("Последнее подключение")
                                    .font(AppTypography.subheadlineBold)
                                Text(displayHost(store.url))
                                    .font(AppTypography.captionRegular)
                                    .foregroundStyle(AuroraTheme.mutedText)
                            }
                            Spacer()
                            Image(systemName: "chevron.right")
                                .font(.caption.bold())
                                .foregroundStyle(AuroraTheme.mutedText)
                        }
                        .foregroundStyle(AuroraTheme.text)
                        .padding(.horizontal, 4)
                        .padding(.vertical, 6)
                    }
                    .accessibilityIdentifier("savedServerButton")
                }
            }
        }
    }

    private var workspaceFeatures: some View {
        HStack(alignment: .top, spacing: 10) {
            feature("bubble.left.and.bubble.right.fill", "Диалоги")
            feature("cpu.fill", "Модели")
            feature("waveform.path", "Поток")
        }
    }

    private func feature(_ systemImage: String, _ title: String) -> some View {
        VStack(spacing: 8) {
            Image(systemName: systemImage)
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(AuroraTheme.teal)
            Text(title)
                .font(AppTypography.captionBold)
                .foregroundStyle(AuroraTheme.secondaryText)
                .lineLimit(1)
                .minimumScaleFactor(0.75)
        }
        .frame(maxWidth: .infinity, minHeight: 66)
        .padding(.vertical, 10)
        .background(AuroraTheme.raisedSurface, in: RoundedRectangle(cornerRadius: 14))
        .overlay {
            RoundedRectangle(cornerRadius: 14)
                .stroke(AuroraTheme.softBorder, lineWidth: 1)
        }
    }

    /// Разбираем ссылку из QR: адрес идёт в настройки, код — в первую загрузку.
    private func handleScan(_ raw: String) {
        let text = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let scannedURL = ServerAddress.validatedURL(text),
              let components = URLComponents(url: scannedURL, resolvingAgainstBaseURL: false),
              let host = components.host, !host.isEmpty,
              let code = URLComponents(string: "?" + (components.fragment ?? ""))?
                .queryItems?.first(where: { $0.name == "code" })?.value
                ?? components.queryItems?.first(where: { $0.name == "code" })?.value,
              code.range(of: "^[0-9]{6}$", options: .regularExpression) != nil else {
            errorText = "Это не QR-код NEYROLOC. Отсканируйте код из окна "
                + "«Удалённый доступ с телефона»."
            return
        }
        var base = components
        base.query = nil
        base.fragment = nil
        base.path = ""
        loadURL = components.string ?? base.string ?? ""
        connect(base.string ?? "")
    }

    // ----- WebView -----

    @ViewBuilder private var webScreen: some View {
        if let u = URL(string: loadURL.isEmpty ? store.url : loadURL) {
            ZStack(alignment: .bottomTrailing) {
                WebView(
                    url: u,
                    onReady: { withAnimation(.easeOut(duration: 0.2)) { webIsReady = true } },
                    onError: { detail in
                        errorText = "Не удалось открыть интерфейс. Проверьте удалённый доступ на компьютере. \(detail)"
                        webIsReady = false
                        screen = .welcome
                    }
                )
                .ignoresSafeArea(.container, edges: .bottom)

                if !webIsReady {
                    loadingOverlay
                }

                Button {
                    draft = ServerAddress.strip(store.url)
                    showingManualSetup = true
                } label: {
                    Image(systemName: "gearshape.fill")
                }
                .buttonStyle(.bordered)
                .buttonBorderShape(.capsule)
                .controlSize(.large)
                .tint(AuroraTheme.text)
                .accessibilityLabel("Настроить адрес сервера")
                .padding(.trailing, 12)
                .padding(.bottom, 94)
            }
            .background(AuroraTheme.background)
        } else {
            welcomeView
        }
    }

    private var loadingOverlay: some View {
        ZStack {
            AuroraBackdrop()
            AuroraPanel {
                VStack(spacing: 16) {
                    logo(58)
                    ProgressView()
                        .tint(AuroraTheme.teal)
                        .scaleEffect(1.15)
                    Text("Открываем NEYROLOC")
                        .font(AppTypography.headlineBold)
                        .foregroundStyle(AuroraTheme.text)
                    Text("Подключение к вашему компьютеру…")
                        .font(AppTypography.calloutRegular)
                        .foregroundStyle(AuroraTheme.mutedText)
                }
            }
            .padding(28)
        }
        .transition(.opacity)
    }

    private var manualSetupSheet: some View {
        NavigationStack {
            ZStack {
                AuroraBackdrop()

                ScrollView {
                    VStack(alignment: .leading, spacing: 18) {
                        AuroraPanel {
                            VStack(alignment: .leading, spacing: 14) {
                                Label("СЕРВЕР NEYROLOC", systemImage: "network")
                                    .font(AppTypography.captionBold)
                                    .tracking(0.8)
                                    .foregroundStyle(AuroraTheme.teal)

                                Text("Локальный IP или HTTPS-адрес")
                                    .font(AppTypography.title2Bold)
                                    .foregroundStyle(AuroraTheme.text)

                                TextField(
                                    "",
                                    text: $draft,
                                    prompt: Text("192.168.1.10:8765").foregroundColor(.nMuted)
                                )
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .keyboardType(.URL)
                                .font(AppTypography.bodyRegular)
                                .foregroundStyle(AuroraTheme.text)
                                .padding(14)
                                .background(AuroraTheme.control, in: RoundedRectangle(cornerRadius: 12))
                                .overlay {
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(AuroraTheme.border, lineWidth: 1)
                                }
                                .accessibilityIdentifier("serverAddressField")
                                .onSubmit { connectFromManualEntry() }

                                Text("HTTP разрешён только для локальных, Tailscale и .local адресов. Публичное подключение должно использовать HTTPS.")
                                    .font(AppTypography.captionRegular)
                                    .foregroundStyle(AuroraTheme.mutedText)
                                    .fixedSize(horizontal: false, vertical: true)

                                Button(action: connectFromManualEntry) {
                                    Label("Подключиться", systemImage: "arrow.right.circle.fill")
                                }
                                .buttonStyle(AuroraPrimaryButtonStyle())
                                .disabled(ServerAddress.validatedURL(draft) == nil)
                                .opacity(ServerAddress.validatedURL(draft) == nil ? 0.55 : 1)
                                .accessibilityIdentifier("connectButton")
                            }
                        }

                        Button {
                            showScannerAfterManual = true
                            showingManualSetup = false
                        } label: {
                            Label("Вместо этого сканировать QR-код", systemImage: "qrcode.viewfinder")
                        }
                        .buttonStyle(AuroraSecondaryButtonStyle())
                    }
                    .padding(20)
                }
            }
            .navigationTitle("Адрес сервера")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Закрыть", systemImage: "xmark") {
                        showingManualSetup = false
                    }
                    .labelStyle(.iconOnly)
                    .accessibilityLabel("Закрыть")
                }
            }
        }
        .preferredColorScheme(.dark)
    }

    // Кредит автора на экране встречи с пользователем
    private var createdByRdev: some View {
        HStack(spacing: 7) {
            Text("created by")
                .font(AppTypography.caption2Regular)
                .foregroundStyle(Color.nMuted.opacity(0.75))
            Image("Rdev").resizable().scaledToFit().frame(height: 15)
        }
        .opacity(0.9)
    }

    // ----- Логика -----

    private func logo(_ size: CGFloat) -> some View {
        Image("Mark")
            .resizable()
            .scaledToFit()
            .frame(width: size * 1.25, height: size * 1.25)
    }

    private func connect(_ raw: String) {
        guard let url = ServerAddress.validatedURL(raw) else {
            errorText = "Проверьте адрес: публичные серверы требуют HTTPS, HTTP доступен только в локальной сети."
            screen = .welcome
            return
        }
        let value = url.absoluteString
        store.url = value
        if loadURL.isEmpty { loadURL = value }
        errorText = nil
        webIsReady = false
        screen = .web
    }

    private func connectFromManualEntry() {
        guard ServerAddress.validatedURL(draft) != nil else { return }
        loadURL = ""
        showingManualSetup = false
        connect(draft)
    }

    private func displayHost(_ raw: String) -> String {
        guard let url = URL(string: raw), let host = url.host else { return raw }
        if let port = url.port { return "\(host):\(port)" }
        return host
    }
}

#Preview {
    ContentView().preferredColorScheme(.dark)
}
