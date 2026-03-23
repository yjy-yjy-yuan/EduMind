//
//  ContentView.swift
//  EduMindIOS
//
//  Created by yuan on 2026/3/12.
//

@preconcurrency import AVFoundation
import Foundation
import OSLog
import Speech
import SwiftUI
import UniformTypeIdentifiers
import UIKit
import WebKit

private enum EduMindLogLevel {
    case debug
    case info
    case notice
    case error
    case fault
}

private enum EduMindLog {
    private static let logger = Logger(
        subsystem: Bundle.main.bundleIdentifier ?? "EduMindIOS",
        category: "EduMindWeb"
    )

    private static func prefix(for level: EduMindLogLevel) -> String {
        switch level {
        case .debug:
            return "[DEBUG]"
        case .info:
            return "[INFO]"
        case .notice:
            return "[NOTICE]"
        case .error:
            return "[ERROR]"
        case .fault:
            return "[FAULT]"
        }
    }

    private static func line(for level: EduMindLogLevel, scope: String?, message: String) -> String {
        if message.hasPrefix("[") {
            return message
        }
        let scopeText = scope.map { "[\($0)]" } ?? ""
        return "\(prefix(for: level))\(scopeText) \(message)"
    }

    static func write(_ level: EduMindLogLevel, scope: String? = nil, _ message: String) {
        let line = line(for: level, scope: scope, message: message)
        switch level {
        case .debug:
            logger.debug("\(line, privacy: .public)")
        case .info:
            logger.info("\(line, privacy: .public)")
        case .notice:
            logger.notice("\(line, privacy: .public)")
        case .error:
            logger.error("\(line, privacy: .public)")
        case .fault:
            logger.fault("\(line, privacy: .public)")
        }
        #if DEBUG
        print(line)
        #endif
    }

    static func debug(_ scope: String, _ message: String) {
        write(.debug, scope: scope, message)
    }

    static func info(_ scope: String, _ message: String) {
        write(.info, scope: scope, message)
    }

    static func notice(_ scope: String, _ message: String) {
        write(.notice, scope: scope, message)
    }

    static func error(_ scope: String, _ message: String) {
        write(.error, scope: scope, message)
    }

