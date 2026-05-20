// PlazaTheme.swift
// Design tokens de Plaza: colores adaptativos, tipografías personalizadas, espaciado y componente PlTag.

import SwiftUI
import UIKit

// MARK: - Colors

extension Color {
    static let plBg      = Color(light: 0xfbf8f1, dark: 0x141210)
    static let plSurface = Color(light: 0xf3eee2, dark: 0x1e1c18)
    static let plFg      = Color(light: 0x0e0c0a, dark: 0xf5f2ec)
    static let plMuted   = Color(light: 0x5c544a, dark: 0xa09888)
    static let plDim     = Color(light: 0x8e8675, dark: 0x7a7268)
    static let plHair    = Color(light: 0xd6cfbf, dark: 0x2e2a24)
    static let plAccent  = Color(light: 0xc5832b, dark: 0xd4923a)
}

extension Color {
    init(hex: UInt32, alpha: Double = 1) {
        let r = Double((hex >> 16) & 0xFF) / 255
        let g = Double((hex >> 8) & 0xFF) / 255
        let b = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: r, green: g, blue: b, opacity: alpha)
    }

    init(light: UInt32, dark: UInt32) {
        self.init(uiColor: UIColor { traits in
            let hex = traits.userInterfaceStyle == .dark ? dark : light
            let r = CGFloat((hex >> 16) & 0xFF) / 255
            let g = CGFloat((hex >> 8) & 0xFF) / 255
            let b = CGFloat(hex & 0xFF) / 255
            return UIColor(red: r, green: g, blue: b, alpha: 1)
        })
    }
}

// MARK: - Fonts

extension Font {
    static func plDisplay(_ size: CGFloat, weight: Font.Weight = .semibold) -> Font {
        .custom("Bricolage Grotesque", size: size, relativeTo: size >= 32 ? .largeTitle : .title).weight(weight)
    }
    static func plSans(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .custom("Bricolage Grotesque", size: size, relativeTo: size >= 16 ? .body : .caption).weight(weight)
    }
    static func plSerifItalic(_ size: CGFloat) -> Font {
        .custom("InstrumentSerif-Italic", size: size, relativeTo: size >= 18 ? .title3 : .subheadline)
    }
    static func plMono(_ size: CGFloat) -> Font {
        .custom("JetBrains Mono", size: size, relativeTo: .caption2)
    }
    // Estilo tipo Playbill: serif condensado bold para encabezados de tarjeta
    static func plPlaybill(_ size: CGFloat) -> Font {
        .system(size: size, weight: .heavy, design: .serif)
    }
}

// MARK: - Card Colors (themeable — futuro: selector de color)

extension Color {
    // Colores de posición para EventImageStack. Orden fijo: izq=rojo, centro=cyan, der=amarillo
    static let plCardLeft   = Color(hex: 0xE03030)
    static let plCardCenter = Color(hex: 0x3AB8D8)
    static let plCardRight  = Color(hex: 0xF0D030)
}

// MARK: - iPad Sidebar Environment

private struct IPadSidebarKey: EnvironmentKey {
    static let defaultValue = false
}

extension EnvironmentValues {
    var isIPadSidebar: Bool {
        get { self[IPadSidebarKey.self] }
        set { self[IPadSidebarKey.self] = newValue }
    }
}

// MARK: - Spacing

enum PlSpace {
    static let gutter: CGFloat = 22
    static let cardRadius: CGFloat = 14
    static let sectionSpacing: CGFloat = 28
}

// MARK: - Tag (mono uppercase label)

struct PlTag: View {
    let text: String
    var color: Color = .plMuted
    var body: some View {
        Text(text.uppercased())
            .font(.plMono(10))
            .tracking(0.6)
            .foregroundStyle(color)
    }
}
