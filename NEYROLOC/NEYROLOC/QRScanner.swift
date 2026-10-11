//
//  QRScanner.swift
//  NEYROLOC
//
//  Считывание QR-кода с экрана компьютера: адрес и код сопряжения приходят
//  одной ссылкой, вводить руками ничего не нужно.
//

import AVFoundation
import SwiftUI

// MARK: - Камера

/// Обёртка над AVCaptureSession: показывает видоискатель и отдаёт первую
/// распознанную строку.
final class ScannerController: UIViewController {
    var onFound: ((String) -> Void)?
    var onUnavailable: (() -> Void)?

    private let session = AVCaptureSession()
    private let sessionQueue = DispatchQueue(label: "ru.dorryn.neyroloc.camera")
    private var preview: AVCaptureVideoPreviewLayer?
    private var finished = false

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        configure()
    }

    private func configure() {
        guard let device = AVCaptureDevice.default(for: .video),
              let input = try? AVCaptureDeviceInput(device: device),
              session.canAddInput(input) else {
            onUnavailable?()
            return
        }
        session.addInput(input)

        let output = AVCaptureMetadataOutput()
        guard session.canAddOutput(output) else {
            onUnavailable?()
            return
        }
        session.addOutput(output)
        output.setMetadataObjectsDelegate(self, queue: .main)
        output.metadataObjectTypes = [.qr]

        let layer = AVCaptureVideoPreviewLayer(session: session)
        layer.videoGravity = .resizeAspectFill
        layer.frame = view.layer.bounds
        view.layer.addSublayer(layer)
        preview = layer

        start()
    }

    func start() {
        sessionQueue.async { [weak self] in
            guard let self, !self.session.isRunning else { return }
            self.session.startRunning()
        }
    }

    func stop() {
        sessionQueue.async { [weak self] in
            guard let self, self.session.isRunning else { return }
            self.session.stopRunning()
        }
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        preview?.frame = view.layer.bounds
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        stop()
    }
}

extension ScannerController: AVCaptureMetadataOutputObjectsDelegate {
    func metadataOutput(_ output: AVCaptureMetadataOutput,
                        didOutput metadataObjects: [AVMetadataObject],
                        from connection: AVCaptureConnection) {
        guard !finished,
              let object = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
              let value = object.stringValue
        else { return }
        finished = true
        UINotificationFeedbackGenerator().notificationOccurred(.success)
        stop()
        onFound?(value)
    }
}

struct ScannerView: UIViewControllerRepresentable {
    var onFound: (String) -> Void
    var onUnavailable: () -> Void

    func makeUIViewController(context: Context) -> ScannerController {
        let controller = ScannerController()
        controller.onFound = onFound
        controller.onUnavailable = onUnavailable
        return controller
    }

    func updateUIViewController(_ controller: ScannerController, context: Context) {}
}

// MARK: - Экран сканирования

struct ScanScreen: View {
    var onScanned: (String) -> Void
    var onManual: () -> Void
    var onCancel: () -> Void

    private enum CameraState {
        case checking
        case ready
        case denied
        case unavailable
    }

