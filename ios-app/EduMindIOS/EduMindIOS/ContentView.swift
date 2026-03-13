//
//  ContentView.swift
//  EduMindIOS
//
//  Created by yuan on 2026/3/12.
//

import SwiftUI
import WebKit

private enum WebAssets {
    static let indexName = "index"
    static let indexExtension = "html"
    static let preferredSubdirectory = "WebAssets"

    static func indexURL() -> URL? {
        // Prefer WebAssets folder, then fall back to app bundle root.
        if let bundled = Bundle.main.url(
            forResource: indexName,
            withExtension: indexExtension,
            subdirectory: preferredSubdirectory
        ) {
            return bundled
        }
        return Bundle.main.url(forResource: indexName, withExtension: indexExtension)
    }
}

private struct H5WebView: UIViewRepresentable {
    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.backgroundColor = .systemBackground
        loadContent(into: webView)
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    private func loadContent(into webView: WKWebView) {
        guard let indexURL = WebAssets.indexURL() else {
            webView.loadHTMLString(
                "<h2 style=\"font-family:-apple-system\">未找到前端资源</h2><p style=\"font-family:-apple-system\">请执行：bash ios-app/sync_ios_web_assets.sh</p>",
                baseURL: nil
            )
            return
        }

        let allowedPath = indexURL.deletingLastPathComponent()
        webView.loadFileURL(indexURL, allowingReadAccessTo: allowedPath)
    }
}

struct ContentView: View {
    var body: some View {
        H5WebView()
            .ignoresSafeArea()
    }
}

#Preview {
    ContentView()
}
