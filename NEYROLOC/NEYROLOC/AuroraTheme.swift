//
//  AuroraTheme.swift
//  NEYROLOC
//
//  Native tokens shared by the iPhone shell. The values mirror the current
//  Premium Workspace stylesheet in the desktop application.
//

import SwiftUI

enum AuroraTheme {
    static let background = Color(red: 7 / 255, green: 10 / 255, blue: 18 / 255)
    static let header = Color(red: 9 / 255, green: 13 / 255, blue: 23 / 255)
    static let rail = Color(red: 13 / 255, green: 18 / 255, blue: 32 / 255)
    static let surface = Color(red: 17 / 255, green: 25 / 255, blue: 42 / 255)
    static let raisedSurface = Color(red: 16 / 255, green: 23 / 255, blue: 39 / 255)
    static let control = Color(red: 19 / 255, green: 28 / 255, blue: 49 / 255)
    static let controlPressed = Color(red: 32 / 255, green: 44 / 255, blue: 71 / 255)
    static let border = Color(red: 45 / 255, green: 61 / 255, blue: 91 / 255)
    static let softBorder = Color(red: 30 / 255, green: 42 / 255, blue: 65 / 255)
    static let text = Color(red: 244 / 255, green: 247 / 255, blue: 255 / 255)
    static let secondaryText = Color(red: 180 / 255, green: 192 / 255, blue: 212 / 255)
    static let mutedText = Color(red: 130 / 255, green: 144 / 255, blue: 168 / 255)
    static let accent = Color(red: 108 / 255, green: 92 / 255, blue: 231 / 255)
    static let accentHover = Color(red: 131 / 255, green: 116 / 255, blue: 244 / 255)
    static let accentSoft = Color(red: 37 / 255, green: 33 / 255, blue: 77 / 255)
    static let teal = Color(red: 51 / 255, green: 214 / 255, blue: 200 / 255)
    static let success = Color(red: 68 / 255, green: 211 / 255, blue: 157 / 255)
    static let danger = Color(red: 255 / 255, green: 107 / 255, blue: 134 / 255)

    static let brandPurple = Color(red: 140 / 255, green: 73 / 255, blue: 254 / 255)
    static let brandBlue = Color(red: 54 / 255, green: 103 / 255, blue: 255 / 255)
    static let brandCyan = Color(red: 70 / 255, green: 205 / 255, blue: 249 / 255)

    static let brandGradient = LinearGradient(
        colors: [brandPurple, brandBlue, brandCyan],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

// Compatibility names used by the existing WebView and scanner code.
extension Color {
    static let nBg = AuroraTheme.background
    static let nSurface = AuroraTheme.surface
    static let nBorder = AuroraTheme.border
    static let nText = AuroraTheme.text
    static let nMuted = AuroraTheme.mutedText
    static let nAccent = AuroraTheme.accent
    static let nDanger = AuroraTheme.danger
}

extension LinearGradient {
    static let nBrand = AuroraTheme.brandGradient
}

struct AuroraBackdrop: View {
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                AuroraTheme.background

                Circle()
                    .fill(AuroraTheme.accent.opacity(0.18))
                    .frame(width: geometry.size.width * 0.95)
                    .blur(radius: 90)
                    .offset(x: geometry.size.width * 0.46, y: -geometry.size.height * 0.34)

                Circle()
                    .fill(AuroraTheme.brandCyan.opacity(0.10))
                    .frame(width: geometry.size.width * 0.78)
                    .blur(radius: 100)
                    .offset(x: -geometry.size.width * 0.48, y: geometry.size.height * 0.42)
            }
        }
        .ignoresSafeArea()
        .accessibilityHidden(true)
    }
}

struct AuroraPanel<Content: View>: View {
    private let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .padding(18)
            .background(AuroraTheme.surface.opacity(0.96), in: RoundedRectangle(cornerRadius: 18))
            .overlay {
                RoundedRectangle(cornerRadius: 18)
                    .stroke(AuroraTheme.softBorder, lineWidth: 1)
            }
    }
}

struct AuroraStatusPill: View {
    let title: String
    let systemImage: String
    var tint: Color = AuroraTheme.secondaryText

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(AppTypography.captionBold)
            .foregroundStyle(tint)
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .background(AuroraTheme.raisedSurface, in: Capsule())
            .overlay {
                Capsule().stroke(AuroraTheme.border, lineWidth: 1)
            }
    }
}

struct AuroraPrimaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(AppTypography.headlineBold)
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity, minHeight: 52)
            .background(
                configuration.isPressed ? AuroraTheme.accentHover : AuroraTheme.accent,
                in: RoundedRectangle(cornerRadius: 14)
            )
            .overlay {
                RoundedRectangle(cornerRadius: 14)
                    .stroke(Color.white.opacity(configuration.isPressed ? 0.16 : 0.10), lineWidth: 1)
            }
            .scaleEffect(configuration.isPressed ? 0.985 : 1)
            .animation(.easeOut(duration: 0.14), value: configuration.isPressed)
    }
}

struct AuroraSecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(AppTypography.subheadlineBold)
            .foregroundStyle(AuroraTheme.text)
            .frame(maxWidth: .infinity, minHeight: 48)
            .background(
                configuration.isPressed ? AuroraTheme.controlPressed : AuroraTheme.control,
                in: RoundedRectangle(cornerRadius: 14)
            )
            .overlay {
                RoundedRectangle(cornerRadius: 14)
                    .stroke(AuroraTheme.border, lineWidth: 1)
            }
    }
}