    @State private var cameraState: CameraState = .checking
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            switch cameraState {
            case .checking:
                permissionCheck
            case .ready:
                ScannerView(
                    onFound: onScanned,
                    onUnavailable: { cameraState = .unavailable }
                )
                .ignoresSafeArea()
                overlay
            case .denied:
                permissionMessage(canOpenSettings: true)
            case .unavailable:
                permissionMessage(canOpenSettings: false)
            }
        }
        .onAppear(perform: checkPermission)
        .onChange(of: scenePhase) { newPhase in
            if newPhase == .active {
                checkPermission()
            }
        }
        .preferredColorScheme(.dark)
    }

    private var overlay: some View {
        GeometryReader { geometry in
            let finderSide = min(244, max(172, min(geometry.size.width - 64, geometry.size.height * 0.32)))

            ZStack {
                Color.black.opacity(0.22).ignoresSafeArea()

                VStack(spacing: 0) {
                HStack(spacing: 10) {
                    logo
                    VStack(alignment: .leading, spacing: 1) {
                        Text("NEYROLOC")
                            .font(AppTypography.subheadlineBold)
                        Text("QR-ПОДКЛЮЧЕНИЕ")
                            .font(AppTypography.caption2Regular)
                            .tracking(1)
                            .foregroundStyle(AuroraTheme.mutedText)
                    }

                    Spacer()

                    Button(action: onCancel) {
                        Image(systemName: "xmark")
                    }
                    .buttonStyle(.bordered)
                    .buttonBorderShape(.capsule)
                    .tint(AuroraTheme.text)
                    .accessibilityLabel("Закрыть сканер")
                }
                .foregroundStyle(.white)
                .padding(.horizontal, 18)
                .padding(.top, 10)

                Spacer()

                RoundedRectangle(cornerRadius: 26)
                    .stroke(AuroraTheme.teal, lineWidth: 3)
                    .frame(width: finderSide, height: finderSide)
                    .shadow(color: AuroraTheme.teal.opacity(0.42), radius: 18)
                    .accessibilityHidden(true)

                Spacer()

                AuroraPanel {
                    VStack(spacing: 12) {
                        Label("Наведите на QR-код", systemImage: "viewfinder")
                            .font(AppTypography.headlineBold)
                            .foregroundStyle(AuroraTheme.text)

                        Text("Код находится на компьютере: «Файл → Удалённый доступ с телефона»")
                            .font(AppTypography.captionRegular)
                            .foregroundStyle(AuroraTheme.secondaryText)
                            .multilineTextAlignment(.center)

                        Button(action: onManual) {
                            Label("Ввести адрес вручную", systemImage: "keyboard")
                        }
                        .buttonStyle(AuroraSecondaryButtonStyle())
                    }
                }
                .padding(.horizontal, 18)
                .padding(.bottom, 18)
                }
            }
        }
    }

    private var permissionCheck: some View {
        ZStack {
            AuroraBackdrop()
            VStack(spacing: 16) {
                logo
                ProgressView()
                    .tint(AuroraTheme.teal)
                Text("Проверяем доступ к камере")
                    .font(AppTypography.headlineBold)
                    .foregroundStyle(AuroraTheme.text)
            }
        }
    }

    private func permissionMessage(canOpenSettings: Bool) -> some View {
        ZStack {
            AuroraBackdrop()
            VStack(spacing: 18) {
                HStack {
                    Spacer()
                    Button(action: onCancel) {
                        Image(systemName: "xmark")
                    }
                    .buttonStyle(.bordered)
                    .buttonBorderShape(.capsule)
                    .tint(AuroraTheme.text)
                    .accessibilityLabel("Закрыть сканер")
                }

                Spacer()

                AuroraPanel {
                    VStack(spacing: 14) {
                        Image(systemName: canOpenSettings ? "camera.fill" : "camera.slash.fill")
                            .font(.system(size: 34, weight: .semibold))
                            .foregroundStyle(AuroraTheme.teal)
                        Text(canOpenSettings ? "Нужен доступ к камере" : "Камера недоступна")
                            .font(AppTypography.title2Bold)
                            .foregroundStyle(AuroraTheme.text)
                        Text(
                            canOpenSettings
                                ? "Разрешите камеру в настройках iPhone или подключитесь по адресу."
                                : "На этом устройстве нельзя запустить сканер. Подключитесь по адресу вручную."
                        )
                        .font(AppTypography.calloutRegular)
                        .foregroundStyle(AuroraTheme.secondaryText)
                        .multilineTextAlignment(.center)

                        if canOpenSettings {
                            Button {
                                guard let url = URL(string: UIApplication.openSettingsURLString) else { return }
                                UIApplication.shared.open(url)
                            } label: {
                                Label("Открыть настройки", systemImage: "gearshape.fill")
                            }
                            .buttonStyle(AuroraPrimaryButtonStyle())
                        }

                        Button(action: onManual) {
                            Label("Ввести адрес вручную", systemImage: "keyboard")
                        }
                        .buttonStyle(AuroraSecondaryButtonStyle())
                    }
                }

                Spacer()
            }
            .padding(20)
        }
    }

    private var logo: some View {
        Image("Mark")
            .resizable()
            .scaledToFit()
            .frame(width: 40, height: 40)
    }

    private func checkPermission() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            cameraState = .ready
        case .notDetermined:
            cameraState = .checking
            AVCaptureDevice.requestAccess(for: .video) { granted in
                DispatchQueue.main.async { cameraState = granted ? .ready : .denied }
            }
        default:
            cameraState = .denied
        }
    }
}