    static func fault(_ scope: String, _ message: String) {
        write(.fault, scope: scope, message)
    }
}

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
    private static let nativeConfigScript = """
        (function() {
          window.__edumindNativeConfig = Object.assign({}, window.__edumindNativeConfig || {}, \(nativeConfigJSONString()));
        })();
    """

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.defaultWebpagePreferences.allowsContentJavaScript = true
        configuration.allowsInlineMediaPlayback = true
        configuration.allowsAirPlayForMediaPlayback = true
        configuration.allowsPictureInPictureMediaPlayback = true
        configuration.mediaTypesRequiringUserActionForPlayback = []
        configuration.userContentController.add(context.coordinator, name: Coordinator.logHandlerName)
        configuration.userContentController.add(context.coordinator, name: Coordinator.nativeBridgeHandlerName)
        configuration.userContentController.addUserScript(WKUserScript(
            source: Self.nativeConfigScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
        configuration.userContentController.addUserScript(WKUserScript(
            source: Coordinator.nativeBridgeScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        ))
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
        context.coordinator.attach(webView: webView)
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
        uiView.configuration.userContentController.removeScriptMessageHandler(forName: Coordinator.nativeBridgeHandlerName)
    }

    private func loadContent(into webView: WKWebView) {
        guard let indexURL = WebAssets.indexURL() else {
            EduMindLog.error("WebView", "index.html not found in bundle. resourceURL=\(Bundle.main.resourceURL?.path ?? "<nil>")")
            webView.loadHTMLString(
                "<h2 style=\"font-family:-apple-system\">未找到前端资源</h2><p style=\"font-family:-apple-system\">请执行：bash ios-app/sync_ios_web_assets.sh</p>",
                baseURL: nil
            )
            return
        }

        let allowedPath = indexURL.deletingLastPathComponent()
        EduMindLog.info("WebView", "loading index from \(indexURL.path)")
        EduMindLog.info("WebView", "allowing read access to \(allowedPath.path)")
        EduMindLog.debug("WebView", "bundle resourceURL=\(Bundle.main.resourceURL?.path ?? "<nil>")")
        do {
            let html = try String(contentsOf: indexURL, encoding: .utf8)
            EduMindLog.debug("WebView", "index.html chars=\(html.count)")
            if usesLegacyAbsoluteAssetPaths(in: html) {
                EduMindLog.error("WebView", "detected legacy absolute asset paths in \(indexURL.path)")
                webView.loadHTMLString(
                    "<h2 style=\"font-family:-apple-system\">前端资源路径不兼容</h2><p style=\"font-family:-apple-system\">请执行：bash ios-app/sync_ios_web_assets.sh</p>",
                    baseURL: nil
                )
                return
            }
            if usesWebBuildAssetLayout(in: html) {
                EduMindLog.error("WebView", "detected web build asset layout in \(indexURL.path)")
                webView.loadHTMLString(
                    "<h2 style=\"font-family:-apple-system\">检测到错误的前端构建产物</h2><p style=\"font-family:-apple-system\">当前 iOS 容器需要 index.js/index.css 结构，请执行：bash ios-app/sync_ios_web_assets.sh</p>",
                    baseURL: nil
                )
                return
            }
        } catch {
            // Ignore and continue with direct file loading.
        }

        webView.loadFileURL(indexURL, allowingReadAccessTo: allowedPath)
        EduMindLog.info("WebView", "loadFileURL requested")
    }

    private static func nativeConfigJSONString() -> String {
        let configuredAPIBase = (
            Bundle.main.object(forInfoDictionaryKey: "EDUMIND_API_BASE_URL") as? String
        )?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let apiBase = configuredAPIBase.isEmpty ? "http://yuandeMacBook-Pro.local:2004" : configuredAPIBase
        EduMindLog.info(
            "WebView",
            "native api base=\(apiBase) | source=\(configuredAPIBase.isEmpty ? "fallback-local-hostname" : "info-plist")"
        )

        let payload: [String: String] = [
            "apiBaseUrl": apiBase
        ]

        guard
            let data = try? JSONSerialization.data(withJSONObject: payload, options: []),
            let text = String(data: data, encoding: .utf8)
        else {
            return #"{"apiBaseUrl":""}"#
        }
        return text
    }

    private func usesLegacyAbsoluteAssetPaths(in html: String) -> Bool {
        html.contains("src=\"/") || html.contains("href=\"/") || html.contains("src='/") || html.contains("href='/")
    }

    private func usesWebBuildAssetLayout(in html: String) -> Bool {
        html.contains("src=\"./assets/index-") || html.contains("src='./assets/index-")
    }

    final class Coordinator: NSObject, WKNavigationDelegate, WKScriptMessageHandler {
        private struct NativeSelectedVideo {
            let taskId: String
            let workingURL: URL
            let fileName: String
            let fileSize: Int
            let fileExt: String
        }

        private struct NativeTranscriptionResult {
            let text: String
            let segments: [[String: Any]]
            let localeIdentifier: String
        }

        private enum NativeOfflineTranscriptionError: LocalizedError {
            case presenterUnavailable
            case pickerBusy
            case pickerCancelled
            case invalidSelection
            case audioExtractionUnavailable
            case speechAuthorizationDenied
            case recognizerUnavailable
            case onDeviceRecognitionUnavailable
            case emptyTranscript

            var errorDescription: String? {
                switch self {
                case .presenterUnavailable:
                    return "当前 iOS 容器无法打开本地视频选择器"
                case .pickerBusy:
                    return "已有一个原生离线转录任务正在选择视频，请稍后再试"
                case .pickerCancelled:
                    return "已取消本地视频选择"
                case .invalidSelection:
                    return "未能读取所选视频文件"
                case .audioExtractionUnavailable:
                    return "当前视频无法提取音频，无法进行本地转录"
                case .speechAuthorizationDenied:
                    return "未获得语音识别权限，无法进行本地离线转录"
                case .recognizerUnavailable:
                    return "当前设备不支持所选语言的语音识别"
                case .onDeviceRecognitionUnavailable:
                    return "当前设备或当前语言暂不支持 Apple 端侧离线识别"
                case .emptyTranscript:
                    return "本地识别已完成，但未生成可用文本"
                }
            }
        }

        static let logHandlerName = "edumindLog"
        static let nativeBridgeHandlerName = "edumindNative"

        static let nativeBridgeScript = """
            (function() {
              if (window.__edumindNativeBridge) return;

              var handlerName = 'edumindNative';
              var version = '1';
              var eventPrefix = 'edumind-native:';
              var seq = 0;
              var pending = Object.create(null);

              function dispatchEvent(name, detail) {
                window.dispatchEvent(new CustomEvent(eventPrefix + name, {
                  detail: detail || {}
                }));
              }

              function send(action, payload) {
                return new Promise(function(resolve, reject) {
                  var requestId = 'native-' + Date.now() + '-' + (++seq);
                  pending[requestId] = { resolve: resolve, reject: reject };
                  try {
                    window.webkit.messageHandlers[handlerName].postMessage({
                      requestId: requestId,
                      action: String(action || ''),
                      payload: payload || {}
                    });
                  } catch (error) {
                    delete pending[requestId];
                    reject(error);
                  }
                });
              }

              window.__edumindHandleNativeResponse = function(message) {
                var body = message || {};
                var requestId = String(body.requestId || '');
                var entry = pending[requestId];
                if (!entry) return false;
                delete pending[requestId];
                if (body.success === false) {
                  entry.reject(new Error(String(body.error || 'Native bridge request failed')));
                  return true;
                }
                entry.resolve(body.payload || {});
                return true;
              };

              window.__edumindReceiveNativeEvent = function(name, payload) {
                dispatchEvent(String(name || 'event'), payload || {});
                return true;
              };

              window.__edumindNativeBridge = {
                version: version,
                isAvailable: function() {
                  return true;
                },
                send: send,
                on: function(name, listener) {
                  var eventName = eventPrefix + String(name || '');
                  window.addEventListener(eventName, listener);
                  return function() {
                    window.removeEventListener(eventName, listener);
                  };
                }
              };

              dispatchEvent('bridge-ready', {
                handlerName: handlerName,
                version: version
              });
            })();
        """

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
        private weak var webView: WKWebView?
        private var pendingVideoPickerRequestId: String?
        private var pendingVideoPickerPayload: [String: Any] = [:]
        private var activeOfflineTasks: [String: Task<Void, Never>] = [:]

        func attach(webView: WKWebView) {
            self.webView = webView
        }

        func startLoadTimeout(for webView: WKWebView) {
            loadTimeoutWorkItem?.cancel()
            EduMindLog.info("Lifecycle", "start load timeout watchdog")
            EduMindLog.debug("Lifecycle", "watchdog target=\(String(describing: webView.url?.absoluteString ?? "<pending>"))")
            let work = DispatchWorkItem { [weak self, weak webView] in
                guard let webView else { return }
                EduMindLog.error("Lifecycle", "load timeout watchdog fired")
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
            EduMindLog.info("Lifecycle", "finish load timeout watchdog")
        }

        private func scheduleBootProbes(for webView: WKWebView) {
            probeWorkItems.forEach { $0.cancel() }
            probeWorkItems.removeAll()

            let delays: [TimeInterval] = [0.2, 1.0, 2.5]
            EduMindLog.debug("Probe", "schedule boot probes delays=\(delays.map { String($0) }.joined(separator: ","))")
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
            EduMindLog.debug("Probe", "run probe stage=\(stage)")
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
                    EduMindLog.error("Probe", "stage=\(stage) error=\(error.localizedDescription)")
                    return
                }
                EduMindLog.info("Probe", "stage=\(stage) payload=\(String(describing: result ?? "<nil>"))")
            }
        }

        private func nativeLogLevel(for level: String) -> EduMindLogLevel {
            switch level {
            case "console.debug":
                return .debug
            case "console.info", "probe", "probe.native", "lifecycle.info":
                return .info
            case "console.log", "mount.watchdog":
                return .notice
            case "console.warn":
                return .notice
            case "console.error", "window.error", "unhandledrejection", "probe.error":
                return .error
            default:
                return .notice
            }
        }

        private func nativeBridgeCapabilities() -> [String: Any] {
            [
                "platform": "ios",
                "bridgeVersion": 1,
                "supportsOfflineTranscription": true,
                "supportsNativeVideoPicker": true,
                "transcriptionEngine": "apple_speech_on_device",
                "requiresSpeechAuthorization": true,
                "availableActions": [
                    "ping",
                    "getCapabilities",
                    "startOfflineTranscription"
                ]
            ]
        }

        private func respondToNativeRequest(
            requestId: String,
            success: Bool,
            payload: [String: Any] = [:],
            errorMessage: String? = nil
        ) {
            var responseBody: [String: Any] = [
                "requestId": requestId,
                "success": success,
                "payload": payload
            ]
            responseBody["error"] = errorMessage ?? NSNull()

            guard
                let webView,
                let data = try? JSONSerialization.data(
                    withJSONObject: responseBody,
                    options: []
                ),
                let json = String(data: data, encoding: .utf8)
            else {
                EduMindLog.error("Bridge", "failed to serialize native bridge response for requestId=\(requestId)")
                return
            }

            let js = """
            (function() {
              if (typeof window.__edumindHandleNativeResponse === 'function') {
                window.__edumindHandleNativeResponse(\(json));
              }
            })();
            """
            DispatchQueue.main.async {
                webView.evaluateJavaScript(js) { _, error in
                    if let error {
                        EduMindLog.error("Bridge", "native response delivery failed requestId=\(requestId) error=\(error.localizedDescription)")
                    }
                }
            }
        }

        private func sendNativeEvent(name: String, payload: [String: Any]) {
            guard
                let webView,
                let data = try? JSONSerialization.data(withJSONObject: payload, options: []),
                let json = String(data: data, encoding: .utf8)
            else {
                EduMindLog.error("Bridge", "failed to serialize native event payload name=\(name)")
                return
            }

            let escapedName = name
                .replacingOccurrences(of: "\\", with: "\\\\")
                .replacingOccurrences(of: "'", with: "\\'")

            let js = """
            (function() {
              if (typeof window.__edumindReceiveNativeEvent === 'function') {
                window.__edumindReceiveNativeEvent('\(escapedName)', \(json));
              }
            })();
            """
            DispatchQueue.main.async {
                webView.evaluateJavaScript(js) { _, error in
                    if let error {
                        EduMindLog.error("Bridge", "native event delivery failed name=\(name) error=\(error.localizedDescription)")
                    }
                }
            }
        }

        private func topViewController() -> UIViewController? {
            if let root = webView?.window?.rootViewController {
                var current: UIViewController? = root
                while let presented = current?.presentedViewController {
                    current = presented
                }
                return current
            }

            let root = UIApplication.shared.connectedScenes
                .compactMap { $0 as? UIWindowScene }
                .flatMap(\.windows)
                .first(where: \.isKeyWindow)?
                .rootViewController

            var current = root
            while let presented = current?.presentedViewController {
                current = presented
            }
            return current
        }

        private func normalizeSpeechLocaleIdentifier(from payload: [String: Any]) -> String {
            let raw = String(describing: payload["language"] ?? "").trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
            if raw.isEmpty || raw == "auto" {
                return Locale.preferredLanguages.first ?? "zh-CN"
            }

            switch raw {
            case "zh", "zh-cn", "zh_hans", "zh-hans", "chinese":
                return "zh-CN"
            case "zh-tw", "zh_hant", "zh-hant":
                return "zh-TW"
            case "en", "en-us", "english":
                return "en-US"
            case "ja", "ja-jp", "japanese":
                return "ja-JP"
            default:
                return raw
            }
        }

        private func createWorkingDirectory() throws -> URL {
            let base = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first
                ?? FileManager.default.temporaryDirectory
            let dir = base.appendingPathComponent("OfflineTranscription", isDirectory: true)
            try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            return dir
        }

        private func copySelectedVideoToWorkingDirectory(from sourceURL: URL) throws -> URL {
            let dir = try createWorkingDirectory()
            let ext = sourceURL.pathExtension.isEmpty ? "mov" : sourceURL.pathExtension.lowercased()
            let destinationURL = dir.appendingPathComponent("\(UUID().uuidString).\(ext)")
            if FileManager.default.fileExists(atPath: destinationURL.path) {
                try FileManager.default.removeItem(at: destinationURL)
            }
            try FileManager.default.copyItem(at: sourceURL, to: destinationURL)
            return destinationURL
        }

        private func buildSelectedVideoMetadata(from sourceURL: URL) throws -> NativeSelectedVideo {
            let workingURL = try copySelectedVideoToWorkingDirectory(from: sourceURL)
            let values = try workingURL.resourceValues(forKeys: [.nameKey, .fileSizeKey])
            let fileName = values.name ?? sourceURL.lastPathComponent
            let fileSize = values.fileSize ?? 0
            let fileExt = workingURL.pathExtension.lowercased()
            return NativeSelectedVideo(
                taskId: UUID().uuidString,
                workingURL: workingURL,
                fileName: fileName,
                fileSize: fileSize,
                fileExt: fileExt
            )
        }

        private func startOfflineTranscriptionFlow(requestId: String, payload: [String: Any]) {
            guard pendingVideoPickerRequestId == nil else {
                respondToNativeRequest(
                    requestId: requestId,
                    success: false,
                    errorMessage: NativeOfflineTranscriptionError.pickerBusy.localizedDescription
                )
                return
            }

            guard let presenter = topViewController() else {
                respondToNativeRequest(
                    requestId: requestId,
                    success: false,
                    errorMessage: NativeOfflineTranscriptionError.presenterUnavailable.localizedDescription
                )
                return
            }

            pendingVideoPickerRequestId = requestId
            pendingVideoPickerPayload = payload

            let picker = UIDocumentPickerViewController(
                forOpeningContentTypes: [UTType.movie, UTType.video],
                asCopy: true
            )
            picker.delegate = self
            picker.allowsMultipleSelection = false
            presenter.present(picker, animated: true)
        }

        private func clearPendingVideoPickerState() {
            pendingVideoPickerRequestId = nil
            pendingVideoPickerPayload = [:]
        }

        private func sendOfflineProgressEvent(
            taskId: String,
            fileName: String,
            fileSize: Int,
            phase: String,
            progress: Int,
            message: String,
            localeIdentifier: String = ""
        ) {
            sendNativeEvent(name: "offline-transcription-progress", payload: [
                "taskId": taskId,
                "fileName": fileName,
                "fileSize": fileSize,
                "phase": phase,
                "status": phase,
                "progress": progress,
                "message": message,
                "locale": localeIdentifier,
                "engine": "apple_speech_on_device"
            ])
        }

        private func sendOfflineFailureEvent(
            taskId: String,
            fileName: String,
            fileSize: Int,
            message: String
        ) {
            sendNativeEvent(name: "offline-transcription-failed", payload: [
                "taskId": taskId,
                "fileName": fileName,
                "fileSize": fileSize,
                "status": "failed",
                "progress": 0,
                "message": message,
                "engine": "apple_speech_on_device"
            ])
        }

        private func requestSpeechAuthorization() async -> SFSpeechRecognizerAuthorizationStatus {
            await withCheckedContinuation { continuation in
                SFSpeechRecognizer.requestAuthorization { status in
                    continuation.resume(returning: status)
                }
            }
        }

        private func exportAudioTrack(from videoURL: URL, taskId: String) async throws -> URL {
            let asset = AVURLAsset(url: videoURL)
            guard let exportSession = AVAssetExportSession(asset: asset, presetName: AVAssetExportPresetAppleM4A) else {
                throw NativeOfflineTranscriptionError.audioExtractionUnavailable
            }

            let workingDirectory = try createWorkingDirectory()
            let outputURL = workingDirectory.appendingPathComponent("\(taskId).m4a")
            if FileManager.default.fileExists(atPath: outputURL.path) {
                try FileManager.default.removeItem(at: outputURL)
            }

            exportSession.outputURL = outputURL
            exportSession.outputFileType = .m4a
            exportSession.shouldOptimizeForNetworkUse = false

            return try await withCheckedThrowingContinuation { continuation in
                exportSession.exportAsynchronously {
                    switch exportSession.status {
                    case .completed:
                        continuation.resume(returning: outputURL)
                    case .failed:
                        continuation.resume(throwing: exportSession.error ?? NativeOfflineTranscriptionError.audioExtractionUnavailable)
                    case .cancelled:
                        continuation.resume(throwing: NativeOfflineTranscriptionError.pickerCancelled)
                    default:
                        continuation.resume(throwing: exportSession.error ?? NativeOfflineTranscriptionError.audioExtractionUnavailable)
                    }
                }
            }
        }

        private func buildSpeechRecognizer(localeIdentifier: String) throws -> SFSpeechRecognizer {
            let candidates = [
                localeIdentifier,
                Locale.preferredLanguages.first ?? "",
                "zh-CN",
                "en-US"
            ].filter { !$0.isEmpty }

            for candidate in candidates {
                if let recognizer = SFSpeechRecognizer(locale: Locale(identifier: candidate)) {
                    return recognizer
                }
            }

            throw NativeOfflineTranscriptionError.recognizerUnavailable
        }

        private func transcribeAudioFile(
            taskId: String,
            audioURL: URL,
            fileName: String,
            fileSize: Int,
            localeIdentifier: String
        ) async throws -> NativeTranscriptionResult {
            let authorizationStatus = await requestSpeechAuthorization()
            guard authorizationStatus == .authorized else {
                throw NativeOfflineTranscriptionError.speechAuthorizationDenied
            }

            let recognizer = try buildSpeechRecognizer(localeIdentifier: localeIdentifier)
            guard recognizer.supportsOnDeviceRecognition else {
                throw NativeOfflineTranscriptionError.onDeviceRecognitionUnavailable
            }

            let request = SFSpeechURLRecognitionRequest(url: audioURL)
            request.requiresOnDeviceRecognition = true
            request.shouldReportPartialResults = true

            return try await withCheckedThrowingContinuation { continuation in
                var hasResumed = false
                var recognitionTask: SFSpeechRecognitionTask?

                recognitionTask = recognizer.recognitionTask(with: request) { [weak self] result, error in
                    guard let self else { return }

                    if let result {
                        let partialText = result.bestTranscription.formattedString.trimmingCharacters(in: .whitespacesAndNewlines)
                        if !partialText.isEmpty {
                            self.sendOfflineProgressEvent(
                                taskId: taskId,
                                fileName: fileName,
                                fileSize: fileSize,
                                phase: "transcribing",
                                progress: result.isFinal ? 95 : 75,
                                message: "正在进行本地语音识别",
                                localeIdentifier: recognizer.locale.identifier
                            )
                        }

                        if result.isFinal && !hasResumed {
                            hasResumed = true
                            let text = partialText
                            let segments = result.bestTranscription.segments.map { segment in
                                [
                                    "text": segment.substring,
                                    "start": segment.timestamp,
                                    "duration": segment.duration,
                                    "confidence": segment.confidence
                                ]
                            }
                            if text.isEmpty {
                                continuation.resume(throwing: NativeOfflineTranscriptionError.emptyTranscript)
                            } else {
                                continuation.resume(returning: NativeTranscriptionResult(
                                    text: text,
                                    segments: segments,
                                    localeIdentifier: recognizer.locale.identifier
                                ))
                            }
                            recognitionTask?.cancel()
                            recognitionTask = nil
                            return
                        }
                    }

                    if let error, !hasResumed {
                        hasResumed = true
                        continuation.resume(throwing: error)
                        recognitionTask?.cancel()
                        recognitionTask = nil
                    }
                }
            }
        }

        private func runOfflineTranscription(task: NativeSelectedVideo, payload: [String: Any]) async {
            let localeIdentifier = normalizeSpeechLocaleIdentifier(from: payload)

            do {
                sendOfflineProgressEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    phase: "preparing",
                    progress: 5,
                    message: "已选择本地视频，准备提取音频",
                    localeIdentifier: localeIdentifier
                )

                sendOfflineProgressEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    phase: "extracting",
                    progress: 25,
                    message: "正在提取本地视频音频",
                    localeIdentifier: localeIdentifier
                )
                let audioURL = try await exportAudioTrack(from: task.workingURL, taskId: task.taskId)

                sendOfflineProgressEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    phase: "transcribing",
                    progress: 55,
                    message: "音频提取完成，开始本地离线识别",
                    localeIdentifier: localeIdentifier
                )
                let transcription = try await transcribeAudioFile(
                    taskId: task.taskId,
                    audioURL: audioURL,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    localeIdentifier: localeIdentifier
                )

                sendNativeEvent(name: "offline-transcription-completed", payload: [
                    "taskId": task.taskId,
                    "fileName": task.fileName,
                    "fileSize": task.fileSize,
                    "fileExt": task.fileExt,
                    "status": "completed",
                    "progress": 100,
                    "message": "本地离线转录完成",
                    "locale": transcription.localeIdentifier,
                    "engine": "apple_speech_on_device",
                    "transcriptText": transcription.text,
                    "segments": transcription.segments
                ])
            } catch {
                EduMindLog.error("OfflineTranscription", "taskId=\(task.taskId) failed error=\(error.localizedDescription)")
                sendOfflineFailureEvent(
                    taskId: task.taskId,
                    fileName: task.fileName,
                    fileSize: task.fileSize,
                    message: error.localizedDescription
                )
            }

            activeOfflineTasks[task.taskId] = nil
        }

        private func handleNativeBridgeMessage(_ body: [String: Any]) {
            let requestId = String(describing: body["requestId"] ?? "")
            let action = String(describing: body["action"] ?? "")
            let payload = body["payload"] as? [String: Any] ?? [:]

            guard !requestId.isEmpty else {
                EduMindLog.error("Bridge", "received native bridge message without requestId")
                return
            }

            EduMindLog.info("Bridge", "native action=\(action) payload=\(payload)")

            switch action {
            case "ping":
                let formatter = ISO8601DateFormatter()
                respondToNativeRequest(
                    requestId: requestId,
                    success: true,
                    payload: [
                        "platform": "ios",
                        "bridgeVersion": 1,
                        "timestamp": formatter.string(from: Date())
                    ]
                )
            case "getCapabilities":
                respondToNativeRequest(
                    requestId: requestId,
                    success: true,
                    payload: nativeBridgeCapabilities()
                )
            case "startOfflineTranscription":
                startOfflineTranscriptionFlow(requestId: requestId, payload: payload)
            default:
                respondToNativeRequest(
                    requestId: requestId,
                    success: false,
                    errorMessage: "Unsupported native bridge action: \(action)"
                )
            }
        }

        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            if message.name == Self.logHandlerName {
                if let body = message.body as? [String: Any] {
                    let level = String(describing: body["level"] ?? "log")
                    let payload = String(describing: body["payload"] ?? "")
                    EduMindLog.write(nativeLogLevel(for: level), payload)
                    return
                }
                EduMindLog.notice("Bridge", String(describing: message.body))
                return
            }

            guard message.name == Self.nativeBridgeHandlerName else { return }
            guard let body = message.body as? [String: Any] else {
                EduMindLog.error("Bridge", "received invalid native bridge payload: \(String(describing: message.body))")
                return
            }
            handleNativeBridgeMessage(body)
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            finishLoad()
            EduMindLog.info("WebView", "didFinish navigation: \(webView.url?.absoluteString ?? "<nil>")")
            scheduleBootProbes(for: webView)
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            finishLoad()
            EduMindLog.error("WebView", "didFail navigation: \(error.localizedDescription)")
            showErrorPage(in: webView, title: "页面加载失败", details: error.localizedDescription)
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            finishLoad()
            EduMindLog.error("WebView", "didFailProvisionalNavigation: \(error.localizedDescription)")
            showErrorPage(in: webView, title: "页面初始化失败", details: error.localizedDescription)
        }

        private func showErrorPage(in webView: WKWebView, title: String, details: String) {
            EduMindLog.error("WebView", "showErrorPage title=\(title) details=\(details)")
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

extension H5WebView.Coordinator: UIDocumentPickerDelegate {
    func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController) {
        guard let requestId = pendingVideoPickerRequestId else { return }
        clearPendingVideoPickerState()
        respondToNativeRequest(
            requestId: requestId,
            success: false,
            errorMessage: NativeOfflineTranscriptionError.pickerCancelled.localizedDescription
        )
    }

    func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
        guard let requestId = pendingVideoPickerRequestId else { return }
        let payload = pendingVideoPickerPayload
        clearPendingVideoPickerState()

        guard let sourceURL = urls.first else {
            respondToNativeRequest(
                requestId: requestId,
                success: false,
                errorMessage: NativeOfflineTranscriptionError.invalidSelection.localizedDescription
            )
            return
        }

        do {
            let task = try buildSelectedVideoMetadata(from: sourceURL)
            respondToNativeRequest(
                requestId: requestId,
                success: true,
                payload: [
                    "taskId": task.taskId,
                    "fileName": task.fileName,
                    "fileSize": task.fileSize,
                    "fileExt": task.fileExt,
                    "status": "preparing",
                    "engine": "apple_speech_on_device",
                    "message": "已选择本地视频，开始本地离线转录"
                ]
            )

            let work = Task { [weak self] in
                guard let self else { return }
                await self.runOfflineTranscription(task: task, payload: payload)
            }
            activeOfflineTasks[task.taskId] = work
        } catch {
            respondToNativeRequest(
                requestId: requestId,
                success: false,
                errorMessage: error.localizedDescription
            )
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
