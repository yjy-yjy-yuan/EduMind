//
//  ContentView.swift
//  EduMindIOS
//
//  Created by yuan on 2026/3/12.
//

import Foundation
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
    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        configuration.userContentController.add(context.coordinator, name: Coordinator.logHandlerName)
        configuration.userContentController.addUserScript(WKUserScript(
            source: Coordinator.consoleBridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: false
        ))
        configuration.userContentController.addUserScript(WKUserScript(
            source: Coordinator.mountWatchdogScript,
            injectionTime: .atDocumentEnd,
            forMainFrameOnly: true
        ))

        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.scrollView.contentInsetAdjustmentBehavior = .never
        webView.scrollView.bounces = false
        webView.backgroundColor = .systemBackground
        webView.isOpaque = false
        webView.navigationDelegate = context.coordinator
        if #available(iOS 16.4, *) {
            webView.isInspectable = true
        }
        context.coordinator.startLoadTimeout(for: webView)
        loadContent(into: webView)
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    static func dismantleUIView(_ uiView: WKWebView, coordinator: Coordinator) {
        uiView.navigationDelegate = nil
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: Coordinator.logHandlerName)
    }

    private func loadContent(into webView: WKWebView) {
        guard let indexURL = WebAssets.indexURL() else {
            NSLog("[EduMindWeb] index.html not found in bundle. resourceURL=%@", Bundle.main.resourceURL?.path ?? "<nil>")
            webView.loadHTMLString(
                "<h2 style=\"font-family:-apple-system\">未找到前端资源</h2><p style=\"font-family:-apple-system\">请执行：bash ios-app/sync_ios_web_assets.sh</p>",
                baseURL: nil
            )
            return
        }

        let allowedPath = indexURL.deletingLastPathComponent()
        NSLog("[EduMindWeb] loading index from %@", indexURL.path)
        NSLog("[EduMindWeb] allowing read access to %@", allowedPath.path)
        do {
            let html = try String(contentsOf: indexURL, encoding: .utf8)
            if usesLegacyAbsoluteAssetPaths(in: html) {
                NSLog("[EduMindWeb] detected legacy absolute asset paths in %@", indexURL.path)
                webView.loadHTMLString(
                    "<h2 style=\"font-family:-apple-system\">前端资源路径不兼容</h2><p style=\"font-family:-apple-system\">请执行：bash ios-app/sync_ios_web_assets.sh</p>",
                    baseURL: nil
                )
                return
            }
        } catch {
            // Ignore and continue with direct file loading.
        }

        webView.loadFileURL(indexURL, allowingReadAccessTo: allowedPath)
    }

    private func usesLegacyAbsoluteAssetPaths(in html: String) -> Bool {
        html.contains("src=\"/") || html.contains("href=\"/") || html.contains("src='/") || html.contains("href='/")
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        static let logHandlerName = "edumindLog"

        static let consoleBridgeScript = """
            (function() {
              if (window.__edumindConsoleHooked__) return;
              window.__edumindConsoleHooked__ = true;
              function post(level, payload) {
                try {
                  window.webkit.messageHandlers.edumindLog.postMessage({
                    level: level,
                    payload: String(payload || '')
                  });
                } catch (e) {}
              }
              function wrapConsole(level) {
                var raw = console[level];
                console[level] = function() {
                  try {
                    var text = Array.prototype.slice.call(arguments).map(function(v) {
                      return typeof v === 'string' ? v : JSON.stringify(v);
                    }).join(' ');
                    post('console.' + level, text);
                  } catch (e) {}
                  return raw && raw.apply(console, arguments);
                };
              }
              ['log', 'info', 'warn', 'error', 'debug'].forEach(wrapConsole);
              window.__edumindNativeProbe = function(stage) {
                try {
                  var app = document.getElementById('app');
                  var payload = {
                    stage: stage || 'probe',
                    href: String(window.location.href || ''),
                    readyState: String(document.readyState || ''),
                    title: String(document.title || ''),
                    appExists: !!app,
                    appChildCount: app ? app.childElementCount : -1,
                    appTextLength: app ? String(app.textContent || '').trim().length : -1,
                    bootStarted: !!window.__edumindBootStarted,
                    bootMounted: !!window.__edumindBootMounted,
                    bootTrace: Array.isArray(window.__edumindBootTrace) ? window.__edumindBootTrace.slice(-12) : [],
                    moduleScriptSrc: (function() {
                      var node = document.querySelector('script[src]');
                      return node ? String(node.getAttribute('src') || '') : '<missing>';
                    })(),
                    bodyChildCount: document.body ? document.body.childElementCount : -1
                  };
                  post('probe', JSON.stringify(payload));
                  return payload;
                } catch (e) {
                  post('probe.error', (e && (e.stack || e.message)) || String(e));
                  return null;
                }
              };
              window.addEventListener('error', function(e) {
                post('window.error', (e && e.message) || 'Unknown error');
              });
              window.addEventListener('unhandledrejection', function(e) {
                post('unhandledrejection', (e && e.reason && (e.reason.stack || e.reason.message)) || String(e && e.reason || 'Unknown rejection'));
              });
            })();
        """

        static let mountWatchdogScript = """
            (function() {
              function renderBootHint(reason) {
                try {
                  var app = document.getElementById('app');
                  if (!app) return;
                  if (app.childElementCount > 0 || app.textContent.trim().length > 0) return;
                  var panel = document.createElement('div');
                  panel.style.cssText = [
                    'margin:16px',
                    'padding:16px',
                    'border-radius:14px',
                    'background:#fff7ed',
                    'border:1px solid #fdba74',
                    'color:#9a3412',
                    'font-family:-apple-system,BlinkMacSystemFont,sans-serif',
                    'line-height:1.6'
                  ].join(';');
                  panel.innerHTML =
                    '<h3 style="margin:0 0 8px;">页面未完成挂载</h3>' +
                    '<div style="font-size:14px;">' + reason + '</div>' +
                    '<div style="margin-top:8px;font-size:12px;white-space:pre-wrap;">请检查 Xcode 控制台中的 [EduMindWeb] 日志。</div>';
                  app.appendChild(panel);
                  if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.edumindLog) {
                    window.webkit.messageHandlers.edumindLog.postMessage({
                      level: 'mount.watchdog',
                      payload: reason
                    });
                  }
                } catch (e) {}
              }

              window.setTimeout(function() {
                try {
                  var app = document.getElementById('app');
                  if (!app) {
                    renderBootHint('index.html 已加载，但页面缺少 #app 节点。');
                    return;
                  }
                  if (app.childElementCount > 0 || app.textContent.trim().length > 0) return;
                  var script = document.querySelector('script[src]');
                  var scriptSrc = script ? (script.getAttribute('src') || '<inline>') : '<missing>';
                  renderBootHint('根节点仍为空，前端脚本可能未执行。script src=' + scriptSrc);
                } catch (e) {
                  renderBootHint('挂载检查异常：' + (e && (e.stack || e.message) || String(e)));
                }
              }, 2500);
            })();
        """

        private var loadTimeoutWorkItem: DispatchWorkItem?
        private var probeWorkItems: [DispatchWorkItem] = []

        func startLoadTimeout(for webView: WKWebView) {
            loadTimeoutWorkItem?.cancel()
            let work = DispatchWorkItem { [weak self, weak webView] in
                guard let webView else { return }
                self?.showErrorPage(
                    in: webView,
                    title: "页面加载超时",
                    details: "请执行：bash ios-app/sync_ios_web_assets.sh\n若仍失败，请检查 WebAssets/index.html 与 index.js 是否在 App 包内。"
                )
            }
            loadTimeoutWorkItem = work
            DispatchQueue.main.asyncAfter(deadline: .now() + 6, execute: work)
        }

        private func finishLoad() {
            loadTimeoutWorkItem?.cancel()
            loadTimeoutWorkItem = nil
        }

        private func scheduleBootProbes(for webView: WKWebView) {
            probeWorkItems.forEach { $0.cancel() }
            probeWorkItems.removeAll()

            let delays: [TimeInterval] = [0.2, 1.0, 2.5]
            for delay in delays {
                let work = DispatchWorkItem { [weak self, weak webView] in
                    guard let self, let webView else { return }
                    self.runProbe(in: webView, stage: "didFinish+\(delay)s")
                }
                probeWorkItems.append(work)
                DispatchQueue.main.asyncAfter(deadline: .now() + delay, execute: work)
            }
        }

        private func runProbe(in webView: WKWebView, stage: String) {
            let escapedStage = stage.replacingOccurrences(of: "'", with: "\\'")
            let js = """
            (function() {
              try {
                if (!window.__edumindNativeProbe) return 'null';
                return JSON.stringify(window.__edumindNativeProbe('\(escapedStage)'));
              } catch (e) {
                return JSON.stringify({
                  stage: '\(escapedStage)',
                  probeError: String((e && (e.stack || e.message)) || e)
                });
              }
            })();
            """
            webView.evaluateJavaScript(js) { result, error in
                if let error {
                    NSLog("[EduMindWeb][probe.native.error] stage=%@ error=%@", stage, error.localizedDescription)
                    return
                }
                NSLog("[EduMindWeb][probe.native] stage=%@ payload=%@", stage, String(describing: result ?? "<nil>"))
            }
        }

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard message.name == Self.logHandlerName else { return }
            if let body = message.body as? [String: Any] {
                let level = String(describing: body["level"] ?? "log")
                let payload = String(describing: body["payload"] ?? "")
                NSLog("[EduMindWeb][%@] %@", level, payload)
                return
            }
            NSLog("[EduMindWeb] %@", String(describing: message.body))
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            finishLoad()
            NSLog("[EduMindWeb] didFinish navigation: %@", webView.url?.absoluteString ?? "<nil>")
            scheduleBootProbes(for: webView)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            finishLoad()
            NSLog("[EduMindWeb] didFail navigation: %@", error.localizedDescription)
            showErrorPage(in: webView, title: "页面加载失败", details: error.localizedDescription)
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            finishLoad()
            NSLog("[EduMindWeb] didFailProvisionalNavigation: %@", error.localizedDescription)
            showErrorPage(in: webView, title: "页面初始化失败", details: error.localizedDescription)
        }

        private func showErrorPage(in webView: WKWebView, title: String, details: String) {
            let html = """
            <div style="font-family:-apple-system;padding:20px;color:#111827;">
              <h2 style="margin:0 0 10px;">\(title)</h2>
              <pre style="white-space:pre-wrap;background:#f3f4f6;border-radius:10px;padding:12px;">\(details)</pre>
            </div>
            """
            webView.loadHTMLString(html, baseURL: nil)
        }
    }
}

struct ContentView: View {
    var body: some View {
        H5WebView()
            .ignoresSafeArea()
    }
}

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        ContentView()
            .previewDisplayName("EduMind iPhone")
            .previewDevice("iPhone 16 Pro")
    }
}
