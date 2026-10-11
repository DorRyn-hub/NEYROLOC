//
//  AppTypography.swift
//  NEYROLOC
//
//  Shared native typography. Onest is bundled with the application and
//  registered through UIAppFonts in Info.plist.
//

import SwiftUI

enum AppTypography {
    private enum Weight {
        case regular
        case bold

        var swiftUI: Font.Weight {
            switch self {
            case .regular: .regular
            case .bold: .bold
            }
        }
    }

    private static func font(
        size: CGFloat,
        relativeTo textStyle: Font.TextStyle,
        weight: Weight
    ) -> Font {
        Font.custom("Onest", size: size, relativeTo: textStyle)
            .weight(weight.swiftUI)
    }

    static let largeTitleBold = font(size: 34, relativeTo: .largeTitle, weight: .bold)
    static let titleBold = font(size: 28, relativeTo: .title, weight: .bold)
    static let title2Bold = font(size: 22, relativeTo: .title2, weight: .bold)
    static let headlineBold = font(size: 17, relativeTo: .headline, weight: .bold)
    static let headlineRegular = font(size: 17, relativeTo: .headline, weight: .regular)
    static let bodyRegular = font(size: 17, relativeTo: .body, weight: .regular)
    static let calloutRegular = font(size: 16, relativeTo: .callout, weight: .regular)
    static let calloutBold = font(size: 16, relativeTo: .callout, weight: .bold)
    static let subheadlineRegular = font(size: 15, relativeTo: .subheadline, weight: .regular)
    static let subheadlineBold = font(size: 15, relativeTo: .subheadline, weight: .bold)
    static let captionRegular = font(size: 12, relativeTo: .caption, weight: .regular)
    static let captionBold = font(size: 12, relativeTo: .caption, weight: .bold)
    static let caption2Regular = font(size: 11, relativeTo: .caption2, weight: .regular)
}
